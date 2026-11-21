# Perhitungan Kriteria Keputusan C1–C6

Dokumen ini menguraikan cara enam kriteria keputusan dihitung beserta dasar
penetapan masing-masing. Seluruh definisi terpusat pada `src/config.py`,
sedangkan perhitungannya tersebar pada `src/knowledge.py`, `src/ml_model.py`,
dan `src/lokalisasi.py` menurut jenis dasarnya.

Keenam kriteria tidak diturunkan dengan cara yang seragam. C1 bersumber pada
aturan lembaga eksternal, C2 dan C6 merupakan transformasi satuan tanpa unsur
penilaian, C3 dan C5 dipelajari dari data historis, sedangkan C4 ditetapkan
sebagai kebijakan pengelola. Pembagian ini mengikuti paradigma Data-Dialog-Model:
komponen yang berasal dari kebijakan manusia dipisahkan dari komponen yang
berasal dari pola data, dan pemisahannya dibuat terlihat pada tingkat berkas.

| Kode | Kriteria | Arah | Rentang | Dasar penetapan |
|---|---|---|---|---|
| C1 | Indeks Kebutuhan Sosial | benefit | 0–10 | Kriteria rumah tangga miskin BPS |
| C2 | Kapasitas Angsur | benefit | 0–100 | Transformasi atribut A8 |
| C3 | Riwayat Kredit | benefit | 0–4 | Kalibrasi empiris data latih |
| C4 | Dampak Produktif | benefit | 0–4 | Kebijakan pengelola koperasi |
| C5 | Probabilitas Gagal Bayar | cost | 0–1 | Model Random Forest |
| C6 | Nilai Pengajuan | cost | Rupiah | Pemetaan kuantil |

---

## 1. C1 Indeks Kebutuhan Sosial

Kriteria ini mengukur tingkat deprivasi pemohon. Dasarnya adalah 14 kriteria
rumah tangga miskin yang dipakai Badan Pusat Statistik. Dari keempat belas
kriteria tersebut, sepuluh memiliki padanan atribut pada basis data historis
dan dipertahankan. Empat sisanya, yaitu luas lantai per kapita, jenis lantai,
jenis dinding, dan sumber air minum, tidak memiliki padanan dan dinyatakan
hilang secara eksplisit pada `IKS_INDIKATOR_TIDAK_TERSEDIA`. Keempatnya tidak
diimputasi, karena imputasi atas indikator yang sama sekali tidak terwakili
akan menghasilkan angka yang tampak sah tanpa dasar.

Setiap indikator bernilai 1 apabila kondisi deprivasi terpenuhi dan 0 apabila
tidak. Skor akhir adalah penjumlahan sederhana tanpa pembobotan, mengikuti cara
BPS memperlakukan keempat belas kriteria aslinya.

```
IKS = K1 + K2 + K3 + K4 + K5 + K6 + K7 + K8 + K9 + K10
```

Definisi kesepuluh indikator beserta frekuensi kemunculannya pada 1.000 data
historis:

| Indikator | Atribut sumber | Kondisi deprivasi | Frekuensi |
|---|---|---|---|
| K1 tanpa rekening | status_rekening | A11, A14 | 66,8% |
| K2 tanpa tabungan | tabungan | A61, A65 | 78,6% |
| K3 tanpa aset | kepemilikan_aset | A124 | 15,4% |
| K4 rumah bukan milik | status_rumah | A151, A153 | 28,7% |
| K5 pekerjaan rentan | jenis_pekerjaan | A171, A172 | 22,2% |
| K6 kerja tidak tetap | lama_bekerja | A71, A72 | 23,4% |
| K7 tanpa telepon | telepon | A191 | 59,6% |
| K8 tanpa penjamin | penjamin | A101 | 90,7% |
| K9 status rentan | status_personal | A91, A92, A95 | 36,0% |
| K10 pekerja asing | pekerja_asing | A201 | 96,3% |

Pada 1.000 data historis skor berkisar 2 sampai 10 dengan rata-rata 5,18 dan
median 5. Pada kohort 40 pemohon periode berjalan skor berkisar 2 sampai 8
dengan rata-rata 4,97.

Kolom per indikator sengaja dipertahankan dan tidak dihapus setelah penjumlahan.
Tanpa kolom tersebut, sistem hanya dapat menyatakan bahwa seorang pemohon
memperoleh skor 7 tanpa dapat menyebutkan indikator mana yang menyusunnya,
sehingga penolakan pengajuan tidak dapat dipertanggungjawabkan kepada pemohon.

Dua keterbatasan melekat pada konstruksi ini. Pertama, indikator K10 terpenuhi
pada 96,3% kasus sehingga nyaris tidak membedakan pemohon satu dari lainnya;
secara efektif skor disusun oleh sembilan indikator. Kedua, kode A95 pada
indikator K9 tidak pernah muncul pada data, dan kode A92 yang tersisa
menggabungkan jenis kelamin dengan status perkawinan dalam satu kategori
sebagaimana didefinisikan sumbernya.

Implementasi: `terapkan_aturan_iks()` pada `src/knowledge.py`.

---

## 2. C2 Kapasitas Angsur

Kriteria ini mengukur keringanan beban angsuran terhadap pendapatan disposabel
pemohon. Atribut sumbernya, A8 pada basis data historis, sudah berskala ordinal
1 sampai 4, dengan nilai 1 menandakan angsuran menyerap porsi terkecil dari
pendapatan.

Arah atribut asli berlawanan dengan kebutuhan pemeringkatan. Nilai yang besar
pada A8 berarti beban yang berat, sedangkan kriteria benefit menuntut nilai
besar berarti kondisi baik. Atribut karena itu dibalik lalu diskalakan ke
rentang 0 sampai 100.

```
kapasitas_angsur = (4 - rasio_angsuran) / 3 × 100
```

Karena atribut sumbernya hanya memiliki empat tingkat, kriteria ini hanya
menghasilkan empat nilai. Sebarannya pada 40 pemohon periode berjalan:

| Nilai C2 | rasio_angsuran | Jumlah pemohon |
|---|---|---|
| 0 | 4 | 24 |
| 33,3 | 3 | 3 |
| 66,7 | 2 | 10 |
| 100 | 1 | 3 |

Rata-rata 26,67. Penumpukan pada nilai terendah berarti kriteria ini tidak
membedakan 24 pemohon tersebut satu sama lain. Keterbatasan ini berasal dari
granularitas atribut sumber, bukan dari rumusnya. Apabila data koperasi
menyediakan nominal angsuran dan pendapatan yang sesungguhnya, rumus diganti
dengan rasio nominal dan kriteria ini menjadi benar-benar kontinu.

Implementasi: `terapkan_kriteria_turunan()` pada `src/knowledge.py`.

---

## 3. C3 Riwayat Kredit

Kriteria ini menilai catatan pembayaran pinjaman pemohon sebelumnya. Penetapan
skornya menempuh dua versi, dan kedua versi dipertahankan di dalam kode untuk
keperluan uji iterasi.

Versi pertama disusun berdasarkan penalaran pakar: pemohon yang belum pernah
menunggak dinilai paling baik, pemohon dengan akun kritis dinilai paling buruk.
Versi kedua diturunkan dari tingkat gagal bayar yang teramati pada data latih,
dan hasilnya berlawanan dengan penalaran versi pertama.

Prosedur kalibrasi mengelompokkan data latih menurut kode riwayat kredit,
menghitung proporsi kasus macet pada tiap kelompok, mengurutkannya dari terendah
ke tertinggi, lalu memberi skor 4 sampai 0 menurut urutan tersebut.

```python
tingkat_macet = df_latih.groupby("riwayat_kredit")["target_macet"].mean().sort_values()
skor = {kode: 4 - i for i, kode in enumerate(tingkat_macet.index)}
```

Hasil kalibrasi pada 700 data latih:

| Kode | Keterangan | Tingkat macet | n | Skor |
|---|---|---|---|---|
| A34 | Akun kritis / kredit di lembaga lain | 17,6% | 205 | 4 |
| A32 | Kredit berjalan, pembayaran lancar | 31,8% | 362 | 3 |
| A33 | Pernah menunggak | 32,8% | 67 | 2 |
| A31 | Semua kredit di bank ini lunas | 55,3% | 38 | 1 |
| A30 | Belum pernah kredit | 57,1% | 28 | 0 |

Temuan utamanya adalah pemohon tanpa riwayat kredit justru paling sering macet.
Gejala ini dikenal sebagai efek *thin file*: berkas yang kosong bukan berkas
yang bersih, melainkan berkas yang belum pernah teruji. Sebaliknya, pemohon
berstatus akun kritis telah dipercaya beberapa lembaga sekaligus dan masih
bertahan.

Kalibrasi hanya boleh memakai data latih. Memanggil prosedur ini dengan data
uji akan membocorkan informasi target dan membuat seluruh metrik evaluasi tidak
sah. Konsekuensinya, C3 tidak dapat dihitung pada tahap ETL dan baru dihitung
setelah pemisahan latih-uji.

Dua kelompok dengan jumlah anggota kecil, yaitu A31 dengan 38 kasus dan A30
dengan 28 kasus, menanggung ketidakpastian lebih besar daripada kelompok lain.
Selisih tingkat macet antara A32 dan A33 juga tipis, yaitu 31,8% berbanding
32,8%, sementara pemeringkatan tetap memberi keduanya skor berbeda.

Implementasi: `kalibrasi_skor_riwayat()` pada `src/knowledge.py`.

---

## 4. C4 Dampak Produktif

Kriteria ini menilai sejauh mana pinjaman membentuk kapasitas menghasilkan
pendapatan. Tidak ada data yang mendasarinya. Skornya ditetapkan pengelola
koperasi sebagai kebijakan prioritas, dan merupakan satu-satunya kriteria yang
sepenuhnya bersifat penilaian.

Penetapan dilakukan lewat tabel pencarian atas atribut tujuan pinjaman:

| Skor | Tujuan pinjaman | Pertimbangan |
|---|---|---|
| 4 | Modal usaha, pelatihan kerja | Langsung membentuk kapasitas produktif |
| 3 | Pendidikan, kendaraan bekas | Investasi berjangka panjang |
| 2 | Perbaikan rumah, perabot, kendaraan baru | Sebagian produktif, sebagian konsumtif |
| 1 | Alat rumah tangga, lainnya | Konsumtif dengan manfaat tidak langsung |
| 0 | Elektronik, liburan | Konsumtif |

Kode tujuan yang tidak terdaftar diberi nilai 1 sebagai nilai tengah netral.
Sebaran pada 40 pemohon periode berjalan menghasilkan rata-rata 1,68, dengan
16 pemohon berada pada skor 2.

Karena tidak bersandar pada data, skala ini wajib dikonfirmasi kepada responden
koperasi. Skala yang berlaku di satu koperasi belum tentu berlaku di koperasi
lain, dan perbedaan itu merupakan keputusan kebijakan, bukan kesalahan
pengukuran.

Implementasi: `SKOR_PRODUKTIF` pada `src/config.py`.

---

## 5. C5 Probabilitas Gagal Bayar

Kriteria ini merupakan keluaran model prediktif, satu-satunya komponen yang
tidak dihitung dengan rumus tertutup. Model yang dipakai adalah Random Forest
dengan 500 pohon keputusan, kedalaman maksimum 12, minimum 8 sampel per daun,
dan pembobotan kelas seimbang.

Setiap pohon menelusuri atribut pemohon hingga mencapai simpul daun, lalu
melaporkan proporsi kasus macet pada daun tersebut. Nilai akhir adalah rata-rata
dari 500 laporan. Masukannya berupa 20 atribut sekaligus, terdiri atas 7 atribut
numerik dan 13 atribut kategorik, sehingga model menemukan sendiri pola
interaksi antaratribut tanpa ditetapkan sebelumnya.

Model terpilih melalui validasi silang pada data latih:

| Model | CV AUC | Simpangan baku |
|---|---|---|
| RandomForest | 0,7746 | 0,0376 |
| LogisticRegression | 0,7618 | 0,0281 |
| HistGradientBoosting | 0,7534 | 0,0254 |

Keunggulan Random Forest terhadap Logistic Regression berada di dalam rentang
simpangan baku, sehingga tidak dapat disebut signifikan. Pada data uji model
menghasilkan AUC-ROC 0,7895, AUC-PR 0,6413, Brier 0,1855, dan recall 0,8222.

Atribut paling berpengaruh menurut *feature importance* adalah status rekening
(20,1%), durasi pinjaman (10,8%), jumlah kredit (10,0%), dan usia (7,0%).

Ambang klasifikasi ditetapkan pada 0,41, bukan 0,50. Dasarnya adalah matriks
biaya dataset yang menyatakan kesalahan meloloskan pemohon macet lima kali lebih
mahal daripada kesalahan menolak pemohon lancar. Pada ambang 0,41 total biaya
mencapai 170 unit, dibandingkan 190 unit pada ambang 0,50 dan 450 unit tanpa
model sama sekali. Ambang dipilih memakai prediksi *out-of-fold* data latih,
sehingga data uji tetap dipakai tepat satu kali.

Di luar ambang tersebut berlaku batas keras 0,60 yang ditetapkan sebagai
kebijakan kelembagaan. Pada rentang di atas nilai itu tingkat gagal bayar
historis melampaui 50 persen, sehingga penyaluran kredit justru merugikan
pemohon itu sendiri.

Nilai yang dihasilkan harus dibaca sebagai skor risiko relatif, bukan taksiran
peluang absolut. Dua alasan mendasarinya. Pembobotan kelas seimbang menggeser
keluaran dari proporsi populasi aslinya, dan nilai pinjaman diterjemahkan lewat
pemetaan kuantil sebagaimana diuraikan pada bagian berikutnya. Pembacaan yang
sah adalah bahwa seorang pemohon lebih berisiko daripada sekian persen pemohon
lain, bukan bahwa peluang gagal bayarnya sekian persen.

Implementasi: `src/ml_model.py`.

---

## 6. C6 Nilai Pengajuan

Kriteria ini mencatat besaran dana yang diminta. Karena basis data historis
berdenominasi Deutsche Mark sementara keputusan koperasi berdenominasi Rupiah,
kedua ruang nilai harus dihubungkan secara eksplisit. Penghubungnya adalah
pemetaan kuantil, bukan perkalian kurs.

Nilai diterjemahkan menurut posisi relatifnya. Pinjaman yang berada pada
persentil ke-60 sebaran historis dipetakan ke persentil ke-60 sebaran pinjaman
koperasi di Surakarta. Prosedurnya terdiri atas tiga langkah:

1. Tentukan posisi persentil nilai pinjaman pada sebaran historis.
2. Ambil nilai pada persentil yang sama dari sebaran rujukan Rupiah.
3. Bulatkan ke kelipatan Rp50.000 mengikuti praktik pencairan koperasi.

Sebaran rujukan dibangkitkan dari sebaran log-normal dengan 4.000 titik,
dinyatakan sebagai kelipatan Upah Minimum Kota Surakarta sebesar Rp2.570.000
agar tetap sahih ketika upah minimum berubah. Rentangnya dibatasi 0,4 sampai 6
kali upah minimum, menghasilkan plafon Rp1.050.000 sampai Rp15.400.000 dengan
median Rp3.350.000. Sebaran log-normal dipilih karena nilai pinjaman mikro
menumpuk pada nominal kecil dengan ekor panjang ke kanan; sebaran normal akan
menghasilkan nilai negatif dan meremehkan ekor kanan.

Pada 40 pemohon periode berjalan nilai pengajuan berkisar Rp1.050.000 sampai
Rp14.650.000 dengan median Rp3.200.000 dan total Rp156.100.000.

Metode ini memikul satu asumsi yang harus dinyatakan terbuka, yaitu bahwa
struktur risiko bersifat ordinal: pemohon yang meminjam relatif besar terhadap
sebaran kelompoknya menanggung risiko lebih tinggi, terlepas dari mata uang dan
negaranya. Asumsi tersebut tidak dapat diuji dengan data yang tersedia, karena
pengujiannya memerlukan data angsuran koperasi Indonesia yang berlabel lancar
atau macet.

Sebaran rujukan sendiri merupakan asumsi produk, bukan statistik terukur.
Fungsi `pasang_sebaran_rujukan()` disediakan untuk menggantinya dengan sebaran
plafon koperasi mitra yang sesungguhnya.

Implementasi: `petakan_nilai_pinjaman()` pada `src/lokalisasi.py`.

---

## 7. Contoh perhitungan

Pemohon P0373, peringkat pertama pada periode berjalan.

Atribut mentah yang relevan: status rekening A14, tabungan A61, kepemilikan
aset A121, status rumah A151, jenis pekerjaan A173, lama bekerja A72, telepon
A191, penjamin A101, status personal A92, pekerja asing A201, riwayat kredit
A34, tujuan pinjaman A42, rasio angsuran 1, jumlah kredit 2.146.

**C1.** Delapan dari sepuluh indikator terpenuhi, yaitu K1, K2, K4, K6, K7, K8,
K9, dan K10. Indikator K3 tidak terpenuhi karena pemohon memiliki properti, dan
K5 tidak terpenuhi karena pekerjaannya tergolong terampil. Skor C1 sama dengan 8.

**C2.** Rasio angsuran bernilai 1, maka (4 − 1) ÷ 3 × 100 = 100.

**C3.** Riwayat kredit berkode A34 dengan tingkat macet terendah pada data
latih, maka skor C3 sama dengan 4.

**C4.** Tujuan pinjaman A42 berupa perabot, tergolong sebagian produktif, maka
skor C4 sama dengan 2.

**C5.** Model menghasilkan probabilitas gagal bayar 0,3023.

**C6.** Pinjaman 2.146 DM berada pada persentil 46,4% sebaran historis. Nilai
pada persentil yang sama di sebaran rujukan adalah Rp3.150.000, dan hasilnya
sudah merupakan kelipatan Rp50.000.

| Kriteria | Nilai | Arah |
|---|---|---|
| C1 Indeks Kebutuhan Sosial | 8 | benefit |
| C2 Kapasitas Angsur | 100 | benefit |
| C3 Riwayat Kredit | 4 | benefit |
| C4 Dampak Produktif | 2 | benefit |
| C5 Probabilitas Gagal Bayar | 0,3023 | cost |
| C6 Nilai Pengajuan | Rp3.150.000 | cost |

Keenam nilai tersebut menghasilkan skor TOPSIS 0,7982 dan menempatkan P0373
pada peringkat pertama dari 40 pemohon dengan status disetujui. Pemohon ini
tidak unggul pada seluruh kriteria; C4 hanya bernilai 2 dari 4, dan C6
menurunkan skornya. Keunggulannya terletak pada dua kriteria berbobot terbesar,
yaitu C1 dengan bobot 0,2887 dan C5 dengan bobot 0,2842.

---

## 8. Urutan perhitungan

Urutan tahapan ditentukan oleh satu batasan, yaitu setiap komponen yang
menyentuh label target hanya boleh dihitung dari data latih.

```
ETL dan C1                     label belum tersentuh
   ↓
Pemisahan 700 latih / 300 uji  data uji disegel
   ↓
Pelatihan model                pemilihan model dan ambang out-of-fold
   ↓
Kalibrasi C3                   memakai label, wajib data latih saja
   ↓
Pengambilan 40 pemohon         diambil dari data uji
   ↓
C2, C4, C5, C6                 dihitung untuk kohort periode berjalan
   ↓
Matriks keputusan 40 × 6       masukan AHP dan TOPSIS
```

C1 boleh dihitung pada tahap ETL karena aturan BPS tidak menyentuh kolom label
sama sekali. C3 tidak boleh, karena skornya diturunkan dari proporsi kasus macet.
Memindahkan kalibrasi C3 ke tahap ETL akan membuat skor tersebut menghafal
jawaban data uji, dan seluruh angka evaluasi kehilangan keabsahannya.

Kohort 40 pemohon diambil dari data uji, bukan data latih, agar meniru berkas
yang baru masuk ke meja petugas. Pengambilan dari data latih akan menghasilkan
probabilitas gagal bayar yang terlalu optimistis karena model sudah pernah
melihat kasus tersebut, dan klaim tingkat macet pada bab evaluasi tidak akan
berarti apa-apa.
