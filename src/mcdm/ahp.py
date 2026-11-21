"""
Analytic Hierarchy Process: menurunkan bobot kriteria dari penilaian manusia.

AHP dipakai, bukan pembobotan objektif seperti Entropy atau CRITIC, karena
seberapa penting kebutuhan sosial dibanding risiko gagal bayar adalah
pertanyaan kebijakan yang tidak punya jawaban di dalam data.

Consistency Ratio mengukur apakah penilaian saling bertentangan, misalnya A
lebih penting dari B, B lebih penting dari C, tetapi C lebih penting dari A.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np

from .. import config as cfg


class KonsistensiRendah(UserWarning):
    """Penilaian seorang responden melampaui ambang CR tetapi tetap dipakai."""


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
    rata-rata kolom ternormalisasi, yang hanya tepat pada matriks konsisten
    sempurna dan paling meleset ketika CR mendekati ambang.
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
            "Penilaian saling bertentangan; ulangi wawancara."
        )
    return hasil


# --------------------------------------------------------------------------
# AGREGASI PENILAIAN KELOMPOK
# --------------------------------------------------------------------------
def agregasi_geometrik(matriks_responden: dict[str, list]) -> np.ndarray:
    """
    Gabungkan matriks beberapa responden dengan rata-rata geometrik elemen.

    Metode Aggregation of Individual Judgments (AIJ) dari Saaty. Rata-rata
    geometrik dipakai, bukan aritmetik, karena hanya rata-rata geometrik yang
    menjaga sifat resiprokal: penilaian 3 dan 1/3 harus menghasilkan 1,
    sedangkan rata-rata aritmetik memberi 1,67.
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

    Konsistensi diperiksa per responden, bukan hanya pada matriks gabungan,
    karena agregasi meratakan ketidakkonsistenan: dua responden yang
    masing-masing tidak konsisten dapat menghasilkan gabungan yang tampak
    konsisten.
    """
    responden = matriks_responden or cfg.AHP_RESPONDEN

    per_responden = {}
    tidak_konsisten = []
    for nama, m in responden.items():
        hasil = hitung_bobot(m)
        per_responden[nama] = hasil
        if not hasil.konsisten:
            tidak_konsisten.append((nama, hasil.cr))

    if tidak_konsisten:
        rincian = ", ".join(f"{nama} CR={cr:.4f}" for nama, cr in tidak_konsisten)
        if cfg.AHP_WAJIB_KONSISTEN_PER_RESPONDEN:
            raise ValueError(
                f"Responden melebihi ambang CR {cfg.CR_THRESHOLD}: {rincian}. "
                "Ulangi wawancara dengan responden tersebut sebelum agregasi."
            )
        # Tidak menghentikan perhitungan, tetapi tercatat di log pipeline.
        warnings.warn(
            f"CR melebihi ambang {cfg.CR_THRESHOLD} pada {len(tidak_konsisten)} "
            f"dari {len(responden)} responden ({rincian}). Perhitungan "
            "dilanjutkan karena AHP_WAJIB_KONSISTEN_PER_RESPONDEN=False, dan "
            "yang diuji adalah matriks gabungan. Agregasi meratakan "
            "pertentangan, sehingga CR gabungan yang rendah TIDAK berarti "
            "penilaian tiap responden koheren.",
            KonsistensiRendah,
            stacklevel=2,
        )

    gabungan = hitung_bobot(agregasi_geometrik(responden))
    return {
        "gabungan": gabungan,
        "per_responden": per_responden,
        "tidak_konsisten": tidak_konsisten,
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
