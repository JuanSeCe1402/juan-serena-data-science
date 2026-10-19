import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,roc_auc_score
import core
from core import Config,ValidationError,FEATURES,make_data,raw_dataset,clean_data,run_experiment,segment


def test_data_is_reproducible_and_synthetic():
    a=make_data(100,42)
    pd.testing.assert_frame_equal(a,make_data(100,42))
    assert a.customer_id.is_unique and a.customer_id.str.startswith("DEMO-").all()
    assert set(a.repurchased.unique())=={0,1}
    assert not a.equals(make_data(100,43))


@pytest.mark.parametrize("args",[(499,42,"logistic"),(3001,42,"logistic"),(500,-1,"logistic"),(500,1000000,"logistic"),(500,42,"other"),(True,42,"logistic"),(500,False,"logistic")])
def test_config_limits(args):
    with pytest.raises(ValidationError):Config(*args)


def test_cleaning_handles_duplicates_missing_and_invalid():
    raw=raw_dataset(Config(500))
    assert len(raw)==505 and raw.total_spent.isna().any()
    raw.loc[len(raw)]=raw.iloc[0]
    raw.loc[len(raw)-1,"customer_id"]="REAL-PERSON"
    raw.loc[1,"discount_usage"]=np.inf
    raw.loc[2,"orders"]=-1
    raw.loc[10,"repurchased"]=3
    cleaned,report=clean_data(raw)
    assert cleaned.customer_id.is_unique and len(cleaned)==499
    assert report["duplicates_removed"]==5 and report["invalid_rows_removed"]==2
    assert pd.isna(cleaned.loc[cleaned.customer_id=="DEMO-00002","discount_usage"]).all()
    assert pd.isna(cleaned.loc[cleaned.customer_id=="DEMO-00003","average_ticket"]).all()


def test_missing_schema_or_single_class_rejected():
    with pytest.raises(ValidationError):clean_data(pd.DataFrame({"x":[1]}))
    df=make_data(100,42);df.repurchased=0
    with pytest.raises(ValidationError):clean_data(df)


@pytest.mark.parametrize("p,expected",[(0,"Low"),(.349999,"Low"),(.35,"Medium"),(.699999,"Medium"),(.70,"High"),(1,"High")])
def test_segment_boundaries(p,expected):assert segment(p)==expected


@pytest.mark.parametrize("p",[-.1,1.1,np.inf,np.nan])
def test_invalid_score_rejected(p):
    with pytest.raises(ValueError):segment(p)


@pytest.mark.parametrize("model",["logistic","forest"])
def test_experiment_metrics_recompute_and_holdout_is_disjoint(model):
    config=Config(500,42,model)
    result=run_experiment(config)
    again=run_experiment(config)
    assert result==again
    assert result["train_count"]==375 and result["test_count"]==125
    assert not set(result["train_ids"]) & set(result["test_ids"])
    assert len(set(result["train_ids"]+result["test_ids"]))==500
    scored=pd.DataFrame(result["predictions"])
    assert set(scored.customer_id)==set(result["test_ids"])
    assert scored.repurchase_score.between(0,1).all()
    assert set(scored.data_source)=={"synthetic_demo"}
    assert set(scored.evaluation_set)=={"held_out_test"}
    assert sum(result["segments"].values())==125
    y=scored.repurchased;p=scored.predicted_class
    for key,fn in [("accuracy",accuracy_score),("precision",precision_score),("recall",recall_score),("f1",f1_score)]:
        assert result["metrics"][key]==pytest.approx(fn(y,p))
    assert result["metrics"]["roc_auc"]==pytest.approx(roc_auc_score(y,scored.repurchase_score))
    majority=int(result["train_positive_count"]>result["train_count"]/2)
    assert result["metrics"]["baseline_accuracy"]==pytest.approx((y==majority).mean())
    assert np.asarray(result["metrics"]["confusion_matrix"]).sum()==125
    assert all(segment(r.repurchase_score)==r.segment for r in scored.itertuples())


def test_preprocessing_fits_only_training_without_id_or_target(monkeypatch):
    captured=[]
    original=core.build_model
    def capture(config):
        model=original(config);captured.append(model);return model
    monkeypatch.setattr(core,"build_model",capture)
    config=Config(500,91)
    result=run_experiment(config)
    clean,_=clean_data(raw_dataset(config))
    train=clean.set_index("customer_id").loc[result["train_ids"]]
    expected=train[list(FEATURES)].median().to_numpy()
    model=captured[0]
    np.testing.assert_allclose(model.named_steps["impute"].statistics_,expected)
    transformed=model.named_steps["impute"].transform(train[list(FEATURES)])
    np.testing.assert_allclose(model.named_steps["scale"].mean_,transformed.mean(axis=0))
    assert list(model.feature_names_in_)==list(FEATURES)
    assert "repurchased" not in model.feature_names_in_ and "customer_id" not in model.feature_names_in_
