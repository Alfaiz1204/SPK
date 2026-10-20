"""
Analytic Hierarchy Process: menurunkan bobot kriteria dari penilaian manusia.

AHP dipakai, bukan pembobotan objektif seperti Entropy atau CRITIC, karena
pertanyaan "seberapa penting kebutuhan sosial dibanding risiko gagal bayar"
tidak punya jawaban di dalam data. Itu pertanyaan kebijakan. Entropy hanya
mengukur sebaran nilai kriteria, dan sebaran tidak sama dengan kepentingan.

Consistency Ratio bukan formalitas. CR > 0.10 berarti penilaian pengambil
keputusan saling bertentangan, misalnya A lebih penting dari B, B lebih
penting dari C, tetapi C lebih penting dari A. Bobot dari matriks semacam itu
tidak boleh dipakai, dan wawancara harus diulang.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .. import config as cfg


@dataclass
class HasilAHP:
    bobot: np.ndarray
    lambda_max: float
    ci: float
    cr: float
    konsisten: bool
    matriks: np.ndarray

    def ringkas(self, nama_kriteria: list[str]) -> str:
        baris = ["BOBOT KRITERIA (AHP)", "=" * 52]
        for nama, w in zip(nama_kriteria, self.bobot):
            bar = "#" * int(round(w * 60))
            baris.append(f"  {nama:<28} {w:.4f}  {bar}")
        baris += [
            "-" * 52,
            f"  lambda_max = {self.lambda_max:.4f}",
            f"  CI         = {self.ci:.4f}",
            f"  CR         = {self.cr:.4f}  (ambang {cfg.CR_THRESHOLD})",
            f"  Status     = {'KONSISTEN' if self.konsisten else 'TIDAK KONSISTEN'}",
        ]
        return "\n".join(baris)


def validasi_matriks(matriks: np.ndarray) -> None:
    """Pastikan matriks persegi, positif, dan resiprokal."""
    n, m = matriks.shape
    if n != m:
        raise ValueError(f"Matriks harus persegi, diterima {n}x{m}.")
    if np.any(matriks <= 0):
        raise ValueError("Seluruh elemen matriks harus positif.")
    if not np.allclose(np.diag(matriks), 1.0):
        raise ValueError("Diagonal matriks harus bernilai 1.")
    # Sifat resiprokal: a_ij harus sama dengan 1 / a_ji.
    if not np.allclose(matriks, 1.0 / matriks.T, rtol=1e-6):
        raise ValueError(
            "Matriks tidak resiprokal: terdapat pasangan a_ij != 1/a_ji. "
            "Periksa kembali pengisian matriks di config.AHP_PAIRWISE."
        )


def hitung_bobot(matriks: np.ndarray | list) -> HasilAHP:
    """
    Turunkan vektor bobot dan ukur konsistensinya.

    Bobot diambil dari eigenvector utama (metode eigenvalue Saaty), bukan
    rata-rata kolom ternormalisasi. Rata-rata kolom hanya aproksimasi yang
    tepat pada matriks konsisten sempurna; selisihnya terasa justru ketika
    CR mendekati ambang, yaitu saat angkanya paling perlu dipercaya.
    """
    A = np.asarray(matriks, dtype=float)
    validasi_matriks(A)
    n = A.shape[0]

    nilai_eigen, vektor_eigen = np.linalg.eig(A)
    idx = int(np.argmax(nilai_eigen.real))
    lambda_max = float(nilai_eigen[idx].real)

    w = np.abs(vektor_eigen[:, idx].real)
    w = w / w.sum()

    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    ri = cfg.SAATY_RI[n - 1] if n <= len(cfg.SAATY_RI) else 1.49
    cr = ci / ri if ri > 0 else 0.0

    return HasilAHP(
        bobot=w,
        lambda_max=lambda_max,
        ci=float(ci),
        cr=float(cr),
        konsisten=bool(cr <= cfg.CR_THRESHOLD),
        matriks=A,
    )


def bobot_dari_konfigurasi() -> HasilAHP:
    """Hitung bobot dari matriks hasil wawancara pada config.py."""
    hasil = hitung_bobot(cfg.AHP_PAIRWISE)
    if not hasil.konsisten:
        raise ValueError(
            f"CR = {hasil.cr:.4f} melebihi ambang {cfg.CR_THRESHOLD}. "
            "Penilaian pengambil keputusan saling bertentangan. "
            "Ulangi wawancara; jangan sunting matriks agar lolos uji."
        )
    return hasil


# --------------------------------------------------------------------------
# AGREGASI PENILAIAN KELOMPOK
# --------------------------------------------------------------------------
def agregasi_geometrik(matriks_responden: dict[str, list]) -> np.ndarray:
    """
    Gabungkan matriks beberapa responden dengan rata-rata geometrik elemen.

    Metode Aggregation of Individual Judgments (AIJ) dari Saaty. Rata-rata
    geometrik WAJIB dipakai, bukan aritmetik: hanya rata-rata geometrik yang
    menjaga sifat resiprokal. Bila responden A menilai 3 dan responden B
    menilai 1/3, hasil yang benar adalah 1. Rata-rata aritmetik memberi 1,67,
    yang berarti kedua penilaian berlawanan itu diklaim condong ke A.
    """
    tumpukan = np.array([np.asarray(m, dtype=float)
                         for m in matriks_responden.values()])
    for nama, m in matriks_responden.items():
        try:
            validasi_matriks(np.asarray(m, dtype=float))
        except ValueError as e:
            raise ValueError(f"Matriks responden {nama} tidak sah: {e}") from e

    return np.exp(np.log(tumpukan).mean(axis=0))


def bobot_kelompok(matriks_responden: dict[str, list] | None = None) -> dict:
    """
    Hitung bobot gabungan beserta konsistensi tiap responden.

    Konsistensi diperiksa PER RESPONDEN, bukan hanya pada matriks gabungan.
    Agregasi cenderung meratakan ketidakkonsistenan: dua responden yang
    masing-masing tidak konsisten dapat menghasilkan gabungan yang tampak
    konsisten. Memeriksa gabungan saja akan menyembunyikan masalah itu.
    """
    responden = matriks_responden or cfg.AHP_RESPONDEN

    per_responden = {}
    for nama, m in responden.items():
        hasil = hitung_bobot(m)
        per_responden[nama] = hasil
        if not hasil.konsisten:
            raise ValueError(
                f"Responden {nama} memiliki CR = {hasil.cr:.4f} melebihi "
                f"ambang {cfg.CR_THRESHOLD}. Ulangi wawancara dengan "
                "responden tersebut sebelum agregasi."
            )

    gabungan = hitung_bobot(agregasi_geometrik(responden))
    return {
        "gabungan": gabungan,
        "per_responden": per_responden,
        "bobot": gabungan.bobot,
    }


def tabel_perbandingan_responden(hasil_kelompok: dict) -> "object":
    """Susun tabel bobot per responden untuk dilampirkan ke laporan."""
    import pandas as pd
    baris = {
        nama: dict(zip(cfg.CRITERIA_CODES, h.bobot.round(4)))
        for nama, h in hasil_kelompok["per_responden"].items()
    }
    baris["GABUNGAN (geometrik)"] = dict(
        zip(cfg.CRITERIA_CODES, hasil_kelompok["gabungan"].bobot.round(4))
    )
    tabel = pd.DataFrame(baris).T
    tabel["CR"] = [
        round(h.cr, 4) for h in hasil_kelompok["per_responden"].values()
    ] + [round(hasil_kelompok["gabungan"].cr, 4)]
    return tabel
