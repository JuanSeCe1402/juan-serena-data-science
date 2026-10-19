import pandas as pd
from core import clean_dataframe, spreadsheet_safe, dataframe_to_sqlite_file

def test_normalized_headers_unique(tmp_path):
    df=pd.DataFrame([['1','2','3']],columns=['A B','a-b','A_B_2'])
    cleaned,_=clean_dataframe(df)
    assert len({c.casefold() for c in cleaned.columns})==3
    dataframe_to_sqlite_file(cleaned,tmp_path/'out.db')

def test_leading_zero_and_ambiguous_dates_preserved():
    df=pd.DataFrame({'customer_id':['001','002'],'amount':['01','02'],'date':['01/02/2026','02/03/2026']})
    cleaned,_=clean_dataframe(df)
    assert cleaned['customer_id'].tolist()==['001','002']
    assert cleaned['amount'].tolist()==['01','02']
    assert cleaned['date'].tolist()==df['date'].tolist()

def test_partial_numeric_does_not_erase_values():
    df=pd.DataFrame({'value':['10']*9+['pending']})
    cleaned,_=clean_dataframe(df)
    assert 'pending' in cleaned['value'].values

def test_duplicates_after_trimming_and_missing():
    cleaned,report=clean_dataframe(pd.DataFrame({'name':[' x ','x','NULL']}))
    assert report['duplicates_found']==1
    assert report['missing_values']==1

def test_csv_formula_neutralized():
    for value in ['=1+1','+SUM(A1)','@test','  -formula']:
        assert spreadsheet_safe(value).startswith("'")
    assert spreadsheet_safe(-10)==-10
