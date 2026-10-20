"""
Subsistem Dialog: antarmuka web SPK Prioritisasi Penyaluran Kredit Mikro.

Jalankan dari akar proyek:
    streamlit run app/app.py

Antarmuka ini bukan sekadar penampil tabel. Tiga hal yang membuatnya layak
disebut komponen Dialog pada paradigma DDM:

  1. Bobot kriteria dapat diubah pengambil keputusan, dan seluruh peringkat
     dihitung ulang seketika. Bobot hasil AHP adalah titik awal, bukan
     ketetapan.
  2. Setiap peringkat disertai alasan: kriteria mana yang mengangkat dan
     mana yang menekan.
  3. Setiap skenario dapat disimpan, sehingga keputusan masa lalu bisa
     ditelusuri dan dibandingkan.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# Akar proyek ditambahkan ke sys.path agar modul src dapat diimpor ketika
# Streamlit dijalankan dari direktori mana pun.
AKAR = Path(__file__).resolve().parents[1]
if str(AKAR) not in sys.path:
    sys.path.insert(0, str(AKAR))

from src import config as cfg                      # noqa: E402
from src import evaluasi, knowledge, ml_model, pipeline, sensitivity  # noqa: E402
from src.mcdm import ahp, ranking                  # noqa: E402

def rupiah(nilai: float, singkat: bool = False) -> str:
    """
    Format nilai rupiah secara seragam di seluruh antarmuka.

    Dibuat terpusat untuk menutup temuan HE-09, yaitu pemisah ribuan yang
    berbeda antartab karena sebagian memakai format bawaan Python.
    """
    if singkat and abs(nilai) >= 1_000_000:
        return f"Rp{nilai / 1_000_000:,.1f} jt".replace(",", ".")
    return f"Rp{nilai:,.0f}".replace(",", ".")


st.set_page_config(
    page_title="SPK Prioritisasi Kredit Mikro",
    page_icon="📊",
    layout="wide",
)


# --------------------------------------------------------------------------
# PEMUATAN DATA
# --------------------------------------------------------------------------
@st.cache_resource(show_spinner="Menjalankan pipeline (ETL, pelatihan model, MCDM)...")
def muat_pipeline() -> dict:
    """
    Jalankan pipeline sekali, lalu simpan hasilnya di cache.

    cache_resource dipakai, bukan cache_data, karena hasil memuat objek
    scikit-learn yang tidak dapat di-hash maupun diserialkan oleh Streamlit.
    """
    return pipeline.jalankan(verbose=False)


def hitung_ulang(konteks: dict, bobot: np.ndarray, metode: str) -> pd.DataFrame:
    """Hitung ulang peringkat dengan bobot pilihan pengguna."""
    matriks = konteks["matriks"]
    benefit = konteks["benefit"]

    fungsi = {"TOPSIS": ranking.topsis, "SAW": ranking.saw, "VIKOR": ranking.vikor}
    skor = fungsi[metode](matriks, bobot, benefit)["skor"]

    df = konteks["df_periode"].copy()
    df["skor"] = skor
    df["rank_TOPSIS"] = (-skor).argsort().argsort() + 1   # nama kolom dipertahankan
    return df


# --------------------------------------------------------------------------
# SIDEBAR
# --------------------------------------------------------------------------
def gambar_sidebar(bobot_ahp: np.ndarray) -> dict:
    st.sidebar.header("Parameter Keputusan")

    # Batas DITURUNKAN dari konfigurasi, tidak ditulis tangan. Versi
    # sebelumnya memakai batas skala Deutsche Mark yang tertinggal saat
    # satuan diubah ke Rupiah, sehingga nilai bawaan Rp60 juta melampaui
    # batas atas Rp200 ribu dan aplikasi gagal dijalankan. Menurunkan batas
    # dari sumber yang sama membuat kesalahan semacam itu tidak bisa terulang.
    plafon_awal = int(cfg.PLAFON_PERIODE)
    langkah = max(1, 10 ** (len(str(plafon_awal)) - 3))   # 2 digit pertama
    plafon = st.sidebar.number_input(
        "Plafon periode (Rp)",
        min_value=int(plafon_awal * 0.1),
        max_value=int(plafon_awal * 5),
        value=plafon_awal,
        step=langkah,
        help=f"Nilai bawaan {rupiah(plafon_awal)} berasal dari config.PLAFON_PERIODE.",
    )
    st.sidebar.caption(f"Plafon aktif: {rupiah(plafon)}")
    pd_batas = st.sidebar.slider(
        "Batas keras PD", 0.30, 0.95, float(cfg.PD_HARD_LIMIT), 0.01,
        help="Pemohon dengan PD di atas nilai ini ditolak berapa pun peringkatnya.",
    )
    metode = st.sidebar.selectbox("Metode pemeringkatan", ["TOPSIS", "SAW", "VIKOR"])

    st.sidebar.divider()
    st.sidebar.subheader("Bobot Kriteria")

    if st.sidebar.button("Kembalikan ke bobot AHP", use_container_width=True):
        for i, kode in enumerate(cfg.CRITERIA_CODES):
            st.session_state[f"w_{kode}"] = float(bobot_ahp[i])

    bobot_mentah = []
    for i, kode in enumerate(cfg.CRITERIA_CODES):
        arah = "benefit" if cfg.CRITERIA_BENEFIT[kode] else "cost"
        bobot_mentah.append(
            st.sidebar.slider(
                f"{kode} · {cfg.CRITERIA_NAMES[kode]} ({arah})",
                0.0, 0.60, float(bobot_ahp[i]), 0.005, key=f"w_{kode}",
            )
        )

    bobot = np.asarray(bobot_mentah, dtype=float)

    # Perbaikan temuan HE-03 (keparahan 4). Sebelumnya seluruh bobot dapat
    # digeser ke nol dan sistem tetap menampilkan peringkat, padahal
    # peringkat tanpa bobot tidak punya makna sama sekali. Kasus ini kini
    # dihentikan dengan pesan yang menjelaskan akibatnya, bukan sekadar
    # dinormalisasi diam-diam.
    if bobot.sum() <= 0:
        st.sidebar.error(
            "Seluruh bobot bernilai nol. Pemeringkatan tidak dapat dihitung "
            "karena tidak ada kriteria yang dipakai membandingkan pemohon. "
            "Naikkan setidaknya satu bobot, atau tekan 'Kembalikan ke bobot AHP'."
        )
        st.stop()

    # Bobot dinormalisasi agar selalu menjumlah 1. Tanpa ini, menaikkan satu
    # slider akan menaikkan skor semua alternatif dan perbandingan jadi tidak sah.
    bobot = bobot / bobot.sum()

    st.sidebar.caption(
        "Bobot dinormalisasi otomatis agar berjumlah 1. "
        f"Total sebelum normalisasi: {sum(bobot_mentah):.3f}"
    )

    # Perbaikan temuan HE-08 (keparahan 4): mode evaluasi dinyatakan eksplisit.
    # st.toggle baru tersedia sejak Streamlit 1.26. checkbox dipakai sebagai
    # cadangan agar aplikasi tetap berjalan pada pemasangan yang lebih lama.
    sakelar = getattr(st.sidebar, "toggle", st.sidebar.checkbox)
    mode_evaluasi = sakelar(
        "Mode evaluasi", value=True,
        help="Menampilkan tingkat gagal bayar sebenarnya. Hanya mungkin pada "
             "data uji berlabel. Pada penyaluran nyata, angka ini belum ada "
             "sampai masa angsuran berjalan.",
    )
    return {"plafon": plafon, "pd_batas": pd_batas, "metode": metode,
            "bobot": bobot, "mode_evaluasi": mode_evaluasi}


# --------------------------------------------------------------------------
# TAB: KEPUTUSAN
# --------------------------------------------------------------------------
def tab_keputusan(df_keputusan: pd.DataFrame, par: dict) -> None:
    disetujui = df_keputusan[df_keputusan["status_keputusan"] == "DISETUJUI"]

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Disetujui", len(disetujui))
    k2.metric(
        "Dana tersalur",
        rupiah(df_keputusan["nominal_disetujui"].sum(), singkat=True),
        f"{df_keputusan['nominal_disetujui'].sum() / par['plafon'] * 100:.1f}% plafon",
    )
    k3.metric(
        "PD rata-rata penerima",
        f"{disetujui['pd_model'].mean():.3f}" if len(disetujui) else "-",
        f"{disetujui['pd_model'].mean() - df_keputusan['pd_model'].mean():+.3f} vs semua"
        if len(disetujui) else None,
        delta_color="inverse",
    )
    k4.metric(
        "IKS rata-rata penerima",
        f"{disetujui['iks_skor'].mean():.2f}" if len(disetujui) else "-",
        f"{disetujui['iks_skor'].mean() - df_keputusan['iks_skor'].mean():+.2f} vs semua"
        if len(disetujui) else None,
    )
    # Perbaikan temuan HE-08 (keparahan 4). Kolom target_macet hanya tersedia
    # karena berkas periode diambil dari data uji berlabel. Pada penyaluran
    # nyata metrik ini MUSTAHIL ada sebelum masa angsuran berjalan, sehingga
    # menampilkannya tanpa keterangan membuat pengguna menyangka sistem dapat
    # memastikan hasil di muka.
    if par.get("mode_evaluasi") and "target_macet" in df_keputusan.columns and len(disetujui):
        k5.metric(
            "Macet aktual  [EVALUASI]",
            f"{disetujui['target_macet'].mean():.1%}",
            f"{disetujui['target_macet'].mean() - df_keputusan['target_macet'].mean():+.1%}",
            delta_color="inverse",
            help="Hanya tersedia pada data uji berlabel. Pada penyaluran "
                 "nyata angka ini belum ada saat keputusan diambil.",
        )
    elif len(disetujui):
        k5.metric("Macet aktual", "—",
                  help="Tidak tersedia di luar mode evaluasi.")

    st.divider()

    saring = st.multiselect(
        "Tampilkan status", ["DISETUJUI", "DITUNDA", "DITOLAK"],
        default=["DISETUJUI", "DITUNDA", "DITOLAK"],
    )
    tampil = df_keputusan[df_keputusan["status_keputusan"].isin(saring)]

    st.dataframe(
        tampil[[
            "rank_TOPSIS", "id_pemohon", "skor", "iks_skor", "kapasitas_angsur",
            "skor_riwayat", "skor_produktif", "pd_model", "nilai_pengajuan_rp",
            "status_keputusan", "alasan",
        ]].rename(columns={
            "rank_TOPSIS": "Peringkat", "id_pemohon": "ID", "skor": "Skor",
            "iks_skor": "C1 IKS", "kapasitas_angsur": "C2 Kapasitas",
            "skor_riwayat": "C3 Riwayat", "skor_produktif": "C4 Produktif",
            "pd_model": "C5 PD", "nilai_pengajuan_rp": "C6 Nilai (Rp)",
            "status_keputusan": "Status", "alasan": "Alasan",
        }).sort_values("Peringkat"),
        use_container_width=True, hide_index=True, height=430,
        column_config={
            "Skor": st.column_config.NumberColumn(format="%.4f"),
            "C5 PD": st.column_config.ProgressColumn(
                format="%.3f", min_value=0.0, max_value=1.0),
            "C6 Nilai (Rp)": st.column_config.NumberColumn(format="%.0f"),
            "C2 Kapasitas": st.column_config.NumberColumn(format="%.1f"),
        },
    )

    st.subheader("Rincian satu pemohon")
    pilihan = st.selectbox("Pilih pemohon", tampil["id_pemohon"].tolist())
    baris = df_keputusan[df_keputusan["id_pemohon"] == pilihan].iloc[0]

    kiri, kanan = st.columns([1, 1])
    with kiri:
        st.markdown(f"**Penjelasan peringkat**\n\n{baris['penjelasan']}")
        st.markdown(f"**Keputusan:** `{baris['status_keputusan']}` — {baris['alasan']}")
    with kanan:
        st.markdown(f"**Indikator deprivasi yang terpenuhi (IKS {int(baris['iks_skor'])}/{cfg.IKS_MAX})**")
        alasan_iks = knowledge.jelaskan_iks(baris)
        st.markdown("\n".join(f"- {a}" for a in alasan_iks) if alasan_iks
                    else "- Tidak ada indikator deprivasi terpenuhi")


# --------------------------------------------------------------------------
# TAB: BOBOT
# --------------------------------------------------------------------------
def tab_bobot(hasil_ahp, bobot_pakai: np.ndarray) -> None:
    kiri, kanan = st.columns([1.1, 1])

    with kiri:
        st.subheader("Matriks perbandingan berpasangan")
        st.dataframe(
            pd.DataFrame(
                hasil_ahp.matriks,
                index=cfg.CRITERIA_CODES, columns=cfg.CRITERIA_CODES,
            ).round(3),
            use_container_width=True,
        )
        warna = "normal" if hasil_ahp.konsisten else "inverse"
        st.metric(
            "Consistency Ratio", f"{hasil_ahp.cr:.4f}",
            f"ambang {cfg.CR_THRESHOLD}", delta_color=warna,
        )
        st.caption(
            f"lambda_max = {hasil_ahp.lambda_max:.4f} · CI = {hasil_ahp.ci:.4f}. "
            "CR di atas 0,10 berarti penilaian saling bertentangan dan "
            "wawancara harus diulang, bukan matriksnya yang disunting."
        )

    with kanan:
        st.subheader("Bobot: AHP vs pilihan pengguna")
        banding = pd.DataFrame({
            "Kriteria": [f"{k} {cfg.CRITERIA_NAMES[k]}" for k in cfg.CRITERIA_CODES],
            "Bobot AHP": hasil_ahp.bobot,
            "Bobot dipakai": bobot_pakai,
            "Selisih": bobot_pakai - hasil_ahp.bobot,
        })
        st.dataframe(
            banding.round(4), use_container_width=True, hide_index=True,
            column_config={
                "Bobot dipakai": st.column_config.ProgressColumn(
                    format="%.4f", min_value=0.0, max_value=0.5),
            },
        )
        st.bar_chart(banding.set_index("Kriteria")[["Bobot AHP", "Bobot dipakai"]])


# --------------------------------------------------------------------------
# TAB: SENSITIVITAS
# --------------------------------------------------------------------------
def tab_sensitivitas(konteks: dict, par: dict) -> None:
    st.subheader("Ketahanan peringkat terhadap perubahan bobot")

    kode = st.selectbox(
        "Kriteria yang divariasikan",
        cfg.CRITERIA_CODES,
        format_func=lambda k: f"{k} · {cfg.CRITERIA_NAMES[k]}",
    )
    n_teratas = st.slider("Batas 'n besar' yang dipantau", 5, 20, 10)
    idx = cfg.CRITERIA_CODES.index(kode)

    sens = sensitivity.analisis_sensitivitas_bobot(
        konteks["matriks"], par["bobot"], konteks["benefit"],
        konteks["id_alternatif"], idx,
    )

    teratas = (
        sens[sens["bobot"] == sens["bobot"].min()]
        .nsmallest(8, "peringkat")["id_pemohon"].tolist()
    )
    pivot = (
        sens[sens["id_pemohon"].isin(teratas)]
        .pivot(index="bobot", columns="id_pemohon", values="peringkat")
    )
    st.line_chart(pivot, height=340)
    st.caption(
        "Sumbu tegak adalah peringkat; garis yang menukik ke bawah berarti "
        "peringkat memburuk. Garis yang saling berpotongan menandakan "
        "pembalikan peringkat (rank reversal)."
    )

    kiri, kanan = st.columns(2)
    with kiri:
        st.markdown(f"**Titik balik komposisi {n_teratas} besar**")
        titik = sensitivity.titik_balik_peringkat(sens, n_teratas=n_teratas)
        if len(titik):
            st.dataframe(titik, use_container_width=True, hide_index=True)
        else:
            st.success(
                f"Komposisi {n_teratas} besar tidak berubah pada seluruh "
                "rentang bobot yang diuji. Hasil sangat stabil."
            )
    with kanan:
        st.markdown("**Stabilitas tiap pemohon**")
        st.dataframe(
            sensitivity.stabilitas_peringkat_teratas(sens, n_teratas=n_teratas).head(12),
            use_container_width=True, hide_index=True,
        )


# --------------------------------------------------------------------------
# TAB: WHAT-IF DAN GOAL SEEKING
# --------------------------------------------------------------------------
def tab_whatif(konteks: dict, par: dict, df_keputusan: pd.DataFrame) -> None:
    kiri, kanan = st.columns(2)

    with kiri:
        st.subheader("What-if")
        st.caption(
            "Ubah nilai satu kriteria pada satu pemohon, lalu lihat dampaknya "
            "pada peringkat. Seluruh alternatif dihitung ulang karena TOPSIS "
            "bersifat relatif terhadap solusi ideal."
        )
        id_target = st.selectbox(
            "Pemohon", konteks["id_alternatif"], key="wi_id",
        )
        kode = st.selectbox(
            "Kriteria", cfg.CRITERIA_CODES, key="wi_krit",
            format_func=lambda k: f"{k} · {cfg.CRITERIA_NAMES[k]}",
        )
        idx_krit = cfg.CRITERIA_CODES.index(kode)
        idx_alt = konteks["id_alternatif"].index(id_target)
        nilai_kini = float(konteks["matriks"][idx_alt, idx_krit])

        kolom = konteks["matriks"][:, idx_krit]
        nilai_baru = st.slider(
            f"Nilai baru {kode} (sekarang {nilai_kini:.4f})",
            float(kolom.min()), float(kolom.max()), nilai_kini,
            key="wi_nilai",
        )

        hasil = sensitivity.what_if_pemohon(
            konteks["matriks"], par["bobot"], konteks["benefit"],
            konteks["id_alternatif"], id_target, {idx_krit: nilai_baru},
        )
        a, b, c = st.columns(3)
        a.metric("Peringkat sebelum", hasil["peringkat_sebelum"])
        b.metric(
            "Peringkat sesudah", hasil["peringkat_sesudah"],
            f"{hasil['delta_peringkat']:+d}",
        )
        c.metric("Alternatif lain bergeser", hasil["alternatif_lain_bergeser"])

    with kanan:
        st.subheader("Goal seeking")
        st.caption(
            "Tetapkan peringkat yang diinginkan, lalu sistem mencari nilai "
            "kriteria minimum yang dibutuhkan untuk mencapainya."
        )
        id_gs = st.selectbox("Pemohon", konteks["id_alternatif"], key="gs_id")
        kode_gs = st.selectbox(
            "Kriteria yang boleh diubah", cfg.CRITERIA_CODES, key="gs_krit",
            format_func=lambda k: f"{k} · {cfg.CRITERIA_NAMES[k]}",
        )
        target = st.number_input(
            "Peringkat target", 1, len(konteks["id_alternatif"]), 5, key="gs_target",
        )

        if st.button("Cari nilai yang dibutuhkan", use_container_width=True):
            hasil_gs = sensitivity.goal_seeking(
                konteks["matriks"], par["bobot"], konteks["benefit"],
                konteks["id_alternatif"], id_gs,
                cfg.CRITERIA_CODES.index(kode_gs), int(target),
            )
            if hasil_gs["tercapai"]:
                st.success(
                    f"{kode_gs} harus bergeser dari "
                    f"{hasil_gs['nilai_awal']:.4f} ke "
                    f"{hasil_gs['nilai_dibutuhkan']:.4f} "
                    f"(selisih {hasil_gs['selisih']:+.4f}) agar mencapai "
                    f"peringkat {hasil_gs['peringkat_tercapai']}."
                )
            else:
                st.warning(hasil_gs["catatan"])


# --------------------------------------------------------------------------
# TAB: VALIDASI
# --------------------------------------------------------------------------
def tab_validasi(konteks: dict, df_keputusan: pd.DataFrame, par: dict) -> None:
    st.subheader("Perbandingan dengan kebijakan alternatif")
    st.caption(
        "Seluruh kebijakan diuji pada plafon dan batas PD yang sama persis. "
        "Kebijakan yang unggul pada kedua kolom sekaligus adalah kebijakan "
        "yang benar-benar lebih baik, bukan yang sekadar menukar satu tujuan "
        "dengan tujuan lain."
    )
    tabel = evaluasi.bandingkan_kebijakan(
        df_keputusan, plafon=par["plafon"], pd_batas=par["pd_batas"],
    )
    st.dataframe(tabel, use_container_width=True)

    st.divider()
    st.subheader("Kinerja model prediktif")
    hasil_model = konteks["hasil_model"]
    m = hasil_model.metrik_uji

    a, b, c, d = st.columns(4)
    a.metric("AUC-ROC (uji)", f"{m['auc']:.4f}")
    b.metric("Recall macet", f"{m['recall']:.4f}")
    c.metric("Brier score", f"{m['brier']:.4f}")
    d.metric(
        "Biaya", f"{m['biaya']:.0f}",
        f"{m['biaya'] - m['biaya_loloskan_semua']:.0f} vs tanpa model",
        delta_color="inverse",
    )

    kiri, kanan = st.columns(2)
    kiri.markdown("**Perbandingan kandidat model (CV pada data latih)**")
    kiri.dataframe(
        hasil_model.perbandingan_model.round(4),
        use_container_width=True, hide_index=True,
    )
    kanan.markdown("**Korelasi Spearman antar metode MCDM**")
    kanan.dataframe(konteks["korelasi_rank"], use_container_width=True)


# --------------------------------------------------------------------------
# TAB: RIWAYAT
# --------------------------------------------------------------------------
def tab_riwayat(df_keputusan: pd.DataFrame, par: dict, hasil_ahp) -> None:
    st.subheader("Riwayat skenario keputusan")
    st.caption(
        "Penyimpanan riwayat inilah yang memisahkan SPK dari kalkulator sekali "
        "pakai: skenario, bobot, dan hasilnya dapat ditelusuri kembali."
    )

    catatan = st.text_input("Catatan skenario", "Skenario uji dari antarmuka")
    if st.button("Simpan skenario ini", type="primary"):
        with sqlite3.connect(cfg.DB_PATH) as conn:
            id_skenario = datetime.now().strftime("SKN-%Y%m%d-%H%M%S")
            conn.execute(
                "INSERT INTO skenario VALUES (?,?,?,?,?,?)",
                (
                    id_skenario, datetime.now().isoformat(timespec="seconds"),
                    float(par["plafon"]), float(hasil_ahp.cr),
                    json.dumps(dict(zip(
                        cfg.CRITERIA_CODES, par["bobot"].round(6).tolist()))),
                    catatan,
                ),
            )
            conn.executemany(
                "INSERT INTO keputusan VALUES (?,?,?,?,?,?,?,?)",
                [
                    (id_skenario, r["id_pemohon"], int(r["rank_TOPSIS"]),
                     float(r["skor"]), float(r["pd_model"]), int(r["iks_skor"]),
                     r["status_keputusan"], float(r["nominal_disetujui"]))
                    for _, r in df_keputusan.iterrows()
                ],
            )
        st.success(f"Tersimpan sebagai {id_skenario}")

    try:
        with sqlite3.connect(cfg.DB_PATH) as conn:
            skenario = pd.read_sql_query(
                "SELECT * FROM skenario ORDER BY waktu DESC LIMIT 25", conn
            )
        st.dataframe(skenario, use_container_width=True, hide_index=True)
    except Exception as e:
        st.info(f"Belum ada riwayat tersimpan. ({e})")

    st.download_button(
        "Unduh keputusan periode ini (CSV)",
        df_keputusan.to_csv(index=False).encode("utf-8"),
        file_name=f"keputusan_{datetime.now():%Y%m%d_%H%M}.csv",
        mime="text/csv",
    )


# --------------------------------------------------------------------------
# UTAMA
# --------------------------------------------------------------------------
def main() -> None:
    st.title("SPK Prioritisasi Penyaluran Kredit Mikro")
    st.caption(
        "Koperasi Simpan Pinjam Sejahtera Mandiri · hybrid data-driven dan "
        "model-driven · AHP + TOPSIS di atas model prediksi gagal bayar"
    )

    konteks = muat_pipeline()
    hasil_ahp = konteks["hasil_ahp"]
    par = gambar_sidebar(hasil_ahp.bobot)

    df_rank = hitung_ulang(konteks, par["bobot"], par["metode"])
    df_keputusan = pipeline.alokasikan_plafon(
        df_rank, plafon=par["plafon"], pd_batas=par["pd_batas"],
    )

    # Penjelasan peringkat dihitung ulang karena bobot pengguna mengubah
    # kontribusi tiap kriteria terhadap skor akhir.
    hasil_topsis = ranking.topsis(konteks["matriks"], par["bobot"], konteks["benefit"])
    peta_idx = {pid: i for i, pid in enumerate(konteks["id_alternatif"])}
    df_keputusan["total_alternatif"] = len(df_keputusan)
    df_keputusan["penjelasan"] = [
        pipeline.jelaskan_peringkat(
            r, hasil_topsis["matriks_terbobot"], peta_idx[r["id_pemohon"]])
        for _, r in df_keputusan.iterrows()
    ]

    if not hasil_ahp.konsisten:
        st.error(
            f"Matriks AHP tidak konsisten (CR = {hasil_ahp.cr:.4f}). "
            "Hasil pemeringkatan tidak layak dipakai."
        )

    tabs = st.tabs([
        "Keputusan", "Bobot & AHP", "Sensitivitas",
        "What-if & Goal Seeking", "Validasi", "Riwayat",
    ])
    with tabs[0]:
        tab_keputusan(df_keputusan, par)
    with tabs[1]:
        tab_bobot(hasil_ahp, par["bobot"])
    with tabs[2]:
        tab_sensitivitas(konteks, par)
    with tabs[3]:
        tab_whatif(konteks, par, df_keputusan)
    with tabs[4]:
        tab_validasi(konteks, df_keputusan, par)
    with tabs[5]:
        tab_riwayat(df_keputusan, par, hasil_ahp)

    st.divider()
    st.caption(
        "Sistem ini bersifat decision support, bukan decision automation. "
        "Keputusan akhir tetap berada pada pengelola koperasi. "
        "Sumber data: UCI Statlog German Credit (id=144), lisensi CC BY 4.0."
    )


if __name__ == "__main__":
    main()
