/**
 * Pembuat slide presentasi demo SPK.
 * Jalankan: node docs/build_deck.js
 *
 * Urutan slide mengikuti kriteria rubrik Demo & Presentasi, yang menilai
 * kemampuan menjelaskan NILAI BISNIS kepada audiens manajerial, bukan
 * kedalaman teknis. Arsitektur baru muncul pada slide 7, setelah masalah,
 * hasil, dan bukti disampaikan lebih dulu.
 */
const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");

const AKAR = path.resolve(__dirname, "..");
const FIG = path.join(AKAR, "outputs", "figures");
const ringkas = JSON.parse(
  fs.readFileSync(path.join(AKAR, "outputs", "ringkasan.json"), "utf8")
);

// Palet
const TINTA = "1A2332";
const REDUP = "5A6B7D";
const AKSEN = "1E6F50";
const BAHAYA = "A33A2E";
const GARIS = "D8DEE4";
const LATAR = "FFFFFF";

const pres = new PptxGenJS();
pres.layout = "LAYOUT_WIDE";          // 13.3 x 7.5 inci
pres.author = "Tim SPK";
pres.title = "SPK Prioritisasi Penyaluran Kredit Mikro";

const W = 13.3;

/** Judul + garis bawah, dipakai setiap slide isi. */
function kepala(s, judul, anak) {
  s.addText(judul, {
    x: 0.6, y: 0.38, w: W - 1.2, h: 0.5,
    fontSize: 26, bold: true, color: TINTA, fontFace: "Calibri",
  });
  if (anak) {
    s.addText(anak, {
      x: 0.6, y: 0.9, w: W - 1.2, h: 0.32,
      fontSize: 13, color: REDUP, fontFace: "Calibri",
    });
  }
  s.addShape(pres.ShapeType.rect, {
    x: 0.6, y: anak ? 1.28 : 0.95, w: W - 1.2, h: 0.022, fill: { color: GARIS },
  });
}

/** Kartu angka besar. */
function kartu(s, x, y, w, nilai, label, warna) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h: 1.5, rectRadius: 0.08,
    fill: { color: "F6F8FA" }, line: { color: GARIS, width: 1 },
  });
  s.addText(nilai, {
    x, y: y + 0.18, w, h: 0.7,
    fontSize: 30, bold: true, color: warna || AKSEN,
    align: "center", fontFace: "Calibri",
  });
  s.addText(label, {
    x: x + 0.1, y: y + 0.88, w: w - 0.2, h: 0.5,
    fontSize: 11, color: REDUP, align: "center", fontFace: "Calibri",
  });
}

// ==========================================================================
// 1  Sampul
// ==========================================================================
let s = pres.addSlide();
s.background = { color: TINTA };
s.addText("Siapa yang didahulukan\nketika dana tidak cukup?", {
  x: 0.9, y: 1.7, w: 11.5, h: 1.9,
  fontSize: 40, bold: true, color: "FFFFFF", fontFace: "Calibri", lineSpacing: 46,
});
s.addText(
  "Sistem Pendukung Keputusan Prioritisasi Penyaluran Kredit Mikro\n" +
  "Koperasi Simpan Pinjam  ·  Kota Surakarta",
  { x: 0.9, y: 3.75, w: 11.5, h: 0.9, fontSize: 17, color: "A9B8C6", fontFace: "Calibri" }
);
s.addShape(pres.ShapeType.rect, { x: 0.9, y: 4.9, w: 2.2, h: 0.04, fill: { color: AKSEN } });
s.addText("Mata Kuliah Sistem Pendukung Keputusan  ·  2026", {
  x: 0.9, y: 5.2, w: 11.5, h: 0.4, fontSize: 13, color: "7E8FA0", fontFace: "Calibri",
});

// ==========================================================================
// 2  Masalah
// ==========================================================================
s = pres.addSlide();
kepala(s, "Masalahnya bukan teknis. Masalahnya memilih.",
  "Setiap periode, pengajuan melebihi dana yang tersedia");

kartu(s, 0.6, 1.65, 2.9, "Rp156 jt", "Total pengajuan\n40 berkas masuk", TINTA);
kartu(s, 3.75, 1.65, 2.9, "Rp60 jt", "Dana tersedia\nplafon periode", TINTA);
kartu(s, 6.9, 1.65, 2.9, "2,6×", "Permintaan terhadap\ndana tersedia", BAHAYA);
kartu(s, 10.05, 1.65, 2.65, "25%", "Gagal bayar pada\npraktik siapa-cepat", BAHAYA);

s.addText("Dua tujuan koperasi saling bertarik", {
  x: 0.6, y: 3.45, w: 12.1, h: 0.4, fontSize: 17, bold: true, color: TINTA, fontFace: "Calibri",
});
s.addText(
  [
    { text: "Misi sosial — dahulukan anggota yang paling membutuhkan.", options: { bullet: true, breakLine: true } },
    { text: "Keberlanjutan — hindari kredit macet, karena kerugiannya menggerus simpanan anggota lain.", options: { bullet: true, breakLine: true } },
    { text: "Seberapa besar bobot kebutuhan sosial dibanding risiko TIDAK ADA jawabannya di dalam data. Itu pertanyaan kebijakan.", options: { bullet: true, bold: true } },
  ],
  { x: 0.8, y: 3.95, w: 11.9, h: 1.5, fontSize: 14, color: TINTA, fontFace: "Calibri", lineSpacing: 24 }
);

s.addShape(pres.ShapeType.roundRect, {
  x: 0.6, y: 5.55, w: 12.1, h: 1.1, rectRadius: 0.08,
  fill: { color: "FDF6EC" }, line: { color: "E8C99B", width: 1 },
});
s.addText(
  "Garis kemiskinan per rumah tangga Jawa Tengah Rp2.571.674  ≈  UMK Surakarta Rp2.570.000.\n" +
  "Selisihnya 0,07%. Pekerja berupah minimum di Solo yang menanggung keluarga rata-rata berada tepat di garis kemiskinan.",
  { x: 0.85, y: 5.72, w: 11.6, h: 0.8, fontSize: 12.5, color: "7A5A1E", fontFace: "Calibri", lineSpacing: 19 }
);

// ==========================================================================
// 3  Hasil
// ==========================================================================
s = pres.addSlide();
kepala(s, "Hasil: dua tujuan tercapai sekaligus",
  "Pada plafon yang sama persis, dibandingkan empat kebijakan alternatif");

const perb = ringkas.perbandingan_kebijakan;
const spk = perb["SPK Hybrid (AHP+TOPSIS)"];
const fcfs = perb["Siapa Cepat (FCFS)"];

kartu(s, 0.6, 1.65, 3.0, `${(spk.tingkat_macet * 100).toFixed(1)}%`,
  `Gagal bayar penerima\nturun dari ${(fcfs.tingkat_macet * 100).toFixed(1)}% praktik lama`, AKSEN);
kartu(s, 3.85, 1.65, 3.0, spk.iks_rata2.toFixed(2),
  "Rata-rata skor kebutuhan\npenerima, naik dari 5,03", AKSEN);
kartu(s, 7.1, 1.65, 3.0, `${spk.n_penerima}`,
  `penerima\n${spk.utilisasi.toFixed(1)}% plafon terpakai`, TINTA);
kartu(s, 10.35, 1.65, 2.35, "p=0,006", "Uji binomial\nbukan kebetulan", AKSEN);

s.addTable(
  [
    [
      { text: "Kebijakan", options: { bold: true, color: "FFFFFF", fill: { color: TINTA } } },
      { text: "Penerima", options: { bold: true, color: "FFFFFF", fill: { color: TINTA }, align: "center" } },
      { text: "Gagal bayar", options: { bold: true, color: "FFFFFF", fill: { color: TINTA }, align: "center" } },
      { text: "Skor kebutuhan", options: { bold: true, color: "FFFFFF", fill: { color: TINTA }, align: "center" } },
    ],
    ...Object.entries(perb).map(([nama, v]) => {
      const utama = nama.startsWith("SPK");
      const gaya = utama
        ? { bold: true, color: "FFFFFF", fill: { color: AKSEN } }
        : { color: TINTA };
      return [
        { text: nama, options: gaya },
        { text: v.n_penerima.toFixed(0), options: { ...gaya, align: "center" } },
        { text: `${(v.tingkat_macet * 100).toFixed(1)}%`, options: { ...gaya, align: "center" } },
        { text: v.iks_rata2.toFixed(2), options: { ...gaya, align: "center" } },
      ];
    }),
  ],
  {
    x: 0.6, y: 3.5, w: 12.1, colW: [5.5, 2.0, 2.3, 2.3],
    fontSize: 12.5, fontFace: "Calibri", border: { type: "solid", color: GARIS, pt: 1 },
    rowH: 0.42, valign: "middle",
  }
);
s.addText(
  "Sistem lebih baik daripada undian pada KEDUA kolom. Ia tidak menukar satu tujuan dengan tujuan lain.",
  { x: 0.6, y: 6.45, w: 12.1, h: 0.4, fontSize: 13, bold: true, color: AKSEN, fontFace: "Calibri" }
);

// ==========================================================================
// 4  Gambar perbandingan
// ==========================================================================
s = pres.addSlide();
kepala(s, "Mengapa bukan sekadar urutkan menurut risiko?",
  "Kebijakan tujuan-tunggal unggul di satu sisi dan gagal di sisi lain");
s.addImage({
  path: path.join(FIG, "05_perbandingan_kebijakan.png"),
  x: 1.25, y: 1.55, w: 10.8, h: 4.12,
});
s.addText(
  "Hanya Kebutuhan mencapai sasaran sosial tertinggi (5,95) tetapi gagal bayarnya 20%. " +
  "Hanya Risiko aman tetapi melayani pemohon yang kurang membutuhkan. Sistem hibrida mengambil keduanya.",
  { x: 0.6, y: 5.9, w: 12.1, h: 0.8, fontSize: 12.5, color: REDUP, fontFace: "Calibri", lineSpacing: 19 }
);

// ==========================================================================
// 5  Temuan yang membalik dugaan
// ==========================================================================
s = pres.addSlide();
kepala(s, "Temuan: penilaian pakar ternyata terbalik",
  "Berkas kosong bukan berkas bersih — efek thin file");

s.addTable(
  [
    [
      { text: "Riwayat kredit pemohon", options: { bold: true, color: "FFFFFF", fill: { color: TINTA } } },
      { text: "Dugaan pakar", options: { bold: true, color: "FFFFFF", fill: { color: TINTA }, align: "center" } },
      { text: "Gagal bayar nyata", options: { bold: true, color: "FFFFFF", fill: { color: TINTA }, align: "center" } },
    ],
    [{ text: "Belum pernah meminjam" }, { text: "Paling aman", options: { align: "center", color: AKSEN } }, { text: "57,1%", options: { align: "center", bold: true, color: BAHAYA } }],
    [{ text: "Semua pinjaman lunas" }, { text: "Aman", options: { align: "center", color: AKSEN } }, { text: "55,3%", options: { align: "center", bold: true, color: BAHAYA } }],
    [{ text: "Pinjaman berjalan lancar" }, { text: "Sedang", options: { align: "center" } }, { text: "31,8%", options: { align: "center" } }],
    [{ text: "Pernah menunggak" }, { text: "Berisiko", options: { align: "center", color: BAHAYA } }, { text: "32,8%", options: { align: "center" } }],
    [{ text: "Akun kritis / pinjam di lembaga lain" }, { text: "Paling berisiko", options: { align: "center", color: BAHAYA } }, { text: "17,6%", options: { align: "center", bold: true, color: AKSEN } }],
  ],
  {
    x: 0.6, y: 1.65, w: 12.1, colW: [6.1, 3.0, 3.0],
    fontSize: 13, fontFace: "Calibri", border: { type: "solid", color: GARIS, pt: 1 },
    rowH: 0.45, valign: "middle", color: TINTA,
  }
);
s.addShape(pres.ShapeType.roundRect, {
  x: 0.6, y: 5.0, w: 12.1, h: 1.55, rectRadius: 0.08,
  fill: { color: "F0F7F3" }, line: { color: AKSEN, width: 1 },
});
s.addText(
  [
    { text: "Mengapa terbalik?  ", options: { bold: true } },
    { text: "Pemohon tanpa riwayat belum pernah diuji kemampuannya membayar. " +
            "Pemohon berstatus akun kritis justru sudah lolos penilaian lembaga lain.\n" },
    { text: "Skor dikalibrasi ulang pada iterasi 2. Versi pakar tetap disimpan di dalam kode sebagai pembanding — " +
            "selisih antara dugaan manusia dan perilaku data adalah temuan, bukan kesalahan yang perlu disembunyikan.",
      options: { italic: true } },
  ],
  { x: 0.85, y: 5.2, w: 11.6, h: 1.2, fontSize: 12.5, color: TINTA, fontFace: "Calibri", lineSpacing: 19 }
);

// ==========================================================================
// 6  Sensitivitas
// ==========================================================================
s = pres.addSlide();
kepala(s, "Seberapa kuat peringkat ini bertahan?",
  "Bobot digeser dari 0,05 sampai 0,60 — mana yang berubah, mana yang tidak");
s.addImage({
  path: path.join(FIG, "03_sensitivitas_C1.png"),
  x: 2.15, y: 1.5, w: 9.0, h: 4.2,
});
s.addText(
  [
    { text: "Empat pemohon teratas bertahan di 10 besar pada 100% skenario bobot — putuskan tanpa ragu.", options: { bullet: true, breakLine: true } },
    { text: "Peringkat menengah berpindah pada 7 titik balik — tinjau manual sebelum memutuskan.", options: { bullet: true } },
  ],
  { x: 0.8, y: 5.85, w: 11.9, h: 0.9, fontSize: 13, color: TINTA, fontFace: "Calibri", lineSpacing: 21 }
);

// ==========================================================================
// 7  Arsitektur
// ==========================================================================
s = pres.addSlide();
kepala(s, "Bagaimana sistem ini dibangun", "Paradigma Data–Model–Dialog, ditambah subsistem pengetahuan");

const blok = [
  { t: "DATA", d: "Basis historis angsuran\nStatistik BPS Jawa Tengah\nUMK Kepgub Jateng 2026", x: 0.6 },
  { t: "MODEL", d: "Random Forest → risiko\nAHP → bobot kriteria\nTOPSIS → peringkat", x: 3.72 },
  { t: "PENGETAHUAN", d: "14 kriteria miskin BPS\nSkor dampak produktif\nBatas keras risiko", x: 6.84 },
  { t: "DIALOG", d: "Antarmuka web 6 tab\nBobot dapat diubah\nRiwayat tersimpan", x: 9.96 },
];
blok.forEach((b) => {
  s.addShape(pres.ShapeType.roundRect, {
    x: b.x, y: 1.6, w: 2.74, h: 2.1, rectRadius: 0.08,
    fill: { color: "F6F8FA" }, line: { color: AKSEN, width: 1.5 },
  });
  s.addText(b.t, {
    x: b.x, y: 1.75, w: 2.74, h: 0.38,
    fontSize: 14, bold: true, color: AKSEN, align: "center", fontFace: "Calibri",
  });
  s.addText(b.d, {
    x: b.x + 0.15, y: 2.2, w: 2.44, h: 1.35,
    fontSize: 11, color: TINTA, align: "center", fontFace: "Calibri", lineSpacing: 17,
  });
});

s.addText("Angka kunci yang bisa diperiksa", {
  x: 0.6, y: 3.95, w: 12.1, h: 0.35, fontSize: 15, bold: true, color: TINTA, fontFace: "Calibri",
});
s.addTable(
  [
    [
      { text: "Model terpilih", options: { bold: true } },
      { text: `${ringkas.model.terpilih} — AUC validasi silang ${ringkas.model.cv_auc_mean.toFixed(4)} ± ${ringkas.model.cv_auc_std.toFixed(4)}` },
    ],
    [
      { text: "Hasil pada data uji", options: { bold: true } },
      { text: `AUC ${ringkas.model.auc.toFixed(4)} · Recall ${ringkas.model.recall.toFixed(3)} · ambang ${ringkas.model.ambang} dipilih out-of-fold` },
    ],
    [
      { text: "Konsistensi AHP", options: { bold: true } },
      { text: `CR = ${ringkas.ahp.cr.toFixed(4)} terhadap ambang 0,10 — agregasi 3 responden, rata-rata geometrik` },
    ],
    [
      { text: "Validasi lintas metode", options: { bold: true } },
      { text: "Korelasi Spearman TOPSIS–SAW 0,946 — peringkat bukan artefak metode" },
    ],
  ],
  {
    x: 0.6, y: 4.38, w: 12.1, colW: [3.2, 8.9],
    fontSize: 12, fontFace: "Calibri", border: { type: "solid", color: GARIS, pt: 1 },
    rowH: 0.42, valign: "middle", color: TINTA,
  }
);

// ==========================================================================
// 8  Keterbatasan
// ==========================================================================
s = pres.addSlide();
kepala(s, "Apa yang BELUM bisa dilakukan sistem ini",
  "Disampaikan di depan, bukan ditunggu sampai ditanya");

s.addTable(
  [
    [
      { text: "Keterbatasan", options: { bold: true, color: "FFFFFF", fill: { color: BAHAYA } } },
      { text: "Akibatnya", options: { bold: true, color: "FFFFFF", fill: { color: BAHAYA } } },
      { text: "Rencana penutupan", options: { bold: true, color: "FFFFFF", fill: { color: BAHAYA } } },
    ],
    [
      { text: "Basis historis berasal dari luar negeri" },
      { text: "PD harus dibaca sebagai peringkat risiko relatif, bukan peluang mutlak" },
      { text: "Latih ulang dengan data angsuran koperasi mitra" },
    ],
    [
      { text: "Kohort pemohon masih simulasi terkalibrasi" },
      { text: "Angka hasil sahih sebagai bukti rancangan, bukan temuan lapangan" },
      { text: "Masalah divalidasi riset pustaka: BPS, SE BI, Kemensos" },
    ],
    [
      { text: "4 dari 14 kriteria BPS tanpa padanan data" },
      { text: "Skor kebutuhan berskala 0–10, bukan 0–14" },
      { text: "4 butir itu sudah masuk formulir pendataan" },
    ],
    [
      { text: "Hanya 18 penerima pada periode uji" },
      { text: "Satu kasus macet menggeser angka 5,6 poin persentase" },
      { text: "Uji binomial dilaporkan (p = 0,006)" },
    ],
    [
      { text: "Evaluator usability adalah pengembang sendiri" },
      { text: "Masalah yang sudah terbiasa dihadapi cenderung terlewat" },
      { text: "Heuristic Evaluation sudah jalan (10 temuan, 2 terparah diperbaiki); SUS siap disebar" },
    ],
  ],
  {
    x: 0.6, y: 1.6, w: 12.1, colW: [3.8, 4.5, 3.8],
    fontSize: 11.5, fontFace: "Calibri", border: { type: "solid", color: GARIS, pt: 1 },
    rowH: 0.62, valign: "middle", color: TINTA,
  }
);
s.addText(
  "Sistem ini decision support, bukan decision automation. Keputusan akhir tetap pada pengurus koperasi, " +
  "dan setiap peringkat disertai alasan agar penolakan dapat dipertanggungjawabkan kepada pemohon.",
  { x: 0.6, y: 5.75, w: 12.1, h: 0.8, fontSize: 13, italic: true, color: REDUP, fontFace: "Calibri", lineSpacing: 20 }
);

// ==========================================================================
// 9  Penutup
// ==========================================================================
s = pres.addSlide();
s.background = { color: TINTA };
s.addText("Yang berubah bagi koperasi", {
  x: 0.9, y: 1.3, w: 11.5, h: 0.65,
  fontSize: 30, bold: true, color: "FFFFFF", fontFace: "Calibri",
});
s.addShape(pres.ShapeType.rect, { x: 0.9, y: 2.1, w: 2.2, h: 0.04, fill: { color: AKSEN } });

[
  ["Sebelum", "Urutan kedatangan berkas. Gagal bayar 25%. Alasan penolakan tidak terdokumentasi.", "A9B8C6"],
  ["Sesudah", "Peringkat berbasis enam kriteria. Gagal bayar 0% pada periode uji. Setiap keputusan disertai alasan tertulis.", "FFFFFF"],
  ["Yang tetap manusia", "Bobot antartujuan ditetapkan pengurus, bukan sistem. Persetujuan akhir tetap di tangan manajer.", "A9B8C6"],
].forEach(([judul, isi, warna], i) => {
  s.addText(judul, {
    x: 0.9, y: 2.55 + i * 1.15, w: 2.4, h: 0.4,
    fontSize: 15, bold: true, color: AKSEN, fontFace: "Calibri",
  });
  s.addText(isi, {
    x: 3.5, y: 2.55 + i * 1.15, w: 8.9, h: 0.85,
    fontSize: 14, color: warna, fontFace: "Calibri", lineSpacing: 22,
  });
});

s.addText("Terima kasih  ·  Pertanyaan?", {
  x: 0.9, y: 6.3, w: 11.5, h: 0.45,
  fontSize: 17, color: "7E8FA0", fontFace: "Calibri",
});

const keluaran = path.join(AKAR, "outputs", "Presentasi_SPK.pptx");
pres.writeFile({ fileName: keluaran }).then(() => {
  console.log("Tersimpan:", keluaran);
});
