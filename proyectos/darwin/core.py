"""Synthetic-only, reproducible holdout experiment. No external datasets or model files."""
from dataclasses import dataclass
import math
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

FEATURES = ("orders", "total_spent", "average_ticket", "days_since_last_purchase", "discount_usage", "returns", "categories_bought")
FEATURE_LABELS = {"orders":"Pedidos previos", "total_spent":"Gasto histórico demo (MXN)", "average_ticket":"Ticket medio derivado (MXN)", "days_since_last_purchase":"Días desde la última compra", "discount_usage":"Proporción de uso de descuentos", "returns":"Devoluciones previas", "categories_bought":"Categorías compradas"}
MODELS = {"logistic":"Regresión logística", "forest":"Random Forest"}
TARGET = "repurchased"
SEED_MAX = 999999
MIN_ROWS, MAX_ROWS = 500, 3000
ACTIONS = {"High":"Revisar una propuesta de continuidad relevante.", "Medium":"Explorar un seguimiento útil según el contexto.", "Low":"Revisar contexto y pedir feedback antes de actuar."}
STEPS = (("Dataset","Creamos historiales ficticios, sin personas reales."), ("Cleaning","Quitamos duplicados y señalamos valores faltantes."), ("Features","Convertimos el historial en señales comparables."), ("Model","El modelo aprende solo con la parte de entrenamiento."), ("Evaluation","Lo probamos con clientes que no vio al aprender."), ("Prediction","Estimamos una señal de recompra por cliente demo."), ("Business Action","Sugerimos un siguiente paso para revisión humana."))

class ValidationError(ValueError):
    pass

@dataclass(frozen=True)
class Config:
    n: int = 1500
    seed: int = 42
    model: str = "logistic"

    def __post_init__(self):
        if type(self.n) is not int or not MIN_ROWS <= self.n <= MAX_ROWS:
            raise ValidationError("Clientes demo: usa un entero entre 500 y 3000.")
        if type(self.seed) is not int or not 0 <= self.seed <= SEED_MAX:
            raise ValidationError("Semilla: usa un entero entre 0 y 999999.")
        if self.model not in MODELS:
            raise ValidationError("Selecciona un modelo de la lista.")


def make_data(n=1500, seed=42):
    # Purely fictional pre-cutoff history and simulated next-30-day binary target.
    rng = np.random.default_rng(seed)
    orders = rng.integers(1, 18, n)
    total = np.round(rng.gamma(3.0, 700, n), 2)
    days = rng.integers(1, 365, n)
    discounts = np.round(np.clip(rng.normal(.25, .18, n), 0, 1), 2)
    returns = rng.poisson(.45, n)
    categories = rng.integers(1, 8, n)
    z = .22*orders + .00035*total - .012*days - .55*returns + .15*categories + .6*discounts - 2.1
    y = rng.binomial(1, np.clip(1/(1+np.exp(-z)), .02, .98))
    return pd.DataFrame({"customer_id":[f"DEMO-{i:05d}" for i in range(1,n+1)], "orders":orders, "total_spent":total, "average_ticket":np.round(total/orders,2), "days_since_last_purchase":days, "discount_usage":discounts, "returns":returns, "categories_bought":categories, TARGET:y})


def raw_dataset(config):
    df = make_data(config.n, config.seed)
    rng = np.random.default_rng(config.seed+1)
    # Known demo imperfections: missing historical values and duplicated IDs.
    for col in ("total_spent", "discount_usage"):
        df.loc[rng.choice(len(df), max(1,len(df)//50), replace=False), col] = np.nan
    df["average_ticket"] = (df.total_spent/df.orders).round(2)
    return pd.concat([df,df.iloc[:max(1,config.n//100)]],ignore_index=True)


def clean_data(raw):
    required = {"customer_id", TARGET, *FEATURES}
    if not required.issubset(raw.columns):
        raise ValidationError("Faltan columnas del esquema demo.")
    df = raw.copy()
    valid_id = df.customer_id.astype(str).str.fullmatch(r"DEMO-[0-9]{5}")
    df = df.loc[valid_id & df[TARGET].isin([0,1])].copy()
    invalid_rows = len(raw)-len(df)
    duplicated = int(df.customer_id.duplicated().sum())
    df = df.drop_duplicates("customer_id",keep="first").reset_index(drop=True)
    bounds = {"orders":(1,100),"total_spent":(0,1e7),"days_since_last_purchase":(0,3650),"discount_usage":(0,1),"returns":(0,100),"categories_bought":(1,100)}
    for col,(low,high) in bounds.items():
        values = pd.to_numeric(df[col],errors="coerce")
        df[col] = values.where(np.isfinite(values) & values.between(low,high))
    # Deterministic per-row feature; never uses the target or population statistics.
    df["average_ticket"] = (df.total_spent/df.orders).round(2)
    if len(df)<100 or df[TARGET].nunique()!=2 or df[TARGET].value_counts().min()<4:
        raise ValidationError("El conjunto demo no permite evaluar ambas clases.")
    df[TARGET] = df[TARGET].astype(int)
    report = {"raw_rows":len(raw),"clean_rows":len(df),"duplicates_removed":duplicated,"invalid_rows_removed":invalid_rows,"missing_cells":int(df[list(FEATURES)].isna().sum().sum())}
    return df, report


def build_model(config):
    steps = [("impute", SimpleImputer(strategy="median"))]
    if config.model == "logistic":
        steps += [("scale", StandardScaler()), ("model", LogisticRegression(max_iter=1000,random_state=config.seed))]
    else:
        steps += [("model", RandomForestClassifier(n_estimators=100,max_depth=6,min_samples_leaf=5,random_state=config.seed,n_jobs=1))]
    return Pipeline(steps)


def segment(probability):
    if not math.isfinite(probability) or not 0<=probability<=1:
        raise ValueError("Probability outside range")
    return "High" if probability>=.70 else "Medium" if probability>=.35 else "Low"


def records(frame):
    # JSON has null instead of NaN; only allow primitive JSON-compatible records.
    return frame.astype(object).where(frame.notna(),None).to_dict(orient="records")


def evaluate(y, predicted, probability, majority):
    return {"accuracy":float(accuracy_score(y,predicted)),"precision":float(precision_score(y,predicted,zero_division=0)),"recall":float(recall_score(y,predicted,zero_division=0)),"f1":float(f1_score(y,predicted,zero_division=0)),"roc_auc":float(roc_auc_score(y,probability)),"baseline_accuracy":float(accuracy_score(y,np.full(len(y),majority))),"positive_rate":float(np.mean(y)),"confusion_matrix":confusion_matrix(y,predicted,labels=[0,1]).tolist()}


def run_experiment(config):
    raw = raw_dataset(config)
    df, cleaning = clean_data(raw)
    # Split before fitting imputer, scaler and model. IDs and target are excluded.
    train, test = train_test_split(df,test_size=.25,random_state=config.seed,stratify=df[TARGET])
    model = build_model(config)
    with threadpool_limits(limits=1):
        model.fit(train[list(FEATURES)],train[TARGET])
        probability = model.predict_proba(test[list(FEATURES)])[:,1]
    predicted = (probability>=.5).astype(int)
    majority = int(train[TARGET].mode().iloc[0])
    metrics = evaluate(test[TARGET],predicted,probability,majority)
    scored = test[["customer_id",*FEATURES,TARGET]].copy()
    scored["repurchase_score"] = probability
    scored["predicted_class"] = predicted
    scored["segment"] = [segment(float(p)) for p in probability]
    scored["suggested_action"] = scored.segment.map(ACTIONS)
    scored["data_source"] = "synthetic_demo"
    scored["evaluation_set"] = "held_out_test"
    scored = scored.sort_values("customer_id")
    return {"config":{"n":config.n,"seed":config.seed,"model":config.model},"model_name":MODELS[config.model],"target":TARGET,"horizon_days":30,"features":list(FEATURES),"cleaning":cleaning,"train_count":len(train),"test_count":len(test),"train_positive_count":int(train[TARGET].sum()),"test_positive_count":int(test[TARGET].sum()),"metrics":metrics,"segments":{s:int((scored.segment==s).sum()) for s in ("High","Medium","Low")},"input_preview":records(raw.head(8)),"predictions":records(scored),"train_ids":train.customer_id.tolist(),"test_ids":test.customer_id.tolist()}
