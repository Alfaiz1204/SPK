# SPK Prioritisasi Penyaluran Kredit Mikro

Prototipe Sistem Pendukung Keputusan untuk memeringkat pemohon kredit mikro
ketika dana yang tersedia lebih kecil daripada total pengajuan.

Sistem ini bersifat **hybrid**: model prediktif menghasilkan probabilitas
gagal bayar dari data historis (*data-driven*), basis aturan menghitung
indeks kebutuhan sosial dari kriteria BPS (*knowledge-driven*), dan metode
multikriteria menggabungkan keduanya dengan bobot yang ditetapkan pengambil
keputusan (*model-driven*).

---

## Masalah yang diselesaikan

Setiap periode, koperasi menerima pengajuan yang jumlahnya melebihi plafon.
Petugas harus memutuskan siapa yang didahulukan, sementara dua tujuan
kelembagaan saling bertarik:

- **Misi sosial** — dahulukan anggota yang paling membutuhkan.
- **Keberlanjutan finansial** — hindari kredit macet, karena kerugiannya
  menggerus dana anggota lain.

Masalah ini **semi-terstruktur**. Komponen risikonya bisa dihitung dari data,
tetapi seberapa besar bobot kebutuhan sosial dibanding risiko adalah
pertanyaan kebijakan yang tidak punya jawaban di dalam data.

---

## Hasil utama

Plafon Rp60.000.000 atas total pengajuan Rp156.100.000 (2,60x dana
tersedia), 40 berkas pemohon:

| Kebijakan | n penerima | Macet aktual | IKS rata-rata |
|---|---|---|---|
| **SPK Hybrid (AHP+TOPSIS)** | 18 | **0,0%** | **5,39** |
| Hanya Risiko (PD terkecil) | 18 | 5,6% | 5,28 |
| Hanya Kebutuhan (IKS terbesar) | 20 | 20,0% | 5,95 |
| Siapa Cepat (FCFS) | 23 | 21,7% | 5,22 |
| Undian (rata-rata 2.000x) | 19,1 | 20,3% | 5,03 |

Pada dimensi risiko, SPK **melampaui** kebijakan tujuan-tunggal (0,0% vs
5,6%). Pada dimensi ketepatan sasaran, SPK menangkap 39,2% dari potensi
perbaikan yang tersedia. Sistem unggul atas undian pada kedua dimensi
sekaligus.

Klaim 0,0% diuji, tidak sekadar diumumkan: uji binomial satu sisi
menunjukkan seleksi acak diperkirakan menghasilkan 4,5 kasus macet dari 18
penerima, sedangkan yang teramati 0 kasus, **p = 0,0056** (signifikan pada
taraf 1%).

---

## Arsitektur (paradigma DDM)

```
spk-kredit/
├── src/
│   ├── config.py        Konfigurasi terpusat: kriteria, matriks AHP, ambang
│   ├── etl.py           [DATA]       ekstraksi, validasi, pembersihan
│   ├── knowledge.py     [KNOWLEDGE]  aturan IKS, kalibrasi skor riwayat
│   ├── ml_model.py      [MODEL]      prediksi gagal bayar + pemilihan ambang
│   ├── mcdm/
│   │   ├── ahp.py       [MODEL]      pembobotan + uji konsistensi
│   │   └── ranking.py   [MODEL]      TOPSIS, SAW, VIKOR
│   ├── sensitivity.py   [MODEL]      sensitivitas, what-if, goal seeking
│   ├── evaluasi.py      [MODEL]      perbandingan kebijakan alokasi
│   ├── pustaka.py       [DATA]       validasi masalah dari sumber terbitan
│   ├── usability.py                  SUS + Heuristic Evaluation Nielsen
│   ├── figur.py                      pembuatan gambar laporan
│   └── pipeline.py                   orkestrator
├── app/
│   └── app.py           [DIALOG]     antarmuka Streamlit
├── data/
│   ├── raw/             berkas sumber
│   └── processed/       data bersih + spk.db (riwayat keputusan)
├── outputs/
│   ├── tables/          9 tabel CSV
│   ├── figures/         6 gambar PNG
│   └── ringkasan.json   seluruh angka hasil
├── instrumen/
│   └── INSTRUMEN_EVALUASI.md  Heuristic Evaluation + kuesioner SUS
└── docs/
    └── CATATAN_ITERASI.md   jejak 8 iterasi pengembangan
```

---

## Cara menjalankan

```bash
pip install -r requirements.txt

python -m src.pipeline    # ETL, pelatihan, MCDM, alokasi, sensitivitas
python -m src.figur       # membuat 6 gambar untuk laporan
streamlit run app/app.py  # antarmuka
```

Berkas sumber diunduh otomatis pada eksekusi pertama. Seluruh tahap memakai
`random_state = 42`, sehingga hasilnya dapat direproduksi persis.

---

## Kriteria keputusan

| Kode | Kriteria | Arah | Bobot AHP | Sumber |
|---|---|---|---|---|
| C1 | Indeks Kebutuhan Sosial (0–10) | benefit | 0,2887 | Basis aturan BPS |
| C2 | Kapasitas Angsur (0–100) | benefit | 0,1666 | Data internal |
| C3 | Riwayat Kredit (0–4) | benefit | 0,1012 | Dikalibrasi ke data latih |
| C4 | Dampak Produktif (0–4) | benefit | 0,1025 | Kebijakan pengelola |
| C5 | Probabilitas Gagal Bayar (0–1) | **cost** | 0,2842 | Model prediktif |
| C6 | Nilai Pengajuan (Rp) | **cost** | 0,0568 | Data internal |

Bobot diagregasi dari **tiga responden** dengan rata-rata geometrik (Saaty
AIJ). Consistency Ratio gabungan **0,0036**; per responden 0,0077, 0,0122,
dan 0,0118 (seluruhnya di bawah ambang 0,10).

---

## Kinerja model prediktif

Protokol bebas kebocoran: pemilihan model dan ambang keduanya memakai
prediksi *out-of-fold* data latih; data uji dipakai tepat satu kali.

| Model | CV AUC (data latih) | |
|---|---|---|
| RandomForest | 0,7746 ± 0,0376 | terpilih |
| LogisticRegression | 0,7619 ± 0,0281 | |
| HistGradientBoosting | 0,7534 ± 0,0254 | |

Selisih Random Forest terhadap Logistic Regression berada di dalam rentang
simpangan baku, sehingga keunggulannya **tidak signifikan**.

Hasil pada data uji: AUC-ROC 0,7895 · AUC-PR 0,6413 · Brier 0,1855 ·
Recall 0,8222 · ambang biaya-minimum 0,41.

Biaya menurut cost matrix dataset (salah loloskan = 5x salah tolak):
**170 unit**, dibanding 190 pada ambang 0,5 dan 450 tanpa model sama sekali.

---

## Validasi masalah dan evaluasi usability

**Masalah divalidasi lewat riset pustaka**, bukan studi lapangan. Bukti
kunci: BPS mencatat rata-rata 56 dari 813 peminjam per koperasi simpan
pinjam di Jawa Tengah mengalami kredit macet (6,89%), sementara ambang sehat
menurut SE BI No. 13/1/PBI/2011 adalah 5%. Rata-rata koperasi di wilayah ini
sudah melampaui ambang regulator sebelum sistem apa pun dibangun. Pada sisi
penyaluran bantuan, Kemensos mengutip kajian DEN yang menemukan 45%
penyaluran perlindungan sosial tidak tepat sasaran.

**Tolok ukur hasil:**

| Tolok ukur | Tingkat macet |
|---|---|
| **Sistem ini (periode uji)** | **0,0%** |
| Segmen UMKM nasional (Mar 2024) | 3,98% |
| Ambang sehat regulator | 5% |
| Rata-rata KSP Jawa Tengah (2020) | 6,89% |

**Evaluasi kemudahan penggunaan** memakai Heuristic Evaluation Nielsen: 10
temuan, melanggar 9 dari 10 heuristik, sebaran 2 bencana, 4 mayor, 3 minor,
1 kosmetik. Dua temuan berkeparahan 4 sudah diperbaiki. Evaluator adalah
pengembang sendiri, sehingga temuan berstatus evaluasi awal. Kuesioner SUS
siap disebar.

## Catatan etika

Sistem ini **decision support, bukan decision automation**. Keputusan akhir
berada pada pengelola koperasi. Setiap peringkat disertai penjelasan kriteria
mana yang mengangkat dan mana yang menekan, sehingga penolakan dapat
dipertanggungjawabkan kepada pemohon.

Dataset tidak memuat NIK, nama, maupun alamat. Pada penerapan nyata, data
pribadi wajib diganti dengan ID ter-*hash*.

---

## Sumber data

**Internal — basis historis angsuran.** Statlog German Credit, UCI Machine
Learning Repository (id = 144), lisensi CC BY 4.0, MD5
`8e2c6d456b3cda1f273bfbbbd73ece6c`. Dipakai sebagai **proksi** karena data
angsuran koperasi Indonesia pada tingkat individu tidak tersedia publik.

**Eksternal — statistik resmi** (seluruhnya pada `src/eksternal.py` lengkap
dengan sumber, periode, dan tautan):

| Angka | Nilai | Sumber |
|---|---|---|
| Garis kemiskinan Jateng | Rp596.676/kapita/bulan | BPS Jateng, Maret 2026 |
| Garis kemiskinan per RT | Rp2.571.674/bulan | BPS Jateng, Maret 2026 |
| Penduduk miskin Jateng | 9,21% (3,29 juta jiwa) | BPS Jateng, Maret 2026 |
| UMK Kota Surakarta | Rp2.570.000/bulan | Kepgub Jateng 100.3.3.1/505/2025 |
| UMP Jawa Tengah | Rp2.327.386/bulan | Kepgub Jateng 100.3.3.1/505/2025 |

**Pelokalan.** Nilai pinjaman diterjemahkan ke Rupiah lewat **pemetaan
kuantil**, bukan dikalikan kurs: pinjaman pada persentil ke-60 sebaran
historis dipetakan ke persentil ke-60 sebaran pinjaman koperasi Surakarta.
Konsekuensinya probabilitas gagal bayar sahih sebagai **peringkat risiko
relatif**, bukan peluang absolut. Pembacaan yang benar: "pemohon ini lebih
berisiko daripada 70 persen pemohon lain", bukan "peluang gagal bayar 38
persen".

## Status kasus

Organisasi pada laporan bersifat **rekaan**, dan kohort 40 pemohon adalah
**simulasi yang dikalibrasi** ke statistik BPS dan UMK terverifikasi di atas.
Tiga instrumen lapangan siap pakai disediakan pada `instrumen/` untuk
menggantinya dengan data primer: formulir pendataan pemohon, kuesioner SUS,
dan lembar wawancara pembobotan AHP. Mengganti kohort simulasi dengan data
nyata hanya memerlukan satu pemanggilan
`lokalisasi.pasang_sebaran_rujukan()`; tidak ada modul lain yang berubah.
