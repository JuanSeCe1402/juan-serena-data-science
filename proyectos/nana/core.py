import re
import sqlite3
import pandas as pd

EMPTY_MARKERS={'','nan','none','null','n/a','<na>'}

def normalize_name(value):
    return re.sub(r'[^\w]+','_',str(value).strip().lower()).strip('_')

def unique_names(columns):
    used=set(); result=[]
    for i,column in enumerate(columns):
        base=normalize_name(column) or f'column_{i+1}'
        name=base; n=2
        while name.casefold() in used:
            name=f'{base}_{n}'; n+=1
        used.add(name.casefold()); result.append(name)
    return result

def clean_dataframe(df):
    df=df.copy(); original_rows=len(df); original_cols=list(df.columns)
    df.columns=unique_names(df.columns)
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            df[col]=df[col].map(lambda v: pd.NA if pd.isna(v) or str(v).strip().lower() in EMPTY_MARKERS else str(v).strip())
    duplicates=int(df.duplicated().sum()); df=df.drop_duplicates().reset_index(drop=True)
    conversions={}
    for col in df.columns:
        s=df[col]; nonnull=s.dropna()
        if nonnull.empty or not all(isinstance(v,str) for v in nonnull): continue
        # Preserve identifiers and leading zeroes; never discard values on partial inference.
        identifier=bool(re.search(r'(^|_)(id|code|codigo|postal|phone|telefono|sku)($|_)',col))
        numeric=nonnull.str.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?').all()
        if numeric and not identifier:
            converted=pd.to_numeric(s,errors='coerce')
            if converted.notna().sum()==len(nonnull): df[col]=converted; conversions[col]='numeric'
        elif nonnull.str.fullmatch(r'\d{4}-\d{2}-\d{2}').all():
            converted=pd.to_datetime(s,format='%Y-%m-%d',errors='coerce')
            if converted.notna().sum()==len(nonnull): df[col]=converted.dt.strftime('%Y-%m-%d'); conversions[col]='date'
    return df,dict(rows_input=original_rows,rows_output=len(df),columns=len(df.columns),
        columns_renamed=sum(a!=b for a,b in zip(original_cols,df.columns)),duplicates_found=duplicates,
        missing_values=int(df.isna().sum().sum()),type_conversions=conversions)

def quality_score(df,duplicates_found):
    cells=max(df.shape[0]*max(df.shape[1],1),1)
    completeness=1-df.isna().sum().sum()/cells
    uniqueness=1-duplicates_found/max(len(df)+duplicates_found,1)
    return max(0,min(100,round((.65*completeness+.35*uniqueness)*100)))

def spreadsheet_safe(value):
    if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')):
        return "'"+value
    return value

def dataframe_to_sqlite_file(df,output_path):
    connection=sqlite3.connect(output_path)
    try:
        df.to_sql('clean_data',connection,if_exists='replace',index=False)
    finally:
        connection.close()

def profile_columns(df):
    return [dict(column=c,dtype=str(df[c].dtype),missing=int(df[c].isna().sum()),unique=int(df[c].nunique(dropna=True))) for c in df.columns]
