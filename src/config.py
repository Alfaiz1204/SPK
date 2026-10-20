"""
Konfigurasi terpusat SPK Prioritisasi Penyaluran Kredit Mikro.

Seluruh konstanta domain (nama kolom, kamus kode, definisi kriteria, matriks AHP)
dikumpulkan di satu tempat agar subsistem Data, Model, dan Dialog membaca
definisi yang sama. Ini mencegah "drift" antara skor yang dihitung pipeline
dan skor yang ditampilkan antarmuka.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# PATH
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
TABLES = OUTPUTS / "tables"

DB_PATH = DATA_PROCESSED / "spk.db"
RAW_CSV = DATA_RAW / "german.csv"

# Sumber data primer. UCI id=144 (Statlog German Credit), lisensi CC BY 4.0.
# URL mirror dipakai karena beberapa jaringan kampus memblokir archive.ics.uci.edu.
SOURCE_URL_PRIMARY = "https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip"
SOURCE_URL_MIRROR = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/german.csv"

RANDOM_STATE = 42

# --------------------------------------------------------------------------
# SKEMA DATASET MENTAH
# Urutan kolom mengikuti berkas german.data asli (20 atribut + 1 target).
# --------------------------------------------------------------------------
RAW_COLUMNS = [
    "status_rekening",        # A1  status rekening giro
    "durasi_bulan",           # A2  tenor
    "riwayat_kredit",         # A3
    "tujuan_pinjaman",        # A4
    "jumlah_kredit",          # A5
    "tabungan",               # A6
    "lama_bekerja",           # A7
    "rasio_angsuran",         # A8  % angsuran terhadap pendapatan disposabel
    "status_personal",        # A9
    "penjamin",               # A10
    "lama_domisili",          # A11
    "kepemilikan_aset",       # A12
    "usia",                   # A13
    "cicilan_lain",           # A14
    "status_rumah",           # A15
    "jumlah_kredit_aktif",    # A16
    "jenis_pekerjaan",        # A17
    "jumlah_tanggungan",      # A18
    "telepon",                # A19
    "pekerja_asing",          # A20
    "label_risiko",           # target: 1 = lancar (good), 2 = macet (bad)
]

NUMERIC_COLUMNS = [
    "durasi_bulan", "jumlah_kredit", "rasio_angsuran", "lama_domisili",
    "usia", "jumlah_kredit_aktif", "jumlah_tanggungan",
]

CATEGORICAL_COLUMNS = [c for c in RAW_COLUMNS[:-1] if c not in NUMERIC_COLUMNS]

# --------------------------------------------------------------------------
# KAMUS KODE -> LABEL TERBACA
# Dibutuhkan subsistem Dialog: pengambil keputusan tidak bisa menilai "A34".
# Sumber definisi: berkas german.doc pada UCI Repository.
# --------------------------------------------------------------------------
CODE_LABELS = {
    "status_rekening": {
        "A11": "Saldo giro negatif",
        "A12": "Saldo 0-200 DM",
        "A13": "Saldo >= 200 DM / gaji disalurkan >= 1 th",
        "A14": "Tidak punya rekening giro",
    },
    "riwayat_kredit": {
        "A30": "Belum pernah kredit / semua lunas",
        "A31": "Semua kredit di bank ini lunas",
        "A32": "Kredit berjalan, pembayaran lancar",
        "A33": "Pernah menunggak",
        "A34": "Akun kritis / kredit di lembaga lain",
    },
    "tujuan_pinjaman": {
        "A40": "Kendaraan baru", "A41": "Kendaraan bekas",
        "A42": "Perabot / peralatan", "A43": "Elektronik",
        "A44": "Alat rumah tangga", "A45": "Perbaikan rumah",
        "A46": "Pendidikan", "A47": "Liburan",
        "A48": "Pelatihan kerja", "A49": "Modal usaha",
        "A410": "Lainnya",
    },
    "tabungan": {
        "A61": "< 100 DM", "A62": "100-500 DM", "A63": "500-1000 DM",
        "A64": ">= 1000 DM", "A65": "Tidak ada / tidak diketahui",
    },
    "lama_bekerja": {
        "A71": "Tidak bekerja", "A72": "< 1 tahun", "A73": "1-4 tahun",
        "A74": "4-7 tahun", "A75": ">= 7 tahun",
    },
    "status_personal": {
        "A91": "Laki-laki, cerai/pisah", "A92": "Perempuan, cerai/menikah",
        "A93": "Laki-laki, lajang", "A94": "Laki-laki, menikah/duda",
        "A95": "Perempuan, lajang",
    },
    "penjamin": {"A101": "Tidak ada", "A102": "Pengaju bersama", "A103": "Penjamin"},
    "kepemilikan_aset": {
        "A121": "Properti / tanah", "A122": "Tabungan perumahan / asuransi jiwa",
        "A123": "Kendaraan / aset lain", "A124": "Tidak ada aset",
    },
    "cicilan_lain": {"A141": "Di bank lain", "A142": "Di toko", "A143": "Tidak ada"},
    "status_rumah": {"A151": "Sewa", "A152": "Milik sendiri", "A153": "Menumpang"},
    "jenis_pekerjaan": {
        "A171": "Tidak bekerja / tidak terampil non-residen",
        "A172": "Tidak terampil, residen",
        "A173": "Terampil / pegawai",
        "A174": "Manajerial / wiraswasta / ahli",
    },
    "telepon": {"A191": "Tidak terdaftar", "A192": "Terdaftar"},
    "pekerja_asing": {"A201": "Ya", "A202": "Tidak"},
}

# --------------------------------------------------------------------------
# COST MATRIX ASLI DATASET
# UCI menyatakan biaya salah klasifikasi tidak simetris: meloloskan pemohon
# macet 5x lebih mahal daripada menolak pemohon lancar. Angka ini dipakai
# sebagai dasar pemilihan ambang (threshold) model, bukan akurasi mentah.
# --------------------------------------------------------------------------
COST_FN = 5.0   # aktual macet, diprediksi lancar
COST_FP = 1.0   # aktual lancar, diprediksi macet

# --------------------------------------------------------------------------
# BASIS PENGETAHUAN: INDEKS KEBUTUHAN SOSIAL (IKS)
#
# Adaptasi 14 kriteria rumah tangga miskin BPS ke atribut yang tersedia pada
# dataset. 10 indikator dipertahankan; 4 indikator BPS (luas lantai, jenis
# lantai, jenis dinding, sumber air minum) tidak punya padanan atribut dan
# dinyatakan hilang secara eksplisit, bukan diimputasi diam-diam.
#
# Setiap indikator bernilai 1 bila kondisi deprivasi terpenuhi. Skor IKS
# adalah jumlah indikator yang terpenuhi, rentang 0-10.
# --------------------------------------------------------------------------
IKS_RULES = {
    "K1_tanpa_rekening":   ("status_rekening", {"A11", "A14"}),
    "K2_tanpa_tabungan":   ("tabungan", {"A61", "A65"}),
    "K3_tanpa_aset":       ("kepemilikan_aset", {"A124"}),
    "K4_rumah_tidak_milik": ("status_rumah", {"A151", "A153"}),
    "K5_pekerjaan_rentan": ("jenis_pekerjaan", {"A171", "A172"}),
    "K6_kerja_tidak_tetap": ("lama_bekerja", {"A71", "A72"}),
    "K7_tanpa_telepon":    ("telepon", {"A191"}),
    "K8_tanpa_penjamin":   ("penjamin", {"A101"}),
    "K9_status_rentan":    ("status_personal", {"A91", "A92", "A95"}),
    "K10_pekerja_asing":   ("pekerja_asing", {"A201"}),
}
IKS_MAX = len(IKS_RULES)

# Indikator BPS yang tidak punya padanan pada dataset. Didaftarkan agar
# keterbatasan ini muncul di laporan, bukan tersembunyi di dalam kode.
IKS_INDIKATOR_TIDAK_TERSEDIA = [
    "Luas lantai per kapita < 8 m2",
    "Jenis lantai tanah/bambu/kayu murahan",
    "Jenis dinding bambu/rumbia/kayu berkualitas rendah",
    "Sumber air minum bukan air bersih terlindungi",
]

# Skor dampak produktif per tujuan pinjaman (0-4).
# Pinjaman yang membentuk kapasitas produktif diberi skor lebih tinggi
# daripada pinjaman konsumtif. Skala ditetapkan pengelola koperasi.
SKOR_PRODUKTIF = {
    "A49": 4,   # modal usaha
    "A48": 4,   # pelatihan kerja
    "A46": 3,   # pendidikan
    "A41": 3,   # kendaraan bekas (sering untuk operasional usaha)
    "A45": 2,   # perbaikan rumah
    "A42": 2,   # perabot / peralatan
    "A40": 2,   # kendaraan baru
    "A44": 1,   # alat rumah tangga
    "A410": 1,  # lainnya
    "A43": 0,   # elektronik
    "A47": 0,   # liburan
}

# Skor riwayat kredit (0-4), makin tinggi makin baik.
#
# V1 - penilaian pakar (iterasi 1). Logikanya: "belum pernah menunggak" dianggap
#      paling baik, "akun kritis" paling buruk. Intuitif, dan SALAH.
#
# V2 - kalibrasi empiris (iterasi 2). Diturunkan dari tingkat gagal bayar yang
#      teramati PADA DATA LATIH SAJA, lalu diperingkat. Data menunjukkan pemohon
#      tanpa riwayat kredit justru paling sering macet (efek thin file):
#      berkas kosong bukan berkas bersih. Lihat docs/CATATAN_ITERASI.md.
#
# V1 sengaja dipertahankan di dalam kode sebagai pembanding pada uji iterasi,
# bukan sebagai sisa kode mati.
SKOR_RIWAYAT_V1_PAKAR = {"A34": 0, "A33": 1, "A32": 2, "A31": 3, "A30": 4}
SKOR_RIWAYAT_V2_KALIBRASI = {"A34": 4, "A32": 3, "A33": 2, "A31": 1, "A30": 0}

VERSI_SKOR_RIWAYAT_AKTIF = "V2"

# --------------------------------------------------------------------------
# KRITERIA KEPUTUSAN MCDM
# benefit=True berarti makin besar makin baik.
# --------------------------------------------------------------------------
CRITERIA = [
    # kode, nama, kolom sumber, benefit?, satuan
    ("C1", "Indeks Kebutuhan Sosial", "iks_skor",        True,  "0-10"),
    ("C2", "Kapasitas Angsur",        "kapasitas_angsur", True,  "0-100"),
    ("C3", "Riwayat Kredit",          "skor_riwayat",     True,  "0-4"),
    ("C4", "Dampak Produktif",        "skor_produktif",   True,  "0-4"),
    ("C5", "Probabilitas Gagal Bayar", "pd_model",        False, "0-1"),
    ("C6", "Nilai Pengajuan",         "nilai_pengajuan_rp", False, "Rp"),
]
CRITERIA_CODES = [c[0] for c in CRITERIA]
CRITERIA_NAMES = {c[0]: c[1] for c in CRITERIA}
CRITERIA_COLUMNS = {c[0]: c[2] for c in CRITERIA}
CRITERIA_BENEFIT = {c[0]: c[3] for c in CRITERIA}

# --------------------------------------------------------------------------
# MATRIKS PERBANDINGAN BERPASANGAN AHP
#
# Hasil wawancara terstruktur dengan Manajer Koperasi (pengambil keputusan).
# Urutan baris/kolom mengikuti CRITERIA_CODES: C1..C6.
# Nilai mengikuti skala Saaty 1-9. Matriks ini WAJIB lolos uji CR <= 0.10;
# bila tidak, wawancara diulang. Jangan "perbaiki" matriks secara diam-diam.
# --------------------------------------------------------------------------
# Penilaian dikumpulkan dari TIGA responden, bukan satu, lalu diagregasi
# dengan rata-rata geometrik (Aggregation of Individual Judgments, Saaty).
# Rata-rata geometrik dipakai, bukan aritmetik, karena hanya rata-rata
# geometrik yang mempertahankan sifat resiprokal matriks: jika responden A
# menilai 3 dan responden B menilai 1/3, hasilnya harus 1, dan rata-rata
# aritmetik akan menghasilkan 1,67.
#
# R1 Manajer Koperasi      - menimbang keberlanjutan dana anggota
# R2 Ketua Pengurus        - menimbang misi sosial koperasi
# R3 Petugas Analis Kredit - menimbang kelayakan teknis berkas
AHP_RESPONDEN = {
    "R1_Manajer": [
        [1.0,   2.0,   3.0,   3.0,   1.0,   5.0],
        [1/2.0, 1.0,   2.0,   2.0,   1/2.0, 3.0],
        [1/3.0, 1/2.0, 1.0,   1.0,   1/2.0, 2.0],
        [1/3.0, 1/2.0, 1.0,   1.0,   1/3.0, 2.0],
        [1.0,   2.0,   2.0,   3.0,   1.0,   4.0],
        [1/5.0, 1/3.0, 1/2.0, 1/2.0, 1/4.0, 1.0],
    ],
    "R2_Ketua": [
        [1.0,   3.0,   4.0,   3.0,   2.0,   5.0],
        [1/3.0, 1.0,   2.0,   1.0,   1/2.0, 3.0],
        [1/4.0, 1/2.0, 1.0,   1/2.0, 1/3.0, 2.0],
        [1/3.0, 1.0,   2.0,   1.0,   1/2.0, 2.0],
        [1/2.0, 2.0,   3.0,   2.0,   1.0,   4.0],
        [1/5.0, 1/3.0, 1/2.0, 1/2.0, 1/4.0, 1.0],
    ],
    "R3_Analis": [
        [1.0,   1.0,   2.0,   3.0,   1/2.0, 4.0],
        [1.0,   1.0,   2.0,   2.0,   1/2.0, 3.0],
        [1/2.0, 1/2.0, 1.0,   2.0,   1/3.0, 2.0],
        [1/3.0, 1/2.0, 1/2.0, 1.0,   1/4.0, 2.0],
        [2.0,   2.0,   3.0,   4.0,   1.0,   5.0],
        [1/4.0, 1/3.0, 1/2.0, 1/2.0, 1/5.0, 1.0],
    ],
}

# Matriks tunggal di bawah dipertahankan untuk uji regresi dan perbandingan
# terhadap hasil agregasi kelompok.
AHP_PAIRWISE = [
    #        C1     C2     C3     C4     C5     C6
    [      1.0,   2.0,   3.0,   3.0,   1.0,   5.0],  # C1 Kebutuhan sosial
    [  1 / 2.0,   1.0,   2.0,   2.0, 1 / 2.0,  3.0],  # C2 Kapasitas angsur
    [  1 / 3.0, 1 / 2.0, 1.0,   1.0, 1 / 2.0,  2.0],  # C3 Riwayat kredit
    [  1 / 3.0, 1 / 2.0, 1.0,   1.0, 1 / 3.0,  2.0],  # C4 Dampak produktif
    [      1.0,   2.0,   2.0,   3.0,   1.0,   4.0],  # C5 Probabilitas gagal bayar
    [  1 / 5.0, 1 / 3.0, 1 / 2.0, 1 / 2.0, 1 / 4.0, 1.0],  # C6 Nilai pengajuan
]

# Random Index Saaty untuk n = 1..10, dipakai menghitung Consistency Ratio.
SAATY_RI = [0.0, 0.0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49]
CR_THRESHOLD = 0.10

# --------------------------------------------------------------------------
# PARAMETER KEPUTUSAN OPERASIONAL
# --------------------------------------------------------------------------
# Plafon Rp60 juta, sementara total pengajuan sekitar Rp156 juta,
# yaitu sekitar 2,6x dana tersedia. Kelangkaan inilah yang menciptakan masalah
# keputusan. Bila plafon mencukupi seluruh pengajuan, pemeringkatan tidak ada
# gunanya dan sistem ini tidak perlu dibangun.
PLAFON_PERIODE = 60_000_000    # total dana periode ini (Rupiah)
N_PEMOHON_PERIODE = 40       # jumlah berkas pengajuan yang diproses

# Batas keras PD. Ditetapkan pengelola koperasi, bukan dioptimasi dari data.
# Pada rentang di atas 0,60 tingkat gagal bayar historis melampaui 50 persen,
# sehingga menyalurkan kredit justru merugikan pemohon itu sendiri.
PD_HARD_LIMIT = 0.60
