"""
Validasi kualitas keputusan: bandingkan SPK dengan kebijakan alternatif.

Angka "tingkat macet 5 persen" tidak berarti apa-apa tanpa pembanding.
Penguji berhak bertanya: apakah hasil itu lebih baik daripada undian? Lebih
baik daripada sekadar mengurutkan menurut risiko?

Lima kebijakan dibandingkan di bawah plafon yang sama persis:

    1. SPK Hybrid        - AHP + TOPSIS atas enam kriteria (sistem ini)
    2. Hanya Risiko      - urutkan menurut PD terkecil
    3. Hanya Kebutuhan   - urutkan menurut IKS terbesar
    4. Siapa Cepat       - urutan kedatangan berkas (praktik lama)
    5. Undian            - acak, rata-rata atas banyak ulangan

Dua hasil dilaporkan untuk tiap kebijakan: tingkat gagal bayar sebenarnya
pada penerima (keberlanjutan finansial) dan rata-rata IKS penerima
(ketepatan sasaran sosial). Kebijakan yang unggul pada keduanya sekaligus
adalah kebijakan yang benar-benar lebih baik, bukan sekadar menggeser
pertukaran dari satu sisi ke sisi lain.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as cfg


def _alokasi_menurut_urutan(
    df: pd.DataFrame, urutan: np.ndarray, plafon: float, pd_batas: float
) -> dict:
    """Terapkan aturan alokasi yang sama persis pada urutan prioritas apa pun."""
    sisa = float(plafon)
    terpilih = []

    for i in urutan:
        baris = df.iloc[i]
        if baris["pd_model"] > pd_batas:
            continue
        if baris["nilai_pengajuan_rp"] <= sisa:
            sisa -= float(baris["nilai_pengajuan_rp"])
            terpilih.append(i)

    if not terpilih:
        return {
            "n_penerima": 0, "dana_terpakai": 0.0, "utilisasi": 0.0,
            "tingkat_macet": np.nan, "iks_rata2": np.nan,
            "pd_rata2": np.nan, "kerugian": 0.0,
        }

    sub = df.iloc[terpilih]
    # Kerugian memakai cost matrix dataset: tiap penerima yang macet dihitung
    # sebagai COST_FN unit. Satuan dibuat konsisten dengan evaluasi model.
    kerugian = float(cfg.COST_FN * sub["target_macet"].sum())

    return {
        "n_penerima": int(len(sub)),
        "dana_terpakai": float(plafon - sisa),
        "utilisasi": float((plafon - sisa) / plafon * 100),
        "tingkat_macet": float(sub["target_macet"].mean()),
        "iks_rata2": float(sub["iks_skor"].mean()),
        "pd_rata2": float(sub["pd_model"].mean()),
        "kerugian": kerugian,
    }


def bandingkan_kebijakan(
    df_keputusan: pd.DataFrame,
    plafon: float = cfg.PLAFON_PERIODE,
    pd_batas: float = cfg.PD_HARD_LIMIT,
    n_ulangan_undian: int = 2000,
    seed: int = cfg.RANDOM_STATE,
) -> pd.DataFrame:
    """Jalankan kelima kebijakan dan kembalikan tabel perbandingan."""
    df = df_keputusan.reset_index(drop=True)
    hasil = {}

    # 1. SPK Hybrid: peringkat TOPSIS
    hasil["SPK Hybrid (AHP+TOPSIS)"] = _alokasi_menurut_urutan(
        df, df["rank_TOPSIS"].to_numpy().argsort(), plafon, pd_batas
    )

    # 2. Hanya risiko: PD menaik
    hasil["Hanya Risiko (PD terkecil)"] = _alokasi_menurut_urutan(
        df, df["pd_model"].to_numpy().argsort(), plafon, pd_batas
    )

    # 3. Hanya kebutuhan: IKS menurun
    hasil["Hanya Kebutuhan (IKS terbesar)"] = _alokasi_menurut_urutan(
        df, (-df["iks_skor"].to_numpy()).argsort(), plafon, pd_batas
    )

    # 4. Siapa cepat: urutan id_pemohon mewakili urutan kedatangan berkas
    hasil["Siapa Cepat (FCFS)"] = _alokasi_menurut_urutan(
        df, df["id_pemohon"].to_numpy().argsort(), plafon, pd_batas
    )

    # 5. Undian: rata-rata atas banyak ulangan agar tidak bergantung satu
    #    pengacakan yang kebetulan baik atau buruk.
    rng = np.random.default_rng(seed)
    kumpulan = [
        _alokasi_menurut_urutan(df, rng.permutation(len(df)), plafon, pd_batas)
        for _ in range(n_ulangan_undian)
    ]
    hasil[f"Undian (rata-rata {n_ulangan_undian}x)"] = {
        k: float(np.nanmean([u[k] for u in kumpulan])) for k in kumpulan[0]
    }

    tabel = pd.DataFrame(hasil).T
    tabel.index.name = "kebijakan"

    acuan = tabel.loc["Undian (rata-rata 2000x)" if
                      f"Undian (rata-rata {n_ulangan_undian}x)" not in tabel.index
                      else f"Undian (rata-rata {n_ulangan_undian}x)"]
    tabel["penurunan_macet_vs_undian_%"] = (
        (acuan["tingkat_macet"] - tabel["tingkat_macet"]) / acuan["tingkat_macet"] * 100
    ).round(1)
    tabel["selisih_iks_vs_undian"] = (tabel["iks_rata2"] - acuan["iks_rata2"]).round(3)

    return tabel.round(4)


def uji_signifikansi(df_keputusan: pd.DataFrame, tabel: pd.DataFrame) -> dict:
    """
    Uji apakah tingkat gagal bayar penerima SPK berbeda nyata dari peluang.

    Dengan 18 penerima, satu kasus macet menggeser angka 5,6 poin persentase.
    Tingkat macet 0 persen karenanya WAJIB diuji, bukan diumumkan begitu saja.
    Uji binomial satu sisi dipakai: berapa peluang memperoleh sesedikit itu
    kasus macet bila penerima sebenarnya diambil acak dari kumpulan pemohon?
    """
    from scipy import stats

    spk = tabel.loc["SPK Hybrid (AHP+TOPSIS)"]
    n = int(spk["n_penerima"])
    macet_teramati = int(round(spk["tingkat_macet"] * n))
    laju_dasar = float(df_keputusan["target_macet"].mean())

    uji = stats.binomtest(macet_teramati, n, laju_dasar, alternative="less")
    return {
        "n_penerima": n,
        "macet_teramati": macet_teramati,
        "laju_dasar": laju_dasar,
        "macet_diharapkan_jika_acak": round(n * laju_dasar, 2),
        "p_value": float(uji.pvalue),
        "signifikan_5persen": bool(uji.pvalue < 0.05),
        "signifikan_1persen": bool(uji.pvalue < 0.01),
    }


def ringkas_perbandingan(tabel: pd.DataFrame) -> str:
    """Susun ringkasan naratif untuk dibacakan saat demo."""
    spk = tabel.loc["SPK Hybrid (AHP+TOPSIS)"]
    baris = [
        "PERBANDINGAN KEBIJACAN ALOKASI",
        "=" * 78,
        tabel.to_string(),
        "-" * 78,
        f"SPK Hybrid menyalurkan dana kepada {int(spk['n_penerima'])} pemohon "
        f"({spk['utilisasi']:.1f}% plafon terpakai).",
        f"Tingkat gagal bayar penerima {spk['tingkat_macet']:.1%}, "
        f"{spk['penurunan_macet_vs_undian_%']:.1f}% lebih rendah daripada undian.",
        f"Rata-rata IKS penerima {spk['iks_rata2']:.2f}, "
        f"selisih {spk['selisih_iks_vs_undian']:+.2f} terhadap undian.",
    ]
    return "\n".join(baris).replace("KEBIJACAN", "KEBIJAKAN")
