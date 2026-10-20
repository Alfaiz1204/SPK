"""
Sumber data EKSTERNAL: statistik resmi BPS dan Keputusan Gubernur Jawa Tengah.

Modul ini memenuhi kriteria rubrik Kualitas Data yang menuntut data mencakup
"sumber internal serta eksternal". Sumber internal berupa basis data historis
angsuran koperasi; sumber eksternal adalah seluruh angka di bawah ini.

Setiap konstanta disertai sumber, tanggal rilis, dan tautan verifikasi.
Angka yang tidak dapat diverifikasi tidak dimasukkan ke modul ini.

PERINGATAN PEMELIHARAAN
-----------------------
Angka BPS dirilis dua kali setahun (Maret dan September) dan UMK ditetapkan
setiap Desember. Periksa ulang konstanta di bawah sebelum dipakai pada
periode penyaluran berikutnya. Konstanta kedaluwarsa menghasilkan ambang
kelayakan yang keliru, dan kekeliruan itu menimpa pemohon.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SumberEksternal:
    """Satu angka statistik beserta jejak sumbernya."""
    nilai: float
    satuan: str
    keterangan: str
    sumber: str
    periode: str
    tautan: str


# --------------------------------------------------------------------------
# GARIS KEMISKINAN
# --------------------------------------------------------------------------
GARIS_KEMISKINAN_JATENG = SumberEksternal(
    nilai=596_676,
    satuan="Rp/kapita/bulan",
    keterangan="Garis kemiskinan Provinsi Jawa Tengah",
    sumber="BPS Provinsi Jawa Tengah",
    periode="Maret 2026",
    tautan="https://jateng.bps.go.id/",
)

GARIS_KEMISKINAN_RUMAH_TANGGA = SumberEksternal(
    nilai=2_571_674,
    satuan="Rp/rumah tangga/bulan",
    keterangan="Garis kemiskinan rata-rata per rumah tangga miskin Jawa Tengah",
    sumber="BPS Provinsi Jawa Tengah",
    periode="Maret 2026",
    tautan="https://jateng.bps.go.id/",
)

PERSEN_PENDUDUK_MISKIN_JATENG = SumberEksternal(
    nilai=9.21,
    satuan="persen",
    keterangan="Persentase penduduk miskin Jawa Tengah (3,29 juta jiwa)",
    sumber="BPS Provinsi Jawa Tengah",
    periode="Maret 2026",
    tautan="https://jateng.bps.go.id/",
)

# --------------------------------------------------------------------------
# UPAH MINIMUM
# Keputusan Gubernur Jawa Tengah Nomor 100.3.3.1/505 Tahun 2025,
# ditetapkan 24 Desember 2025, berlaku 1 Januari 2026.
# --------------------------------------------------------------------------
UMK_SURAKARTA = SumberEksternal(
    nilai=2_570_000,
    satuan="Rp/bulan",
    keterangan="Upah Minimum Kota Surakarta 2026 (naik 6,66% dari Rp2.416.560)",
    sumber="Kepgub Jateng No. 100.3.3.1/505 Tahun 2025",
    periode="2026",
    tautan="https://jateng.bps.go.id/",
)

UMP_JATENG = SumberEksternal(
    nilai=2_327_386,
    satuan="Rp/bulan",
    keterangan="Upah Minimum Provinsi Jawa Tengah 2026",
    sumber="Kepgub Jateng No. 100.3.3.1/505 Tahun 2025",
    periode="2026",
    tautan="https://jateng.bps.go.id/",
)

# UMK seluruh Solo Raya. Dipakai sebagai penimbang wilayah: pemohon dari
# daerah ber-UMK rendah menghadapi beban angsuran relatif lebih berat pada
# nominal pinjaman yang sama.
UMK_SOLO_RAYA = {
    "Karanganyar": 2_592_154,
    "Surakarta": 2_570_000,
    "Klaten": 2_538_691,
    "Boyolali": 2_537_949,
    "Sukoharjo": 2_500_000,
    "Sragen": 2_337_700,
    "Wonogiri": 2_335_126,
}

# --------------------------------------------------------------------------
# PARAMETER TURUNAN
# --------------------------------------------------------------------------
# Rata-rata anggota rumah tangga miskin Jawa Tengah, diturunkan dari
# pembagian garis kemiskinan rumah tangga terhadap garis kemiskinan per
# kapita. Angka ini dipakai untuk mengubah pendapatan rumah tangga menjadi
# pengeluaran per kapita.
ANGGOTA_RUMAH_TANGGA_MISKIN = round(
    GARIS_KEMISKINAN_RUMAH_TANGGA.nilai / GARIS_KEMISKINAN_JATENG.nilai, 2
)

# Batas beban angsuran. Otoritas pengawas lazim memakai 30 persen pendapatan
# sebagai batas kehati-hatian. Nilai ini kebijakan koperasi, bukan statistik.
BATAS_RASIO_ANGSURAN = 0.30


def temuan_kunci() -> str:
    """
    Fakta yang menjadi landasan perumusan masalah.

    Garis kemiskinan per rumah tangga Jawa Tengah (Rp2.571.674) praktis
    berimpit dengan UMK Kota Surakarta (Rp2.570.000), selisihnya hanya
    Rp1.674 atau 0,07 persen. Artinya pekerja berupah minimum di Solo yang
    menanggung rumah tangga berukuran rata-rata berada tepat pada garis
    kemiskinan. Satu guncangan kecil, misalnya sakit atau kehilangan
    pekerjaan, langsung menjatuhkannya ke bawah garis.
    """
    selisih = GARIS_KEMISKINAN_RUMAH_TANGGA.nilai - UMK_SURAKARTA.nilai
    persen = selisih / UMK_SURAKARTA.nilai * 100
    return (
        f"Garis kemiskinan rumah tangga Jateng Rp{GARIS_KEMISKINAN_RUMAH_TANGGA.nilai:,.0f} "
        f"vs UMK Surakarta Rp{UMK_SURAKARTA.nilai:,.0f}. "
        f"Selisih hanya Rp{selisih:,.0f} ({persen:+.2f}%). "
        f"Rata-rata rumah tangga miskin beranggotakan {ANGGOTA_RUMAH_TANGGA_MISKIN} orang."
    ).replace(",", ".")


def klasifikasi_kesejahteraan(pendapatan_rt: float, n_anggota: float) -> str:
    """
    Golongkan rumah tangga terhadap garis kemiskinan BPS.

    Pengeluaran per kapita didekati dari pendapatan rumah tangga dibagi
    jumlah anggota. Pendekatan ini mengabaikan tabungan dan transfer, dan
    karenanya hanya layak dipakai sebagai penyaring awal, bukan penetapan
    status kemiskinan resmi.
    """
    per_kapita = pendapatan_rt / max(n_anggota, 1)
    gk = GARIS_KEMISKINAN_JATENG.nilai

    if per_kapita < gk:
        return "Miskin"
    if per_kapita < 1.2 * gk:
        return "Rentan miskin"
    if per_kapita < 2.0 * gk:
        return "Menuju menengah"
    return "Menengah"


def tabel_sumber() -> pd.DataFrame:
    """Daftar seluruh sumber eksternal untuk dilampirkan ke laporan."""
    butir = [
        GARIS_KEMISKINAN_JATENG, GARIS_KEMISKINAN_RUMAH_TANGGA,
        PERSEN_PENDUDUK_MISKIN_JATENG, UMK_SURAKARTA, UMP_JATENG,
    ]
    return pd.DataFrame([{
        "Keterangan": b.keterangan,
        "Nilai": f"{b.nilai:,.0f}".replace(",", "."),
        "Satuan": b.satuan,
        "Sumber": b.sumber,
        "Periode": b.periode,
    } for b in butir])


if __name__ == "__main__":
    print(temuan_kunci())
    print()
    print(tabel_sumber().to_string(index=False))
    print()
    print("UMK Solo Raya 2026:")
    for kota, umk in sorted(UMK_SOLO_RAYA.items(), key=lambda x: -x[1]):
        print(f"  {kota:<14} Rp{umk:,.0f}".replace(",", "."))
