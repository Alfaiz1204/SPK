"""
Orkestrator SPK: menyatukan subsistem Data, Model, dan Pengetahuan.

Jalankan dengan:
    python -m src.pipeline

Seluruh keluaran ditulis ke outputs/ sebagai CSV dan JSON agar bisa dibaca
antarmuka Streamlit maupun dilampirkan ke laporan tanpa menjalankan ulang
pipeline.

Alur:
    ETL -> pisah latih/uji -> kalibrasi basis pengetahuan -> latih model
        -> bentuk berkas pengajuan periode berjalan -> matriks keputusan
        -> AHP -> TOPSIS/SAW/VIKOR -> alokasi plafon -> sensitivitas
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd

from . import config as cfg
from . import eksternal as ext
from . import etl, evaluasi, knowledge, lokalisasi, ml_model
from . import pustaka, sensitivity, usability
from .mcdm import ahp, ranking


# --------------------------------------------------------------------------
# MATRIKS KEPUTUSAN
# --------------------------------------------------------------------------
def bentuk_matriks_keputusan(df: pd.DataFrame) -> tuple[np.ndarray, list[str], list[bool]]:
    """Susun matriks (m alternatif x n kriteria) sesuai urutan config.CRITERIA."""
    kolom = [cfg.CRITERIA_COLUMNS[k] for k in cfg.CRITERIA_CODES]
    hilang = [k for k in kolom if k not in df.columns]
    if hilang:
        raise KeyError(f"Kolom kriteria belum dihitung: {hilang}")

    matriks = df[kolom].to_numpy(dtype=float)
    benefit = [cfg.CRITERIA_BENEFIT[k] for k in cfg.CRITERIA_CODES]
    return matriks, kolom, benefit


# --------------------------------------------------------------------------
# ALOKASI PLAFON
# --------------------------------------------------------------------------
def alokasikan_plafon(
    df_peringkat: pd.DataFrame,
    plafon: float = cfg.PLAFON_PERIODE,
    pd_batas: float = cfg.PD_HARD_LIMIT,
) -> pd.DataFrame:
    """
    Terjemahkan peringkat menjadi keputusan penyaluran di bawah batas anggaran.

    Dua aturan yang berlaku di atas peringkat:

    1. Batas keras PD. Pemohon dengan PD di atas ambang ditolak berapa pun
       peringkatnya. MCDM bersifat kompensatoris: skor kebutuhan sosial yang
       sangat tinggi secara matematis bisa menutupi risiko yang sangat tinggi.
       Secara kelembagaan itu tidak bisa diterima, karena kredit macet merugikan
       pemohon itu sendiri sekaligus menggerus dana anggota lain.

    2. Alokasi berurutan. Plafon diberikan menurut peringkat sampai dana habis.
       Pemohon yang nilainya melebihi sisa dana DILEWATI, bukan menghentikan
       alokasi, sehingga sisa dana tetap terpakai oleh peringkat di bawahnya.
    """
    df = df_peringkat.sort_values("rank_TOPSIS").copy()

    sisa = float(plafon)
    status, nominal, alasan = [], [], []

    for _, baris in df.iterrows():
        diminta = float(baris["nilai_pengajuan_rp"])

        if baris["pd_model"] > pd_batas:
            status.append("DITOLAK")
            nominal.append(0.0)
            alasan.append(f"PD {baris['pd_model']:.3f} melampaui batas {pd_batas}")
        elif diminta <= sisa:
            status.append("DISETUJUI")
            nominal.append(diminta)
            sisa -= diminta
            alasan.append("Disetujui penuh sesuai peringkat")
        else:
            status.append("DITUNDA")
            nominal.append(0.0)
            alasan.append(f"Sisa plafon Rp{sisa:,.0f} tidak mencukupi Rp{diminta:,.0f}")

    df["status_keputusan"] = status
    df["nominal_disetujui"] = nominal
    df["alasan"] = alasan
    df["sisa_plafon"] = plafon - np.cumsum(nominal)
    return df


# --------------------------------------------------------------------------
# PENJELASAN KEPUTUSAN
# --------------------------------------------------------------------------
def jelaskan_peringkat(
    baris: pd.Series, matriks_terbobot: np.ndarray, idx: int
) -> str:
    """
    Susun narasi singkat: kriteria mana yang paling mengangkat dan menekan skor.

    Rubrik menuntut rekomendasi yang bisa ditafsirkan. Angka 0.6731 tanpa
    penjelasan tidak bisa dibacakan kepada pemohon yang pengajuannya ditolak.
    """
    kontribusi = matriks_terbobot[idx]
    urut = np.argsort(kontribusi)

    terlemah = cfg.CRITERIA_CODES[urut[0]]
    terkuat = cfg.CRITERIA_CODES[urut[-1]]

    return (
        f"Peringkat {int(baris['rank_TOPSIS'])} dari {int(baris['total_alternatif'])}. "
        f"Faktor pengangkat utama: {cfg.CRITERIA_NAMES[terkuat]}. "
        f"Faktor penekan utama: {cfg.CRITERIA_NAMES[terlemah]}. "
        f"IKS {int(baris['iks_skor'])}/{cfg.IKS_MAX}, "
        f"PD {baris['pd_model']:.3f}."
    )


# --------------------------------------------------------------------------
# PENYIMPANAN
# --------------------------------------------------------------------------
def simpan_ke_basis_data(
    df_keputusan: pd.DataFrame, bobot: np.ndarray, hasil_ahp
) -> None:
    """
    Simpan riwayat keputusan ke SQLite.

    Riwayat inilah yang membedakan SPK dari kalkulator sekali pakai: skenario,
    bobot yang dipakai, dan hasil peringkat tersimpan sehingga keputusan masa
    lalu bisa ditelusuri dan dibandingkan.
    """
    cfg.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(cfg.DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS skenario (
                id_skenario   TEXT PRIMARY KEY,
                waktu         TEXT NOT NULL,
                plafon        REAL NOT NULL,
                cr_ahp        REAL NOT NULL,
                bobot_json    TEXT NOT NULL,
                catatan       TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS keputusan (
                id_skenario   TEXT NOT NULL,
                id_pemohon    TEXT NOT NULL,
                peringkat     INTEGER NOT NULL,
                skor_topsis   REAL NOT NULL,
                pd_model      REAL NOT NULL,
                iks_skor      INTEGER NOT NULL,
                status        TEXT NOT NULL,
                nominal       REAL NOT NULL,
                PRIMARY KEY (id_skenario, id_pemohon)
            )
        """)

        id_skenario = datetime.now().strftime("SKN-%Y%m%d-%H%M%S")
        conn.execute(
            "INSERT INTO skenario VALUES (?,?,?,?,?,?)",
            (
                id_skenario,
                datetime.now().isoformat(timespec="seconds"),
                float(cfg.PLAFON_PERIODE),
                float(hasil_ahp.cr),
                json.dumps(dict(zip(cfg.CRITERIA_CODES, bobot.round(6).tolist()))),
                f"Skor riwayat versi {cfg.VERSI_SKOR_RIWAYAT_AKTIF}",
            ),
        )
        conn.executemany(
            "INSERT INTO keputusan VALUES (?,?,?,?,?,?,?,?)",
            [
                (
                    id_skenario,
                    r["id_pemohon"],
                    int(r["rank_TOPSIS"]),
                    float(r["skor_TOPSIS"]),
                    float(r["pd_model"]),
                    int(r["iks_skor"]),
                    r["status_keputusan"],
                    float(r["nominal_disetujui"]),
                )
                for _, r in df_keputusan.iterrows()
            ],
        )


# --------------------------------------------------------------------------
# PIPELINE UTAMA
# --------------------------------------------------------------------------
def jalankan(verbose: bool = True) -> dict:
    """Jalankan seluruh alur dan kembalikan seluruh artefak dalam satu dict."""
    cfg.OUTPUTS.mkdir(parents=True, exist_ok=True)
    cfg.TABLES.mkdir(parents=True, exist_ok=True)
    cfg.FIGURES.mkdir(parents=True, exist_ok=True)

    def judul(teks):
        if verbose:
            print(f"\n{'=' * 70}\n{teks}\n{'=' * 70}")

    # ---- 1. ETL ----------------------------------------------------------
    judul("TAHAP 1  EKSTRAKSI DAN PEMBERSIHAN DATA")
    df, laporan_etl = etl.jalankan_etl(verbose=verbose)

    # ---- 2. Model prediktif ---------------------------------------------
    judul("TAHAP 2  PELATIHAN MODEL PREDIKTIF")
    hasil_model, df_latih, df_uji = ml_model.latih_model(df, verbose=verbose)

    # ---- 3. Kalibrasi basis pengetahuan (data latih saja) ---------------
    judul("TAHAP 3  KALIBRASI BASIS PENGETAHUAN")
    peta_riwayat = knowledge.ambil_peta_skor_riwayat(df_latih)
    if verbose:
        print(f"Versi skor riwayat aktif : {cfg.VERSI_SKOR_RIWAYAT_AKTIF}")
        print(f"Peta pakar (V1)          : {cfg.SKOR_RIWAYAT_V1_PAKAR}")
        print(f"Peta kalibrasi (V2)      : {peta_riwayat}")
        tingkat = (
            df_latih.groupby("riwayat_kredit")["target_macet"]
            .agg(["mean", "count"]).round(4)
        )
        print("\nTingkat gagal bayar per kode riwayat (data latih):")
        print(tingkat.to_string())

    # ---- 4. Berkas pengajuan periode berjalan ---------------------------
    # Diambil dari data UJI: pemohon yang belum pernah dilihat model, meniru
    # berkas yang baru masuk. Mengambil dari data latih akan menghasilkan PD
    # yang terlalu optimistis karena model sudah menghafal kasus tersebut.
    judul("TAHAP 4  BERKAS PENGAJUAN PERIODE BERJALAN")
    df_periode = (
        df_uji.sample(n=cfg.N_PEMOHON_PERIODE, random_state=cfg.RANDOM_STATE)
        .copy()
        .reset_index(drop=True)
    )
    df_periode = knowledge.terapkan_kriteria_turunan(df_periode, peta_riwayat)
    df_periode["pd_model"] = ml_model.prediksi_pd(hasil_model.pipeline, df_periode)

    # Pelokalan ke konteks Kota Surakarta: nilai pinjaman diterjemahkan ke
    # Rupiah lewat pemetaan kuantil, lalu beban angsuran dan status
    # kesejahteraan dihitung terhadap garis kemiskinan BPS.
    df_periode = lokalisasi.lokalkan(
        df_periode, sebaran_historis=df["jumlah_kredit"].to_numpy()
    )

    if verbose:
        print(f"Jumlah pemohon      : {len(df_periode)}")
        print(f"Total diajukan      : Rp{df_periode['nilai_pengajuan_rp'].sum():,.0f}")
        print(f"Plafon tersedia     : Rp{cfg.PLAFON_PERIODE:,.0f}")
        print(
            f"Rasio permintaan    : "
            f"{df_periode['nilai_pengajuan_rp'].sum() / cfg.PLAFON_PERIODE:.2f}x plafon"
        )
        print()
        print(lokalisasi.ringkas_pelokalan(df_periode))
        print(
            f"PD: min {df_periode['pd_model'].min():.3f}, "
            f"median {df_periode['pd_model'].median():.3f}, "
            f"maks {df_periode['pd_model'].max():.3f}"
        )
        # Arah pertukaran DIPERIKSA, bukan diasumsikan. Versi sebelumnya
        # mencetak klaim "korelasi positif" tanpa melihat angkanya, dan
        # klaim itu salah pada kohort ini.
        korelasi_periode = df_periode["iks_skor"].corr(df_periode["pd_model"])
        korelasi_populasi = df["iks_skor"].corr(df["target_macet"])
        print(f"\nKorelasi IKS vs gagal bayar (populasi) : {korelasi_populasi:+.4f}")
        print(f"Korelasi IKS vs PD (periode ini)       : {korelasi_periode:+.4f}")
        if korelasi_periode > 0.10:
            print("Pertukaran MENGIKAT pada periode ini: pemohon yang paling "
                  "membutuhkan juga paling berisiko, sehingga pembobotan "
                  "menentukan hasil.")
        elif korelasi_periode < -0.10:
            print("Pertukaran BERBALIK pada periode ini: pemohon berkebutuhan "
                  "tinggi justru lebih aman, sehingga kedua tujuan dapat "
                  "dipenuhi bersamaan.")
        else:
            print("Pertukaran NYARIS TIDAK MENGIKAT pada periode ini "
                  "(|r| < 0,10), sehingga pemohon berkebutuhan tinggi dapat "
                  "diprioritaskan tanpa tambahan risiko berarti. Kesimpulan "
                  "ini berlaku untuk kohort ini saja dan wajib diperiksa "
                  "ulang setiap periode.")

    # ---- 5. Bobot AHP ----------------------------------------------------
    judul("TAHAP 5  PEMBOBOTAN KRITERIA (AHP KELOMPOK)")
    hasil_kelompok = ahp.bobot_kelompok()
    hasil_ahp = hasil_kelompok["gabungan"]
    bobot = hasil_ahp.bobot
    tabel_responden = ahp.tabel_perbandingan_responden(hasil_kelompok)
    if verbose:
        print("Agregasi 3 responden dengan rata-rata geometrik (Saaty AIJ):")
        print(tabel_responden.to_string())
        print()
        print(hasil_ahp.ringkas(
            [f"{k} {cfg.CRITERIA_NAMES[k]}" for k in cfg.CRITERIA_CODES]
        ))

    # ---- 6. Pemeringkatan ------------------------------------------------
    judul("TAHAP 6  PEMERINGKATAN MULTIKRITERIA")
    matriks, kolom_kriteria, benefit = bentuk_matriks_keputusan(df_periode)
    id_alternatif = df_periode["id_pemohon"].tolist()

    df_banding = ranking.bandingkan_metode(matriks, bobot, benefit, id_alternatif)
    korelasi_rank = ranking.korelasi_peringkat(df_banding)

    hasil_topsis = ranking.topsis(matriks, bobot, benefit)

    df_hasil = df_periode.merge(df_banding, on="id_pemohon")
    df_hasil["total_alternatif"] = len(df_hasil)
    df_hasil["penjelasan"] = [
        jelaskan_peringkat(baris, hasil_topsis["matriks_terbobot"], i)
        for i, (_, baris) in enumerate(df_hasil.iterrows())
    ]

    if verbose:
        print("Korelasi Spearman antar metode:")
        print(korelasi_rank.to_string())
        print(
            "\nKorelasi tinggi berarti peringkat tidak bergantung pada pilihan "
            "metode, sehingga hasil layak dipakai."
        )

    # ---- 7. Alokasi plafon ----------------------------------------------
    judul("TAHAP 7  ALOKASI PLAFON")
    df_keputusan = alokasikan_plafon(df_hasil)

    ringkas_status = df_keputusan["status_keputusan"].value_counts().to_dict()
    total_cair = df_keputusan["nominal_disetujui"].sum()

    if verbose:
        print(f"Status keputusan    : {ringkas_status}")
        print(
            f"Total dicairkan     : Rp{total_cair:,.0f} "
            f"({total_cair / cfg.PLAFON_PERIODE * 100:.1f}% plafon)"
        )
        disetujui = df_keputusan[df_keputusan["status_keputusan"] == "DISETUJUI"]
        if len(disetujui):
            print(f"PD rata-rata disetujui  : {disetujui['pd_model'].mean():.4f}")
            print(f"IKS rata-rata disetujui : {disetujui['iks_skor'].mean():.2f}")
            print(f"PD rata-rata semua      : {df_keputusan['pd_model'].mean():.4f}")
            print(f"IKS rata-rata semua     : {df_keputusan['iks_skor'].mean():.2f}")
            # Tingkat macet sebenarnya pada kelompok yang disetujui. Angka ini
            # tersedia karena berkas periode diambil dari data uji berlabel.
            print(
                f"Tingkat macet aktual pada yang disetujui : "
                f"{disetujui['target_macet'].mean():.4f} "
                f"(vs {df_keputusan['target_macet'].mean():.4f} pada seluruh pemohon)"
            )

        print("\n10 peringkat teratas:")
        kolom_tampil = [
            "rank_TOPSIS", "id_pemohon", "skor_TOPSIS", "iks_skor",
            "pd_model", "nilai_pengajuan_rp", "status_keputusan",
        ]
        print(
            df_keputusan.nsmallest(10, "rank_TOPSIS")[kolom_tampil]
            .round(4).to_string(index=False)
        )

    # ---- 7b. Perbandingan kebijakan --------------------------------------
    judul("TAHAP 7B  VALIDASI TERHADAP KEBIJAKAN ALTERNATIF")
    tabel_kebijakan = evaluasi.bandingkan_kebijakan(df_keputusan)
    if verbose:
        print(evaluasi.ringkas_perbandingan(tabel_kebijakan))

        # Berapa persen dari potensi perbaikan yang berhasil ditangkap SPK?
        acuan = tabel_kebijakan.loc[tabel_kebijakan.index.str.startswith("Undian")].iloc[0]
        murni_risiko = tabel_kebijakan.loc["Hanya Risiko (PD terkecil)"]
        murni_butuh = tabel_kebijakan.loc["Hanya Kebutuhan (IKS terbesar)"]
        spk = tabel_kebijakan.loc["SPK Hybrid (AHP+TOPSIS)"]

        # Rasio "porsi potensi yang tertangkap" hanya bermakna selama SPK
        # berada DI ANTARA acuan dan kebijakan tujuan-tunggal. Bila SPK
        # melampaui kebijakan tujuan-tunggal, rasio itu melewati 100 persen
        # dan berhenti bermakna. Versi pertama mencetak "137,8 persen", yang
        # tidak masuk akal sebagai porsi. Kedua kasus kini dibedakan.
        def lapor_dimensi(nama, nilai_spk, nilai_acuan, nilai_murni, lebih_kecil_lebih_baik):
            arah = -1 if lebih_kecil_lebih_baik else 1
            rentang = arah * (nilai_murni - nilai_acuan)
            capaian = arah * (nilai_spk - nilai_acuan)
            if rentang <= 0:
                return f"{nama}: kebijakan tujuan-tunggal tidak lebih baik dari acuan."
            if capaian >= rentang:
                return (
                    f"{nama}: SPK MELAMPAUI kebijakan tujuan-tunggal "
                    f"({nilai_spk:.4f} vs {nilai_murni:.4f}), bukan sekadar "
                    "mendekatinya."
                )
            return (
                f"{nama}: SPK menangkap {capaian / rentang * 100:.1f}% dari "
                "potensi perbaikan yang tersedia."
            )

        print()
        print(lapor_dimensi("Penurunan risiko", spk["tingkat_macet"],
                            acuan["tingkat_macet"], murni_risiko["tingkat_macet"], True))
        print(lapor_dimensi("Ketepatan sasaran", spk["iks_rata2"],
                            acuan["iks_rata2"], murni_butuh["iks_rata2"], False))

        sig = evaluasi.uji_signifikansi(df_keputusan, tabel_kebijakan)
        print(
            f"\nUji binomial satu sisi: {sig['macet_teramati']} kasus macet dari "
            f"{sig['n_penerima']} penerima, sementara seleksi acak diperkirakan "
            f"menghasilkan {sig['macet_diharapkan_jika_acak']} kasus. "
            f"p = {sig['p_value']:.4f} "
            f"({'signifikan' if sig['signifikan_5persen'] else 'TIDAK signifikan'} "
            "pada taraf 5%)."
        )

        # Aturan beban angsuran dilaporkan walau tidak mengikat. Aturan yang
        # tidak pernah aktif tetap harus terlihat, supaya tidak disangka
        # sudah menyaring padahal tidak.
        n_lewat = int((df_periode["rasio_angsuran_pendapatan"] > ext.BATAS_RASIO_ANGSURAN).sum())
        print(
            f"\nAturan beban angsuran maksimum "
            f"{ext.BATAS_RASIO_ANGSURAN:.0%} pendapatan: {n_lewat} pemohon melanggar "
            f"(rasio tertinggi {df_periode['rasio_angsuran_pendapatan'].max():.1%}). "
            "Aturan ini TIDAK MENGIKAT pada kohort ini karena nilai pinjaman "
            "tergolong kecil terhadap pendapatan; aturan tetap dipertahankan "
            "sebagai penyaring untuk pengajuan bernilai besar."
        )

    # ---- 7C. Tolok ukur pustaka -----------------------------------------
    judul("TAHAP 7C  PEMBANDINGAN TERHADAP TOLOK UKUR TERBITAN")
    spk_macet = float(tabel_kebijakan.loc["SPK Hybrid (AHP+TOPSIS)", "tingkat_macet"])
    tabel_tolok_ukur = pustaka.bandingkan_dengan_tolok_ukur(spk_macet)
    if verbose:
        print(tabel_tolok_ukur.to_string(index=False))
        print()
        print(
            "Tolok ukur paling relevan adalah rata-rata KSP Jawa Tengah "
            "(6,89 persen), karena wilayahnya sama dengan kasus yang dimodelkan "
            "dan sudah melampaui ambang sehat regulator 5 persen."
        )

    # ---- 7D. Evaluasi kemudahan penggunaan ------------------------------
    judul("TAHAP 7D  EVALUASI KEMUDAHAN PENGGUNAAN")
    ringkasan_he = usability.ringkas_he()
    if verbose:
        print(usability.laporan_he())

    # ---- 8. Sensitivitas -------------------------------------------------
    judul("TAHAP 8  ANALISIS SENSITIVITAS")
    idx_c1 = cfg.CRITERIA_CODES.index("C1")
    idx_c5 = cfg.CRITERIA_CODES.index("C5")

    sens_c1 = sensitivity.analisis_sensitivitas_bobot(
        matriks, bobot, benefit, id_alternatif, idx_c1
    )
    sens_c5 = sensitivity.analisis_sensitivitas_bobot(
        matriks, bobot, benefit, id_alternatif, idx_c5
    )
    titik_balik_c1 = sensitivity.titik_balik_peringkat(sens_c1, n_teratas=10)
    stabilitas_c1 = sensitivity.stabilitas_peringkat_teratas(sens_c1, n_teratas=10)

    if verbose:
        print(f"Titik balik komposisi 10 besar saat bobot C1 bergeser: "
              f"{len(titik_balik_c1)} kejadian")
        if len(titik_balik_c1):
            print(titik_balik_c1.head(8).to_string(index=False))
        print("\nPemohon paling stabil di 10 besar (lintas skenario bobot C1):")
        print(stabilitas_c1.head(8).to_string(index=False))

    # ---- 9. What-if dan goal seeking ------------------------------------
    judul("TAHAP 9  WHAT-IF DAN GOAL SEEKING")
    id_contoh = df_keputusan.nsmallest(15, "rank_TOPSIS")["id_pemohon"].iloc[-1]

    hasil_whatif = sensitivity.what_if_pemohon(
        matriks, bobot, benefit, id_alternatif, id_contoh,
        # Skenario: pemohon menghadirkan penjamin, sehingga PD turun 40%.
        {idx_c5: float(df_periode.loc[
            df_periode["id_pemohon"] == id_contoh, "pd_model"
        ].iloc[0] * 0.6)},
    )

    hasil_goal = sensitivity.goal_seeking(
        matriks, bobot, benefit, id_alternatif, id_contoh, idx_c5,
        peringkat_target=5,
    )

    if verbose:
        print(f"WHAT-IF untuk {id_contoh} (PD turun 40% karena ada penjamin):")
        for k, v in hasil_whatif.items():
            print(f"  {k:<26}: {v}")
        print(f"\nGOAL SEEKING: berapa PD agar {id_contoh} masuk peringkat 5?")
        for k, v in hasil_goal.items():
            print(f"  {k:<26}: {v}")

    # ---- 10. Simpan artefak ---------------------------------------------
    judul("TAHAP 10  PENYIMPANAN ARTEFAK")
    df_keputusan.to_csv(cfg.TABLES / "keputusan_periode.csv", index=False)
    tabel_kebijakan.to_csv(cfg.TABLES / "perbandingan_kebijakan.csv")
    tabel_responden.to_csv(cfg.TABLES / "ahp_per_responden.csv")
    ext.tabel_sumber().to_csv(cfg.TABLES / "sumber_eksternal.csv", index=False)
    pustaka.tabel_rujukan().to_csv(cfg.TABLES / "rujukan_pustaka.csv", index=False)
    tabel_tolok_ukur.to_csv(cfg.TABLES / "tolok_ukur_npl.csv", index=False)
    usability.tabel_temuan().to_csv(cfg.TABLES / "temuan_heuristik.csv", index=False)
    df_banding.to_csv(cfg.TABLES / "perbandingan_metode.csv", index=False)
    korelasi_rank.to_csv(cfg.TABLES / "korelasi_metode.csv")
    sens_c1.to_csv(cfg.TABLES / "sensitivitas_C1.csv", index=False)
    sens_c5.to_csv(cfg.TABLES / "sensitivitas_C5.csv", index=False)
    stabilitas_c1.to_csv(cfg.TABLES / "stabilitas_peringkat.csv", index=False)
    hasil_model.perbandingan_model.to_csv(
        cfg.TABLES / "perbandingan_model.csv", index=False
    )
    hasil_model.pentingnya_fitur.to_csv(
        cfg.TABLES / "pentingnya_fitur.csv", index=False
    )
    hasil_model.kurva_biaya.to_csv(cfg.TABLES / "kurva_biaya.csv", index=False)

    ringkasan = {
        "waktu_jalan": datetime.now().isoformat(timespec="seconds"),
        "checksum_sumber": laporan_etl.checksum_sumber,
        "etl": {
            "baris_awal": laporan_etl.baris_awal,
            "baris_akhir": laporan_etl.baris_akhir,
            "outlier_winsorize": laporan_etl.outlier_di_winsorize,
            "distribusi_label": laporan_etl.distribusi_label,
        },
        "model": {
            "terpilih": hasil_model.nama_model,
            "cv_auc_mean": hasil_model.cv_auc[0],
            "cv_auc_std": hasil_model.cv_auc[1],
            "ambang": hasil_model.ambang_optimal,
            **{k: v for k, v in hasil_model.metrik_uji.items()},
        },
        "ahp": {
            "bobot": dict(zip(cfg.CRITERIA_CODES, bobot.round(6).tolist())),
            "lambda_max": hasil_ahp.lambda_max,
            "ci": hasil_ahp.ci,
            "cr": hasil_ahp.cr,
            "konsisten": hasil_ahp.konsisten,
        },
        "periode": {
            "n_pemohon": int(len(df_periode)),
            "total_diajukan": float(df_periode["nilai_pengajuan_rp"].sum()),
            "plafon": float(cfg.PLAFON_PERIODE),
            "total_dicairkan": float(total_cair),
            "status": ringkas_status,
            "korelasi_iks_pd": float(
                df_periode["iks_skor"].corr(df_periode["pd_model"])
            ),
        },
        "korelasi_metode": korelasi_rank.to_dict(),
        "perbandingan_kebijakan": tabel_kebijakan.to_dict(orient="index"),
        "what_if": hasil_whatif,
        "goal_seeking": hasil_goal,
        "uji_signifikansi": evaluasi.uji_signifikansi(df_keputusan, tabel_kebijakan),
        "eksternal": {
            "garis_kemiskinan_jateng": ext.GARIS_KEMISKINAN_JATENG.nilai,
            "umk_surakarta": ext.UMK_SURAKARTA.nilai,
            "anggota_rt_miskin": ext.ANGGOTA_RUMAH_TANGGA_MISKIN,
        },
        "ahp_per_responden": tabel_responden.to_dict(orient="index"),
        "heuristic_evaluation": ringkasan_he,
    }
    (cfg.OUTPUTS / "ringkasan.json").write_text(
        json.dumps(ringkasan, indent=2, ensure_ascii=False)
    )

    simpan_ke_basis_data(df_keputusan, bobot, hasil_ahp)

    if verbose:
        print(f"Artefak tersimpan di {cfg.OUTPUTS}")
        print(f"Riwayat keputusan di  {cfg.DB_PATH}")

    return {
        "df": df,
        "df_latih": df_latih,
        "df_uji": df_uji,
        "df_periode": df_periode,
        "df_keputusan": df_keputusan,
        "hasil_model": hasil_model,
        "hasil_ahp": hasil_ahp,
        "matriks": matriks,
        "bobot": bobot,
        "benefit": benefit,
        "id_alternatif": id_alternatif,
        "sens_c1": sens_c1,
        "sens_c5": sens_c5,
        "korelasi_rank": korelasi_rank,
        "tabel_kebijakan": tabel_kebijakan,
        "hasil_kelompok": hasil_kelompok,
        "tabel_responden": tabel_responden,
        "ringkasan": ringkasan,
        "laporan_etl": laporan_etl,
    }


if __name__ == "__main__":
    jalankan()
