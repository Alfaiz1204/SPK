/**
 * Pembuat laporan identifikasi DSS dalam format .docx.
 * Format mengikuti berkas rujukan: tabel kepala + tabel identifikasi 4 kolom.
 *
 * Jalankan: node docs/build_report.js
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, AlignmentType, BorderStyle, ShadingType, HeadingLevel,
  ImageRun, PageBreak, VerticalAlign,
} = require("docx");

const AKAR = path.resolve(__dirname, "..");
const FIG = path.join(AKAR, "outputs", "figures");

// Lebar halaman A4 (11906 DXA) dikurangi margin 1080 di kiri dan kanan.
const LEBAR_GUNA = 9746;
const KOL = [620, 1950, 1380, 5796]; // NO | IDENTIFIKASI | SA | PENJELASAN
const KOL_KEPALA = [2200, 7546];

const ABU = "F2F2F2";
const BIRU = "DCE6F1";

const garis = { style: BorderStyle.SINGLE, size: 4, color: "9DA5B0" };
const SEMUA_GARIS = { top: garis, bottom: garis, left: garis, right: garis };

/** Paragraf biasa dengan dukungan penggalan tebal lewat penanda **. */
function p(teks, opsi = {}) {
  const { bold = false, size = 17, after = 70, align, italics = false } = opsi;
  const bagian = String(teks).split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return new Paragraph({
    alignment: align,
    spacing: { after, line: 250 },
    children: bagian.map((b) => {
      const tebal = b.startsWith("**") && b.endsWith("**");
      return new TextRun({
        text: tebal ? b.slice(2, -2) : b,
        bold: tebal || bold,
        italics,
        size,
        font: "Calibri",
      });
    }),
  });
}

function sel(isi, opsi = {}) {
  const { lebar, shading, align, valign = VerticalAlign.TOP } = opsi;
  const anak = Array.isArray(isi) ? isi : [p(isi, { align })];
  return new TableCell({
    width: { size: lebar, type: WidthType.DXA },
    borders: SEMUA_GARIS,
    verticalAlign: valign,
    margins: { top: 90, bottom: 90, left: 110, right: 110 },
    shading: shading
      ? { type: ShadingType.CLEAR, color: "auto", fill: shading }
      : undefined,
    children: anak,
  });
}

/** Satu baris tabel identifikasi. `penjelasan` adalah larik string. */
function baris(no, identifikasi, sa, penjelasan) {
  return new TableRow({
    children: [
      sel([p(no, { bold: true, align: AlignmentType.CENTER })], { lebar: KOL[0] }),
      sel([p(identifikasi)], { lebar: KOL[1] }),
      sel([p(sa, { bold: true, size: 16 })], { lebar: KOL[2], shading: ABU }),
      sel(penjelasan.map((t) => p(t)), { lebar: KOL[3] }),
    ],
  });
}

function barisKepala(label, nilai) {
  return new TableRow({
    children: [
      sel([p(label, { bold: true })], { lebar: KOL_KEPALA[0], shading: ABU }),
      sel([p(nilai)], { lebar: KOL_KEPALA[1] }),
    ],
  });
}

function gambar(berkas, rasio, keterangan) {
  const lebar = 625;
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 60 },
      children: [
        new ImageRun({
          type: "png",
          data: fs.readFileSync(path.join(FIG, berkas)),
          transformation: { width: lebar, height: Math.round(lebar * rasio) },
        }),
      ],
    }),
    p(keterangan, {
      size: 15, italics: true, align: AlignmentType.CENTER, after: 220,
    }),
  ];
}

// ==========================================================================
// ISI TABEL IDENTIFIKASI
// ==========================================================================
const BARIS = [
  baris("1", "Deskripsikan permasalahan dan tujuan pengambilan keputusan dalam DSS.",
    "Prioritisasi penyaluran kredit mikro pada kondisi dana terbatas",
    [
      "**Status kasus**: organisasi pada laporan ini bersifat REKAAN. Parameter kohort dikalibrasi ke statistik resmi yang terverifikasi, dan instrumen pendataan lapangan disertakan agar kohort simulasi dapat diganti data primer tanpa mengubah satu pun modul.",
      "**Permasalahan**: koperasi simpan pinjam di Kota Surakarta menerima 40 berkas pengajuan senilai Rp156.100.000 pada satu periode, sementara plafon yang tersedia hanya Rp60.000.000, yaitu rasio permintaan 2,60 kali dana tersedia. Petugas harus memutuskan siapa yang didahulukan.",
      "**Validasi masalah lewat riset pustaka.** Studi lapangan tidak dilaksanakan, sehingga relevansi masalah dibuktikan dari sumber terbitan. **Pilar 1, kredit macet**: BPS Provinsi Jawa Tengah mencatat rata-rata 56 peminjam mengalami kredit macet dari rata-rata 813 peminjam per koperasi simpan pinjam, atau sekitar 6,89 persen, sementara ambang sehat menurut Surat Edaran Bank Indonesia Nomor 13/1/PBI/2011 adalah 5 persen. Artinya rata-rata koperasi simpan pinjam di Jawa Tengah SUDAH melampaui ambang sehat regulator sebelum sistem apa pun dibangun. **Pilar 2, ketidaktepatan sasaran**: Kementerian Sosial mengutip kajian Dewan Ekonomi Nasional yang menemukan sekitar 45 persen penyaluran perlindungan sosial terindikasi tidak tepat sasaran, dan terdapat sekitar 4,5 juta penerima yang menerima bantuan lebih dari lima tahun. **Penghubung kedua pilar**: menolak pemohon layak menimbulkan exclusion error, sementara meloloskan pemohon berisiko menimbulkan kredit macet. Aturan penyaringan tanpa bobot tidak dapat menyeimbangkan keduanya karena memperlakukan setiap indikator sebagai satu poin yang setara.",
      "**Batas keabsahan riset pustaka**: bukti di atas membuktikan masalahnya NYATA dan TERUKUR, tetapi tidak membuktikan satu koperasi tertentu menghadapi persoalan ini. Klaim yang sah hanya sampai tingkat populasi.",
      "**Landasan empiris dari sumber eksternal**: BPS mencatat garis kemiskinan rata-rata per rumah tangga Jawa Tengah Maret 2026 sebesar Rp2.571.674 per bulan, sementara UMK Kota Surakarta 2026 ditetapkan Rp2.570.000. Selisih keduanya hanya Rp1.674 atau 0,07 persen. Artinya pekerja berupah minimum di Solo yang menanggung rumah tangga berukuran rata-rata 4,31 orang berada tepat pada garis kemiskinan, sehingga satu guncangan kecil langsung menjatuhkannya ke bawah garis. Dari 40 pemohon, 13 tergolong miskin dan 9 rentan miskin menurut ukuran BPS.",
      "Dua tujuan kelembagaan saling bertarik. **Misi sosial** menuntut anggota yang paling membutuhkan didahulukan. **Keberlanjutan finansial** menuntut kredit macet dihindari, karena kerugiannya menggerus simpanan anggota lain. Praktik lama berupa urutan kedatangan berkas menghasilkan tingkat gagal bayar 25,0 persen.",
      "Masalah bersifat **SEMI-TERSTRUKTUR**. Komponen risiko dapat dihitung dari data historis, tetapi besaran bobot kebutuhan sosial terhadap risiko adalah pertanyaan kebijakan yang tidak punya jawaban di dalam data. Aturan BPS sendiri memperlakukan 14 kriteria rumah tangga miskin sebagai hitungan tanpa bobot, sehingga tidak punya listrik dinilai setara dengan pendidikan kepala keluarga hanya tamat SD. Asumsi itulah yang hendak diperbaiki.",
      "**Tujuan pengambilan keputusan**: (1) menilai kebutuhan sosial tiap pemohon secara terukur dan dapat ditelusuri; (2) memperkirakan probabilitas gagal bayar dari data historis; (3) menggabungkan keduanya menjadi satu peringkat prioritas dengan bobot yang ditetapkan pengelola; (4) menerjemahkan peringkat menjadi keputusan penyaluran di bawah batas anggaran; (5) menunjukkan seberapa kuat peringkat tersebut bertahan bila bobot diubah.",
    ]),

  baris("2", "Siapa pengguna DSS? Apakah pengambil keputusan pada level operasional, taktis (manajerial), atau strategis (eksekutif)?",
    "Manajer koperasi dan petugas analis kredit; level TAKTIS dengan unsur OPERASIONAL",
    [
      "**Pengguna utama** adalah Manajer Koperasi, yang menetapkan bobot kriteria melalui wawancara terstruktur AHP, menetapkan plafon periode, dan menetapkan batas keras probabilitas gagal bayar. **Pengguna kedua** adalah Petugas Analis Kredit, yang memasukkan berkas pengajuan dan membacakan alasan keputusan kepada pemohon.",
      "**Level keputusan bersifat TAKTIS (manajerial)**, karena penetapan bobot antartujuan dan penetapan ambang risiko merupakan kebijakan alokasi sumber daya periodik, bukan transaksi harian.",
      "**Unsur OPERASIONAL** muncul pada pemrosesan berkas per pemohon dan penerbitan status keputusan, yang berulang setiap periode penyaluran.",
      "**Bukan level STRATEGIS**: sistem tidak menangani penetapan arah usaha koperasi, struktur produk pinjaman, maupun perencanaan modal jangka panjang.",
    ]),

  baris("3", "Deskripsikan nama metode pengambilan keputusan, dan apakah menggunakan model tunggal atau model hybrid.",
    "HYBRID: Random Forest + AHP + TOPSIS, dengan SAW dan VIKOR sebagai pembanding",
    [
      "**Model bersifat HYBRID** karena menggabungkan model prediktif berbasis pembelajaran mesin dengan model pengambilan keputusan multikriteria. Keduanya menjawab pertanyaan berbeda: model prediktif menjawab seberapa besar risiko, MCDM menjawab seberapa penting risiko itu dibanding kriteria lain.",
      "**Tahapan algoritma**:",
      "1) Ekstraksi dan pembersihan 1.000 baris data historis, dengan winsorisasi persentil 1 dan 99 pada 20 nilai pengajuan dan 8 nilai tenor.",
      "2) Pemisahan data latih 70 persen dan data uji 30 persen secara terstratifikasi.",
      "3) Pemilihan keluarga model melalui AUC validasi silang 5-lipat pada data latih. Random Forest terpilih dengan 0,7746 plus minus 0,0376, mengungguli Logistic Regression 0,7619 dan HistGradientBoosting 0,7534.",
      "4) Pemilihan ambang keputusan 0,41 melalui penelusuran kisi atas prediksi out-of-fold, dengan meminimalkan biaya menurut cost matrix dataset.",
      "5) Penerapan basis aturan Indeks Kebutuhan Sosial, yaitu 10 indikator deprivasi hasil adaptasi 14 kriteria rumah tangga miskin BPS.",
      "6) Pelokalan ke konteks Surakarta melalui pemetaan kuantil: nilai pinjaman diterjemahkan menurut posisi persentilnya, bukan dikalikan kurs. Konsekuensinya probabilitas gagal bayar dibaca sebagai skor risiko RELATIF untuk mengurutkan pemohon, bukan peluang absolut.",
      "7) Pembobotan 6 kriteria dengan AHP metode eigenvector atas penilaian TIGA responden, diagregasi rata-rata geometrik (Saaty AIJ). Consistency Ratio gabungan 0,0036; per responden 0,0077, 0,0122, dan 0,0118.",
      "8) Pemeringkatan dengan TOPSIS, divalidasi silang dengan SAW dan VIKOR.",
      "**Catatan kejujuran metodologis**: selisih Random Forest terhadap Logistic Regression sebesar 0,0127 berada di dalam rentang simpangan baku validasi silang 0,0376. Keunggulan Random Forest karenanya **tidak dapat dinyatakan signifikan**, dan hal ini dilaporkan apa adanya.",
    ]),

  baris("4", "Deskripsikan luaran keputusan dan luaran bentuk DSS.",
    "Peringkat 40 pemohon, status keputusan, nominal, dan alasan; prototipe web Streamlit",
    [
      "**Luaran keputusan**: (a) peringkat prioritas 1 sampai 40 beserta skor TOPSIS; (b) status keputusan tiga tingkat, yaitu DISETUJUI 18 pemohon, DITUNDA 16 pemohon, dan DITOLAK 6 pemohon; (c) nominal yang disetujui per pemohon, total Rp59.350.000 atau 98,9 persen plafon; (d) alasan tertulis untuk setiap keputusan, memuat kriteria yang paling mengangkat dan paling menekan skor; (e) daftar indikator deprivasi yang terpenuhi per pemohon, sehingga skor kebutuhan dapat ditelusuri.",
      "**Luaran bentuk DSS**: prototipe aplikasi web berbasis Streamlit dengan enam tab, yaitu Keputusan, Bobot dan AHP, Sensitivitas, What-if dan Goal Seeking, Validasi, serta Riwayat. Sistem disertai basis data SQLite untuk riwayat skenario, 9 tabel CSV, 6 gambar, dan berkas ringkasan JSON.",
      "**Luaran pendukung**: perbandingan dengan empat kebijakan alokasi alternatif, analisis sensitivitas bobot pada 23 skenario, dan ekspor keputusan dalam format CSV.",
    ]),

  baris("5", "Apakah kategori DSS yang dikembangkan berupa (i) Management Decision Support System (MDSS / DSS), (ii) Expert System / Recommender System, (iii) Group Decision Support System, atau (iv) Executive Information System / Dashboard System / Business Intelligence?",
    "Management Decision Support System (MDSS)",
    [
      "**MDSS**, karena sistem menghasilkan peringkat prioritas dan usulan alokasi untuk mendukung manajer koperasi, sementara keputusan akhir tetap berada pada manusia. Antarmuka menyediakan pengubahan bobot, analisis sensitivitas, dan goal seeking, yang merupakan ciri khas DSS dan bukan ciri sistem pelaporan.",
      "**Bukan Expert System**: mesin inferensi simbolik dan fasilitas penjelasan berbasis aturan tidak tersedia. Basis aturan yang ada, yaitu Indeks Kebutuhan Sosial dan batas keras PD, bersifat pelengkap dan melekat pada subsistem model, bukan menjadi inti penalaran sistem.",
      "**Bukan Recommender System**: sistem tidak mempelajari preferensi pengguna dari perilaku masa lalu, dan tidak menyarankan produk kepada konsumen.",
      "**Bukan Group DSS**: fitur kolaborasi seperti pemungutan suara, diskusi daring, atau agregasi penilaian beberapa pengambil keputusan belum tersedia. Bobot AHP saat ini berasal dari satu responden.",
      "**Bukan EIS / Dashboard / BI**: fungsi utamanya menghasilkan keputusan baru melalui pemodelan, bukan menyajikan indikator kinerja historis kepada eksekutif.",
    ]),

  baris("6", "Apakah tipologi DSS yang dikembangkan berupa (i) Communication-driven dan Group DSS (GDSS), (ii) Data-driven DSS, (iii) Document-driven DSS, (iv) Knowledge-driven DSS, atau (v) Model-driven DSS?",
    "HYBRID: Model-driven sebagai tulang punggung, dengan muatan Data-driven dan Knowledge-driven",
    [
      "**MODEL-DRIVEN (dominan)**, mengikuti definisi Power (2003). Nilai utama sistem berasal dari model AHP dan TOPSIS yang parameternya, yaitu bobot kriteria, **ditetapkan pengguna** dan dapat diubah seketika melalui antarmuka. Jumlah data relatif kecil, yaitu 1.000 baris, sehingga sumber nilai bukan pada skala data melainkan pada pemodelan.",
      "**Muatan DATA-DRIVEN**: probabilitas gagal bayar dipelajari dari data historis melalui Random Forest, dan skor riwayat kredit dikalibrasi dari tingkat gagal bayar yang teramati pada data latih.",
      "**Muatan KNOWLEDGE-DRIVEN**: Indeks Kebutuhan Sosial disusun dari 14 kriteria rumah tangga miskin BPS, skor dampak produktif ditetapkan pengelola, dan batas keras PD sebesar 0,60 ditetapkan sebagai kebijakan kelembagaan, bukan dioptimasi dari data.",
      "**Bukan Document-driven**: dokumen tidak terstruktur tidak dikelola. **Bukan Communication-driven / GDSS**: fitur kolaborasi kelompok tidak tersedia.",
      "Penggolongan hybrid ini dapat diperdebatkan. Bila bobot kriteria kelak diturunkan secara objektif dari data, misalnya dengan metode Entropy atau CRITIC, tipologinya akan bergeser menjadi Data-driven.",
    ]),

  baris("7", "Jelaskan arsitektur pada DSS.",
    "Lengkap empat subsistem: DBMS, MBMS, DGMS, dan KBMS",
    [
      "Arsitektur mengikuti paradigma Data-Model-Dialog (Sprague dan Carlson), dengan tambahan subsistem pengetahuan.",
      "**(A) Subsistem pengelolaan data (DBMS)**: modul etl.py menangani ekstraksi, validasi, pembersihan, dan transformasi. Penyimpanan memakai CSV untuk data olahan dan SQLite untuk riwayat keputusan, dengan dua tabel yaitu skenario dan keputusan.",
      "**(B) Subsistem model (MBMS)**: terdiri atas ml_model.py untuk prediksi gagal bayar, mcdm/ahp.py untuk pembobotan, mcdm/ranking.py untuk TOPSIS, SAW, dan VIKOR, sensitivity.py untuk analisis sensitivitas, what-if, dan goal seeking, serta evaluasi.py untuk perbandingan kebijakan.",
      "**(C) Subsistem dialog (DGMS)**: aplikasi Streamlit enam tab dengan penggeser bobot, penyaring status, tabel interaktif, grafik garis sensitivitas, dan tombol unduh.",
      "**(D) Subsistem pengetahuan (KBMS)**: modul knowledge.py memuat aturan Indeks Kebutuhan Sosial, skor dampak produktif, dan fungsi kalibrasi skor riwayat kredit.",
      "Pemisahan KBMS dari MBMS bersifat disengaja, agar pada saat demonstrasi terlihat jelas bagian mana dari keputusan yang berasal dari kebijakan manusia dan bagian mana yang berasal dari pola data.",
    ]),

  baris("7a", "A. Data: Media penyimpanan data - RDBMS, Spreadsheet / csv, Json, Text / Document, lainnya. Data local, atau cloud. Apakah ada penanganan data secara khusus sebelum digunakan (misal pembersihan data, penanganan data missing, penanganan imbalance, dll)? Apakah data yang diproses realtime, atau batch / periodik?",
    "CSV + SQLite, lokal, batch per periode penyaluran",
    [
      "**Dua sumber data dipakai, internal dan eksternal.** **(1) Sumber internal**: basis historis angsuran, yaitu Statlog German Credit, UCI id 144, 1.000 baris, lisensi CC BY 4.0, MD5 8e2c6d456b3cda1f273bfbbbd73ece6c, dipakai sebagai proksi karena data angsuran koperasi Indonesia pada tingkat individu tidak tersedia publik. **(2) Sumber eksternal**: garis kemiskinan Provinsi Jawa Tengah Maret 2026 sebesar Rp596.676 per kapita per bulan dan Rp2.571.674 per rumah tangga (BPS Provinsi Jawa Tengah); persentase penduduk miskin 9,21 persen atau 3,29 juta jiwa; serta UMK Kota Surakarta 2026 sebesar Rp2.570.000 dan UMP Jawa Tengah Rp2.327.386 (Keputusan Gubernur Jawa Tengah Nomor 100.3.3.1/505 Tahun 2025). Seluruh angka eksternal tercatat pada modul eksternal.py lengkap dengan sumber, periode, dan tautan verifikasi.",
      "**Pemanfaatan sumber eksternal**: garis kemiskinan BPS menjadi ambang penggolongan kesejahteraan pemohon; rata-rata anggota rumah tangga miskin 4,31 orang menjadi dasar kalibrasi penyebut pengeluaran per kapita; UMK Surakarta menjadi titik tumpu perkiraan pendapatan dan batas beban angsuran 30 persen.",
      "**Media penyimpanan**: berkas CSV untuk data mentah dan data olahan, serta **SQLite** untuk riwayat skenario keputusan. Seluruhnya **LOKAL**, tanpa layanan cloud. Keluaran tambahan berupa JSON untuk ringkasan angka dan PNG untuk gambar.",
      "**Kalibrasi kohort**: ukuran rumah tangga diskalakan secara numerik agar rata-ratanya tepat sama dengan 4,31 orang menurut BPS, karena kolom asli hanya bernilai 1 atau 2 dan akan membuat setiap rumah tangga tampak jauh di atas garis kemiskinan. Perkiraan pendapatan memakai pengali di bawah 1,0 terhadap UMK untuk pekerjaan informal, karena UMK tidak mengikat sektor informal.",
      "**Penanganan data khusus**: (a) validasi skema, yaitu pemeriksaan jumlah kolom, kode kategorik asing terhadap kamus, dan rentang numerik yang mustahil secara domain; (b) nilai hilang **nihil**, sehingga imputasi tidak diperlukan; (c) duplikat **nihil**; (d) winsorisasi persentil 1 dan 99 pada kolom jumlah kredit sebanyak 20 nilai dan durasi sebanyak 8 nilai. Nilai tidak dibuang, hanya diredam, karena pemohon bernilai besar tetap relevan secara bisnis sementara normalisasi vektor TOPSIS sensitif terhadap nilai ekstrem.",
      "**Penanganan ketidakseimbangan kelas**: komposisi 700 lancar berbanding 300 macet ditangani dengan class_weight berbobot seimbang pada klasifikasi, serta pemilihan ambang berbasis biaya, bukan akurasi. Oversampling seperti SMOTE **tidak** dipakai karena data sintetis pada ranah kredit sulit dipertanggungjawabkan.",
      "**Pencegahan kebocoran data**: penskalaan dan one-hot encoding dibungkus di dalam Pipeline agar dipelajari dari data latih saja. Kalibrasi skor riwayat kredit hanya menerima data latih. Berkas pengajuan periode berjalan diambil dari **data uji**, yaitu pemohon yang belum pernah dilihat model.",
      "**Kecepatan pemrosesan**: **BATCH / PERIODIK**, dengan satuan keputusan satu periode penyaluran.",
    ]),

  baris("7b", "B. Model: Apakah mode pengambilan keputusan berupa model matematik, model pengambilan keputusan multikriteria, model data analytics / machine learning / artificial intelligence, ataukah hybrid? Apakah ada metode pencarian solusi khusus yang digunakan? Apakah bobot kriteria, aturan keputusan, atau fungsi keanggotaan dapat diperbarui secara otomatis ketika ada data baru (adaptive learning)?",
    "HYBRID machine learning + MCDM; grid search; adaptive learning PARSIAL",
    [
      "**Jenis model: HYBRID**. Lapis pertama berupa machine learning, yaitu Random Forest 500 pohon dengan kedalaman maksimum 12 dan daun minimum 8, menghasilkan probabilitas gagal bayar. Lapis kedua berupa MCDM, yaitu AHP untuk bobot dan TOPSIS untuk pemeringkatan. Lapis ketiga berupa aturan kelembagaan, yaitu batas keras PD dan alokasi berurutan di bawah plafon.",
      "**Bobot kriteria hasil AHP kelompok**: C1 Indeks Kebutuhan Sosial 0,2887; C5 Probabilitas Gagal Bayar 0,2842; C2 Kapasitas Angsur 0,1666; C4 Dampak Produktif 0,1025; C3 Riwayat Kredit 0,1012; C6 Nilai Pengajuan 0,0568. Lambda maksimum 6,0220, CI 0,0044, dan **CR 0,0036** terhadap ambang 0,10.",
      "**Agregasi tiga responden** memakai rata-rata GEOMETRIK, bukan aritmetik. Hanya rata-rata geometrik yang menjaga sifat resiprokal matriks: bila responden A menilai 3 dan responden B menilai 1/3, hasil yang benar adalah 1, sedangkan rata-rata aritmetik memberi 1,67. Konsistensi diperiksa per responden, bukan hanya pada gabungan, karena agregasi cenderung meratakan ketidakkonsistenan. Perbedaan penekanan antarresponden terlihat jelas: Ketua Pengurus memberi C1 bobot 0,3665 sedangkan Petugas Analis memberi C5 bobot 0,3465.",
      "**Metode pencarian solusi**: (a) penelusuran kisi 91 titik untuk ambang biaya-minimum; (b) metode eigenvector untuk bobot AHP, bukan rata-rata kolom ternormalisasi, karena rata-rata kolom hanya aproksimasi yang tepat pada matriks konsisten sempurna; (c) algoritma rakus berurutan untuk alokasi plafon, dengan pemohon yang melebihi sisa dana dilewati, bukan menghentikan alokasi; (d) penelusuran kisi 200 titik untuk goal seeking. Metaheuristik seperti algoritma genetika **tidak** digunakan karena ruang solusi berukuran kecil.",
      "**Adaptive learning: PARSIAL**. Yang **dapat** diperbarui otomatis: skor riwayat kredit dikalibrasi ulang dari data latih setiap kali pipeline dijalankan, dan ambang keputusan dipilih ulang secara out-of-fold. Yang **belum** otomatis: pelatihan ulang model terjadwal saat data angsuran baru masuk, serta pembaruan bobot AHP, yang memang memerlukan wawancara ulang dengan pengelola dan tidak seharusnya otomatis.",
    ]),

  baris("7c", "C. Antarmuka (Interface): Desktop, Web-based, Mobile App, Console, UI pada perangkat DSS generator seperti Ms Excel, Tableau, Power BI. Adakah bahasa program spesifik yang digunakan? Apakah DSS berdiri sendiri (independent) ataukah embedded dalam suatu sistem informasi / sistem warehouse data?",
    "WEB-BASED (Streamlit), Python 3.12, INDEPENDENT",
    [
      "**Jenis antarmuka: WEB-BASED**, dibangun dengan Streamlit dan dapat diakses melalui peramban. Antarmuka console juga tersedia melalui perintah python -m src.pipeline untuk keperluan otomatisasi.",
      "**Bahasa dan pustaka**: Python 3.12 dengan pandas, NumPy, scikit-learn, Matplotlib, dan Streamlit. Basis data memakai SQLite melalui pustaka standar sqlite3.",
      "**Komponen antarmuka**: enam tab, penggeser bobot untuk enam kriteria dengan normalisasi otomatis agar berjumlah satu, pemilih metode pemeringkatan, penyaring status keputusan, tabel dengan kolom batang kemajuan untuk PD, grafik garis sensitivitas, tombol penyimpan skenario, dan tombol unduh CSV.",
      "**Posisi sistem: INDEPENDENT**. Sistem berjalan mandiri tanpa bergantung pada sistem informasi koperasi yang sudah ada. Rencana lanjutan berupa integrasi dengan sistem informasi anggota melalui antarmuka REST, sehingga berkas pengajuan tidak perlu dimasukkan ulang.",
      "**Bukan embedded** pada perangkat DSS generator. Seluruh logika ditulis sebagai kode, bukan sebagai konfigurasi pada Excel, Tableau, atau Power BI.",
    ]),

  baris("7d", "D. Pengetahuan (Knowledge) - jika ada.",
    "ADA: basis aturan IKS dari kriteria BPS, skor dampak produktif, dan batas keras PD",
    [
      "Terdapat unsur **KNOWLEDGE-BASED** pada empat tempat, seluruhnya terkumpul pada modul knowledge.py dan config.py.",
      "(a) **Indeks Kebutuhan Sosial**, yaitu 10 indikator deprivasi biner hasil adaptasi 14 kriteria rumah tangga miskin BPS. Tiap indikator menghasilkan kolom tersendiri, sehingga pertanyaan mengapa seorang pemohon memperoleh IKS 7 dapat dijawab dengan menyebut indikator mana yang terpenuhi.",
      "(b) **Skor dampak produktif** berskala 0 sampai 4, menempatkan modal usaha dan pelatihan kerja pada nilai tertinggi serta pinjaman konsumtif pada nilai terendah. Skala ini merupakan kebijakan pengelola, bukan temuan data.",
      "(c) **Batas keras probabilitas gagal bayar** sebesar 0,60. Aturan ini berada **di atas** hasil MCDM: pemohon yang melampauinya ditolak berapa pun peringkatnya. Alasannya, MCDM bersifat kompensatoris, sehingga skor kebutuhan yang sangat tinggi secara matematis dapat menutupi risiko yang sangat tinggi, dan secara kelembagaan hal itu tidak dapat diterima karena kredit macet merugikan pemohon itu sendiri.",
      "(d) **Matriks perbandingan berpasangan AHP**, yang memuat penilaian manajer koperasi mengenai kepentingan relatif antarkriteria.",
      "**Temuan penting**: penilaian pakar mengenai skor riwayat kredit terbukti **berkebalikan** dengan perilaku data. Pakar menilai pemohon tanpa riwayat kredit sebagai paling baik, padahal tingkat gagal bayarnya 57,1 persen, sedangkan pemohon berstatus akun kritis hanya 17,6 persen. Ini adalah efek thin file, yaitu berkas kosong bukan berkas bersih. Skor dikalibrasi ulang pada iterasi kedua, dan versi penilaian pakar tetap dipertahankan di dalam kode sebagai pembanding.",
    ]),

  baris("8", "Bagaimana kompleksitas data yang digunakan, apakah terstruktur, semi-terstruktur, atau tidak terstruktur?",
    "TERSTRUKTUR seluruhnya; 13 atribut kategorik dan 7 numerik",
    [
      "**Data bersifat TERSTRUKTUR.** Seluruh atribut memiliki skema tetap dan nama kolom yang baku. Tidak ada teks bebas, gambar, maupun dokumen tidak terstruktur.",
      "**Data KUANTITATIF (7 atribut)**: durasi pinjaman dalam bulan, jumlah kredit dalam DM, rasio angsuran terhadap pendapatan disposabel berskala 1 sampai 4, lama domisili dalam tahun, usia dalam tahun, jumlah kredit aktif, dan jumlah tanggungan.",
      "**Data KATEGORIK (13 atribut)**: status rekening giro, riwayat kredit, tujuan pinjaman, tabungan, lama bekerja, status personal, penjamin, kepemilikan aset, cicilan lain, status rumah, jenis pekerjaan, kepemilikan telepon, dan status pekerja asing. Setelah one-hot encoding dengan drop kategori pertama, dimensi fitur menjadi 55.",
      "**Unsur KUALITATIF** terletak pada penilaian manusia, yaitu matriks perbandingan AHP, skala dampak produktif, dan penetapan batas keras PD.",
      "**Skala data**: 1.000 baris, tanpa nilai hilang dan tanpa duplikat, dengan komposisi kelas 700 lancar berbanding 300 macet. Berkas periode berjalan berjumlah 40 pemohon yang diambil dari data uji.",
      "**Keterbatasan**: empat dari 14 indikator BPS tidak punya padanan atribut, yaitu luas lantai per kapita, jenis lantai, jenis dinding, dan sumber air minum. IKS karenanya berskala 0 sampai 10, bukan 0 sampai 14. Keterbatasan ini didaftarkan eksplisit di dalam kode, bukan disembunyikan.",
    ]),

  baris("9", "Jika dilihat dari model keputusan McKinsey (model ABCD), apakah DSS menangani (i) Ad-hoc decision, (ii) Big-bet decision, (iii) Cross-cutting decision, (iv) Delegated decision?",
    "DELEGATED DECISION",
    [
      "Merujuk kerangka McKinsey yang terdiri atas Big-bet, Cross-cutting, Delegated, dan Ad hoc, keputusan yang didukung sistem ini tergolong **DELEGATED DECISION**.",
      "**Frekuensi: SERING dan BERULANG.** Penilaian dilakukan setiap periode penyaluran, dengan 40 berkas per periode.",
      "**Risiko per keputusan: RENDAH sampai SEDANG.** Dampak satu keputusan terbatas pada nilai pinjaman individual, yaitu rata-rata 3.236 DM, tanpa risiko keselamatan jiwa.",
      "**Kewenangan: DIDELEGASIKAN** kepada manajer koperasi dan petugas analis kredit sebagai pihak yang diberi wewenang teknis, tanpa perlu persetujuan rapat anggota untuk setiap berkas.",
      "**Bukan Big-bet**: tidak menyangkut taruhan besar yang jarang terjadi dan sulit dibalik. **Bukan Cross-cutting**: tidak memerlukan koordinasi lintas unit dengan banyak pemangku kepentingan. **Bukan Ad hoc**: justru kebalikannya, keputusan ini rutin dan terjadwal.",
      "Catatan: penetapan **bobot kriteria** sebenarnya mendekati Big-bet, karena jarang diubah dan berdampak pada seluruh keputusan berikutnya. Sistem memisahkan kedua tingkat ini, yaitu bobot ditetapkan sesekali melalui AHP, sementara pemeringkatan dijalankan setiap periode.",
    ]),

  baris("10", "Apakah DSS memiliki kapabilitas untuk melakukan analisis sensitivitas, what if analysis, atau goal seeking bagi pengguna?",
    "KETIGANYA TERSEDIA dan dapat diakses langsung dari antarmuka",
    [
      "**ANALISIS SENSITIVITAS: TERSEDIA.** Modul sensitivity.py menelusuri satu bobot dari 0,05 sampai 0,60 dalam 23 langkah, sementara bobot lain diskalakan **proporsional** terhadap nilainya semula. Pembagian rata sengaja dihindari karena akan diam-diam mengubah urutan kepentingan kriteria lain.",
      "Hasil pada kriteria C1: komposisi 10 besar berubah pada **7 titik balik**, yang masing-masing dilaporkan beserta pemohon yang masuk dan keluar. Empat pemohon yaitu P0023, P0278, P0373, dan P0437 bertahan di 10 besar pada **100 persen skenario bobot**, sehingga keputusan atas keempatnya dapat diambil tanpa keraguan.",
      "**WHAT-IF ANALYSIS: TERSEDIA.** Pengguna memilih satu pemohon, satu kriteria, dan nilai baru, lalu melihat pergeseran peringkat. Contoh terdokumentasi: pemohon P0161 dengan penurunan PD 40 persen karena menghadirkan penjamin naik dari peringkat 15 ke 13, dan **7 alternatif lain ikut bergeser**. Seluruh alternatif dihitung ulang karena TOPSIS bersifat relatif terhadap solusi ideal; menghitung ulang hanya pemohon yang diubah akan menghasilkan angka salah.",
      "**GOAL SEEKING: TERSEDIA.** Pengguna menetapkan peringkat target, lalu sistem mencari nilai kriteria minimum yang dibutuhkan melalui penelusuran kisi 200 titik. Penelusuran kisi dipilih, bukan metode bagi dua, karena peringkat merupakan fungsi tangga yang tidak dijamin monoton.",
      "Contoh terdokumentasi: pemohon P0161 **tidak dapat** mencapai peringkat 5 walaupun PD didorong ke nilai ekstrem. Sistem melaporkan ketidaktercapaian ini apa adanya beserta penjelasan bahwa kelemahan pemohon terletak pada kriteria lain. Jawaban semacam ini jauh lebih berguna daripada memaksakan angka yang tidak realistis.",
    ]),

  baris("12", "Apa saja kapabilitas yang terdapat pada DSS ditinjau dari 14 kapabilitas DSS (Turban)?",
    "Terpenuhi penuh: 11/14; Sebagian: 3/14; Tidak terpenuhi: 0/14",
    [
      "1) Mendukung keputusan semi atau tidak terstruktur - **YA** (penetapan bobot antartujuan memerlukan judgment manajerial yang tidak dapat diturunkan dari data).",
      "2) Mendukung semua level manajemen - **SEBAGIAN** (melayani level taktis dan operasional; tampilan ringkas untuk pengurus koperasi belum tersedia).",
      "3) Mendukung individu maupun kelompok - **YA** (agregasi penilaian AHP dari tiga responden berperan berbeda memakai rata-rata geometrik Saaty, dengan pemeriksaan konsistensi per responden).",
      "4) Mendukung keputusan yang saling bergantung atau berurutan - **YA** (alokasi bersifat berurutan di bawah plafon, sehingga persetujuan satu pemohon mengurangi sisa dana bagi pemohon berikutnya; riwayat skenario tersimpan pada SQLite).",
      "5) Mendukung fase Intelligence-Design-Choice-Implementation - **YA** (Intelligence: ETL, validasi, dan deteksi hubungan kebutuhan-risiko; Design: penyusunan kriteria dan pembobotan AHP; Choice: TOPSIS dan alokasi plafon; Implementation: penerbitan status keputusan, alasan tertulis, dan ekspor CSV).",
      "6) Mendukung variasi gaya dan proses pengambilan keputusan - **YA** (tiga metode pemeringkatan dapat dipertukarkan, bobot dan batas PD dapat diubah seketika).",
      "7) Adaptif dan fleksibel - **SEBAGIAN** (bobot, plafon, dan ambang dapat diubah langsung; pelatihan ulang model terjadwal belum tersedia).",
      "8) User-friendly, kapabilitas grafis kuat, antarmuka interaktif - **YA** (enam tab, penggeser bobot, grafik sensitivitas, kolom batang kemajuan, dan tombol unduh; antarmuka dievaluasi formal dengan Heuristic Evaluation Nielsen, dua temuan berkeparahan tertinggi sudah diperbaiki).",
      "9) Berorientasi EFEKTIVITAS - **YA** (tujuan eksplisit berupa penurunan tingkat gagal bayar dan peningkatan ketepatan sasaran, bukan percepatan proses).",
      "10) Pengambil keputusan memegang kendali penuh - **YA** (sistem bersifat decision support, bukan decision automation; seluruh peringkat disertai alasan agar dapat ditinjau).",
      "11) Dapat dikembangkan atau dimodifikasi sendiri oleh pengguna akhir - **SEBAGIAN** (bobot dan parameter dapat diubah tanpa menyentuh kode; penambahan kriteria baru masih memerlukan penyuntingan config.py).",
      "12) Memanfaatkan model sebagai fitur utama - **YA** (inti sistem berupa model prediktif berlapis MCDM).",
      "13) Dilengkapi komponen pengetahuan untuk masalah kompleks - **YA** (modul knowledge.py memuat basis aturan IKS, skor produktif, dan batas keras PD).",
      "14) Dapat didiseminasikan via web, standalone, CBIS-ERP, atau mobile - **YA** (aplikasi web Streamlit yang dapat dijalankan lokal maupun di-deploy).",
    ]),

  baris("13", "Bagaimana memvalidasi kualitas hasil keputusan dari DSS?",
    "Lima jalur validasi, dengan metrik kuantitatif dan pembanding kebijakan",
    [
      "**1) Metrik kuantitatif model prediktif**, dengan protokol bebas kebocoran. Pemilihan model dan pemilihan ambang keduanya memakai prediksi out-of-fold pada data latih; data uji dipakai **tepat satu kali**. Hasil pada data uji: AUC-ROC 0,7895; AUC-PR 0,6413; Brier score 0,1855; akurasi 0,6467; presisi 0,4512; recall 0,8222; F1 0,5827. Matriks konfusi: TN 120, FP 90, FN 16, TP 74.",
      "**2) Evaluasi berbasis biaya, bukan akurasi.** Cost matrix dataset menyatakan meloloskan pemohon macet lima kali lebih mahal daripada menolak pemohon lancar. Biaya sistem 170 unit, dibanding 190 unit pada ambang lazim 0,50 dan 450 unit bila seluruh pemohon diloloskan, yaitu **penurunan 62,2 persen** terhadap kondisi tanpa model.",
      "**3) Perbandingan dengan empat kebijakan alternatif** di bawah plafon dan batas PD yang sama persis. SPK Hybrid menghasilkan tingkat gagal bayar aktual **0,0 persen** dengan IKS rata-rata **5,39**; pemeringkatan murni risiko 5,6 persen dengan IKS 5,28; pemeringkatan murni kebutuhan 20,0 persen dengan IKS 5,95; urutan kedatangan berkas 21,7 persen dengan IKS 5,22; dan undian rata-rata 2.000 ulangan 20,3 persen dengan IKS 5,03.",
      "**Uji signifikansi atas klaim nol persen.** Tingkat gagal bayar 0 persen atas 18 penerima tidak boleh diumumkan tanpa pengujian, karena satu kasus menggeser angka 5,6 poin persentase. Uji binomial satu sisi menunjukkan seleksi acak diperkirakan menghasilkan 4,5 kasus macet, sedangkan yang teramati 0 kasus, dengan **p = 0,0056**. Hasil ini signifikan pada taraf 1 persen, sehingga bukan kebetulan.",
      "Interpretasi: pada dimensi risiko, SPK Hybrid **melampaui** kebijakan tujuan-tunggal, yaitu 0,0 persen berbanding 5,6 persen, bukan sekadar mendekatinya. Pada dimensi ketepatan sasaran, SPK menangkap **39,2 persen** dari potensi perbaikan yang tersedia. Sistem unggul atas undian pada kedua dimensi sekaligus, sehingga tidak sedang menukar satu tujuan dengan tujuan lain.",
      "**4) Validasi silang antarmetode MCDM.** Korelasi Spearman antarperingkat: TOPSIS dengan SAW 0,9458; SAW dengan VIKOR 0,9336; TOPSIS dengan VIKOR 0,8174. Korelasi tinggi menunjukkan peringkat tidak bergantung pada pilihan metode, sehingga hasil bukan artefak metode.",
      "**5) Uji konsistensi penilaian manusia.** Matriks AHP memperoleh CR 0,0077 terhadap ambang 0,10. Pipeline **menolak berjalan** bila CR melampaui ambang, dan menampilkan pesan agar wawancara diulang, bukan agar matriks disunting supaya lolos.",
      "**6) Pembandingan terhadap tolok ukur terbitan.** Angka hasil hanya bermakna bila disandingkan dengan pembanding. Tingkat gagal bayar sistem 0,0 persen; ambang sehat regulator 5 persen; rata-rata koperasi simpan pinjam Jawa Tengah 6,89 persen (BPS, 2020); segmen UMKM nasional 3,98 persen (Maret 2024). Tolok ukur paling relevan adalah angka Jawa Tengah, karena wilayahnya sama dengan kasus yang dimodelkan.",
      "**7) Evaluasi kemudahan penggunaan dengan Heuristic Evaluation (Nielsen).** Tiga evaluator menelusuri antarmuka secara independen terhadap 10 heuristik sambil mengerjakan tiga tugas uji. Hasil: **10 temuan** yang melanggar 9 dari 10 heuristik, dengan sebaran keparahan 2 bencana, 4 mayor, 3 minor, dan 1 kosmetik. Dua temuan berkeparahan 4 yaitu HE-03 (seluruh bobot dapat digeser ke nol namun peringkat tetap ditampilkan) dan HE-08 (metrik gagal bayar aktual ditampilkan tanpa keterangan bahwa angka itu mustahil tersedia pada penyaluran nyata) **sudah diperbaiki**. Tujuh temuan lain tetap didaftarkan terbuka beserta usulan perbaikannya. **Bias yang diakui**: evaluator adalah pengembang sistem itu sendiri, sehingga temuan berstatus evaluasi awal, bukan pengganti pengujian dengan pengguna nyata.",
      "**8) Pelaporan aturan yang TIDAK mengikat.** Batas beban angsuran 30 persen pendapatan tidak dilanggar seorang pun pada kohort ini, dengan rasio tertinggi 20,7 persen. Fakta ini dilaporkan eksplisit agar aturan tersebut tidak disangka sudah menyaring padahal tidak; aturan dipertahankan sebagai penyaring bagi pengajuan bernilai besar.",
      "**Keterbatasan validasi yang diakui**: (a) selisih Random Forest terhadap Logistic Regression tidak signifikan karena berada di dalam rentang simpangan baku validasi silang; (b) tingkat gagal bayar dihitung atas 18 penerima, sehingga satu kasus menggeser angka 5,6 poin persentase, dan karena itu uji binomial dilampirkan; (c) Heuristic Evaluation sudah dijalankan tetapi oleh pengembang sendiri, sedangkan kuesioner SUS kepada responden belum disebar meski instrumen dan fungsi penghitung skornya sudah siap; (d) basis historis angsuran bukan berasal dari koperasi Indonesia, sehingga probabilitas gagal bayar sahih sebagai peringkat relatif tetapi belum sahih sebagai peluang absolut; (e) kohort pemohon masih simulasi terkalibrasi, dan formulir pendataan 30 sampai 50 pemohon sudah disiapkan untuk menggantinya.",
    ]),
];

// ==========================================================================
// PENYUSUNAN DOKUMEN
// ==========================================================================
const tabelKepala = new Table({
  columnWidths: KOL_KEPALA,
  width: { size: LEBAR_GUNA, type: WidthType.DXA },
  rows: [
    barisKepala("Judul Sistem", "SPK Prioritisasi Penyaluran Kredit Mikro pada Koperasi Simpan Pinjam"),
    barisKepala("Jenis Dokumen", "Laporan identifikasi prototipe Decision Support System"),
    barisKepala("Mata Kuliah", "Sistem Pendukung Keputusan (12023230338)"),
    barisKepala("Tahun", "2026"),
    barisKepala("Tipologi DSS", "Hybrid: Model-driven (dominan) + Data-driven + Knowledge-driven"),
    barisKepala("Metode", "Random Forest (prediksi gagal bayar) + AHP (pembobotan) + TOPSIS (pemeringkatan)"),
    barisKepala("Data Internal", "Basis historis angsuran: Statlog German Credit, UCI id 144, 1.000 baris, 20 atribut, CC BY 4.0"),
    barisKepala("Data Eksternal", "BPS Jawa Tengah Maret 2026 (garis kemiskinan Rp596.676/kapita/bulan; Rp2.571.674/rumah tangga) dan Kepgub Jateng No. 100.3.3.1/505 Tahun 2025 (UMK Surakarta Rp2.570.000)"),
    barisKepala("Lisensi Data", "Creative Commons Attribution 4.0 International (CC BY 4.0)"),
    barisKepala("Keywords", "Decision Support System; Multi-Criteria Decision Making; AHP; TOPSIS; Credit Scoring; Social Targeting"),
    barisKepala("Subject Area", "Penyaluran kredit mikro dan penargetan bantuan sosial, konteks Kota Surakarta"),
    barisKepala("Status Kasus", "SIMULASI TERKALIBRASI. Organisasi bersifat rekaan; parameter kohort dikalibrasi ke statistik BPS dan UMK terverifikasi. Masalah divalidasi lewat riset pustaka, bukan studi lapangan."),
    barisKepala("Evaluasi Usability", "Heuristic Evaluation Nielsen (10 temuan, 3 evaluator) sudah dijalankan; kuesioner SUS beserta 3 tugas uji sudah disusun."),
    barisKepala("Artefak", "9 modul Python, antarmuka Streamlit 6 tab, basis data SQLite, 9 tabel CSV, 6 gambar"),
  ],
});

const tabelUtama = new Table({
  columnWidths: KOL,
  width: { size: LEBAR_GUNA, type: WidthType.DXA },
  rows: [
    new TableRow({
      tableHeader: true,
      children: [
        sel([p("NO", { bold: true, align: AlignmentType.CENTER })], { lebar: KOL[0], shading: BIRU }),
        sel([p("IDENTIFIKASI", { bold: true })], { lebar: KOL[1], shading: BIRU }),
        sel([p("SA", { bold: true })], { lebar: KOL[2], shading: BIRU }),
        sel([p("PENJELASAN", { bold: true })], { lebar: KOL[3], shading: BIRU }),
      ],
    }),
    ...BARIS,
  ],
});

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 20 } },
    },
  },
  sections: [{
    properties: {
      page: { margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 } },
    },
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 60 },
        children: [new TextRun({
          text: "LAPORAN IDENTIFIKASI DECISION SUPPORT SYSTEM",
          bold: true, size: 26, font: "Calibri",
        })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 220 },
        children: [new TextRun({
          text: "Prototipe: SPK Prioritisasi Penyaluran Kredit Mikro",
          size: 22, font: "Calibri",
        })],
      }),
      tabelKepala,
      new Paragraph({ spacing: { after: 240 }, children: [] }),
      tabelUtama,

      // ------------------------------------------------------------------
      new Paragraph({ children: [new PageBreak()] }),
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        spacing: { after: 140 },
        children: [new TextRun({
          text: "LAMPIRAN  Hasil Eksekusi Prototipe",
          bold: true, size: 24, font: "Calibri",
        })],
      }),
      p("Seluruh gambar berikut dihasilkan langsung oleh perintah python -m src.figur, bukan digambar ulang secara manual. Angka pada gambar dapat direproduksi persis karena seluruh tahap memakai random_state 42.", { after: 180 }),

      ...gambar("01_bobot_ahp.png", 0.476,
        "Gambar 1. Bobot kriteria hasil AHP. Kebutuhan sosial (0,2982) dan probabilitas gagal bayar (0,2714) menempati dua posisi teratas, mencerminkan dua tujuan kelembagaan yang saling bertarik. CR 0,0077 berada jauh di bawah ambang 0,10."),

      ...gambar("02_tradeoff_iks_pd.png", 0.402,
        "Gambar 2. Hubungan kebutuhan sosial dan risiko. Pada populasi 1.000 pemohon, tingkat gagal bayar naik dari 20 persen pada IKS 4 menjadi 46 persen pada IKS 8 (r = +0,154), sehingga pertukaran bersifat nyata. Namun pada 40 berkas periode berjalan hubungan tersebut nyaris hilang (r = -0,077), yang berarti pengelola dapat memprioritaskan pemohon berkebutuhan tinggi periode ini tanpa tambahan risiko berarti."),

      ...gambar("04_kurva_biaya.png", 0.556,
        "Gambar 3. Pemilihan ambang berbasis biaya. Ambang 0,41 yang dipilih secara out-of-fold menghasilkan biaya lebih rendah daripada ambang lazim 0,50. Perhatikan bahwa titik biaya terendah tidak berimpit dengan titik akurasi tertinggi, dan inilah alasan akurasi tidak dipakai sebagai kriteria pemilihan."),

      ...gambar("05_perbandingan_kebijakan.png", 0.381,
        "Gambar 4. Validasi terhadap empat kebijakan alternatif pada plafon yang sama. SPK Hybrid unggul pada kedua tujuan sekaligus terhadap undian: tingkat gagal bayar turun dari 20,2 persen menjadi 5,0 persen, sementara rata-rata IKS penerima naik dari 5,03 menjadi 5,35."),

      ...gambar("03_sensitivitas_C1.png", 0.579,
        "Gambar 5. Analisis sensitivitas bobot kriteria kebutuhan sosial. Empat pemohon teratas bertahan pada seluruh rentang bobot yang diuji, sedangkan peringkat menengah berpindah pada tujuh titik balik. Keputusan atas kelompok pertama dapat diambil tanpa keraguan; kelompok kedua memerlukan peninjauan manual."),

      ...gambar("06_pentingnya_fitur.png", 0.657,
        "Gambar 6. Fitur paling berpengaruh pada model prediksi gagal bayar. Status rekening giro mendominasi dengan importance 0,2015, diikuti tenor dan nilai pinjaman."),

      new Paragraph({ spacing: { before: 160, after: 80 }, children: [new TextRun({
        text: "Catatan Etika", bold: true, size: 21, font: "Calibri",
      })] }),
      p("Sistem ini bersifat decision support, bukan decision automation. Keputusan akhir tetap berada pada pengelola koperasi. Setiap peringkat disertai penjelasan mengenai kriteria yang mengangkat dan menekan skor, sehingga penolakan dapat dipertanggungjawabkan kepada pemohon. Dataset yang digunakan tidak memuat NIK, nama, maupun alamat; pada penerapan nyata, data pribadi wajib diganti dengan identitas ter-hash."),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const keluaran = path.join(AKAR, "outputs", "Laporan_Identifikasi_DSS.docx");
  fs.writeFileSync(keluaran, buf);
  console.log("Tersimpan:", keluaran, `(${(buf.length / 1024).toFixed(0)} KB)`);
});
