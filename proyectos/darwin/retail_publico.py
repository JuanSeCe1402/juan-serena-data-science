"""Evaluación temporal de recompra con Online Retail II (UCI, CC BY 4.0).

Ejecutar desde esta carpeta; consultar datos-publicos/README.md.
No exporta identificadores, transacciones ni modelos serializados.
"""
import argparse
import hashlib
from importlib.metadata import version
import json
import math
import platform
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

SOURCE = "https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip"
FEATURES = ["orders", "spend_gbp", "units", "products", "active_days", "recency_days", "ticket_gbp"]
CUTOFFS = {"train": "2010-09-01", "validation": "2011-03-01", "test": "2011-09-01"}
OBSERVED_START = pd.Timestamp("2009-12-01")
OBSERVED_END = pd.Timestamp("2011-12-09")  # Exclusive: discard the incomplete last day.


def clean_transactions(raw):
    """Sequential, auditable rules; cancellations are excluded, not netted."""
    df = raw.rename(columns={"Customer ID": "CustomerID", "Price": "UnitPrice"}).copy()
    columns = ["Invoice", "StockCode", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID"]
    df = df[columns]
    counts = {"input_rows": len(df)}
    for col in ["Quantity", "UnitPrice", "CustomerID"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["InvoiceDate"] = pd.to_datetime(df.InvoiceDate, errors="coerce")
    valid = df[columns].notna().all(axis=1)
    valid &= np.isfinite(df[["Quantity", "UnitPrice", "CustomerID"]]).all(axis=1)
    counts["missing_or_invalid_removed"] = int((~valid).sum())
    df = df.loc[valid].copy()
    valid = (~df.Invoice.astype(str).str.upper().str.startswith("C")) & (df.Quantity > 0) & (df.UnitPrice > 0)
    counts["cancellations_nonpositive_removed"] = int((~valid).sum())
    df = df.loc[valid].copy()
    before = len(df)
    df = df.drop_duplicates(subset=columns)
    counts["duplicate_lines_removed"] = before - len(df)
    valid = (df.InvoiceDate >= OBSERVED_START) & (df.InvoiceDate < OBSERVED_END)
    counts["outside_complete_observation_removed"] = int((~valid).sum())
    df = df.loc[valid].copy()
    df["amount"] = df.Quantity * df.UnitPrice
    counts["retained_rows"] = len(df)
    return df, counts


def snapshot(df, cutoff, lookback=180, horizon=30):
    cutoff = pd.Timestamp(cutoff)
    start = cutoff - pd.Timedelta(days=lookback)
    end = cutoff + pd.Timedelta(days=horizon)
    if lookback <= 0 or horizon <= 0 or start < OBSERVED_START or end > OBSERVED_END:
        raise ValueError("La ventana debe quedar completamente observada.")
    history = df.loc[(df.InvoiceDate >= start) & (df.InvoiceDate < cutoff)].copy()
    history["day"] = history.InvoiceDate.dt.normalize()
    grouped = history.groupby("CustomerID", sort=True)
    features = grouped.agg(orders=("Invoice", "nunique"), spend_gbp=("amount", "sum"),
                           units=("Quantity", "sum"), products=("StockCode", "nunique"),
                           active_days=("day", "nunique"), last=("InvoiceDate", "max"))
    features["recency_days"] = (cutoff - features.pop("last")).dt.total_seconds() / 86400
    features["ticket_gbp"] = features.spend_gbp / features.orders
    future = df.loc[(df.InvoiceDate >= cutoff) & (df.InvoiceDate < end), "CustomerID"]
    features["repurchased"] = features.index.isin(future).astype(int)
    if features.empty or features.repurchased.nunique() != 2:
        raise ValueError("Se requieren clientes e integrantes de ambas clases.")
    return features


def metrics(y, scores):
    y, scores = np.asarray(y), np.asarray(scores)
    k = max(1, math.ceil(len(y) * .20))
    # Stable ID-sorted input makes ties deterministic. Lift is descriptive, not causal.
    top = np.argsort(-scores, kind="stable")[:k]
    precision = float(y[top].mean())
    return {"roc_auc": float(roc_auc_score(y, scores)),
            "average_precision": float(average_precision_score(y, scores)),
            "brier": float(brier_score_loss(y, scores)),
            "top_20_count": k, "precision_top_20": precision,
            "lift_top_20": precision / float(y.mean())}


def write_summary(report, output):
    test = report["partitions"]["test"]
    rows = ["# Resultados medidos · Online Retail II", "",
            f"Modelo elegido en validación: **{report['selected']}**. Corte final: {test['cutoff']}.", "",
            f"Prueba: **{test['customers']:,} clientes**, {test['positives']:,} recompraron en 30 días ({test['prevalence']:.1%}).", "",
            "| Método | ROC AUC | Average precision | Precisión del 20% superior | Lift del 20% superior |",
            "|---|---:|---:|---:|---:|"]
    for name, key in [(report["selected"], "test"), ("Recencia", "test_recency_ranking"), ("Constante de entrenamiento", "test_constant_train_prevalence")]:
        m = report[key]
        rows.append(f"| {name} | {m['roc_auc']:.3f} | {m['average_precision']:.3f} | {m['precision_top_20']:.1%} | {m['lift_top_20']:.2f} |")
    rows += ["", "El lift es concentración retrospectiva de recompras; no mide ventas generadas por una campaña.", "",
             "El desempate de scores iguales sigue el orden de ID; la precisión superior del score constante no es una selección informada.", "",
             "Una sola ventana final no acredita generalización. Consultar [método y límites](README.md) y [salida completa con hash y versiones](metricas.json).", ""]
    (output / "RESULTADOS.md").write_text("\n".join(rows), encoding="utf-8")


def run(archive, output):
    with zipfile.ZipFile(archive) as z:
        with z.open("online_retail_II.xlsx") as f:
            sheets = pd.read_excel(f, sheet_name=None, engine="openpyxl")
    df, cleaning = clean_transactions(pd.concat(sheets.values(), ignore_index=True))
    sets = {name: snapshot(df, date) for name, date in CUTOFFS.items()}
    train, val, test = (sets[n] for n in ("train", "validation", "test"))
    candidates = {
        "logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, random_state=42)),
        "forest": RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=20, random_state=42, n_jobs=1),
    }
    with threadpool_limits(limits=1):
        for model in candidates.values():
            model.fit(train[FEATURES], train.repurchased)
        validation = {name: metrics(val.repurchased, m.predict_proba(val[FEATURES])[:, 1]) for name, m in candidates.items()}
        selected = max(validation, key=lambda name: validation[name]["average_precision"])
        scores = candidates[selected].predict_proba(test[FEATURES])[:, 1]
    report = {
        "source": SOURCE, "doi": "10.24432/C5CG6D", "license": "CC BY 4.0",
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "versions": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "sklearn": sklearn.__version__, "openpyxl": version("openpyxl")},
        "seed": 42, "lookback_days": 180, "horizon_days": 30, "features": FEATURES,
        "cleaning": cleaning,
        "partitions": {n: {"cutoff": CUTOFFS[n], "customers": len(s), "positives": int(s.repurchased.sum()), "prevalence": float(s.repurchased.mean())} for n, s in sets.items()},
        "customer_overlap_train_test": len(train.index.intersection(test.index)),
        "validation": validation, "selection_rule": "maximum validation average_precision; no refit", "selected": selected,
        "test": metrics(test.repurchased, scores),
        "test_constant_train_prevalence": metrics(test.repurchased, np.full(len(test), train.repurchased.mean())),
        "test_recency_ranking": {k: v for k, v in metrics(test.repurchased, np.exp(-test.recency_days / 30)).items() if k != "brier"},
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "metricas.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_summary(report, output)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("datos-publicos"))
    args = parser.parse_args()
    run(args.archive, args.output)
