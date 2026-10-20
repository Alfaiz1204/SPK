"""
Pelokalan berkas pengajuan ke konteks Kota Surakarta.

MASALAH YANG DISELESAIKAN
-------------------------
Basis data historis angsuran yang tersedia publik berdenominasi Deutsche Mark
dan berasal dari Jerman. Model risiko dapat dilatih di atasnya, tetapi berkas
pengajuan yang diputuskan koperasi berdenominasi Rupiah dengan besaran yang
sama sekali berbeda. Dua ruang nilai ini harus dihubungkan secara eksplisit,
bukan dengan mengalikan kurs.

METODE: PEMETAAN KUANTIL (quantile mapping)
-------------------------------------------
Nilai pinjaman diterjemahkan berdasarkan POSISI RELATIFNYA, bukan nominalnya.
Pinjaman yang berada pada persentil ke-60 sebaran historis dipetakan ke
persentil ke-60 sebaran pinjaman koperasi di Surakarta.

Asumsi yang dipikul metode ini, dan harus dinyatakan terbuka:

  (a) Struktur risiko bersifat ORDINAL. Pemohon yang meminjam relatif besar
      terhadap sebaran kelompoknya menanggung risiko lebih tinggi, terlepas
      dari mata uang dan negaranya.
  (b) Asumsi (a) TIDAK dapat diuji dengan data yang tersedia. Pengujiannya
      membutuhkan data angsuran koperasi Indonesia yang berlabel lancar atau
      macet, dan data itu belum ada pada prototipe ini.

Konsekuensinya, probabilitas gagal bayar yang dihasilkan harus dibaca sebagai
SKOR RISIKO RELATIF untuk mengurutkan pemohon, bukan sebagai taksiran peluang
absolut. Menyebutnya "peluang 38 persen gagal bayar" kepada pengurus koperasi
akan menyesatkan. Menyebutnya "pemohon ini lebih berisiko daripada 70 persen
pemohon lain" sudah tepat.

Atribut selain nilai pinjaman, yaitu seluruh atribut kategorik, usia, tenor,
jumlah tanggungan, dan lama domisili, berpindah apa adanya karena satuannya
memang universal.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as cfg
from . import eksternal as ext


# --------------------------------------------------------------------------
# SEBARAN RUJUKAN PINJAMAN KOPERASI SIMPAN PINJAM
# --------------------------------------------------------------------------
# Sebaran plafon pinjaman mikro koperasi simpan pinjam di Solo Raya,
# dinyatakan sebagai kelipatan UMK Surakarta agar tetap sahih ketika UMK
# berubah. Rentang 0,4x sampai 6x UMK mencerminkan produk pinjaman mikro:
# dari pinjaman darurat sekitar satu juta rupiah sampai modal usaha sekitar
# lima belas juta rupiah.
#
# PENTING: sebaran ini adalah ASUMSI PRODUK, bukan statistik terukur. Ganti
# dengan sebaran plafon sesungguhnya begitu data koperasi mitra tersedia.
# Fungsi `pasang_sebaran_rujukan()` disediakan khusus untuk itu.
KELIPATAN_UMK_MIN = 0.4
KELIPATAN_UMK_MAKS = 6.0

_SEBARAN_RUJUKAN: np.ndarray | None = None


def sebaran_rujukan_pinjaman(n: int = 4000, seed: int = cfg.RANDOM_STATE) -> np.ndarray:
    """
    Bangkitkan sebaran rujukan plafon pinjaman koperasi dalam Rupiah.

    Sebaran log-normal dipilih karena nilai pinjaman mikro menumpuk pada
    nominal kecil dengan ekor panjang ke kanan: banyak pinjaman satu sampai
    tiga juta, sedikit pinjaman belasan juta. Sebaran normal akan keliru
    menghasilkan nilai negatif dan meremehkan ekor kanan.
    """
    global _SEBARAN_RUJUKAN
    if _SEBARAN_RUJUKAN is not None and len(_SEBARAN_RUJUKAN) == n:
        return _SEBARAN_RUJUKAN

    rng = np.random.default_rng(seed)
    umk = ext.UMK_SURAKARTA.nilai

    # Parameter log-normal dipilih agar median mendekati 1,3x UMK dan
    # persentil ke-95 mendekati 5x UMK.
    nilai = rng.lognormal(mean=np.log(1.3), sigma=0.62, size=n) * umk
    nilai = np.clip(nilai, KELIPATAN_UMK_MIN * umk, KELIPATAN_UMK_MAKS * umk)

    # Dibulatkan ke kelipatan Rp50.000, mengikuti praktik pencairan koperasi.
    _SEBARAN_RUJUKAN = np.round(nilai / 50_000) * 50_000
    return _SEBARAN_RUJUKAN


def pasang_sebaran_rujukan(nilai_nyata: np.ndarray) -> None:
    """
    Ganti sebaran rujukan dengan data plafon koperasi mitra yang sesungguhnya.

    Panggil fungsi ini SEBELUM `petakan_nilai_pinjaman()` begitu data riil
    tersedia. Tidak ada bagian lain dari sistem yang perlu diubah.
    """
    global _SEBARAN_RUJUKAN
    _SEBARAN_RUJUKAN = np.asarray(nilai_nyata, dtype=float)


# --------------------------------------------------------------------------
# PEMETAAN KUANTIL
# --------------------------------------------------------------------------
def petakan_nilai_pinjaman(
    nilai_historis: np.ndarray, sebaran_historis: np.ndarray | None = None
) -> np.ndarray:
    """
    Terjemahkan nilai pinjaman historis ke Rupiah lewat kesesuaian persentil.

    Parameters
    ----------
    nilai_historis   : nilai yang hendak diterjemahkan
    sebaran_historis : sebaran rujukan asal. Bila None, `nilai_historis`
                       sendiri dipakai sebagai rujukan.
    """
    nilai_historis = np.asarray(nilai_historis, dtype=float)
    rujukan_asal = (
        np.asarray(sebaran_historis, dtype=float)
        if sebaran_historis is not None else nilai_historis
    )
    rujukan_tujuan = sebaran_rujukan_pinjaman()

    # Posisi persentil tiap nilai pada sebaran asal, lalu nilai pada
    # persentil yang sama di sebaran tujuan.
    persentil = np.searchsorted(np.sort(rujukan_asal), nilai_historis) / len(rujukan_asal)
    persentil = np.clip(persentil, 0.001, 0.999)

    hasil = np.quantile(rujukan_tujuan, persentil)
    return np.round(hasil / 50_000) * 50_000


def perkirakan_pendapatan(df: pd.DataFrame) -> np.ndarray:
    """
    Perkirakan pendapatan rumah tangga bulanan dari atribut yang tersedia.

    Dibangun dari UMK Surakarta sebagai titik tumpu, lalu disesuaikan menurut
    jenis pekerjaan dan lama bekerja. Ini PERKIRAAN untuk menghitung beban
    angsuran, bukan pendapatan terlapor. Pada penerapan nyata, kolom ini diisi
    dari formulir pendataan pemohon (lihat instrumen/FORMULIR_PENDATAAN.md).
    """
    umk = ext.UMK_SURAKARTA.nilai

    # Pengali menurut jenis pekerjaan, dinyatakan terhadap UMK Surakarta.
    #
    # Nilai di bawah 1,0 mendominasi karena anggota koperasi simpan pinjam
    # mikro sebagian besar bekerja di sektor INFORMAL: pedagang pasar, buruh
    # harian, pengemudi ojek daring, pekerja rumahan. UMK tidak mengikat
    # sektor informal, sehingga memakai UMK sebagai lantai pendapatan akan
    # melebih-lebihkan kemampuan bayar dan membuat seluruh pemohon tampak
    # layak. Itulah yang terjadi pada kalibrasi pertama: 40 dari 40 pemohon
    # lolos batas 30 persen, sehingga uji kelayakan kehilangan daya pisah.
    pengali_kerja = {
        "A171": 0.42,   # tidak bekerja / tidak terampil non-residen
        "A172": 0.62,   # tidak terampil, residen (buruh harian, pedagang kecil)
        "A173": 0.95,   # terampil / pegawai
        "A174": 1.55,   # manajerial / wiraswasta / ahli
    }
    # Penambah menurut lama bekerja: masa kerja panjang menaikkan upah.
    tambahan_masa_kerja = {
        "A71": 0.00, "A72": 0.04, "A73": 0.12, "A74": 0.20, "A75": 0.28,
    }

    dasar = df["jenis_pekerjaan"].map(pengali_kerja).fillna(0.7).to_numpy()
    tambah = df["lama_bekerja"].map(tambahan_masa_kerja).fillna(0.08).to_numpy()

    return np.round((dasar + tambah) * umk / 50_000) * 50_000


def hitung_anggota_rumah_tangga(df: pd.DataFrame) -> np.ndarray:
    """
    Perkirakan jumlah anggota rumah tangga, dikalibrasi ke rata-rata BPS.

    Kolom `jumlah_tanggungan` pada data historis hanya bernilai 1 atau 2,
    karena definisi aslinya adalah "jumlah orang yang wajib dinafkahi",
    bukan jumlah penghuni rumah. Memakainya apa adanya menghasilkan rumah
    tangga beranggotakan 2 sampai 3 orang, padahal BPS mencatat rata-rata
    rumah tangga miskin Jawa Tengah beranggotakan 4,31 orang.

    Selisih itu bukan detail sepele: jumlah anggota adalah PENYEBUT pada
    perhitungan pengeluaran per kapita, sehingga meremehkannya membuat
    setiap rumah tangga tampak jauh di atas garis kemiskinan.

    Faktor skala diselesaikan secara numerik agar rata-rata kohort tepat
    sama dengan angka BPS, bukan ditebak.
    """
    tanggungan = df["jumlah_tanggungan"].to_numpy(dtype=float)
    target = ext.ANGGOTA_RUMAH_TANGGA_MISKIN

    # Selesaikan k pada persamaan  mean(1 + k * tanggungan) = target
    rata_tanggungan = tanggungan.mean()
    k = (target - 1.0) / rata_tanggungan if rata_tanggungan > 0 else 1.0

    return np.clip(np.round(1 + k * tanggungan), 2, 9).astype(int)


def hitung_beban_angsuran(
    nilai_pinjaman: np.ndarray, tenor_bulan: np.ndarray, pendapatan: np.ndarray,
    bunga_tahunan: float = 0.18,
) -> dict[str, np.ndarray]:
    """
    Hitung angsuran bulanan dan rasionya terhadap pendapatan.

    Bunga 18 persen efektif per tahun mewakili kisaran lazim koperasi simpan
    pinjam, yang berada di antara bank umum dan rentenir. Angsuran memakai
    rumus anuitas, bukan bunga flat, karena anuitas mencerminkan beban
    sesungguhnya secara lebih tepat.
    """
    pokok = np.asarray(nilai_pinjaman, dtype=float)
    n = np.asarray(tenor_bulan, dtype=float)
    i = bunga_tahunan / 12

    # Rumus anuitas: A = P * i / (1 - (1+i)^-n)
    angsuran = pokok * i / (1 - (1 + i) ** (-n))
    rasio = angsuran / np.maximum(pendapatan, 1)

    return {
        "angsuran_bulanan": np.round(angsuran),
        "rasio_angsuran_pendapatan": rasio,
        "sisa_pendapatan": pendapatan - angsuran,
        "lolos_batas_30persen": rasio <= ext.BATAS_RASIO_ANGSURAN,
    }


# --------------------------------------------------------------------------
# PELOKALAN LENGKAP
# --------------------------------------------------------------------------
def lokalkan(df: pd.DataFrame, sebaran_historis: np.ndarray) -> pd.DataFrame:
    """
    Tambahkan seluruh kolom berkonteks Surakarta ke berkas pengajuan.

    Kolom asli `jumlah_kredit` dalam DM DIPERTAHANKAN dengan nama
    `jumlah_kredit_historis`, supaya penelusuran balik ke sumber tetap bisa
    dilakukan dan pemetaan kuantil dapat diaudit.
    """
    df = df.copy()
    df["jumlah_kredit_historis"] = df["jumlah_kredit"]

    df["nilai_pengajuan_rp"] = petakan_nilai_pinjaman(
        df["jumlah_kredit"].to_numpy(), sebaran_historis
    )
    df["pendapatan_rt_rp"] = perkirakan_pendapatan(df)

    beban = hitung_beban_angsuran(
        df["nilai_pengajuan_rp"].to_numpy(),
        df["durasi_bulan"].to_numpy(),
        df["pendapatan_rt_rp"].to_numpy(),
    )
    for kolom, nilai in beban.items():
        df[kolom] = nilai

    df["anggota_rt"] = hitung_anggota_rumah_tangga(df)
    df["pengeluaran_per_kapita_rp"] = np.round(
        df["pendapatan_rt_rp"] / df["anggota_rt"]
    )

    df["status_kesejahteraan"] = [
        ext.klasifikasi_kesejahteraan(p, n)
        for p, n in zip(df["pendapatan_rt_rp"], df["anggota_rt"])
    ]
    # Rasio terhadap garis kemiskinan: di bawah 1 berarti miskin menurut BPS.
    df["rasio_garis_kemiskinan"] = (
        df["pengeluaran_per_kapita_rp"] / ext.GARIS_KEMISKINAN_JATENG.nilai
    ).round(3)

    return df


def ringkas_pelokalan(df: pd.DataFrame) -> str:
    """Ringkasan untuk dicetak pipeline."""
    gk = ext.GARIS_KEMISKINAN_JATENG.nilai
    return "\n".join([
        f"Nilai pengajuan   : Rp{df['nilai_pengajuan_rp'].min():,.0f} "
        f"sampai Rp{df['nilai_pengajuan_rp'].max():,.0f} "
        f"(median Rp{df['nilai_pengajuan_rp'].median():,.0f})",
        f"Pendapatan RT     : Rp{df['pendapatan_rt_rp'].min():,.0f} "
        f"sampai Rp{df['pendapatan_rt_rp'].max():,.0f}",
        f"Angsuran bulanan  : Rp{df['angsuran_bulanan'].min():,.0f} "
        f"sampai Rp{df['angsuran_bulanan'].max():,.0f}",
        f"Lolos batas 30%   : {int(df['lolos_batas_30persen'].sum())} "
        f"dari {len(df)} pemohon",
        f"Di bawah garis kemiskinan (Rp{gk:,.0f}/kapita): "
        f"{int((df['rasio_garis_kemiskinan'] < 1).sum())} pemohon",
        "Status kesejahteraan: "
        + ", ".join(
            f"{k} {v}" for k, v in
            df["status_kesejahteraan"].value_counts().items()
        ),
    ]).replace(",", ".")
