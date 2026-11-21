"""
Konstanta domain: skema kolom, kamus kode, definisi kriteria, matriks AHP.

Dikumpulkan di satu tempat agar pipeline dan antarmuka membaca definisi yang
sama.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
TABLES = OUTPUTS / "tables"

DB_PATH = DATA_PROCESSED / "spk.db"
RAW_CSV = DATA_RAW / "german.csv"

# Statlog German Credit, UCI id=144, lisensi CC BY 4.0. Mirror dipakai karena
# sebagian jaringan kampus memblokir archive.ics.uci.edu.
SOURCE_URL_PRIMARY = "https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip"
SOURCE_URL_MIRROR = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/german.csv"

RANDOM_STATE = 42

# Urutan mengikuti german.data asli. Berkasnya tanpa header, sehingga kolom
# dipetakan murni dari urutan ini.
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

# Sumber definisi: berkas german.doc pada UCI Repository.
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

# Biaya salah klasifikasi menurut dataset: meloloskan pemohon macet 5x lebih
# mahal daripada menolak pemohon lancar. Dipakai memilih ambang model.
COST_FN = 5.0   # aktual macet, diprediksi lancar
COST_FP = 1.0   # aktual lancar, diprediksi macet

# Adaptasi 14 kriteria rumah tangga miskin BPS; 10 indikator punya padanan
# atribut. Tiap indikator bernilai 1 bila deprivasi terpenuhi, IKS = jumlahnya.
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

# Empat indikator BPS tanpa padanan atribut, didaftarkan agar keterbatasan ini
# terbawa ke laporan alih-alih diimputasi diam-diam.
IKS_INDIKATOR_TIDAK_TERSEDIA = [
    "Luas lantai per kapita < 8 m2",
    "Jenis lantai tanah/bambu/kayu murahan",
    "Jenis dinding bambu/rumbia/kayu berkualitas rendah",
    "Sumber air minum bukan air bersih terlindungi",
]

# Skor dampak produktif per tujuan pinjaman (0-4), ditetapkan pengelola
# koperasi. Tidak diturunkan dari data.
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

# Skor riwayat kredit (0-4), makin tinggi makin baik. V1 penilaian pakar; V2
# diperingkat dari tingkat gagal bayar pada data latih, dan urutannya ternyata
# terbalik dari V1 (efek thin file). V1 dipertahankan sebagai pembanding pada
# uji iterasi. Lihat docs/CATATAN_ITERASI.md.
SKOR_RIWAYAT_V1_PAKAR = {"A34": 0, "A33": 1, "A32": 2, "A31": 3, "A30": 4}
SKOR_RIWAYAT_V2_KALIBRASI = {"A34": 4, "A32": 3, "A33": 2, "A31": 1, "A30": 0}

VERSI_SKOR_RIWAYAT_AKTIF = "V2"

# benefit=True berarti makin besar makin baik.
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

# Hasil wawancara pembobotan dengan tiga pengurus koperasi, dikumpulkan lewat
# borang daring pada 20-21 November 2026. Instrumennya ada pada
# instrumen/INSTRUMEN_WAWANCARA_AHP.md, dan jawaban mentahnya pada berkas
# "Penilaian Prioritas Penyaluran Kredit Koperasi (Jawaban).xlsx".
#
# Matriks disusun src/wawancara.py dari 15 jawaban berpasangan tiap responden,
# tidak diketik tangan: matriks yang salah ketik tetap lolos uji CR, hanya
# bobotnya yang keliru. Urutan baris/kolom mengikuti CRITERIA_CODES C1..C6.
#
# Agregasi memakai rata-rata geometrik (Saaty AIJ), bukan aritmetik, karena
# hanya rata-rata geometrik yang mempertahankan sifat resiprokal matriks.
#
# Ketiga responden melampaui ambang CR 0,10 secara individu (0,5005, 0,1634,
# 0,2296) sementara gabungannya lolos dengan 0,0643. Lihat
# AHP_WAJIB_KONSISTEN_PER_RESPONDEN di bawah.
#
# R1 Umi Yulianti           - Manajer / Bendahara Koperasi
# R2 Kun Zamza              - Manajer / Bendahara Koperasi
# R3 Mohammad Adib Alfiyan  - Ketua Pengurus
AHP_RESPONDEN = {
    "R1_Umi_Manajer": [
        [  1.0,   1.0,   9.0,   1.0, 1/5.0,   1.0],
        [  1.0,   1.0,   1.0, 1/5.0,   1.0,   5.0],
        [1/9.0,   1.0,   1.0,   1.0, 1/5.0,   7.0],
        [  1.0,   5.0,   1.0,   1.0, 1/5.0,   9.0],
        [  5.0,   1.0,   5.0,   5.0,   1.0,   1.0],
        [  1.0, 1/5.0, 1/7.0, 1/9.0,   1.0,   1.0],
    ],
    "R2_Kun_Bendahara": [
        [  1.0, 1/9.0, 1/7.0, 1/7.0, 1/7.0,   1.0],
        [  9.0,   1.0, 1/7.0,   1.0, 1/9.0,   1.0],
        [  7.0,   7.0,   1.0,   7.0,   1.0,   7.0],
        [  7.0,   1.0, 1/7.0,   1.0, 1/7.0,   7.0],
        [  7.0,   9.0,   1.0,   7.0,   1.0,   9.0],
        [  1.0,   1.0, 1/7.0, 1/7.0, 1/9.0,   1.0],
    ],
    "R3_Adib_Ketua": [
        [  1.0, 1/7.0, 1/9.0, 1/7.0, 1/5.0,   1.0],
        [  7.0,   1.0, 1/5.0,   1.0, 1/3.0,   5.0],
        [  9.0,   5.0,   1.0,   1.0,   1.0,   3.0],
        [  7.0,   1.0,   1.0,   1.0,   1.0, 1/3.0],
        [  5.0,   3.0,   1.0,   1.0,   1.0,   3.0],
        [  1.0, 1/5.0, 1/3.0,   3.0, 1/3.0,   1.0],
    ],
}

# Haruskah tiap responden lolos CR <= 0,10 secara individu?
# True  - responden tidak konsisten ditolak, pipeline berhenti.
# False - dilaporkan sebagai peringatan, yang diuji matriks gabungan. Dasarnya
#         metode AIJ (Forman & Peniwati, 1998): yang dinilai konsistensi
#         kelompok, bukan tiap individu.
# Kembalikan ke True setelah wawancara ulang dijalankan.
AHP_WAJIB_KONSISTEN_PER_RESPONDEN = False

# Matriks tunggal dipertahankan untuk uji regresi dan perbandingan terhadap
# hasil agregasi kelompok. Isinya MENGACU ke salah satu responden, tidak
# disalin, supaya tidak bisa berbeda diam-diam dari AHP_RESPONDEN.
#
# Perhatikan bahwa matriks ini mewakili SATU responden dengan CR 0,5005.
# Bobot yang sah untuk pengambilan keputusan adalah bobot gabungan dari
# ahp.bobot_kelompok(), bukan bobot dari matriks ini.
AHP_PAIRWISE = AHP_RESPONDEN["R1_Umi_Manajer"]

# Random Index Saaty untuk n = 1..10, dipakai menghitung Consistency Ratio.
SAATY_RI = [0.0, 0.0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49]
CR_THRESHOLD = 0.10

# Plafon Rp60 juta atas total pengajuan sekitar Rp156 juta (2,6x). Kelangkaan
# inilah yang menciptakan masalah keputusannya.
PLAFON_PERIODE = 60_000_000    # total dana periode ini (Rupiah)
N_PEMOHON_PERIODE = 40       # jumlah berkas pengajuan yang diproses

# Batas keras PD, ditetapkan pengelola koperasi. Di atas 0,60 tingkat gagal
# bayar historis melampaui 50 persen.
PD_HARD_LIMIT = 0.60
