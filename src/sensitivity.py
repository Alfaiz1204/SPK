"""
Subsistem Model (bagian 3): analisis sensitivitas, what-if, dan goal seeking.

Modul inilah yang memisahkan Sistem Pendukung Keputusan dari kalkulator
peringkat. Kalkulator menjawab "siapa yang menang". SPK menjawab "seberapa
kuat kemenangan itu, dan apa yang harus berubah agar hasilnya berbeda".

Tiga kapabilitas yang disediakan:
    1. analisis_sensitivitas_bobot  - satu bobot divariasikan, sisanya
                                      diskalakan proporsional
    2. what_if_pemohon              - ubah atribut satu pemohon, lihat
                                      dampaknya pada peringkat
    3. goal_seeking                 - cari nilai kriteria minimum agar
                                      pemohon mencapai peringkat target
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as cfg
from .mcdm import ranking


# --------------------------------------------------------------------------
# 1. ANALISIS SENSITIVITAS BOBOT
# --------------------------------------------------------------------------
def skalakan_ulang_bobot(
    bobot_awal: np.ndarray, indeks: int, nilai_baru: float
) -> np.ndarray:
    """
    Ubah satu bobot ke nilai_baru, lalu skalakan sisanya agar total tetap 1.

    Sisa bobot diskalakan PROPORSIONAL terhadap nilainya semula, bukan
    dibagi rata. Membagi rata akan diam-diam mengubah urutan kepentingan
    kriteria lain, sehingga yang terukur bukan lagi pengaruh satu bobot.
    """
    bobot = bobot_awal.copy().astype(float)
    sisa_lama = bobot.sum() - bobot[indeks]
    sisa_baru = 1.0 - nilai_baru

    if sisa_lama <= 0:
        bobot[:] = sisa_baru / (len(bobot) - 1)
    else:
        faktor = sisa_baru / sisa_lama
        bobot = bobot * faktor
    bobot[indeks] = nilai_baru
    return bobot


def analisis_sensitivitas_bobot(
    matriks: np.ndarray,
    bobot_awal: np.ndarray,
    benefit: list[bool],
    id_alternatif: list[str],
    indeks_kriteria: int,
    langkah: np.ndarray | None = None,
) -> pd.DataFrame:
    """
    Telusuri satu bobot dari 0.05 sampai 0.60 dan catat peringkat tiap alternatif.

    Keluaran berformat panjang (satu baris per kombinasi bobot x alternatif)
    agar langsung bisa digambar sebagai grafik garis pada antarmuka.
    """
    if langkah is None:
        langkah = np.arange(0.05, 0.61, 0.025)

    baris = []
    for w in langkah:
        bobot = skalakan_ulang_bobot(bobot_awal, indeks_kriteria, float(w))
        skor = ranking.topsis(matriks, bobot, benefit)["skor"]
        peringkat = (-skor).argsort().argsort() + 1
        for i, id_alt in enumerate(id_alternatif):
            baris.append({
                "bobot": round(float(w), 4),
                "id_pemohon": id_alt,
                "skor": float(skor[i]),
                "peringkat": int(peringkat[i]),
            })
    return pd.DataFrame(baris)


def titik_balik_peringkat(
    df_sensitivitas: pd.DataFrame, n_teratas: int = 10
) -> pd.DataFrame:
    """
    Temukan nilai bobot yang membuat komposisi n besar berubah.

    Inilah angka yang dibutuhkan pengambil keputusan: bukan "peringkat bisa
    berubah", melainkan "peringkat berubah tepat ketika bobot melewati 0.35".
    """
    perubahan = []
    himpunan_sebelumnya, bobot_sebelumnya = None, None

    for bobot, kelompok in df_sensitivitas.groupby("bobot", sort=True):
        teratas = set(
            kelompok.nsmallest(n_teratas, "peringkat")["id_pemohon"].tolist()
        )
        if himpunan_sebelumnya is not None and teratas != himpunan_sebelumnya:
            masuk = sorted(teratas - himpunan_sebelumnya)
            keluar = sorted(himpunan_sebelumnya - teratas)
            perubahan.append({
                "bobot_dari": bobot_sebelumnya,
                "bobot_ke": bobot,
                "masuk_n_besar": ", ".join(masuk),
                "keluar_n_besar": ", ".join(keluar),
            })
        himpunan_sebelumnya, bobot_sebelumnya = teratas, bobot

    return pd.DataFrame(perubahan)


def stabilitas_peringkat_teratas(
    df_sensitivitas: pd.DataFrame, n_teratas: int = 10
) -> pd.DataFrame:
    """Hitung berapa persen skenario bobot menempatkan tiap pemohon di n besar."""
    total_skenario = df_sensitivitas["bobot"].nunique()
    masuk = (
        df_sensitivitas[df_sensitivitas["peringkat"] <= n_teratas]
        .groupby("id_pemohon")
        .size()
        .rename("jumlah_skenario")
        .reset_index()
    )
    masuk["persen_stabilitas"] = (masuk["jumlah_skenario"] / total_skenario * 100).round(1)
    return masuk.sort_values("persen_stabilitas", ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------
# 2. WHAT-IF
# --------------------------------------------------------------------------
def what_if_pemohon(
    matriks: np.ndarray,
    bobot: np.ndarray,
    benefit: list[bool],
    id_alternatif: list[str],
    id_target: str,
    perubahan: dict[int, float],
) -> dict:
    """
    Terapkan perubahan nilai kriteria pada satu pemohon dan bandingkan hasilnya.

    Parameters
    ----------
    perubahan : {indeks_kriteria: nilai_baru}

    Catatan: seluruh alternatif lain ikut dihitung ulang. TOPSIS bersifat
    relatif terhadap solusi ideal, sehingga mengubah satu alternatif dapat
    menggeser solusi ideal dan dengan demikian menggeser peringkat yang lain.
    Menghitung ulang hanya pemohon yang diubah akan menghasilkan angka salah.
    """
    idx = id_alternatif.index(id_target)

    skor_awal = ranking.topsis(matriks, bobot, benefit)["skor"]
    peringkat_awal = (-skor_awal).argsort().argsort() + 1

    matriks_baru = matriks.copy()
    for j, nilai in perubahan.items():
        matriks_baru[idx, j] = nilai

    skor_baru = ranking.topsis(matriks_baru, bobot, benefit)["skor"]
    peringkat_baru = (-skor_baru).argsort().argsort() + 1

    return {
        "id_pemohon": id_target,
        "skor_sebelum": float(skor_awal[idx]),
        "skor_sesudah": float(skor_baru[idx]),
        "peringkat_sebelum": int(peringkat_awal[idx]),
        "peringkat_sesudah": int(peringkat_baru[idx]),
        "delta_peringkat": int(peringkat_awal[idx] - peringkat_baru[idx]),
        "alternatif_lain_bergeser": int(
            (peringkat_awal != peringkat_baru).sum() - 1
        ),
    }


# --------------------------------------------------------------------------
# 3. GOAL SEEKING
# --------------------------------------------------------------------------
def goal_seeking(
    matriks: np.ndarray,
    bobot: np.ndarray,
    benefit: list[bool],
    id_alternatif: list[str],
    id_target: str,
    indeks_kriteria: int,
    peringkat_target: int,
    n_langkah: int = 200,
) -> dict:
    """
    Cari nilai kriteria minimum yang dibutuhkan untuk mencapai peringkat target.

    Pencarian memakai penelusuran kisi (grid search), bukan bagi dua (bisection),
    karena peringkat adalah fungsi tangga yang tidak dijamin monoton: menggeser
    satu alternatif dapat menggeser solusi ideal TOPSIS dan membalik urutan
    pasangan lain. Bisection bisa melompati solusi pada fungsi semacam ini.

    Mengembalikan nilai_dibutuhkan = None bila peringkat target tidak tercapai
    pada seluruh rentang nilai yang mungkin. Ini jawaban yang sah, dan jauh
    lebih berguna daripada memaksakan angka yang tidak realistis.
    """
    idx = id_alternatif.index(id_target)
    kolom = matriks[:, indeks_kriteria]
    nilai_awal = float(matriks[idx, indeks_kriteria])

    # Rentang penelusuran diperluas 20% di luar data agar nilai di luar
    # pengalaman historis tetap terjangkau, lalu dipotong pada 0 untuk
    # kriteria yang tidak boleh negatif.
    lo, hi = float(kolom.min()), float(kolom.max())
    bentang = (hi - lo) or 1.0
    lo, hi = max(0.0, lo - 0.2 * bentang), hi + 0.2 * bentang

    kandidat = np.linspace(lo, hi, n_langkah)
    if not benefit[indeks_kriteria]:
        kandidat = kandidat[::-1]   # untuk kriteria cost, nilai kecil lebih baik

    for nilai in kandidat:
        uji = matriks.copy()
        uji[idx, indeks_kriteria] = nilai
        skor = ranking.topsis(uji, bobot, benefit)["skor"]
        peringkat = int((-skor).argsort().argsort()[idx]) + 1
        if peringkat <= peringkat_target:
            return {
                "id_pemohon": id_target,
                "kriteria": cfg.CRITERIA_CODES[indeks_kriteria],
                "nilai_awal": nilai_awal,
                "nilai_dibutuhkan": float(nilai),
                "selisih": float(nilai - nilai_awal),
                "peringkat_target": peringkat_target,
                "peringkat_tercapai": peringkat,
                "tercapai": True,
            }

    return {
        "id_pemohon": id_target,
        "kriteria": cfg.CRITERIA_CODES[indeks_kriteria],
        "nilai_awal": nilai_awal,
        "nilai_dibutuhkan": None,
        "selisih": None,
        "peringkat_target": peringkat_target,
        "peringkat_tercapai": None,
        "tercapai": False,
        "catatan": (
            "Peringkat target tidak tercapai walau kriteria ini didorong ke "
            "nilai ekstrem. Kelemahan pemohon terletak pada kriteria lain."
        ),
    }
