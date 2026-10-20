# Instrumen Evaluasi

Dua instrumen untuk memenuhi Tugas 2(b): *"melakukan evaluasi rancangan SPK
pada aspek kemudahan penggunaan"*.

Instrumen 1 sudah **dikerjakan** dan hasilnya ada di `src/usability.py`.
Instrumen 2 **perlu Anda sebar** — 30 menit, 5 teman sekelas, di ruang kelas.

> Wawancara pembobotan AHP sengaja tidak disertakan. Rubrik Pemodelan hanya
> menuntut "pembobotan menggunakan metode tertentu", dan AHP dengan CR 0,0036
> plus agregasi tiga responden sudah memenuhinya tanpa data lapangan.

---

# INSTRUMEN 1 — Heuristic Evaluation (Nielsen)

**Status: SUDAH DIKERJAKAN.** 10 temuan, hasil di `outputs/tables/temuan_heuristik.csv`.

Gunakan lembar di bawah bila ingin menambah evaluator atau mengevaluasi
ulang setelah perbaikan.

## Cara kerja

Setiap evaluator menelusuri antarmuka **sendirian**, tanpa berdiskusi.
Diskusi hanya dilakukan setelah semua selesai mencatat. Evaluator yang
berdiskusi lebih dulu akan saling menular sudut pandang dan jumlah temuan
unik berkurang.

Nielsen menganjurkan 3–5 evaluator. Satu evaluator rata-rata menemukan
sekitar 35% masalah; lima evaluator menemukan sekitar 75%.

## Sepuluh heuristik

| Kode | Heuristik | Pertanyaan pemandu |
|---|---|---|
| H1 | Visibilitas status sistem | Apakah pengguna tahu apa yang sedang terjadi? |
| H2 | Kesesuaian dengan dunia nyata | Apakah istilahnya dipahami pengurus koperasi? |
| H3 | Kendali dan kebebasan | Bisakah pengguna membatalkan tindakan? |
| H4 | Konsistensi dan standar | Apakah hal sama ditampilkan dengan cara sama? |
| H5 | Pencegahan kesalahan | Apakah sistem mencegah masukan yang merusak? |
| H6 | Mengenali, bukan mengingat | Haruskah pengguna menghafal sesuatu? |
| H7 | Fleksibilitas dan efisiensi | Adakah jalan pintas bagi pengguna mahir? |
| H8 | Desain estetis dan minimalis | Adakah elemen yang tidak perlu? |
| H9 | Pemulihan dari kesalahan | Apakah pesan galat menjelaskan jalan keluar? |
| H10 | Bantuan dan dokumentasi | Tersediakah bantuan saat dibutuhkan? |

## Skala keparahan

| Nilai | Arti | Tindakan |
|---|---|---|
| 0 | Bukan masalah | Abaikan |
| 1 | Kosmetik | Perbaiki bila ada waktu |
| 2 | Minor | Prioritas rendah |
| 3 | Mayor | Prioritas tinggi |
| 4 | Bencana | Wajib diperbaiki sebelum rilis |

**Jangan jumlahkan nilai keparahan menjadi satu skor.** Empat masalah
kosmetik tidak setara dengan satu bencana, meski jumlahnya sama.

## Lembar isian

| Kode | Heuristik | Lokasi (tab/komponen) | Masalah | Keparahan | Usulan perbaikan |
|---|---|---|---|---|---|
| HE-11 | | | | | |
| HE-12 | | | | | |
| HE-13 | | | | | |

## Hasil evaluasi awal

10 temuan, 9 dari 10 heuristik terlanggar:

| Keparahan | Jumlah |
|---|---|
| 4 Bencana | 2 |
| 3 Mayor | 4 |
| 2 Minor | 3 |
| 1 Kosmetik | 1 |

**Tiga sudah ditindaklanjuti:**

- **HE-01** (H1, keparahan 3) — pemuatan 20–40 detik tanpa keterangan.
  Ditambahkan pesan bertahap pada `cache_resource`.
- **HE-03** (H5, keparahan 4) — seluruh bobot dapat digeser ke nol dan
  sistem tetap menampilkan peringkat, padahal peringkat tanpa bobot tidak
  bermakna. Sekarang perhitungan dihentikan disertai penjelasan.
- **HE-08** (H1, keparahan 4) — metrik "Macet aktual" ditampilkan tanpa
  keterangan bahwa angka itu hanya ada pada data uji berlabel. Pada
  penyaluran nyata, angka itu mustahil tersedia saat keputusan diambil.
  Ditambahkan sakelar **Mode evaluasi** dan label `[EVALUASI]`.

**Tujuh masih terbuka**, terdokumentasi lengkap dengan usulan perbaikan di
`src/usability.py`. Temuan terbuka bukan kelalaian — mendaftarkannya secara
eksplisit lebih jujur daripada diam-diam tidak mengevaluasi.

## Bias yang wajib ditulis di laporan

Evaluator adalah pengembang sistem itu sendiri. Orang yang menilai karyanya
sendiri cenderung melewatkan masalah yang sudah terbiasa ia hadapi. Temuan
ini berstatus **evaluasi awal**, bukan pengganti pengujian dengan pengguna.

---

# INSTRUMEN 2 — System Usability Scale

**Status: PERLU DISEBAR.** Target 5–10 responden, 30 menit total.

Responden tidak harus pengurus koperasi. Lima teman sekelas sudah sah
secara metodologis selama keterbatasannya ditulis di laporan.

## Prosedur

Berikan **tiga tugas** tanpa dibimbing. Catat waktu penyelesaian dan berapa
kali responden bertanya.

| Tugas | Perintah | Target waktu |
|---|---|---|
| T1 | Cari tahu siapa pemohon peringkat 1 dan apa alasannya | < 2 menit |
| T2 | Naikkan bobot Kebutuhan Sosial ke 0,40, sebutkan siapa yang keluar dari 10 besar | < 4 menit |
| T3 | Cari PD yang dibutuhkan pemohon P0161 agar masuk peringkat 5 | < 4 menit |

Kuesioner diberikan **setelah** ketiga tugas selesai, bukan sebelumnya.

## Kuesioner

Skala **1 = Sangat tidak setuju … 5 = Sangat setuju**

| # | Pernyataan | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| 1 | Saya rasa saya akan sering menggunakan sistem ini | | | | | |
| 2 | Saya merasa sistem ini terlalu rumit | | | | | |
| 3 | Saya rasa sistem ini mudah digunakan | | | | | |
| 4 | Saya rasa saya butuh bantuan teknis untuk bisa menggunakan sistem ini | | | | | |
| 5 | Saya rasa berbagai fungsi dalam sistem ini terpadu dengan baik | | | | | |
| 6 | Saya rasa ada terlalu banyak ketidakkonsistenan dalam sistem ini | | | | | |
| 7 | Saya rasa kebanyakan orang akan cepat belajar menggunakan sistem ini | | | | | |
| 8 | Saya rasa sistem ini sangat merepotkan untuk digunakan | | | | | |
| 9 | Saya merasa sangat percaya diri saat menggunakan sistem ini | | | | | |
| 10 | Saya perlu belajar banyak hal sebelum bisa menggunakan sistem ini | | | | | |

**Dua pertanyaan terbuka (wajib):**
- Bagian mana yang paling membingungkan?
- Satu hal yang paling ingin Anda ubah?

## Menghitung skor

Fungsi sudah tersedia. Masukkan jawaban dan jalankan:

```python
from src.usability import ringkas_sus

jawaban = {
    "R1": [4, 2, 4, 2, 4, 2, 4, 2, 4, 2],
    "R2": [3, 3, 4, 3, 4, 2, 3, 2, 3, 3],
    # ... sampai R5
}
hasil = ringkas_sus(jawaban)
print(hasil["rata_rata"], hasil["predikat"])
print(hasil["butir_terlemah"])   # tiga aspek paling lemah
```

## Tafsir (Bangor, Kortum & Miller, 2009)

| Rentang | Predikat |
|---|---|
| ≥ 85 | Excellent |
| 72–84 | Good |
| 68–71 | OK (rata-rata industri) |
| 51–67 | Poor |
| < 51 | Awful |

Skor SUS **bukan persentase**. Skor 68 bukan "68 persen puas", melainkan
titik tengah rujukan dari basis data ribuan sistem.

## Cara melaporkan

Laporkan **rata-rata, simpangan baku, DAN skor terendah**. Dengan 5–10
responden, satu nilai ekstrem menggeser rata-rata beberapa poin. Rata-rata
75 yang menyembunyikan satu responden bernilai 40 adalah temuan, bukan
gangguan yang perlu diratakan.

Sertakan juga tiga butir dengan kontribusi terendah — itulah aspek yang
paling perlu diperbaiki, dan biasanya bertemu dengan temuan heuristik yang
masih terbuka.

## Keterbatasan yang wajib ditulis

Bila responden adalah teman sekelas, tulis apa adanya: mereka mahasiswa
informatika, bukan pengurus koperasi. Mereka lebih terbiasa dengan istilah
teknis dan antarmuka berbasis data, sehingga skor SUS yang diperoleh
kemungkinan **lebih tinggi** daripada skor dari pengguna sesungguhnya.
