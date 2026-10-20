"""
Metode pemeringkatan multikriteria: TOPSIS, SAW, dan VIKOR.

Tiga metode disediakan bukan untuk menambah fitur, melainkan untuk menguji
ketahanan hasil. Bila peringkat teratas berubah drastis ketika metode
diganti padahal data dan bobotnya sama, peringkat itu artefak metode, bukan
kesimpulan tentang pemohon. Perbandingan lintas metode adalah bentuk validasi
yang paling murah dan paling sering dilewatkan.

Konvensi seluruh fungsi:
    matriks : ndarray (m alternatif x n kriteria), nilai mentah
    bobot   : ndarray (n,), menjumlah 1
    benefit : list[bool] (n,), True bila makin besar makin baik
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _periksa_bentuk(matriks: np.ndarray, bobot: np.ndarray, benefit: list[bool]) -> None:
    m, n = matriks.shape
    if len(bobot) != n:
        raise ValueError(f"Panjang bobot {len(bobot)} != jumlah kriteria {n}.")
    if len(benefit) != n:
        raise ValueError(f"Panjang benefit {len(benefit)} != jumlah kriteria {n}.")
    if not np.isclose(bobot.sum(), 1.0, atol=1e-6):
        raise ValueError(f"Bobot harus menjumlah 1, saat ini {bobot.sum():.6f}.")
    if np.any(~np.isfinite(matriks)):
        raise ValueError("Matriks keputusan mengandung NaN atau inf.")


# --------------------------------------------------------------------------
# TOPSIS
# --------------------------------------------------------------------------
def topsis(
    matriks: np.ndarray, bobot: np.ndarray, benefit: list[bool]
) -> dict[str, np.ndarray]:
    """
    Technique for Order Preference by Similarity to Ideal Solution.

    Normalisasi memakai norma vektor (akar jumlah kuadrat per kolom), sesuai
    rumusan asli Hwang dan Yoon. Inilah tahap yang paling sering salah: jika
    normalisasi min-max dipakai, alternatif terbaik pada suatu kriteria selalu
    bernilai 1 dan terburuk selalu 0, sehingga jarak antar alternatif di
    tengah ikut terdistorsi.

    Arah kriteria cost ditangani saat menentukan solusi ideal, bukan dengan
    membalik nilai mentah lebih dahulu. Membalik nilai (misal 1/x) mengubah
    jarak relatif antar alternatif secara non-linear.
    """
    _periksa_bentuk(matriks, bobot, benefit)

    # Kolom konstan menghasilkan pembagian nol. Diberi nilai 1 agar kolom
    # ternormalisasi menjadi nol dan kriteria itu tidak memengaruhi peringkat,
    # yang memang benar secara logika: kriteria tanpa variasi tidak membedakan.
    penyebut = np.sqrt((matriks ** 2).sum(axis=0))
    penyebut = np.where(penyebut == 0, 1.0, penyebut)
    R = matriks / penyebut

    V = R * bobot

    benefit_arr = np.asarray(benefit, dtype=bool)
    ideal_positif = np.where(benefit_arr, V.max(axis=0), V.min(axis=0))
    ideal_negatif = np.where(benefit_arr, V.min(axis=0), V.max(axis=0))

    d_plus = np.sqrt(((V - ideal_positif) ** 2).sum(axis=1))
    d_minus = np.sqrt(((V - ideal_negatif) ** 2).sum(axis=1))

    total = d_plus + d_minus
    total = np.where(total == 0, 1e-12, total)
    skor = d_minus / total          # closeness coefficient, 0-1

    return {
        "skor": skor,
        "d_plus": d_plus,
        "d_minus": d_minus,
        "matriks_ternormalisasi": R,
        "matriks_terbobot": V,
        "ideal_positif": ideal_positif,
        "ideal_negatif": ideal_negatif,
    }


# --------------------------------------------------------------------------
# SAW
# --------------------------------------------------------------------------
def saw(
    matriks: np.ndarray, bobot: np.ndarray, benefit: list[bool]
) -> dict[str, np.ndarray]:
    """
    Simple Additive Weighting dengan normalisasi min-max.

    Dipakai sebagai pembanding paling sederhana. SAW bersifat kompensatoris
    penuh: nilai sangat buruk pada satu kriteria dapat tertutup sepenuhnya
    oleh nilai sangat baik pada kriteria lain. Sifat ini berbahaya untuk
    kriteria risiko, dan justru karena itu perlu ditunjukkan.
    """
    _periksa_bentuk(matriks, bobot, benefit)

    R = np.zeros_like(matriks, dtype=float)
    for j in range(matriks.shape[1]):
        kolom = matriks[:, j]
        rentang = kolom.max() - kolom.min()
        if rentang == 0:
            R[:, j] = 1.0
        elif benefit[j]:
            R[:, j] = (kolom - kolom.min()) / rentang
        else:
            R[:, j] = (kolom.max() - kolom) / rentang

    return {"skor": (R * bobot).sum(axis=1), "matriks_ternormalisasi": R}


# --------------------------------------------------------------------------
# VIKOR
# --------------------------------------------------------------------------
def vikor(
    matriks: np.ndarray, bobot: np.ndarray, benefit: list[bool], v: float = 0.5
) -> dict[str, np.ndarray]:
    """
    VIseKriterijumska Optimizacija I Kompromisno Resenje.

    Berbeda dari TOPSIS, VIKOR menyeimbangkan kegunaan kelompok (S) dengan
    penyesalan individu maksimum (R). Parameter v mengatur bobot keduanya;
    v = 0.5 memberi perlakuan setara.

    Nilai Q lebih kecil berarti lebih baik. Tanda di sini DIBALIK agar
    konvensinya sama dengan TOPSIS dan SAW (makin besar makin baik), sehingga
    perbandingan antar metode tidak perlu penyesuaian arah di pemanggil.
    """
    _periksa_bentuk(matriks, bobot, benefit)

    benefit_arr = np.asarray(benefit, dtype=bool)
    f_terbaik = np.where(benefit_arr, matriks.max(axis=0), matriks.min(axis=0))
    f_terburuk = np.where(benefit_arr, matriks.min(axis=0), matriks.max(axis=0))

    rentang = f_terbaik - f_terburuk
    rentang = np.where(rentang == 0, 1e-12, rentang)

    selisih_terbobot = bobot * (f_terbaik - matriks) / rentang
    S = selisih_terbobot.sum(axis=1)   # kegunaan kelompok
    R = selisih_terbobot.max(axis=1)   # penyesalan individu maksimum

    S_min, S_maks = S.min(), S.max()
    R_min, R_maks = R.min(), R.max()
    bagi_S = (S_maks - S_min) or 1e-12
    bagi_R = (R_maks - R_min) or 1e-12

    Q = v * (S - S_min) / bagi_S + (1 - v) * (R - R_min) / bagi_R

    return {"skor": -Q, "Q": Q, "S": S, "R": R}


# --------------------------------------------------------------------------
# PERBANDINGAN LINTAS METODE
# --------------------------------------------------------------------------
def bandingkan_metode(
    matriks: np.ndarray,
    bobot: np.ndarray,
    benefit: list[bool],
    id_alternatif: list[str],
) -> pd.DataFrame:
    """Jalankan ketiga metode dan kembalikan peringkat berdampingan."""
    hasil = {
        "TOPSIS": topsis(matriks, bobot, benefit)["skor"],
        "SAW": saw(matriks, bobot, benefit)["skor"],
        "VIKOR": vikor(matriks, bobot, benefit)["skor"],
    }

    df = pd.DataFrame({"id_pemohon": id_alternatif})
    for nama, skor in hasil.items():
        df[f"skor_{nama}"] = skor
        # ascending=False lalu +1: skor tertinggi memperoleh peringkat 1.
        df[f"rank_{nama}"] = (-skor).argsort().argsort() + 1
    return df


def korelasi_peringkat(df_perbandingan: pd.DataFrame) -> pd.DataFrame:
    """Korelasi Spearman antar peringkat metode."""
    kolom_rank = [k for k in df_perbandingan.columns if k.startswith("rank_")]
    return df_perbandingan[kolom_rank].corr(method="spearman").round(4)
