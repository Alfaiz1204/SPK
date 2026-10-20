"""
Subsistem Pengetahuan (Knowledge-Based Subsystem).

Memuat aturan yang DITETAPKAN, bukan dipelajari dari data:
  1. Indeks Kebutuhan Sosial  - adaptasi 14 kriteria rumah tangga miskin BPS
  2. Skor dampak produktif    - skala prioritas pengelola koperasi
  3. Skor riwayat kredit      - penilaian pakar, lalu dikalibrasi ulang ke data

Memisahkan modul ini dari model statistik membuat satu hal terlihat jelas pada
saat demo: bagian mana dari keputusan yang berasal dari kebijakan manusia, dan
bagian mana yang berasal dari pola data.
"""

from __future__ import annotations

import pandas as pd

from . import config as cfg


# --------------------------------------------------------------------------
# INDEKS KEBUTUHAN SOSIAL
# --------------------------------------------------------------------------
def terapkan_aturan_iks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hasilkan satu kolom biner per indikator deprivasi, lalu jumlahkan.

    Kolom per indikator sengaja dipertahankan agar antarmuka bisa menjawab
    "mengapa pemohon ini mendapat IKS 7?" dengan menyebut indikator mana yang
    terpenuhi. Skor tanpa penjelasan tidak bisa dipertanggungjawabkan kepada
    pemohon yang pengajuannya ditolak.
    """
    df = df.copy()
    for nama_indikator, (kolom, kode_deprivasi) in cfg.IKS_RULES.items():
        df[nama_indikator] = df[kolom].isin(kode_deprivasi).astype(int)
    df["iks_skor"] = df[list(cfg.IKS_RULES.keys())].sum(axis=1)
    return df


def jelaskan_iks(baris: pd.Series) -> list[str]:
    """Kembalikan daftar indikator deprivasi yang terpenuhi untuk satu pemohon."""
    terpenuhi = []
    for nama_indikator, (kolom, _) in cfg.IKS_RULES.items():
        if baris.get(nama_indikator, 0) == 1:
            label = cfg.CODE_LABELS.get(kolom, {}).get(baris[kolom], baris[kolom])
            terpenuhi.append(f"{nama_indikator}: {label}")
    return terpenuhi


# --------------------------------------------------------------------------
# KALIBRASI SKOR RIWAYAT KREDIT
# --------------------------------------------------------------------------
def kalibrasi_skor_riwayat(df_latih: pd.DataFrame) -> dict[str, int]:
    """
    Turunkan skor riwayat kredit dari tingkat gagal bayar yang teramati.

    PENTING: hanya boleh menerima data latih. Memanggil fungsi ini dengan data
    uji menimbulkan kebocoran target, dan metrik evaluasi menjadi tidak sah.

    Kode dengan tingkat macet terendah memperoleh skor 4, tertinggi skor 0.
    """
    tingkat_macet = (
        df_latih.groupby("riwayat_kredit")["target_macet"].mean().sort_values()
    )
    return {kode: 4 - i for i, kode in enumerate(tingkat_macet.index)}


def ambil_peta_skor_riwayat(df_latih: pd.DataFrame | None = None) -> dict[str, int]:
    """Pilih peta skor sesuai versi aktif pada konfigurasi."""
    if cfg.VERSI_SKOR_RIWAYAT_AKTIF == "V1":
        return cfg.SKOR_RIWAYAT_V1_PAKAR
    if df_latih is not None:
        return kalibrasi_skor_riwayat(df_latih)
    return cfg.SKOR_RIWAYAT_V2_KALIBRASI


# --------------------------------------------------------------------------
# KRITERIA TURUNAN
# --------------------------------------------------------------------------
def terapkan_kriteria_turunan(
    df: pd.DataFrame, peta_riwayat: dict[str, int]
) -> pd.DataFrame:
    """Hitung C2, C3, C4 beserta target biner."""
    df = df.copy()

    # C2 Kapasitas angsur. Kolom rasio_angsuran berskala ordinal 1-4, di mana
    # 1 berarti angsuran menyerap porsi terkecil dari pendapatan disposabel.
    # Dibalik lalu diskalakan ke 0-100 supaya menjadi kriteria benefit.
    df["kapasitas_angsur"] = (4 - df["rasio_angsuran"]) / 3 * 100

    # C3 Riwayat kredit. fillna(2) memberi nilai tengah netral bila muncul kode
    # baru yang belum pernah terlihat saat kalibrasi.
    df["skor_riwayat"] = df["riwayat_kredit"].map(peta_riwayat).fillna(2).astype(int)

    # C4 Dampak produktif.
    df["skor_produktif"] = (
        df["tujuan_pinjaman"].map(cfg.SKOR_PRODUKTIF).fillna(1).astype(int)
    )

    df["target_macet"] = (df["label_risiko"] == 2).astype(int)
    return df
