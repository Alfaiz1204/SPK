"""
Subsistem Model (bagian 1): model prediktif probabilitas gagal bayar.

Keluaran modul ini adalah satu angka per pemohon, yaitu PD (probability of
default) pada rentang 0-1, yang masuk ke matriks keputusan MCDM sebagai
kriteria C5 bertipe cost.

PROTOKOL EVALUASI
-----------------
Data uji dipakai TEPAT SATU KALI, di akhir. Seluruh pemilihan dilakukan di
dalam data latih memakai prediksi out-of-fold:

    1. Pisahkan latih (70%) dan uji (30%), terstratifikasi.
    2. Pilih keluarga model dengan AUC validasi silang 5-lipat pada data latih.
    3. Pilih ambang keputusan dari prediksi out-of-fold data latih, dengan
       meminimalkan biaya yang diharapkan menurut cost matrix dataset.
    4. Latih ulang model terpilih pada seluruh data latih.
    5. Evaluasi sekali pada data uji.

Memilih ambang langsung pada data uji membuat metrik yang dilaporkan terlalu
optimistis. Kesalahan ini tidak terlihat pada keluaran program, hanya terlihat
pada urutan pemanggilan fungsi.

DUA KEPUTUSAN DESAIN
--------------------
1. Ambang TIDAK ditetapkan 0.5. Dataset menyertakan cost matrix yang
   menyatakan meloloskan pemohon macet 5x lebih mahal daripada menolak
   pemohon lancar. Pada komposisi kelas 70:30, akurasi tinggi bisa dicapai
   dengan selalu menebak "lancar", dan model semacam itu tidak berguna.

2. PD dipakai sebagai nilai kontinu di dalam MCDM, bukan label biner.
   Mengubahnya menjadi lolos/tolak lebih dahulu membuang gradasi yang justru
   dibutuhkan pada tahap pemeringkatan.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_predict,
    cross_val_score,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from . import config as cfg

FITUR_NUMERIK = [
    "durasi_bulan", "jumlah_kredit", "rasio_angsuran",
    "lama_domisili", "usia", "jumlah_kredit_aktif", "jumlah_tanggungan",
]
FITUR_KATEGORIK = [
    "status_rekening", "riwayat_kredit", "tujuan_pinjaman", "tabungan",
    "lama_bekerja", "status_personal", "penjamin", "kepemilikan_aset",
    "cicilan_lain", "status_rumah", "jenis_pekerjaan", "telepon", "pekerja_asing",
]
SEMUA_FITUR = FITUR_NUMERIK + FITUR_KATEGORIK

# Jumlah proses ditetapkan eksplisit, bukan -1. Pada Windows, nilai -1
# memaksa joblib menghitung jumlah inti fisik lewat pemanggilan proses luar
# yang kerap gagal dan memunculkan peringatan WinError 2. Menyebut angkanya
# langsung membuat langkah itu tidak diperlukan.
N_JOBS = max(1, (os.cpu_count() or 2) - 1)


# --------------------------------------------------------------------------
# WADAH HASIL
# --------------------------------------------------------------------------
@dataclass
class HasilModel:
    nama_model: str = ""
    pipeline: Pipeline = None
    ambang_optimal: float = 0.5
    metrik_uji: dict = field(default_factory=dict)
    perbandingan_model: pd.DataFrame = None
    matriks_konfusi: np.ndarray = None
    pentingnya_fitur: pd.DataFrame = None
    kurva_biaya: pd.DataFrame = None
    cv_auc: tuple = (0.0, 0.0)

    def ringkas(self) -> str:
        m = self.metrik_uji
        return "\n".join([
            "EVALUASI MODEL PREDIKTIF",
            "=" * 64,
            f"Model terpilih        : {self.nama_model}",
            f"AUC validasi silang   : {self.cv_auc[0]:.4f} +/- {self.cv_auc[1]:.4f} (data latih)",
            f"Ambang biaya-minimum  : {self.ambang_optimal:.2f} (dipilih out-of-fold)",
            "-" * 64,
            "HASIL PADA DATA UJI (dipakai sekali):",
            f"  AUC-ROC             : {m['auc']:.4f}",
            f"  AUC-PR              : {m['auc_pr']:.4f}",
            f"  Brier score         : {m['brier']:.4f}",
            f"  Akurasi             : {m['akurasi']:.4f}",
            f"  Presisi (macet)     : {m['presisi']:.4f}",
            f"  Recall  (macet)     : {m['recall']:.4f}",
            f"  F1      (macet)     : {m['f1']:.4f}",
            f"  Biaya total         : {m['biaya']:.1f} unit",
            f"  Biaya bila ambang .5: {m['biaya_pada_05']:.1f} unit",
            f"  Biaya bila semua diloloskan: {m['biaya_loloskan_semua']:.1f} unit",
        ])


# --------------------------------------------------------------------------
# PRAPEMROSESAN
# --------------------------------------------------------------------------
def _prapemrosesan() -> ColumnTransformer:
    """
    Penskalaan dan one-hot encoding dipelajari dari data latih saja.

    Dibungkus ColumnTransformer di dalam Pipeline, bukan diterapkan manual ke
    seluruh DataFrame, karena transformasi manual atas gabungan latih+uji
    adalah sumber kebocoran yang paling sering lolos dari perhatian.
    """
    return ColumnTransformer([
        ("num", StandardScaler(), FITUR_NUMERIK),
        ("kat", OneHotEncoder(handle_unknown="ignore", drop="first"), FITUR_KATEGORIK),
    ])


def kandidat_model() -> dict[str, Pipeline]:
    """Tiga keluarga model dengan karakteristik berbeda sebagai pembanding."""
    return {
        "LogisticRegression": Pipeline([
            ("prep", _prapemrosesan()),
            ("clf", LogisticRegression(
                max_iter=2000, class_weight="balanced",
                random_state=cfg.RANDOM_STATE)),
        ]),
        "RandomForest": Pipeline([
            ("prep", _prapemrosesan()),
            ("clf", RandomForestClassifier(
                n_estimators=500, max_depth=12, min_samples_leaf=8,
                max_features="sqrt", class_weight="balanced",
                random_state=cfg.RANDOM_STATE, n_jobs=N_JOBS)),
        ]),
        "HistGradientBoosting": Pipeline([
            ("prep", _prapemrosesan()),
            ("clf", HistGradientBoostingClassifier(
                max_depth=4, learning_rate=0.06, max_iter=300,
                l2_regularization=1.0, random_state=cfg.RANDOM_STATE)),
        ]),
    }


# --------------------------------------------------------------------------
# PEMILIHAN AMBANG
# --------------------------------------------------------------------------
def cari_ambang_biaya_minimum(
    y_benar: np.ndarray, pd_prediksi: np.ndarray
) -> tuple[float, pd.DataFrame]:
    """
    Telusuri ambang 0.05-0.95 dan pilih yang meminimalkan biaya yang diharapkan.

        biaya = COST_FN * (macet yang lolos) + COST_FP * (lancar yang ditolak)

    Harus dipanggil dengan prediksi out-of-fold dari data latih.
    """
    baris = []
    for ambang in np.arange(0.05, 0.96, 0.01):
        prediksi = (pd_prediksi >= ambang).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_benar, prediksi, labels=[0, 1]).ravel()
        baris.append({
            "ambang": round(float(ambang), 2),
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
            "biaya": float(cfg.COST_FN * fn + cfg.COST_FP * fp),
            "recall": float(tp / (tp + fn)) if (tp + fn) else 0.0,
            "presisi": float(tp / (tp + fp)) if (tp + fp) else 0.0,
        })
    kurva = pd.DataFrame(baris)
    return float(kurva.loc[kurva["biaya"].idxmin(), "ambang"]), kurva


def _hitung_metrik(y_benar, pd_prediksi, ambang) -> dict:
    prediksi = (pd_prediksi >= ambang).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_benar, prediksi, labels=[0, 1]).ravel()
    _, fp5, fn5, _ = confusion_matrix(
        y_benar, (pd_prediksi >= 0.5).astype(int), labels=[0, 1]
    ).ravel()

    return {
        "auc": float(roc_auc_score(y_benar, pd_prediksi)),
        "auc_pr": float(average_precision_score(y_benar, pd_prediksi)),
        "brier": float(brier_score_loss(y_benar, pd_prediksi)),
        "akurasi": float(accuracy_score(y_benar, prediksi)),
        "presisi": float(precision_score(y_benar, prediksi, zero_division=0)),
        "recall": float(recall_score(y_benar, prediksi, zero_division=0)),
        "f1": float(f1_score(y_benar, prediksi, zero_division=0)),
        "biaya": float(cfg.COST_FN * fn + cfg.COST_FP * fp),
        "biaya_pada_05": float(cfg.COST_FN * fn5 + cfg.COST_FP * fp5),
        # Pembanding "tanpa model": loloskan semua pemohon.
        "biaya_loloskan_semua": float(cfg.COST_FN * int(y_benar.sum())),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def ekstrak_pentingnya_fitur(pipeline: Pipeline) -> pd.DataFrame | None:
    """Petakan importance kembali ke nama fitur setelah one-hot encoding."""
    clf = pipeline.named_steps["clf"]
    prep = pipeline.named_steps["prep"]
    nama_fitur = FITUR_NUMERIK + (
        prep.named_transformers_["kat"].get_feature_names_out(FITUR_KATEGORIK).tolist()
    )

    if hasattr(clf, "feature_importances_"):
        skor = clf.feature_importances_
    elif hasattr(clf, "coef_"):
        # Untuk model linier, besaran koefisien atas fitur terstandar dipakai
        # sebagai proksi kepentingan. Arah tanda hilang, sehingga ini hanya
        # menjawab "seberapa berpengaruh", bukan "ke arah mana".
        skor = np.abs(clf.coef_[0])
    else:
        return None

    return (
        pd.DataFrame({"fitur": nama_fitur, "importance": skor})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


# --------------------------------------------------------------------------
# PELATIHAN
# --------------------------------------------------------------------------
def latih_model(
    df: pd.DataFrame, verbose: bool = True
) -> tuple[HasilModel, pd.DataFrame, pd.DataFrame]:
    """Jalankan protokol lengkap. Mengembalikan (HasilModel, df_latih, df_uji)."""
    df_latih, df_uji = train_test_split(
        df, test_size=0.30, stratify=df["target_macet"],
        random_state=cfg.RANDOM_STATE,
    )

    X_latih, y_latih = df_latih[SEMUA_FITUR], df_latih["target_macet"].to_numpy()
    X_uji, y_uji = df_uji[SEMUA_FITUR], df_uji["target_macet"].to_numpy()

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=cfg.RANDOM_STATE)

    # --- Langkah 2: pemilihan keluarga model pada data latih -----------------
    baris_perbandingan, oof_tersimpan = [], {}
    for nama, pipa in kandidat_model().items():
        skor = cross_val_score(pipa, X_latih, y_latih, cv=cv, scoring="roc_auc")
        oof = cross_val_predict(
            pipa, X_latih, y_latih, cv=cv, method="predict_proba"
        )[:, 1]
        oof_tersimpan[nama] = oof
        baris_perbandingan.append({
            "model": nama,
            "cv_auc_mean": float(skor.mean()),
            "cv_auc_std": float(skor.std()),
            "oof_auc_pr": float(average_precision_score(y_latih, oof)),
            "oof_brier": float(brier_score_loss(y_latih, oof)),
        })

    perbandingan = (
        pd.DataFrame(baris_perbandingan)
        .sort_values("cv_auc_mean", ascending=False)
        .reset_index(drop=True)
    )
    nama_terpilih = str(perbandingan.loc[0, "model"])

    # --- Langkah 3: pemilihan ambang dari prediksi out-of-fold ---------------
    ambang, kurva = cari_ambang_biaya_minimum(y_latih, oof_tersimpan[nama_terpilih])

    # --- Langkah 4: latih ulang pada seluruh data latih ----------------------
    pipeline = kandidat_model()[nama_terpilih]
    pipeline.fit(X_latih, y_latih)

    # --- Langkah 5: evaluasi sekali pada data uji ----------------------------
    pd_uji = pipeline.predict_proba(X_uji)[:, 1]
    metrik_uji = _hitung_metrik(y_uji, pd_uji, ambang)

    hasil = HasilModel(
        nama_model=nama_terpilih,
        pipeline=pipeline,
        ambang_optimal=ambang,
        metrik_uji=metrik_uji,
        perbandingan_model=perbandingan,
        matriks_konfusi=confusion_matrix(
            y_uji, (pd_uji >= ambang).astype(int), labels=[0, 1]
        ),
        pentingnya_fitur=ekstrak_pentingnya_fitur(pipeline),
        kurva_biaya=kurva,
        cv_auc=(
            float(perbandingan.loc[0, "cv_auc_mean"]),
            float(perbandingan.loc[0, "cv_auc_std"]),
        ),
    )

    if verbose:
        print("PERBANDINGAN KANDIDAT MODEL (validasi silang pada data latih)")
        print("=" * 64)
        print(perbandingan.round(4).to_string(index=False))
        print()
        print(hasil.ringkas())

    return hasil, df_latih, df_uji


def prediksi_pd(pipeline: Pipeline, df: pd.DataFrame) -> np.ndarray:
    """Hitung PD untuk sekumpulan pemohon."""
    return pipeline.predict_proba(df[SEMUA_FITUR])[:, 1]
