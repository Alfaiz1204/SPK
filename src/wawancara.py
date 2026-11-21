"""
Olah hasil wawancara pembobotan AHP menjadi matriks perbandingan berpasangan.

Responden menjawab 15 perbandingan, sedangkan matriks 6x6 punya 36 sel; 15
sisanya resiprokal dan 6 diagonal selalu 1. Mengisinya dengan tangan adalah
kesalahan yang tidak terdeteksi, karena matriks yang salah ketik tetap lolos
uji CR dan hanya bobotnya yang keliru.

Pemakaian: lihat instrumen/INSTRUMEN_WAWANCARA_AHP.md
"""

from __future__ import annotations

from itertools import combinations

import numpy as np

from . import config as cfg
from .mcdm import ahp

# Urutan 15 pasangan, mengikuti nomor butir pada lembar wawancara.
# combinations() menjamin urutannya sama persis dengan urutan baris pada
# lembar: (C1,C2), (C1,C3), ... (C4,C6), (C5,C6).
PASANGAN = list(combinations(cfg.CRITERIA_CODES, 2))
N_PERTANYAAN = len(PASANGAN)


def _nama(kode: str) -> str:
    return cfg.CRITERIA_NAMES[kode]


def matriks_dari_jawaban(jawaban: list[float]) -> list[list[float]]:
    """
    Susun matriks perbandingan berpasangan dari 15 jawaban bertanda.

    Konvensi tanda mengikuti lembar wawancara: untuk pasangan (A, B), nilai +s
    berarti A lebih penting daripada B dengan kekuatan s pada skala Saaty,
    nilai -s berarti B yang lebih penting, dan 1 berarti sama penting.
    """
    if len(jawaban) != N_PERTANYAAN:
        raise ValueError(
            f"Dibutuhkan {N_PERTANYAAN} jawaban, diterima {len(jawaban)}. "
            "Periksa apakah ada butir lembar wawancara yang terlewat."
        )

    n = len(cfg.CRITERIA_CODES)
    M = np.ones((n, n), dtype=float)

    for (kode_a, kode_b), nilai in zip(PASANGAN, jawaban):
        v = float(nilai)
        if v == 0:
            raise ValueError(
                f"Pasangan {kode_a}-{kode_b} bernilai 0. Skala Saaty tidak "
                "mengenal nol; gunakan 1 untuk 'sama penting'."
            )
        kekuatan = abs(v)
        if not 1 <= kekuatan <= 9:
            raise ValueError(
                f"Pasangan {kode_a}-{kode_b} bernilai {v}. Skala Saaty hanya "
                "mencakup 1 sampai 9 (dengan tanda untuk arah)."
            )

        i = cfg.CRITERIA_CODES.index(kode_a)
        j = cfg.CRITERIA_CODES.index(kode_b)
        # Nilai positif: baris i (A) unggul. Negatif: baris j (B) unggul.
        M[i, j] = kekuatan if v > 0 else 1.0 / kekuatan
        M[j, i] = 1.0 / M[i, j]

    return M.tolist()


def pasangan_paling_tidak_konsisten(
    matriks: np.ndarray, bobot: np.ndarray, teratas: int = 3
) -> list[tuple[str, str, float, float]]:
    """
    Tunjukkan penilaian mana yang paling bertentangan dengan jawaban lain.

    Dipakai ketika CR melewati ambang, agar wawancara ulang dapat menyasar
    pasangan tertentu alih-alih seluruh lembar.

    Ukurannya selisih antara penilaian langsung a_ij dan yang tersirat dari
    bobot hasil, w_i / w_j.
    """
    A = np.asarray(matriks, dtype=float)
    temuan = []

    for i, j in combinations(range(len(cfg.CRITERIA_CODES)), 2):
        tersirat = bobot[i] / bobot[j]
        langsung = A[i, j]
        # Rasio dibuat selalu >= 1 agar besar penyimpangan bisa diperingkat
        # tanpa terpengaruh arah.
        penyimpangan = max(langsung / tersirat, tersirat / langsung)
        temuan.append(
            (cfg.CRITERIA_CODES[i], cfg.CRITERIA_CODES[j], langsung, tersirat)
        )

    temuan.sort(
        key=lambda t: max(t[2] / t[3], t[3] / t[2]), reverse=True
    )
    return temuan[:teratas]


def periksa_responden(nama: str, jawaban: list[float]) -> dict:
    """Hitung bobot dan konsistensi satu responden, tanpa melempar galat."""
    matriks = matriks_dari_jawaban(jawaban)
    # hitung_bobot dipakai langsung agar responden yang tidak konsisten tetap
    # terlaporkan alih-alih menghentikan seluruh proses.
    hasil = ahp.hitung_bobot(matriks)
    return {"nama": nama, "matriks": matriks, "hasil": hasil}


def blok_konfigurasi(hasil_per_responden: list[dict]) -> str:
    """Hasilkan teks AHP_RESPONDEN siap tempel ke config.py."""
    baris = ["AHP_RESPONDEN = {"]
    for r in hasil_per_responden:
        baris.append(f'    "{r["nama"]}": [')
        for row in r["matriks"]:
            sel = ", ".join(
                f"{v:.4f}" if abs(v - round(v)) > 1e-9 else f"{v:.1f}"
                for v in row
            )
            baris.append(f"        [{sel}],")
        baris.append("    ],")
    baris.append("}")
    return "\n".join(baris)


def rangkum_wawancara(jawaban_per_responden: dict[str, list[float]]) -> dict:
    """
    Olah seluruh hasil wawancara dan cetak laporannya.

    Mencetak, berurutan: konsistensi tiap responden, pasangan yang perlu
    ditanyakan ulang bila ada yang gagal, bobot gabungan, dan blok konfigurasi.
    """
    hasil_per_responden = [
        periksa_responden(nama, jawaban)
        for nama, jawaban in jawaban_per_responden.items()
    ]

    print("=" * 64)
    print("KONSISTENSI PER RESPONDEN")
    print("=" * 64)

    gagal = []
    for r in hasil_per_responden:
        h = r["hasil"]
        status = "LOLOS" if h.konsisten else "GAGAL"
        print(f"  {r['nama']:<20} CR = {h.cr:.4f}   {status}")
        if not h.konsisten:
            gagal.append(r)

    for r in gagal:
        print()
        print(f"  Responden {r['nama']} perlu wawancara ulang.")
        print("  Tanyakan ulang pasangan berikut (urut dari paling bertentangan):")
        for kode_a, kode_b, langsung, tersirat in pasangan_paling_tidak_konsisten(
            r["matriks"], r["hasil"].bobot
        ):
            print(
                f"    - {_nama(kode_a)} vs {_nama(kode_b)}: "
                f"dijawab {langsung:.2f}x, "
                f"tersirat dari jawaban lain {tersirat:.2f}x"
            )

    if gagal:
        print()
        print("  Perbaiki responden di atas lebih dulu. Bobot gabungan tidak")
        print("  dihitung selama masih ada responden yang tidak konsisten.")
        return {"per_responden": hasil_per_responden, "gagal": [r["nama"] for r in gagal]}

    responden = {r["nama"]: r["matriks"] for r in hasil_per_responden}
    kelompok = ahp.bobot_kelompok(responden)

    print()
    print("=" * 64)
    print("BOBOT GABUNGAN (agregasi rata-rata geometrik)")
    print("=" * 64)
    print(kelompok["gabungan"].ringkas(
        [cfg.CRITERIA_NAMES[k] for k in cfg.CRITERIA_CODES]
    ))

    print()
    print("=" * 64)
    print("TEMPEL BLOK BERIKUT MENIMPA AHP_RESPONDEN DI src/config.py")
    print("=" * 64)
    print(blok_konfigurasi(hasil_per_responden))
    print()
    print("Lalu jalankan:  python -m src.pipeline && python -m src.figur")

    return {
        "per_responden": hasil_per_responden,
        "kelompok": kelompok,
        "gagal": [],
    }
