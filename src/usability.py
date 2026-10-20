"""
Evaluasi kemudahan penggunaan: Heuristic Evaluation dan System Usability Scale.

Memenuhi Tugas 2(b), yaitu "melakukan evaluasi rancangan SPK pada aspek
kemudahan penggunaan".

DUA METODE, DUA PERAN BERBEDA
-----------------------------
Heuristic Evaluation (Nielsen) menemukan MASALAH. Evaluator menelusuri
antarmuka terhadap 10 heuristik dan mencatat pelanggaran beserta tingkat
keparahannya. Tidak membutuhkan responden, sehingga dapat dijalankan tim
pengembang sendiri.

System Usability Scale (Brooke) mengukur PERSEPSI. Sepuluh pernyataan
menghasilkan satu skor 0-100 yang dapat dibandingkan lintas sistem.
Membutuhkan responden, meski cukup 5 sampai 10 orang.

Keduanya saling melengkapi dan tidak saling menggantikan. HE menjawab "apa
yang salah"; SUS menjawab "seberapa buruk rasanya bagi pengguna".

BIAS YANG WAJIB DIAKUI
----------------------
Evaluasi heuristik di bawah dikerjakan oleh tim pengembang sistem itu
sendiri. Evaluator yang menilai karyanya sendiri cenderung melewatkan
masalah yang sudah terbiasa ia hadapi. Temuan ini karenanya berstatus
EVALUASI AWAL, bukan pengganti pengujian dengan pengguna nyata. Nielsen
menganjurkan 3 sampai 5 evaluator independen; di sini tersedia 3 anggota tim.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


# --------------------------------------------------------------------------
# SYSTEM USABILITY SCALE
# --------------------------------------------------------------------------
BUTIR_SUS = [
    "Saya rasa saya akan sering menggunakan sistem ini",
    "Saya merasa sistem ini terlalu rumit",
    "Saya rasa sistem ini mudah digunakan",
    "Saya rasa saya butuh bantuan teknis untuk bisa menggunakan sistem ini",
    "Saya rasa berbagai fungsi dalam sistem ini terpadu dengan baik",
    "Saya rasa ada terlalu banyak ketidakkonsistenan dalam sistem ini",
    "Saya rasa kebanyakan orang akan cepat belajar menggunakan sistem ini",
    "Saya rasa sistem ini sangat merepotkan untuk digunakan",
    "Saya merasa sangat percaya diri saat menggunakan sistem ini",
    "Saya perlu belajar banyak hal sebelum bisa menggunakan sistem ini",
]


def skor_sus(jawaban: list[int]) -> float:
    """
    Hitung skor SUS dari 10 jawaban skala 1-5.

    Butir ganjil (1,3,5,7,9) bernada positif: kontribusi = nilai - 1.
    Butir genap (2,4,6,8,10) bernada negatif: kontribusi = 5 - nilai.
    Jumlah kontribusi (0-40) dikalikan 2,5 menjadi skala 0-100.

    Skor SUS BUKAN persentase. Skor 68 tidak berarti "68 persen puas",
    melainkan titik tengah rujukan dari basis data ribuan sistem.
    """
    if len(jawaban) != 10:
        raise ValueError(f"Butuh tepat 10 jawaban, diterima {len(jawaban)}.")
    if not all(isinstance(n, int) and 1 <= n <= 5 for n in jawaban):
        raise ValueError("Seluruh jawaban harus bilangan bulat 1 sampai 5.")

    ganjil = sum(jawaban[i] - 1 for i in range(0, 10, 2))
    genap = sum(5 - jawaban[i] for i in range(1, 10, 2))
    return (ganjil + genap) * 2.5


def predikat_sus(skor: float) -> str:
    """Tafsir skor menurut Bangor, Kortum, dan Miller (2009)."""
    if skor >= 85:
        return "Excellent"
    if skor >= 72:
        return "Good"
    if skor >= 68:
        return "OK (rata-rata industri)"
    if skor >= 51:
        return "Poor"
    return "Awful"


def ringkas_sus(jawaban_responden: dict[str, list[int]]) -> dict:
    """
    Agregasi skor SUS beberapa responden.

    Skor TERENDAH ikut dilaporkan, bukan hanya rata-rata. Dengan 5 sampai 10
    responden, satu nilai ekstrem menggeser rata-rata beberapa poin, dan
    rata-rata 75 yang menyembunyikan satu responden bernilai 40 adalah
    temuan, bukan gangguan yang perlu diratakan.
    """
    if not jawaban_responden:
        return {"status": "belum ada responden"}

    skor = {nama: skor_sus(j) for nama, j in jawaban_responden.items()}
    nilai = pd.Series(skor)

    # Butir dengan kontribusi terendah menunjukkan aspek paling lemah.
    kontribusi = []
    for i in range(10):
        if i % 2 == 0:
            k = [j[i] - 1 for j in jawaban_responden.values()]
        else:
            k = [5 - j[i] for j in jawaban_responden.values()]
        kontribusi.append({
            "butir": i + 1,
            "pernyataan": BUTIR_SUS[i],
            "kontribusi_rata2": round(sum(k) / len(k), 2),   # maksimum 4
        })

    return {
        "n_responden": len(skor),
        "skor_per_responden": {k: round(v, 1) for k, v in skor.items()},
        "rata_rata": round(float(nilai.mean()), 1),
        "simpangan_baku": round(float(nilai.std(ddof=1)), 1) if len(nilai) > 1 else 0.0,
        "terendah": round(float(nilai.min()), 1),
        "tertinggi": round(float(nilai.max()), 1),
        "predikat": predikat_sus(float(nilai.mean())),
        "butir_terlemah": sorted(kontribusi, key=lambda x: x["kontribusi_rata2"])[:3],
    }


# --------------------------------------------------------------------------
# HEURISTIC EVALUATION (NIELSEN)
# --------------------------------------------------------------------------
HEURISTIK = {
    "H1": "Visibilitas status sistem",
    "H2": "Kesesuaian sistem dengan dunia nyata",
    "H3": "Kendali dan kebebasan pengguna",
    "H4": "Konsistensi dan standar",
    "H5": "Pencegahan kesalahan",
    "H6": "Mengenali, bukan mengingat",
    "H7": "Fleksibilitas dan efisiensi penggunaan",
    "H8": "Desain estetis dan minimalis",
    "H9": "Bantuan pengguna mengenali dan memulihkan kesalahan",
    "H10": "Bantuan dan dokumentasi",
}

# Skala keparahan Nielsen. Angka 0 sampai 4 dipakai untuk menentukan urutan
# perbaikan, bukan untuk dijumlahkan menjadi satu skor tunggal.
KEPARAHAN = {
    0: "Bukan masalah",
    1: "Kosmetik, perbaiki bila ada waktu",
    2: "Minor, prioritas rendah",
    3: "Mayor, prioritas tinggi",
    4: "Bencana, wajib diperbaiki sebelum rilis",
}


@dataclass
class TemuanHE:
    kode: str
    heuristik: str
    lokasi: str
    masalah: str
    keparahan: int
    usulan: str
    status: str = "terbuka"      # terbuka | diperbaiki | ditunda


# --------------------------------------------------------------------------
# HASIL EVALUASI AWAL
#
# Dikerjakan tim pengembang terhadap antarmuka Streamlit, menelusuri enam tab
# sambil mengerjakan tiga tugas uji. Status "diperbaiki" menandai temuan yang
# sudah ditindaklanjuti; status "terbuka" menandai yang belum.
# --------------------------------------------------------------------------
TEMUAN_AWAL = [
    TemuanHE(
        "HE-01", "H1", "Tab Keputusan, saat pertama dibuka",
        "Pipeline berjalan 20 sampai 40 detik pada pemuatan pertama tanpa "
        "penjelasan tahap apa yang sedang berlangsung. Pengguna tidak tahu "
        "apakah sistem bekerja atau menggantung.",
        3,
        "Tambahkan spinner bertahap: ekstraksi data, pelatihan model, "
        "pemeringkatan. Sudah diterapkan lewat pesan pada cache_resource.",
        "diperbaiki",
    ),
    TemuanHE(
        "HE-02", "H2", "Tabel keputusan, nama kolom",
        "Kolom bernama C1 sampai C6 tidak bermakna bagi pengurus koperasi "
        "yang belum membaca laporan. Istilah teknis dipakai tanpa padanan "
        "bahasa sehari-hari.",
        3,
        "Ganti judul kolom menjadi 'C1 IKS', 'C5 PD' dan seterusnya, lalu "
        "sediakan tooltip berisi definisi lengkap. Diterapkan sebagian; "
        "tooltip per kolom belum ada.",
        "ditunda",
    ),
    TemuanHE(
        "HE-03", "H5", "Sidebar, penggeser bobot",
        "Pengguna dapat menggeser seluruh bobot ke 0, sehingga pemeringkatan "
        "kehilangan makna. Sistem tetap menampilkan hasil tanpa peringatan.",
        4,
        "Ditambahkan pemeriksaan jumlah bobot nol yang menghentikan "
        "perhitungan dan menjelaskan akibatnya, bukan menormalisasi diam-diam.",
        "diperbaiki",
    ),
    TemuanHE(
        "HE-04", "H9", "Tab What-if, setelah mengubah nilai",
        "Ketika peringkat tidak berubah sama sekali, sistem menampilkan "
        "delta 0 tanpa menjelaskan mengapa. Pengguna tidak dapat membedakan "
        "antara 'perubahan terlalu kecil' dan 'kriteria ini tidak berpengaruh'.",
        2,
        "Tambahkan keterangan naratif yang menyebut kontribusi kriteria "
        "tersebut terhadap skor akhir pemohon bersangkutan.",
        "terbuka",
    ),
    TemuanHE(
        "HE-05", "H6", "Tab Sensitivitas, grafik garis",
        "Sumbu tegak dibalik agar peringkat 1 berada di atas, tetapi tidak "
        "ada penanda visual yang menjelaskannya. Pembaca harus mengingat "
        "konvensi ini dari keterangan di bawah grafik.",
        2,
        "Beri label 'terbaik' pada ujung atas sumbu dan 'terburuk' pada "
        "ujung bawah.",
        "terbuka",
    ),
    TemuanHE(
        "HE-06", "H10", "Seluruh tab",
        "Tidak ada bantuan dalam aplikasi. Definisi IKS, PD, dan TOPSIS hanya "
        "tersedia pada laporan terpisah, sehingga pengguna harus keluar dari "
        "sistem untuk memahami istilahnya.",
        3,
        "Tambahkan expander 'Apa arti istilah ini?' pada setiap tab.",
        "terbuka",
    ),
    TemuanHE(
        "HE-07", "H3", "Tab Riwayat, tombol simpan skenario",
        "Skenario tersimpan permanen tanpa konfirmasi dan tanpa cara "
        "membatalkan. Salah klik menghasilkan baris yang tidak dapat dihapus "
        "dari antarmuka.",
        3,
        "Tambahkan dialog konfirmasi dan tombol hapus skenario.",
        "terbuka",
    ),
    TemuanHE(
        "HE-08", "H1", "Tab Keputusan, metrik macet aktual",
        "Metrik 'Macet aktual penerima' ditampilkan tanpa penjelasan bahwa "
        "kolom tersebut hanya tersedia karena berkas periode diambil dari "
        "data uji berlabel. Pada penggunaan nyata metrik ini mustahil ada "
        "sebelum masa angsuran berjalan.",
        4,
        "Ditambahkan sakelar Mode evaluasi pada sidebar; metrik diberi label "
        "[EVALUASI] dan disembunyikan di luar mode tersebut.",
        "diperbaiki",
    ),
    TemuanHE(
        "HE-09", "H4", "Tab Keputusan dan Tab Validasi",
        "Nilai rupiah ditampilkan dengan pemisah berbeda antar-tab, yaitu "
        "titik pada satu tempat dan koma pada tempat lain, karena sebagian "
        "berasal dari format Python bawaan.",
        1,
        "Seragamkan lewat satu fungsi pemformat rupiah terpusat.",
        "terbuka",
    ),
    TemuanHE(
        "HE-10", "H7", "Tab Keputusan, pemilihan pemohon",
        "Untuk melihat rincian satu pemohon, pengguna harus menggulir ke "
        "bawah tabel lalu memakai dropdown terpisah. Tidak ada cara memilih "
        "langsung dari baris tabel.",
        2,
        "Aktifkan pemilihan baris pada dataframe dan hubungkan ke panel "
        "rincian.",
        "terbuka",
    ),
]


def tabel_temuan(temuan: list[TemuanHE] | None = None) -> pd.DataFrame:
    """Susun tabel temuan, diurutkan dari paling parah."""
    daftar = temuan or TEMUAN_AWAL
    df = pd.DataFrame([{
        "Kode": t.kode,
        "Heuristik": f"{t.heuristik} {HEURISTIK[t.heuristik]}",
        "Lokasi": t.lokasi,
        "Masalah": t.masalah,
        "Keparahan": t.keparahan,
        "Tingkat": KEPARAHAN[t.keparahan],
        "Usulan perbaikan": t.usulan,
        "Status": t.status,
    } for t in daftar])
    return df.sort_values("Keparahan", ascending=False).reset_index(drop=True)


def ringkas_he(temuan: list[TemuanHE] | None = None) -> dict:
    """
    Ringkasan temuan untuk laporan.

    Keparahan TIDAK dijumlahkan menjadi satu skor. Menjumlahkannya akan
    menyamakan empat masalah kosmetik dengan satu masalah bencana, padahal
    keduanya menuntut tindakan yang sama sekali berbeda.
    """
    daftar = temuan or TEMUAN_AWAL
    sebaran = pd.Series([t.keparahan for t in daftar]).value_counts().sort_index(ascending=False)

    return {
        "n_temuan": len(daftar),
        "n_evaluator": 3,
        "heuristik_terlanggar": sorted({t.heuristik for t in daftar}),
        "sebaran_keparahan": {
            f"{k} {KEPARAHAN[k]}": int(v) for k, v in sebaran.items()
        },
        "wajib_diperbaiki": [t.kode for t in daftar if t.keparahan == 4],
        "prioritas_tinggi": [t.kode for t in daftar if t.keparahan == 3],
        "sudah_diperbaiki": [t.kode for t in daftar if t.status == "diperbaiki"],
        "masih_terbuka": [t.kode for t in daftar if t.status == "terbuka"],
    }


def laporan_he(temuan: list[TemuanHE] | None = None) -> str:
    """Laporan naratif untuk dicetak."""
    r = ringkas_he(temuan)
    baris = [
        "EVALUASI HEURISTIK (NIELSEN)",
        "=" * 72,
        f"Jumlah temuan        : {r['n_temuan']}",
        f"Jumlah evaluator     : {r['n_evaluator']} (tim pengembang)",
        f"Heuristik terlanggar : {len(r['heuristik_terlanggar'])} dari 10 "
        f"({', '.join(r['heuristik_terlanggar'])})",
        "",
        "Sebaran keparahan:",
    ]
    baris += [f"  {k}: {v}" for k, v in r["sebaran_keparahan"].items()]
    baris += [
        "",
        f"Wajib diperbaiki sebelum rilis : {', '.join(r['wajib_diperbaiki']) or 'tidak ada'}",
        f"Prioritas tinggi               : {', '.join(r['prioritas_tinggi']) or 'tidak ada'}",
        f"Sudah ditindaklanjuti          : {', '.join(r['sudah_diperbaiki']) or 'tidak ada'}",
        "",
        "CATATAN BIAS: evaluator adalah pengembang sistem itu sendiri,",
        "sehingga masalah yang sudah terbiasa dihadapi cenderung terlewat.",
        "Temuan ini berstatus evaluasi awal, bukan pengganti pengujian",
        "dengan pengguna nyata.",
    ]
    return "\n".join(baris)


if __name__ == "__main__":
    print(laporan_he())
    print()
    print(tabel_temuan()[["Kode", "Heuristik", "Keparahan", "Status"]].to_string(index=False))
