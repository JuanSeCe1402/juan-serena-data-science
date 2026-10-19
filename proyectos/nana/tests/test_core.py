import pandas as pd
from core import clean_dataframe, quality_score

def test_duplicate_removal():
    df = pd.DataFrame({"A":[1,1], "B":["x","x"]})
    clean, report = clean_dataframe(df)
    assert len(clean) == 1
    assert report["duplicates_found"] == 1

def test_score_range():
    df = pd.DataFrame({"a":[1,None], "b":[2,3]})
    score = quality_score(df, 0)
    assert 0 <= score <= 100
