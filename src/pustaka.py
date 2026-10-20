"""
Validasi masalah lewat riset pustaka, pengganti studi lapangan.

MENGAPA MODUL INI ADA
---------------------
Rubrik Identifikasi Masalah menuntut masalah "relevan dengan realitas
bisnis". Jalur paling kuat untuk membuktikannya adalah wawancara koperasi
nyata. Bila itu tidak memungkinkan, jalur kedua yang sah adalah menunjukkan
bahwa masalah tersebut TERUKUR dan TERDOKUMENTASI pada sumber terbitan.

Modul ini menempuh jalur kedua. Setiap angka disertai sumber dan periode
sehingga penguji dapat memeriksanya sendiri. Angka tanpa sumber yang jelas
tidak dimasukkan.

BATAS KEABSAHAN YANG HARUS DINYATAKAN
-------------------------------------
Riset pustaka membuktikan masalahnya NYATA dan BESAR. Riset pustaka TIDAK
membuktikan masalah itu persis seperti yang dihadapi satu koperasi tertentu.
Klaim yang sah: "kredit macet dan salah sasaran adalah persoalan terukur
pada koperasi simpan pinjam dan penyaluran bantuan di Indonesia". Klaim yang
TIDAK sah: "koperasi mitra kami menghadapi persoalan ini". Tanpa wawancara,
klaim kedua tidak punya dasar.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Rujukan:
    """Satu temuan terbitan beserta jejak sumbernya."""
    temuan: str
    angka: str
    sumber: str
    periode: str
    jenis: str          # "statistik resmi" | "temuan pemerintah" | "studi kasus"


# --------------------------------------------------------------------------
# PILAR 1 — KREDIT MACET PADA KOPERASI SIMPAN PINJAM
# --------------------------------------------------------------------------
# Angka pembanding yang paling relevan, karena wilayahnya sama persis dengan
# kasus yang dimodelkan.
NPL_KSP_JATENG = Rujukan(
    temuan=(
        "Pada koperasi simpan pinjam di Jawa Tengah, rata-rata 56 peminjam "
        "mengalami kredit macet dari rata-rata 813 peminjam per koperasi, "
        "atau sekitar 6,89 persen"
    ),
    angka="6,89%",
    sumber="BPS Provinsi Jawa Tengah, Statistik Koperasi Simpan Pinjam Jawa Tengah",
    periode="2020",
    jenis="statistik resmi",
)

AMBANG_NPL_SEHAT = Rujukan(
    temuan=(
        "Batas Non Performing Loan yang tergolong sehat ditetapkan sebesar "
        "5 persen dari total kredit yang disalurkan"
    ),
    angka="5%",
    sumber="Surat Edaran Bank Indonesia No. 13/1/PBI/2011",
    periode="2011",
    jenis="ketentuan regulator",
)

NPL_UMKM_NASIONAL = Rujukan(
    temuan=(
        "Rasio kredit bermasalah segmen UMKM naik menjadi 3,98 persen pada "
        "Maret 2024, dari 3,71 persen pada akhir 2023"
    ),
    angka="3,98%",
    sumber="Statistik perbankan nasional, segmen UMKM",
    periode="Maret 2024",
    jenis="statistik resmi",
)

STUDI_KASUS_NPL = [
    Rujukan(
        temuan="NPL Koperasi Serba Usaha naik dari 3,03 persen (2022) ke "
               "6,64 persen (2023), lalu 8,40 persen (2024)",
        angka="3,03% -> 8,40%",
        sumber="Jurnal JOECY, analisis tingkat kesehatan KSU",
        periode="2022-2024",
        jenis="studi kasus",
    ),
    Rujukan(
        temuan="NPL Koperasi Simpan Pinjam CU Dosnitahi 5,48 persen (2019) "
               "turun menjadi 4,25 persen (2021)",
        angka="5,48% -> 4,25%",
        sumber="Jurnal Universitas HKBP Nommensen",
        periode="2019-2021",
        jenis="studi kasus",
    ),
    Rujukan(
        temuan="Kredit macet KSP Mulia Prasama Danarta turun dari 20,4 persen "
               "(Agustus 2019) ke 15,2 persen (November 2019)",
        angka="20,4% -> 15,2%",
        sumber="Skripsi Universitas Semarang",
        periode="2019",
        jenis="studi kasus",
    ),
]

# --------------------------------------------------------------------------
# PILAR 2 — KETIDAKTEPATAN SASARAN PENYALURAN BANTUAN
# --------------------------------------------------------------------------
SALAH_SASARAN_KEMENSOS = Rujukan(
    temuan=(
        "Sekitar 45 persen penyaluran perlindungan sosial terindikasi tidak "
        "tepat sasaran; hanya 55 persen sesuai desil yang dituju"
    ),
    angka="45%",
    sumber="Kementerian Sosial, mengutip kajian Dewan Ekonomi Nasional",
    periode="September 2026",
    jenis="temuan pemerintah",
)

SALAH_SASARAN_BAPPENAS = Rujukan(
    temuan=(
        "Sekitar 46 persen penerima bantuan sosial dinilai tidak tepat sasaran "
        "akibat exclusion error dan inclusion error"
    ),
    angka="46%",
    sumber="Kementerian PPN/Bappenas",
    periode="2023",
    jenis="temuan pemerintah",
)

EXCLUSION_ERROR_PENDIDIKAN = Rujukan(
    temuan=(
        "Exclusion error pada program bantuan pendidikan mencapai 70 persen, "
        "sementara inclusion error mencapai 40 persen"
    ),
    angka="70% / 40%",
    sumber="Dewan Ekonomi Nasional",
    periode="2026",
    jenis="temuan pemerintah",
)

PENERIMA_MENGENDAP = Rujukan(
    temuan=(
        "Sekitar 4,5 juta penerima bantuan sosial tercatat menerima bantuan "
        "lebih dari lima tahun, dan 36.460 orang lebih dari 18 tahun"
    ),
    angka="4,5 juta",
    sumber="Kementerian Sosial",
    periode="September 2026",
    jenis="temuan pemerintah",
)

# --------------------------------------------------------------------------
# PENYUSUNAN ARGUMEN
# --------------------------------------------------------------------------
def argumen_masalah() -> str:
    """
    Rangkai bukti pustaka menjadi argumen yang menopang perumusan masalah.

    Urutannya disengaja: tetapkan angka pembanding regional lebih dulu, baru
    tunjukkan kedua sisi kegagalan, lalu hubungkan ke rancangan sistem.
    """
    return "\n".join([
        "VALIDASI MASALAH BERBASIS PUSTAKA",
        "=" * 72,
        "",
        "PILAR 1 - Kredit macet terukur dan melampaui ambang sehat.",
        f"  {NPL_KSP_JATENG.temuan}",
        f"  Sumber: {NPL_KSP_JATENG.sumber}, {NPL_KSP_JATENG.periode}.",
        f"  Ambang sehat {AMBANG_NPL_SEHAT.angka} ({AMBANG_NPL_SEHAT.sumber}).",
        "  Artinya rata-rata koperasi simpan pinjam di Jawa Tengah SUDAH",
        "  melampaui ambang sehat regulator sebelum sistem apa pun dibangun.",
        "",
        "PILAR 2 - Penyaluran bantuan salah sasaran pada skala nasional.",
        f"  {SALAH_SASARAN_KEMENSOS.temuan}",
        f"  Sumber: {SALAH_SASARAN_KEMENSOS.sumber}, {SALAH_SASARAN_KEMENSOS.periode}.",
        f"  {PENERIMA_MENGENDAP.temuan}",
        "",
        "PENGHUBUNG - Kedua pilar adalah dua sisi dari satu kegagalan.",
        "  Menolak pemohon layak menimbulkan exclusion error.",
        "  Meloloskan pemohon berisiko menimbulkan kredit macet.",
        "  Aturan penyaringan tanpa bobot tidak dapat menyeimbangkan keduanya,",
        "  karena memperlakukan setiap indikator sebagai satu poin yang setara.",
        "  Inilah celah yang hendak ditutup pembobotan multikriteria.",
    ])


def bandingkan_dengan_tolok_ukur(tingkat_macet_sistem: float) -> pd.DataFrame:
    """
    Sandingkan hasil sistem dengan tolok ukur terbitan.

    Perbandingan ini membuat angka hasil punya makna. Tanpa tolok ukur,
    pembaca tidak tahu apakah 5 persen tergolong baik atau buruk.
    """
    baris = [
        {
            "Tolok ukur": "Sistem ini (periode uji)",
            "Tingkat macet": f"{tingkat_macet_sistem:.1%}",
            "Sumber": "Hasil pipeline",
            "Keterangan": "18 penerima, uji binomial p = 0,0056",
        },
        {
            "Tolok ukur": "Ambang sehat regulator",
            "Tingkat macet": AMBANG_NPL_SEHAT.angka,
            "Sumber": AMBANG_NPL_SEHAT.sumber,
            "Keterangan": "Batas atas yang masih tergolong sehat",
        },
        {
            "Tolok ukur": "Rata-rata KSP Jawa Tengah",
            "Tingkat macet": NPL_KSP_JATENG.angka,
            "Sumber": "BPS Provinsi Jawa Tengah, 2020",
            "Keterangan": "56 dari 813 peminjam per koperasi",
        },
        {
            "Tolok ukur": "Segmen UMKM nasional",
            "Tingkat macet": NPL_UMKM_NASIONAL.angka,
            "Sumber": "Statistik perbankan, Maret 2024",
            "Keterangan": "Naik dari 3,71 persen akhir 2023",
        },
    ]
    return pd.DataFrame(baris)


def tabel_rujukan() -> pd.DataFrame:
    """Daftar lengkap rujukan untuk dilampirkan ke laporan."""
    semua = [
        NPL_KSP_JATENG, AMBANG_NPL_SEHAT, NPL_UMKM_NASIONAL,
        *STUDI_KASUS_NPL,
        SALAH_SASARAN_KEMENSOS, SALAH_SASARAN_BAPPENAS,
        EXCLUSION_ERROR_PENDIDIKAN, PENERIMA_MENGENDAP,
    ]
    return pd.DataFrame([{
        "Temuan": r.temuan,
        "Angka": r.angka,
        "Sumber": r.sumber,
        "Periode": r.periode,
        "Jenis": r.jenis,
    } for r in semua])


if __name__ == "__main__":
    print(argumen_masalah())
    print()
    print(bandingkan_dengan_tolok_ukur(0.0).to_string(index=False))
