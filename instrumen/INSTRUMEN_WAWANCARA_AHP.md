# Instrumen 3 — Wawancara Pembobotan AHP

**Status: PERLU DIJALANKAN.** Target 3 responden, 25–40 menit per orang.

Instrumen ini menggantikan matriks rekaan pada `src/config.py` (`AHP_RESPONDEN`)
dengan penilaian responden sungguhan. Metode perhitungannya sudah jadi dan
teruji; yang belum ada hanyalah datanya.

---

## Siapa yang diwawancara

Minimal **tiga** orang dengan kepentingan yang **berbeda**, bukan tiga orang
yang sepakat. Perbedaan sudut pandang justru yang membuat agregasi geometrik
punya arti.

| Kode | Peran | Yang ia timbang |
|---|---|---|
| R1 | Manajer / Bendahara Koperasi | Keberlanjutan dana anggota |
| R2 | Ketua Pengurus | Misi sosial koperasi |
| R3 | Petugas / Analis Kredit | Kelayakan teknis berkas |

Bila koperasi nyata tidak bisa diakses, responden pengganti yang sah: dosen
pembimbing, pengurus KSP/BMT/kelompok simpan pinjam di lingkungan sekitar,
atau pegawai bank mikro. **Tulis apa adanya siapa respondennya di laporan.**
Responden pengganti tetap jauh lebih kuat daripada matriks karangan.

---

## Aturan pelaksanaan

1. **Wawancara satu per satu.** Jangan bertiga sekaligus. Responden yang
   mendengar jawaban orang lain akan ikut, dan tiga matriks yang nyaris
   identik membuat agregasi tidak ada gunanya.
2. **Bacakan konteks keputusan secara verbatim** (di bawah) kepada ketiganya.
   Pertanyaan yang sama hanya sah bila konteksnya sama.
3. **Jangan tunjukkan sistem lebih dulu.** Responden yang sudah melihat
   peringkat akan membobot mundur agar cocok dengan hasil yang ia lihat.
4. **Jangan sebut kriteria sebagai "C1"–"C6"** di depan responden. Pakai nama
   panjangnya.
5. Rekam audio bila diizinkan. Alasan yang responden ucapkan lebih berharga
   daripada angkanya untuk bab pembahasan.

---

## Naskah pembuka (bacakan apa adanya)

> "Koperasi punya dana Rp60 juta untuk periode ini. Yang masuk 40 pengajuan
> dengan total Rp156 juta. Artinya tidak semua bisa dibiayai, dan harus ada
> yang didahulukan.
>
> Saya akan sebutkan enam hal yang bisa dipakai menilai pemohon. Lalu saya
> akan membandingkannya dua-dua: dalam memutuskan siapa yang didahulukan,
> mana yang lebih penting dipertimbangkan, dan seberapa jauh lebih penting.
>
> Tidak ada jawaban benar atau salah. Saya ingin tahu cara Bapak/Ibu menimbang,
> bukan menguji pengetahuan. Kalau ada pertanyaan yang terasa janggal, katakan
> saja — itu justru informasi buat saya."

---

## Enam hal yang dibandingkan

Bacakan satu per satu. Pastikan responden paham keenamnya **sebelum**
pertanyaan pertama.

| | Nama | Penjelasan untuk responden |
|---|---|---|
| C1 | **Kebutuhan Sosial** | Seberapa tidak mampu pemohon: tidak punya rekening, tidak punya tabungan, tidak punya aset, rumah bukan milik sendiri, pekerjaan tidak tetap |
| C2 | **Kapasitas Angsur** | Seberapa ringan cicilannya dibanding penghasilan pemohon |
| C3 | **Riwayat Kredit** | Catatan pembayaran pinjaman pemohon sebelumnya |
| C4 | **Dampak Produktif** | Uangnya dipakai untuk apa: modal usaha dan pelatihan, atau konsumsi |
| C5 | **Risiko Gagal Bayar** | Perkiraan sistem seberapa besar kemungkinan pemohon ini macet |
| C6 | **Nilai Pengajuan** | Besar nominal yang diminta — makin kecil, makin banyak anggota bisa dilayani |

> **Peringatan untuk pewawancara.** C5 dan C6 adalah kriteria *cost* (makin
> kecil makin baik), tetapi yang ditanyakan di sini **bukan arahnya, melainkan
> seberapa penting hal itu dipertimbangkan**. Arah sudah ditangani sistem.
> Bila responden menjawab "ya risiko rendah kan bagus", luruskan:
> *"betul, tapi pertanyaannya seberapa besar porsi perhatian Bapak/Ibu pada
> risiko dibanding pada hal lain."*

---

## Skala jawaban

Tanyakan **dua langkah**, jangan sodorkan angka 1–9 mentah:

**Langkah 1 — "Mana yang lebih penting?"** (atau sama penting)
**Langkah 2 — "Seberapa lebih penting?"** Bacakan pilihannya:

| Jawaban responden | Nilai |
|---|---|
| Sama penting | 1 |
| Sedikit lebih penting | 3 |
| Jelas lebih penting | 5 |
| Sangat jelas lebih penting | 7 |
| Mutlak lebih penting, tidak sebanding | 9 |
| *(ragu di antara dua pilihan di atas)* | 2, 4, 6, 8 |

Catat sebagai **nilai bertanda**: positif bila yang kiri menang, negatif bila
yang kanan menang. Contoh: "Kebutuhan Sosial sedikit lebih penting daripada
Riwayat Kredit" → `+3`. Kebalikannya → `-3`. Sama penting → `1`.

---

## Lembar isian (15 pertanyaan)

Responden: ____________  Peran: ____________  Tanggal: ____________

| # | "Dalam menentukan siapa yang didahulukan, mana yang lebih penting?" | Nilai | Alasan singkat |
|---|---|---|---|
| 1 | **Kebutuhan Sosial** vs **Kapasitas Angsur** | | |
| 2 | **Kebutuhan Sosial** vs **Riwayat Kredit** | | |
| 3 | **Kebutuhan Sosial** vs **Dampak Produktif** | | |
| 4 | **Kebutuhan Sosial** vs **Risiko Gagal Bayar** | | |
| 5 | **Kebutuhan Sosial** vs **Nilai Pengajuan** | | |
| 6 | **Kapasitas Angsur** vs **Riwayat Kredit** | | |
| 7 | **Kapasitas Angsur** vs **Dampak Produktif** | | |
| 8 | **Kapasitas Angsur** vs **Risiko Gagal Bayar** | | |
| 9 | **Kapasitas Angsur** vs **Nilai Pengajuan** | | |
| 10 | **Riwayat Kredit** vs **Dampak Produktif** | | |
| 11 | **Riwayat Kredit** vs **Risiko Gagal Bayar** | | |
| 12 | **Riwayat Kredit** vs **Nilai Pengajuan** | | |
| 13 | **Dampak Produktif** vs **Risiko Gagal Bayar** | | |
| 14 | **Dampak Produktif** vs **Nilai Pengajuan** | | |
| 15 | **Risiko Gagal Bayar** vs **Nilai Pengajuan** | | |

**Butir 16 — uji keajegan (tidak dimasukkan ke matriks).**
Di akhir sesi, tanyakan ulang butir 4 dengan urutan dibalik:
*"Risiko Gagal Bayar dibanding Kebutuhan Sosial, mana yang lebih penting?"*

Jawaban: ________ → seharusnya kebalikan butir 4. Bila berbeda jauh, responden
belum stabil; bahas ulang keenam kriteria lalu ulangi sesi.

**Dua pertanyaan terbuka (wajib, untuk bab pembahasan):**
- Adakah hal penting yang **tidak ada** dalam enam kriteria tadi?
- Pernahkah ada keputusan penyaluran yang Bapak/Ibu sesali? Apa sebabnya?

---

## Memasukkan hasil ke sistem

Ketik jawaban apa adanya — konversi ke matriks 6×6 dikerjakan kode, bukan
tangan. Mengisi 36 sel secara manual adalah sumber kesalahan terbesar pada
tahap ini.

```python
from src.wawancara import rangkum_wawancara

JAWABAN = {
    #                1   2   3   4   5   6   7   8   9  10  11  12  13  14  15
    "R1_Manajer": [  2,  3,  3,  1,  5,  2,  2, -2,  3,  1, -2,  2, -3,  2,  4],
    "R2_Ketua":   [  3,  4,  3,  2,  5,  2,  1, -2,  3, -2, -3,  2, -2,  2,  4],
    "R3_Analis":  [  1,  2,  3, -2,  4,  2,  2, -2,  3,  2, -3,  2, -4,  2,  5],
}

rangkum_wawancara(JAWABAN)   # cetak CR, bobot, dan blok siap tempel ke config.py
```

Urutan 15 angka mengikuti nomor butir pada lembar isian. Fungsi ini mencetak
blok `AHP_RESPONDEN` yang tinggal ditempel menimpa [config.py:237](../src/config.py#L237),
lalu jalankan:

```bash
python -m src.pipeline
python -m src.figur
```

---

## Bila CR > 0,10

Ini **sering terjadi** pada responden sungguhan dan bukan kegagalan penelitian.
CR 0,0036 pada matriks rekaan justru terlalu rapi untuk manusia; responden asli
lazimnya mendarat di 0,05–0,09.

`rangkum_wawancara` menunjuk **pasangan mana** yang paling bertentangan dengan
jawaban lainnya. Prosedurnya:

1. Hubungi kembali responden itu saja, bukan ketiganya.
2. Bacakan ulang **hanya** pasangan yang ditunjuk, beserta jawaban lain yang
   bertentangan dengannya. Contoh: *"tadi Bapak bilang A lebih penting daripada
   B, dan B lebih penting daripada C, tetapi juga C lebih penting daripada A.
   Mana yang ingin Bapak ubah?"*
3. Ganti nilainya, hitung ulang.

**Jangan sunting angka sendiri agar CR lolos.** [ahp.py:102](../src/mcdm/ahp.py#L102)
sengaja menolak jalan bila CR melewati ambang, dan itu perilaku yang benar.
Bobot dari penilaian yang saling bertentangan tidak layak dipakai memutuskan
siapa yang mendapat kredit dan siapa yang tidak.

---

## Yang wajib ditulis di laporan

- Siapa respondennya, perannya, dan tanggal wawancara.
- CR **per responden**, bukan hanya CR gabungan. Agregasi meratakan
  ketidakkonsistenan; melaporkan yang gabungan saja menyembunyikannya.
- Berapa kali wawancara diulang karena CR gagal, bila terjadi.
- Bila responden adalah pengganti (dosen, pengurus KSP lain), sebutkan
  keterbatasannya: bobot mencerminkan penilaian mereka, bukan kebijakan satu
  koperasi tertentu.
- Jawaban pertanyaan terbuka pertama. Bila dua dari tiga responden menyebut
  hal yang sama dan hal itu tidak ada di C1–C6, itu temuan, bukan gangguan.
