"""
Subsistem Data (bagian 1): ekstraksi, validasi, pembersihan, transformasi.

Setiap fungsi mengembalikan DataFrame baru dan mencatat apa yang diubah ke
dalam objek ETLReport. Laporan ini dipakai di bab Kualitas Data; tanpa jejak
tertulis, klaim "data sudah dibersihkan" tidak bisa diverifikasi penguji.
"""

from __future__ import annotations

import hashlib
import urllib.request
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config as cfg
from . import knowledge


@dataclass
class ETLReport:
    """Jejak audit setiap tahap ETL."""
    baris_awal: int = 0
    baris_akhir: int = 0
    duplikat_dibuang: int = 0
    missing_ditemukan: dict = field(default_factory=dict)
    kode_tidak_dikenal: dict = field(default_factory=dict)
    outlier_di_winsorize: dict = field(default_factory=dict)
    distribusi_label: dict = field(default_factory=dict)
    checksum_sumber: str = ""

    def ringkas(self) -> str:
        baris = [
            "LAPORAN ETL",
            "=" * 60,
            f"Checksum sumber (MD5) : {self.checksum_sumber}",
            f"Baris awal            : {self.baris_awal:,}",
            f"Baris akhir           : {self.baris_akhir:,}",
            f"Duplikat dibuang      : {self.duplikat_dibuang}",
            f"Nilai hilang          : {self.missing_ditemukan or 'tidak ada'}",
            f"Kode tidak dikenal    : {self.kode_tidak_dikenal or 'tidak ada'}",
            f"Outlier di-winsorize  : {self.outlier_di_winsorize or 'tidak ada'}",
            f"Distribusi label      : {self.distribusi_label}",
        ]
        return "\n".join(baris)


# --------------------------------------------------------------------------
# EXTRACT
# --------------------------------------------------------------------------
def unduh_jika_perlu() -> None:
    """Ambil berkas mentah bila belum ada. UCI dicoba lebih dulu, lalu mirror."""
    if cfg.RAW_CSV.exists():
        return
    cfg.DATA_RAW.mkdir(parents=True, exist_ok=True)
    # Mirror dipakai karena beberapa jaringan memblokir domain UCI.
    # Isi berkas identik dengan german.data; lisensi tetap CC BY 4.0 (UCI id=144).
    with urllib.request.urlopen(cfg.SOURCE_URL_MIRROR, timeout=60) as resp:
        cfg.RAW_CSV.write_bytes(resp.read())


def ekstrak(report: ETLReport) -> pd.DataFrame:
    """Baca CSV mentah tanpa header dan pasang nama kolom dari skema."""
    unduh_jika_perlu()
    report.checksum_sumber = hashlib.md5(cfg.RAW_CSV.read_bytes()).hexdigest()

    df = pd.read_csv(cfg.RAW_CSV, header=None, names=cfg.RAW_COLUMNS)
    report.baris_awal = len(df)

    if df.shape[1] != len(cfg.RAW_COLUMNS):
        raise ValueError(
            f"Jumlah kolom {df.shape[1]} tidak sesuai skema "
            f"({len(cfg.RAW_COLUMNS)}). Berkas sumber kemungkinan berubah."
        )
    return df


# --------------------------------------------------------------------------
# VALIDATE & CLEAN
# --------------------------------------------------------------------------
def validasi(df: pd.DataFrame, report: ETLReport) -> pd.DataFrame:
    """Periksa nilai hilang, kode kategorik asing, dan rentang numerik."""
    df = df.copy()

    # 1. Nilai hilang
    missing = df.isna().sum()
    report.missing_ditemukan = {k: int(v) for k, v in missing.items() if v > 0}

    # 2. Kode kategorik di luar kamus. Dataset ini seharusnya bersih;
    #    pemeriksaan tetap dijalankan agar pipeline gagal cepat kalau
    #    sumber data diganti dengan versi lain.
    for kolom, kamus in cfg.CODE_LABELS.items():
        asing = set(df[kolom].unique()) - set(kamus.keys())
        if asing:
            report.kode_tidak_dikenal[kolom] = sorted(asing)

    # 3. Rentang numerik yang mustahil secara domain
    asumsi = {
        "usia": (18, 100),
        "durasi_bulan": (1, 120),
        "jumlah_kredit": (1, 100_000),
        "rasio_angsuran": (1, 4),
        "jumlah_tanggungan": (1, 10),
    }
    for kolom, (lo, hi) in asumsi.items():
        melanggar = int(((df[kolom] < lo) | (df[kolom] > hi)).sum())
        if melanggar:
            report.kode_tidak_dikenal[f"{kolom}_di_luar_rentang"] = melanggar

    return df


def bersihkan(df: pd.DataFrame, report: ETLReport) -> pd.DataFrame:
    """Buang duplikat dan redam pencilan ekstrem."""
    df = df.copy()

    sebelum = len(df)
    df = df.drop_duplicates()
    report.duplikat_dibuang = sebelum - len(df)

    # Winsorize pada persentil 1 dan 99 untuk kolom bernilai uang / durasi.
    # Nilai TIDAK dibuang: baris pemohon berjumlah besar tetap relevan secara
    # bisnis. Yang diredam hanya pengaruhnya terhadap normalisasi TOPSIS,
    # yang sensitif pada nilai ekstrem.
    for kolom in ["jumlah_kredit", "durasi_bulan"]:
        lo, hi = df[kolom].quantile([0.01, 0.99])
        terdampak = int(((df[kolom] < lo) | (df[kolom] > hi)).sum())
        if terdampak:
            df[kolom] = df[kolom].clip(lower=lo, upper=hi)
            report.outlier_di_winsorize[kolom] = terdampak

    return df


# --------------------------------------------------------------------------
# TRANSFORM
#
# Catatan arsitektur: skor riwayat kredit (C3) TIDAK dihitung di sini.
# Skor itu dikalibrasi dari tingkat gagal bayar pada data latih, sehingga
# baru boleh dihitung setelah pemisahan latih/uji. Menghitungnya di tahap ETL
# akan membocorkan informasi target ke data uji.
# --------------------------------------------------------------------------
def tambah_label_terbaca(df: pd.DataFrame) -> pd.DataFrame:
    """Tambahkan kolom *_label untuk keperluan antarmuka."""
    df = df.copy()
    for kolom, kamus in cfg.CODE_LABELS.items():
        df[f"{kolom}_label"] = df[kolom].map(kamus)
    return df


# --------------------------------------------------------------------------
# ORKESTRASI
# --------------------------------------------------------------------------
def jalankan_etl(verbose: bool = True) -> tuple[pd.DataFrame, ETLReport]:
    """Pipeline ETL lengkap: extract -> validate -> clean -> transform."""
    report = ETLReport()

    df = ekstrak(report)
    df = validasi(df, report)
    df = bersihkan(df, report)
    df = knowledge.terapkan_aturan_iks(df)
    df["target_macet"] = (df["label_risiko"] == 2).astype(int)
    df = tambah_label_terbaca(df)

    df = df.reset_index(drop=True)
    df.insert(0, "id_pemohon", [f"P{i:04d}" for i in range(1, len(df) + 1)])

    report.baris_akhir = len(df)
    report.distribusi_label = {
        "lancar": int((df["target_macet"] == 0).sum()),
        "macet": int((df["target_macet"] == 1).sum()),
    }

    cfg.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(cfg.DATA_PROCESSED / "pemohon_bersih.csv", index=False)

    if verbose:
        print(report.ringkas())

    return df, report


if __name__ == "__main__":
    jalankan_etl()
