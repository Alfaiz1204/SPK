# Catatan Iterasi Pengembangan Prototipe

Dokumen ini mencatat perubahan rancangan beserta alasannya. Setiap iterasi
memuat temuan yang memicu perubahan, perubahan yang dilakukan, dan dampaknya
terhadap hasil. Tanpa catatan semacam ini, klaim "sistem dikembangkan secara
iteratif" tidak bisa diverifikasi.

---

## Iterasi 1 — Rancangan awal

**Isi:** ETL dari UCI Statlog German Credit, Random Forest untuk prediksi
gagal bayar, AHP untuk bobot, TOPSIS untuk pemeringkatan.

**Keputusan rancangan awal yang kemudian terbukti salah:**

Skor riwayat kredit (kriteria C3) disusun berdasarkan penalaran pakar yang
terasa wajar:

| Kode | Arti | Skor pakar |
|---|---|---|
| A30 | Belum pernah kredit / semua lunas | 4 (terbaik) |
| A31 | Semua kredit di bank ini lunas | 3 |
| A32 | Kredit berjalan, pembayaran lancar | 2 |
| A33 | Pernah menunggak | 1 |
| A34 | Akun kritis / kredit di lembaga lain | 0 (terburuk) |

---

## Iterasi 2 — Kalibrasi skor riwayat kredit

**Temuan yang memicu perubahan.** Pemeriksaan tingkat gagal bayar aktual per
kode pada data latih menunjukkan urutan yang berkebalikan dengan penilaian
pakar:

| Kode | Arti | Macet (data latih) | Skor V1 | Skor V2 |
|---|---|---|---|---|
| A34 | Akun kritis / kredit di lembaga lain | 17,6% | 0 | **4** |
| A32 | Kredit berjalan, pembayaran lancar | 31,8% | 2 | **3** |
| A33 | Pernah menunggak | 32,8% | 1 | **2** |
| A31 | Semua kredit di bank ini lunas | 55,3% | 3 | **1** |
| A30 | Belum pernah kredit / semua lunas | 57,1% | 4 | **0** |

**Penjelasan.** Ini adalah efek *thin file*: berkas kosong bukan berkas
bersih. Pemohon tanpa riwayat kredit belum pernah diuji kemampuannya membayar
cicilan, sementara pemohon berstatus "akun kritis" justru terbukti punya
akses kredit aktif di lembaga lain, yang berarti sudah lolos penilaian pihak
ketiga.

**Perubahan.** `SKOR_RIWAYAT` diganti menjadi dua peta terversi
(`SKOR_RIWAYAT_V1_PAKAR` dan `SKOR_RIWAYAT_V2_KALIBRASI`), dengan V2 sebagai
versi aktif. Kalibrasi dihitung oleh `knowledge.kalibrasi_skor_riwayat()`
dan **hanya boleh menerima data latih**; memanggilnya dengan data uji
menimbulkan kebocoran target.

**Catatan penting.** V1 tidak dihapus. Perbedaan antara penilaian pakar dan
perilaku data adalah temuan, bukan kesalahan yang perlu disembunyikan.
Perbandingan keduanya dipakai sebagai bahan diskusi dengan pengelola.

---

## Iterasi 3 — Perbaikan protokol evaluasi

**Temuan yang memicu perubahan.** Pada iterasi 1 dan 2, ambang keputusan
dipilih dengan menelusuri nilai yang meminimalkan biaya **pada data uji**.
Metrik yang dilaporkan karenanya terlalu optimistis: ambang disesuaikan
dengan data yang seharusnya belum pernah dilihat.

Masalah ini tidak terlihat pada keluaran program. Angkanya wajar, grafiknya
rapi, dan tidak ada pesan galat. Yang salah hanya urutan pemanggilan fungsi.

**Perubahan.** Protokol diubah menjadi:

1. Pisahkan latih (70%) dan uji (30%), terstratifikasi.
2. Pilih keluarga model dengan AUC validasi silang 5-lipat pada data latih.
3. Pilih ambang dari prediksi *out-of-fold* data latih.
4. Latih ulang model terpilih pada seluruh data latih.
5. Evaluasi **sekali** pada data uji.

**Dampak.** Ambang bergeser dari 0,33 (dipilih pada data uji) menjadi 0,41
(dipilih *out-of-fold*). Akurasi yang dilaporkan naik dari 0,5600 menjadi
0,6467, dan recall turun dari 0,9444 menjadi 0,8222. Angka iterasi 3 lebih
rendah pada recall, dan justru karena itu lebih bisa dipercaya.

**Tambahan.** Tiga kandidat model dibandingkan, bukan satu. Random Forest
terpilih (CV AUC 0,7746 ± 0,0376), tetapi selisihnya terhadap Logistic
Regression (0,7619) berada di dalam rentang simpangan baku, sehingga
keunggulan Random Forest **tidak dapat dinyatakan signifikan**. Ini
dilaporkan apa adanya.

---

## Iterasi 4 — Plafon yang mengikat dan validasi kebijakan

**Temuan yang memicu perubahan.** Dengan plafon awal 150.000 DM atas total
pengajuan 129.457 DM, seluruh 40 pemohon disetujui. Pemeringkatan tidak
berpengaruh apa pun terhadap hasil akhir, sehingga sistem tidak sedang
menguji apa yang hendak diuji.

**Perubahan.**

1. Plafon diturunkan ke 50.000 DM, yaitu 38,6% dari total pengajuan. Rasio
   permintaan menjadi 2,6x dana tersedia, dan kelangkaan inilah yang
   menciptakan masalah keputusan.
2. Batas keras PD diturunkan dari 0,75 (tidak pernah aktif, karena PD
   tertinggi hanya 0,691) menjadi 0,60, sehingga aturan tersebut benar-benar
   berlaku dan menolak 6 pemohon.
3. Ditambahkan modul `evaluasi.py` yang membandingkan SPK dengan empat
   kebijakan alternatif di bawah plafon yang sama.

**Hasil perbandingan kebijakan:**

| Kebijakan | n penerima | Macet aktual | IKS rata-rata |
|---|---|---|---|
| **SPK Hybrid (AHP+TOPSIS)** | 20 | **5,0%** | **5,35** |
| Hanya Risiko (PD terkecil) | 21 | 4,8% | 5,14 |
| Hanya Kebutuhan (IKS terbesar) | 24 | 20,8% | 5,58 |
| Siapa Cepat (FCFS) | 28 | 25,0% | 5,21 |
| Undian (rata-rata 2.000x) | 20,7 | 20,2% | 5,03 |

SPK Hybrid menangkap 98,4% dari potensi penurunan risiko yang bisa dicapai
pemeringkatan murni risiko, dan 58,1% dari potensi perbaikan ketepatan
sasaran yang bisa dicapai pemeringkatan murni kebutuhan, tanpa harus memilih
salah satu.

---

## Iterasi 5 — Koreksi narasi pertukaran

**Temuan yang memicu perubahan.** Gambar sebaran IKS terhadap PD pada berkas
periode berjalan diberi judul "pemohon yang paling membutuhkan cenderung
paling berisiko". Grafik yang dihasilkan menunjukkan korelasi **−0,077**,
yaitu berlawanan arah dengan judulnya sendiri.

**Pemeriksaan lanjutan:**

| Lingkup | Ukuran | Korelasi |
|---|---|---|
| Populasi (n = 1.000) | IKS vs gagal bayar aktual | **+0,154** |
| Periode berjalan (n = 40) | IKS vs PD model | **−0,077** |
| Periode berjalan (n = 40) | IKS vs gagal bayar aktual | **−0,071** |

Pada populasi, tingkat gagal bayar naik dari 20% pada IKS 4 menjadi 46% pada
IKS 8. Hubungan itu nyata. Namun pada 40 berkas periode ini, hubungan
tersebut nyaris tidak ada.

**Perubahan.** Gambar diubah menjadi dua panel: kiri menampilkan tingkat
gagal bayar aktual per tingkat IKS pada seluruh populasi, kanan menampilkan
sebaran berkas periode berjalan. Nilai IKS dengan kurang dari 10 pengamatan
disembunyikan dari panel kiri agar persentase tidak dihitung dari sampel yang
terlalu kecil.

**Implikasi bagi pengelola.** Pertukaran antara kebutuhan sosial dan risiko
bersifat struktural, tetapi **tidak mengikat pada periode ini**. Artinya
pengelola dapat memprioritaskan pemohon berkebutuhan tinggi bulan ini tanpa
menanggung tambahan risiko berarti. Kesimpulan ini akan berbeda pada periode
lain, dan karena itu pemeriksaan korelasi dimasukkan ke dalam pipeline
sebagai keluaran rutin, bukan analisis sekali jalan.

---

## Iterasi 6 — Pelokalan ke konteks Surakarta dan sumber eksternal

**Temuan yang memicu perubahan.** Rubrik Kualitas Data menuntut data
mencakup sumber internal DAN eksternal. Prototipe hanya memakai satu
dataset. Selain itu, laporan menyebut koperasi di Surakarta tetapi seluruh
angka berdenominasi Deutsche Mark, yang tidak masuk akal bagi penguji.

**Perubahan.**

1. Modul `eksternal.py` memuat statistik resmi terverifikasi: garis
   kemiskinan Jawa Tengah Maret 2026 (Rp596.676/kapita, Rp2.571.674/rumah
   tangga), persentase penduduk miskin 9,21 persen, serta UMK Surakarta
   Rp2.570.000 dan UMP Jateng Rp2.327.386 (Kepgub 100.3.3.1/505/2025).
2. Modul `lokalisasi.py` menerjemahkan nilai pinjaman ke Rupiah lewat
   **pemetaan kuantil**, bukan perkalian kurs, lalu menghitung angsuran
   anuitas, pengeluaran per kapita, dan status kesejahteraan terhadap garis
   kemiskinan BPS.
3. Asumsi metode dinyatakan terbuka: PD sahih sebagai peringkat risiko
   relatif, belum sahih sebagai peluang absolut, dan asumsi itu tidak dapat
   diuji tanpa data angsuran koperasi Indonesia berlabel.

**Temuan dari kalibrasi pertama yang gagal.** Versi awal memakai UMK sebagai
lantai pendapatan dan `jumlah_tanggungan` apa adanya sebagai ukuran rumah
tangga. Hasilnya: 40 dari 40 pemohon lolos batas angsuran 30 persen dan
**nol** pemohon berada di bawah garis kemiskinan. Keduanya mustahil bagi
koperasi yang melayani anggota berpenghasilan rendah.

Dua akar masalah: (a) UMK tidak mengikat sektor informal, tempat sebagian
besar anggota koperasi mikro bekerja; (b) kolom `jumlah_tanggungan` hanya
bernilai 1 atau 2 karena definisinya "orang yang wajib dinafkahi", bukan
penghuni rumah, sehingga rumah tangga tampak beranggotakan 2 sampai 3 orang
padahal BPS mencatat rata-rata 4,31. Jumlah anggota adalah PENYEBUT
pengeluaran per kapita, sehingga meremehkannya membuat semua orang tampak
jauh di atas garis kemiskinan.

**Dampak setelah kalibrasi ulang.** 13 pemohon tergolong miskin dan 9
rentan miskin, sebaran yang wajar bagi koperasi simpan pinjam mikro.

---

## Iterasi 7 — Agregasi penilaian kelompok dan pengujian klaim

**Perubahan 1: AHP tiga responden.** Bobot sebelumnya berasal dari satu
orang. Kini diagregasi dari Manajer, Ketua Pengurus, dan Petugas Analis
dengan rata-rata **geometrik** (Saaty AIJ), bukan aritmetik, karena hanya
rata-rata geometrik yang menjaga sifat resiprokal matriks. Konsistensi
diperiksa per responden; agregasi cenderung meratakan ketidakkonsistenan,
sehingga memeriksa gabungan saja akan menyembunyikan masalah.

Perbedaan penekanan terlihat jelas: Ketua Pengurus memberi bobot kebutuhan
sosial 0,3665, sedangkan Petugas Analis memberi bobot risiko 0,3465.
Gabungan menempatkan keduanya nyaris setara (0,2887 dan 0,2842), yang justru
mencerminkan ketegangan kelembagaan sesungguhnya. CR gabungan 0,0036.

**Perubahan 2: klaim "137,8 persen" diperbaiki.** Rasio porsi potensi yang
tertangkap hanya bermakna selama SPK berada DI ANTARA acuan dan kebijakan
tujuan-tunggal. Ketika SPK melampaui kebijakan tujuan-tunggal, rasio itu
melewati 100 persen dan berhenti bermakna. Kode kini membedakan kedua kasus
dan melaporkan "melampaui" alih-alih mencetak persentase yang tidak masuk
akal.

**Perubahan 3: klaim nol persen diuji.** Tingkat gagal bayar 0 persen atas
18 penerima tidak boleh diumumkan tanpa pengujian. Uji binomial satu sisi
ditambahkan: seleksi acak diperkirakan menghasilkan 4,5 kasus macet,
teramati 0 kasus, **p = 0,0056**, signifikan pada taraf 1 persen.

**Perubahan 4: aturan yang tidak mengikat dilaporkan.** Batas beban angsuran
30 persen tidak dilanggar seorang pun (rasio tertinggi 20,7 persen). Fakta
ini dicetak eksplisit agar aturan tersebut tidak disangka sudah menyaring
padahal tidak.

---

## Iterasi 8 — Validasi pustaka dan evaluasi kemudahan penggunaan

**Latar.** Studi lapangan tidak memungkinkan. Dua celah rubrik ditutup
dengan metode yang tidak menuntut responden eksternal.

### 8a. Validasi masalah lewat riset pustaka

Modul `pustaka.py` mengumpulkan bukti terbitan yang menopang perumusan
masalah, masing-masing dengan sumber dan periode:

| Pilar | Temuan | Sumber |
|---|---|---|
| Kredit macet | 56 dari 813 peminjam per KSP Jawa Tengah macet (6,89%) | BPS Jateng, 2020 |
| Ambang regulator | NPL sehat maksimum 5% | SE BI No. 13/1/PBI/2011 |
| UMKM nasional | NPL 3,98% (naik dari 3,71%) | Maret 2024 |
| Salah sasaran | 45% penyaluran perlinsos tidak tepat sasaran | Kemensos, Sept 2026 |
| Bantuan mengendap | 4,5 juta penerima >5 tahun; 36.460 orang >18 tahun | Kemensos, Sept 2026 |

**Temuan paling kuat:** rata-rata koperasi simpan pinjam di Jawa Tengah
(6,89%) **sudah melampaui** ambang sehat regulator (5%) sebelum sistem apa
pun dibangun. Masalahnya bukan hipotetis.

**Batas keabsahan yang dinyatakan terbuka.** Riset pustaka membuktikan
masalah itu nyata pada tingkat populasi. Ia TIDAK membuktikan satu koperasi
tertentu menghadapinya. Klaim "koperasi mitra kami menghadapi persoalan ini"
tetap tidak punya dasar tanpa wawancara.

### 8b. Heuristic Evaluation (Nielsen)

Tiga evaluator menelusuri antarmuka secara independen terhadap 10 heuristik
sambil mengerjakan tiga tugas uji. Hasil: **10 temuan**, melanggar 9 dari 10
heuristik.

| Keparahan | Jumlah | Kode |
|---|---|---|
| 4 Bencana | 2 | HE-03, HE-08 |
| 3 Mayor | 4 | HE-01, HE-02, HE-06, HE-07 |
| 2 Minor | 3 | HE-04, HE-05, HE-10 |
| 1 Kosmetik | 1 | HE-09 |

**Dua temuan berkeparahan 4 diperbaiki sebelum laporan ditutup:**

**HE-03 (H5 Pencegahan kesalahan).** Seluruh penggeser bobot dapat digeser
ke nol, dan sistem tetap menampilkan peringkat. Peringkat tanpa bobot tidak
punya makna sama sekali: tidak ada kriteria yang dipakai membandingkan
pemohon. Versi lama menormalisasi diam-diam dan menampilkan hasil seolah
sah. Sekarang perhitungan dihentikan disertai penjelasan akibatnya.

**HE-08 (H1 Visibilitas status sistem).** Metrik "Macet aktual penerima"
ditampilkan tanpa keterangan bahwa angka itu hanya tersedia karena berkas
periode diambil dari data uji berlabel. Pada penyaluran nyata, angka ini
MUSTAHIL ada saat keputusan diambil — baru muncul setelah masa angsuran
berjalan. Menampilkannya polos membuat pengguna menyangka sistem dapat
memastikan hasil di muka. Ditambahkan sakelar **Mode evaluasi** dan label
`[EVALUASI]` pada metriknya.

Tujuh temuan lain tetap terbuka, terdokumentasi lengkap dengan usulan
perbaikan. Mendaftarkannya eksplisit lebih jujur daripada diam-diam tidak
mengevaluasi.

**Bias yang diakui.** Evaluator adalah pengembang sistem itu sendiri. Orang
yang menilai karyanya sendiri cenderung melewatkan masalah yang sudah
terbiasa ia hadapi. Temuan ini berstatus evaluasi awal, bukan pengganti
pengujian dengan pengguna.

### 8c. Pembandingan terhadap tolok ukur terbitan

Angka hasil kini disandingkan dengan pembanding, karena 0 persen tidak
bermakna tanpa tahu berapa angka yang lazim:

| Tolok ukur | Tingkat macet |
|---|---|
| **Sistem ini (periode uji)** | **0,0%** (18 penerima, p = 0,0056) |
| Segmen UMKM nasional | 3,98% |
| Ambang sehat regulator | 5% |
| Rata-rata KSP Jawa Tengah | 6,89% |

---

## Keterbatasan yang belum teratasi

1. **Padanan kriteria BPS tidak lengkap.** Empat dari 14 indikator rumah
   tangga miskin BPS tidak punya padanan atribut pada dataset: luas lantai
   per kapita, jenis lantai, jenis dinding, dan sumber air minum. IKS
   karenanya berskala 0–10, bukan 0–14. Keterbatasan ini didaftarkan
   eksplisit pada `config.IKS_INDIKATOR_TIDAK_TERSEDIA`.

2. **Dataset bukan data Indonesia.** German Credit dipakai sebagai proksi
   karena data kredit mikro Indonesia pada tingkat individu tidak tersedia
   publik. Satuan mata uang tetap DM dan tidak dikonversi, agar tidak
   menimbulkan kesan data ini berasal dari koperasi nyata.

3. **Penilaian AHP masih tersimulasi.** Mekanisme agregasi tiga responden
   sudah berjalan dan lolos uji konsistensi, tetapi matriksnya belum berasal
   dari wawancara nyata.

4. **Kuesioner SUS belum disebar.** Instrumen, tiga tugas uji, dan fungsi
   penghitung skor sudah siap pada `instrumen/INSTRUMEN_EVALUASI.md` dan
   `src/usability.py`. Butuh 5–10 responden, sekitar 30 menit.

5. **Tujuh temuan heuristik masih terbuka.** Dua yang berkeparahan tertinggi
   sudah diperbaiki; sisanya berkeparahan 1 sampai 3 dan terdokumentasi
   lengkap dengan usulan perbaikan.

6. **Kohort pemohon masih simulasi terkalibrasi.** Parameter dikalibrasi ke
   statistik BPS dan UMK terverifikasi, tetapi bukan berkas pengajuan nyata.

6. **Probabilitas gagal bayar belum sahih sebagai peluang absolut.** Pemetaan
   kuantil mengasumsikan struktur risiko bersifat ordinal dan dapat
   berpindah lintas konteks. Asumsi ini tidak dapat diuji tanpa data angsuran
   koperasi Indonesia yang berlabel lancar atau macet.
