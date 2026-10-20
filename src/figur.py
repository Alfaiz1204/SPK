"""
Pembuatan gambar untuk laporan dan presentasi.

Jalankan setelah pipeline:
    python -m src.figur

Seluruh gambar memakai matplotlib tanpa gaya pihak ketiga agar bisa
direproduksi di lingkungan mana pun.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")           # backend tanpa layar, wajib untuk server
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config as cfg
from .mcdm import ahp

plt.rcParams.update({
    "figure.dpi": 130,
    "savefig.bbox": "tight",
    "font.size": 9,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def gambar_bobot_ahp() -> None:
    hasil = ahp.bobot_dari_konfigurasi()
    # Nama kriteria dipendekkan agar label sumbu tidak saling menimpa.
    pendek = {
        "C1": "Kebutuhan\nSosial", "C2": "Kapasitas\nAngsur",
        "C3": "Riwayat\nKredit", "C4": "Dampak\nProduktif",
        "C5": "Prob. Gagal\nBayar", "C6": "Nilai\nPengajuan",
    }
    nama = [f"{k}\n{pendek[k]}" for k in cfg.CRITERIA_CODES]

    fig, ax = plt.subplots(figsize=(8.2, 3.9))
    warna = ["#c0392b" if not cfg.CRITERIA_BENEFIT[k] else "#2c6fbb"
             for k in cfg.CRITERIA_CODES]
    bar = ax.bar(nama, hasil.bobot, color=warna)
    ax.bar_label(bar, fmt="%.4f", padding=2, fontsize=8)
    ax.set_ylabel("Bobot")
    ax.set_ylim(0, max(hasil.bobot) * 1.22)
    ax.set_title(
        f"Bobot kriteria hasil AHP  (CR = {hasil.cr:.4f}, ambang {cfg.CR_THRESHOLD})"
    )
    # Legenda manual: dua warna membedakan arah kriteria.
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(color="#2c6fbb", label="Benefit (makin besar makin baik)"),
        Patch(color="#c0392b", label="Cost (makin kecil makin baik)"),
    ], fontsize=8, loc="upper right")
    fig.savefig(cfg.FIGURES / "01_bobot_ahp.png")
    plt.close(fig)


def gambar_trade_off() -> None:
    """
    Dua panel: hubungan kebutuhan-risiko pada tingkat populasi dan pada periode ini.

    Dipisah karena keduanya menjawab pertanyaan berbeda, dan jawabannya tidak
    sama. Panel kiri menjawab "apakah pertukaran itu nyata secara struktural";
    panel kanan menjawab "seberapa mengikat pertukaran itu pada berkas yang
    sedang diputuskan". Menggabungkan keduanya dalam satu grafik akan
    menyembunyikan selisih yang justru perlu dilihat pengambil keputusan.
    """
    populasi = pd.read_csv(cfg.DATA_PROCESSED / "pemohon_bersih.csv")
    periode = pd.read_csv(cfg.TABLES / "keputusan_periode.csv")

    r_populasi = populasi["iks_skor"].corr(populasi["target_macet"])
    r_periode = periode["iks_skor"].corr(periode["pd_model"])

    fig, (kiri, kanan) = plt.subplots(1, 2, figsize=(11.2, 4.5))

    # ---- Panel kiri: populasi -------------------------------------------
    # Nilai IKS dengan kurang dari 10 pengamatan digabung agar persentase
    # tidak dihitung dari sampel yang terlalu kecil untuk ditafsirkan.
    agg = populasi.groupby("iks_skor")["target_macet"].agg(["mean", "count"])
    layak = agg[agg["count"] >= 10]
    jarang = agg[agg["count"] < 10]

    bar = kiri.bar(
        layak.index.astype(str), layak["mean"] * 100,
        color="#2c6fbb", width=0.72,
    )
    kiri.bar_label(
        bar, labels=[f"{v:.0f}%\nn={int(n)}" for v, n in
                     zip(layak["mean"] * 100, layak["count"])],
        padding=2, fontsize=7.5,
    )
    kiri.axhline(
        populasi["target_macet"].mean() * 100, color="#c0392b", ls="--", lw=1.2,
    )
    kiri.text(
        -0.4, populasi["target_macet"].mean() * 100 + 1.4,
        f"Rata-rata populasi {populasi['target_macet'].mean():.1%}",
        color="#c0392b", fontsize=8,
    )
    kiri.set_xlabel("Indeks Kebutuhan Sosial")
    kiri.set_ylabel("Tingkat gagal bayar aktual (%)")
    kiri.set_ylim(0, layak["mean"].max() * 128)
    kiri.set_title(
        f"POPULASI (n={len(populasi):,})\n"
        f"Pertukaran nyata secara struktural: r = {r_populasi:+.3f}",
        fontsize=9.5,
    )
    if len(jarang):
        kiri.text(
            0.98, 0.03,
            f"IKS {', '.join(map(str, jarang.index))} disembunyikan (n < 10)",
            transform=kiri.transAxes, ha="right", fontsize=7, color="#7f8c8d",
        )

    # ---- Panel kanan: periode berjalan ----------------------------------
    gaya = {
        "DISETUJUI": ("#1e8449", "o", 1.0),
        "DITUNDA": ("#b7950b", "s", 0.75),
        "DITOLAK": ("#922b21", "X", 0.9),
    }
    for status, (warna, penanda, alfa) in gaya.items():
        sub = periode[periode["status_keputusan"] == status]
        kanan.scatter(
            sub["iks_skor"], sub["pd_model"],
            s=sub["nilai_pengajuan_rp"] / 95_000, c=warna, marker=penanda,
            alpha=alfa, edgecolors="white", linewidths=0.6,
            label=f"{status} (n={len(sub)})",
        )

    kanan.axhline(cfg.PD_HARD_LIMIT, color="#922b21", ls="--", lw=1.1)
    kanan.text(
        periode["iks_skor"].min(), cfg.PD_HARD_LIMIT - 0.028,
        f"Batas keras PD {cfg.PD_HARD_LIMIT}", color="#922b21",
        fontsize=7.5, ha="left", va="top",
    )

    kemiringan, potongan = np.polyfit(periode["iks_skor"], periode["pd_model"], 1)
    x = np.linspace(periode["iks_skor"].min(), periode["iks_skor"].max(), 50)
    kanan.plot(x, kemiringan * x + potongan, color="#34495e", lw=1.3, ls=":")

    kanan.set_xlabel("Indeks Kebutuhan Sosial")
    kanan.set_ylabel("Probabilitas gagal bayar (PD)")
    kanan.set_ylim(0.08, 0.80)
    kanan.set_title(
        f"PERIODE BERJALAN (n={len(periode)})\n"
        f"Pertukaran nyaris tidak mengikat: r = {r_periode:+.3f}",
        fontsize=9.5,
    )
    kanan.legend(fontsize=7.5, loc="upper left", framealpha=0.92)

    fig.suptitle(
        "Hubungan kebutuhan sosial dan risiko gagal bayar: kuat pada populasi, "
        "lemah pada berkas periode ini",
        fontsize=10, y=1.045,
    )
    fig.savefig(cfg.FIGURES / "02_tradeoff_iks_pd.png")
    plt.close(fig)


def gambar_sensitivitas() -> None:
    """Jejak peringkat 8 pemohon teratas saat bobot C1 divariasikan."""
    sens = pd.read_csv(cfg.TABLES / "sensitivitas_C1.csv")
    keputusan = pd.read_csv(cfg.TABLES / "keputusan_periode.csv")
    teratas = keputusan.nsmallest(8, "rank_TOPSIS")["id_pemohon"].tolist()

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    peta_warna = plt.cm.tab10(np.linspace(0, 1, 10))
    for i, pid in enumerate(teratas):
        sub = sens[sens["id_pemohon"] == pid].sort_values("bobot")
        ax.plot(sub["bobot"], sub["peringkat"], marker="o", ms=3.2, lw=1.4,
                color=peta_warna[i], label=pid)

    bobot_awal = ahp.bobot_dari_konfigurasi().bobot[cfg.CRITERIA_CODES.index("C1")]
    ax.axvline(bobot_awal, color="#34495e", ls="--", lw=1.2)
    ax.text(bobot_awal + 0.006, 2, f"Bobot hasil AHP\n{bobot_awal:.3f}", fontsize=8)

    ax.axhspan(0.5, 10.5, color="#2ecc71", alpha=0.08)
    ax.text(0.055, 10.2, "Zona 10 besar", fontsize=8, color="#1e8449")

    ax.invert_yaxis()
    ax.set_xlabel("Bobot kriteria C1 (Indeks Kebutuhan Sosial)")
    ax.set_ylabel("Peringkat (1 = teratas)")
    ax.set_title("Analisis sensitivitas: ketahanan peringkat terhadap perubahan bobot")
    ax.legend(fontsize=7.5, ncol=4, loc="lower right")
    fig.savefig(cfg.FIGURES / "03_sensitivitas_C1.png")
    plt.close(fig)


def gambar_kurva_biaya() -> None:
    """Biaya yang diharapkan sebagai fungsi ambang keputusan."""
    kurva = pd.read_csv(cfg.TABLES / "kurva_biaya.csv")
    ambang_optimal = float(kurva.loc[kurva["biaya"].idxmin(), "ambang"])

    fig, kiri = plt.subplots(figsize=(7.2, 4.0))
    kiri.plot(kurva["ambang"], kurva["biaya"], color="#c0392b", lw=1.8,
              label="Biaya yang diharapkan")
    kiri.axvline(ambang_optimal, color="#2c3e50", ls="--", lw=1.2)
    kiri.axvline(0.5, color="#7f8c8d", ls=":", lw=1.2)
    kiri.set_xlabel("Ambang keputusan atas PD")
    kiri.set_ylabel("Biaya (unit cost matrix)", color="#c0392b")
    kiri.tick_params(axis="y", labelcolor="#c0392b")

    biaya_optimal = kurva["biaya"].min()
    biaya_05 = float(kurva.loc[(kurva["ambang"] - 0.5).abs().idxmin(), "biaya"])
    kiri.annotate(
        f"Ambang optimal {ambang_optimal:.2f}\nbiaya {biaya_optimal:.0f}",
        xy=(ambang_optimal, biaya_optimal), xytext=(ambang_optimal + 0.13,
                                                    biaya_optimal + 90),
        arrowprops=dict(arrowstyle="->", color="#2c3e50"), fontsize=8,
    )
    kiri.annotate(
        f"Ambang lazim 0.50\nbiaya {biaya_05:.0f}",
        xy=(0.5, biaya_05), xytext=(0.6, biaya_05 + 150),
        arrowprops=dict(arrowstyle="->", color="#7f8c8d"), fontsize=8,
    )

    kanan = kiri.twinx()
    kanan.plot(kurva["ambang"], kurva["recall"], color="#2c6fbb", lw=1.3,
               label="Recall (macet tertangkap)")
    kanan.plot(kurva["ambang"], kurva["presisi"], color="#16a085", lw=1.3,
               label="Presisi")
    kanan.set_ylabel("Recall / Presisi")
    kanan.grid(False)

    garis = kiri.get_lines()[:1] + kanan.get_lines()
    kiri.legend(garis, [g.get_label() for g in garis], fontsize=8, loc="upper center")
    kiri.set_title(
        "Pemilihan ambang berbasis biaya, bukan akurasi\n"
        f"(cost matrix dataset: salah loloskan = {cfg.COST_FN:.0f}x salah tolak)"
    )
    fig.savefig(cfg.FIGURES / "04_kurva_biaya.png")
    plt.close(fig)


def gambar_perbandingan_kebijakan() -> None:
    """Dua sumbu: tingkat gagal bayar dan ketepatan sasaran per kebijakan."""
    tabel = pd.read_csv(cfg.TABLES / "perbandingan_kebijakan.csv", index_col=0)

    nama_pendek = {
        "SPK Hybrid (AHP+TOPSIS)": "SPK Hybrid",
        "Hanya Risiko (PD terkecil)": "Hanya Risiko",
        "Hanya Kebutuhan (IKS terbesar)": "Hanya Kebutuhan",
        "Siapa Cepat (FCFS)": "Siapa Cepat",
    }
    label = [nama_pendek.get(i, "Undian") for i in tabel.index]
    warna = ["#1e8449" if l == "SPK Hybrid" else "#95a5a6" for l in label]

    fig, (kiri, kanan) = plt.subplots(1, 2, figsize=(10.5, 4.0))

    b1 = kiri.bar(label, tabel["tingkat_macet"] * 100, color=warna)
    kiri.bar_label(b1, fmt="%.1f%%", padding=2, fontsize=8)
    kiri.set_ylabel("Tingkat gagal bayar penerima (%)")
    kiri.set_title("Keberlanjutan finansial\n(makin rendah makin baik)")
    kiri.tick_params(axis="x", rotation=28, labelsize=8)
    kiri.set_ylim(0, max(tabel["tingkat_macet"]) * 118)

    b2 = kanan.bar(label, tabel["iks_rata2"], color=warna)
    kanan.bar_label(b2, fmt="%.2f", padding=2, fontsize=8)
    kanan.set_ylabel("Rata-rata IKS penerima")
    kanan.set_title("Ketepatan sasaran sosial\n(makin tinggi makin baik)")
    kanan.tick_params(axis="x", rotation=28, labelsize=8)
    kanan.set_ylim(4.5, max(tabel["iks_rata2"]) * 1.06)

    fig.suptitle(
        "Validasi: SPK Hybrid unggul pada kedua tujuan sekaligus, "
        "bukan menukar satu dengan yang lain", fontsize=10, y=1.02,
    )
    fig.savefig(cfg.FIGURES / "05_perbandingan_kebijakan.png")
    plt.close(fig)


def gambar_pentingnya_fitur() -> None:
    fitur = pd.read_csv(cfg.TABLES / "pentingnya_fitur.csv").head(14)[::-1]

    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    bar = ax.barh(fitur["fitur"], fitur["importance"], color="#2c6fbb")
    ax.bar_label(bar, fmt="%.3f", padding=2, fontsize=7.5)
    ax.set_xlabel("Importance")
    ax.set_title("14 fitur paling berpengaruh pada model prediksi gagal bayar")
    ax.set_xlim(0, fitur["importance"].max() * 1.18)
    fig.savefig(cfg.FIGURES / "06_pentingnya_fitur.png")
    plt.close(fig)


def buat_semua() -> None:
    cfg.FIGURES.mkdir(parents=True, exist_ok=True)
    for fungsi in [
        gambar_bobot_ahp, gambar_trade_off, gambar_sensitivitas,
        gambar_kurva_biaya, gambar_perbandingan_kebijakan,
        gambar_pentingnya_fitur,
    ]:
        fungsi()
        print(f"  dibuat: {fungsi.__name__}")
    print(f"Seluruh gambar tersimpan di {cfg.FIGURES}")


if __name__ == "__main__":
    buat_semua()
