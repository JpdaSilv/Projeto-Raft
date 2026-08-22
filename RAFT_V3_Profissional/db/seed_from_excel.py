"""Importa dimensões do Projeto.xlsm sem apagar fatos históricos.
Uso:
python db/seed_from_excel.py --xlsm "Projeto.xlsm" --db "banco/raft_app.db"
"""
import argparse, sqlite3, sys
from pathlib import Path
import pandas as pd
from db.migrate import rodar_migracoes

def read(path,sheet,header):
    return pd.read_excel(path,sheet_name=sheet,header=header)

def normal(df, rename, cols, key):
    df=df.rename(columns=rename)
    df=df[[c for c in cols if c in df.columns]].copy()
    if key in df: df=df.dropna(subset=[key]).drop_duplicates(key)
    return df

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--xlsm",required=True); p.add_argument("--db",default="banco/raft_app.db")
    a=p.parse_args(); rodar_migracoes(a.db)
    conn=sqlite3.connect(a.db); conn.execute("PRAGMA foreign_keys=ON")
    prod=normal(read(a.xlsm,"Especificação_Produtos",7),
      {"Código":"codigo","Descrição":"descricao","Tipo de Telha":"tipo_telha","Fator da bobina":"fator_bobina"},
      ["codigo","descricao","tipo_telha","fator_bobina"],"codigo")
    spec=normal(read(a.xlsm,"Especificação_Bobinas",7),
      {"Código":"codigo","Descrição":"descricao","Desc. Curta":"desc_curta","MEDIDA":"medida","Esp.":"espessura",
       "Largura":"largura","Tipo":"tipo","Cor":"cor","Face":"face","Peso Específico":"peso_especifico","Saldo Atual":"saldo_atual"},
      ["codigo","descricao","desc_curta","medida","espessura","largura","tipo","cor","face","peso_especifico","saldo_atual"],"codigo")
    fis=normal(read(a.xlsm,"Banco_Bobina",2),
      {"Lote":"lote","Código":"codigo_spec","Galpão":"galpao","Local Físico":"local_fisico","N° Ref":"n_ref",
       "Peso Real":"peso_real","Data Pesagem":"data_pesagem","Data Validade":"data_validade"},
      ["lote","codigo_spec","galpao","local_fisico","n_ref","peso_real","data_pesagem","data_validade"],"lote")
    comp=normal(read(a.xlsm,"Especificação_Componentes",7),
      {"Código":"codigo","Descrição":"descricao","Tipo":"tipo","Esp.":"espessura","Desc. Curta":"desc_curta","Estoque atual":"estoque_atual"},
      ["codigo","descricao","tipo","espessura","desc_curta","estoque_atual"],"codigo")
    ped=normal(read(a.xlsm,"Pedidos",1),
      {"Pedido":"pedido","OP":"op","Cliente":"cliente","Produto":"produto_codigo","Metragem":"metragem","Tipo Prod.":"tipo_prod","Data":"data"},
      ["pedido","op","cliente","produto_codigo","metragem","tipo_prod","data"],"pedido")
    # Upsert: não apaga fatos e não derruba PK/FK.
    def upsert(df,table,key):
        if df.empty:return
        cols=list(df.columns); marks=",".join("?"*len(cols))
        # UPSERT preserva a identidade da linha pai e não quebra FKs dos fatos.
        key_col = key
        update_cols = [c for c in cols if c != key_col]
        if update_cols:
            updates = ",".join(f"{c}=excluded.{c}" for c in update_cols)
            sql=f"INSERT INTO {table} ({','.join(cols)}) VALUES ({marks}) ON CONFLICT({key_col}) DO UPDATE SET {updates}"
        else:
            sql=f"INSERT OR IGNORE INTO {table} ({','.join(cols)}) VALUES ({marks})"
        for row in df.itertuples(index=False,name=None):
            conn.execute(sql,row)
    conn.execute("BEGIN")
    upsert(prod,"dim_produto","codigo"); upsert(spec,"dim_bobina_spec","codigo")
    upsert(fis,"dim_bobina_fisica","lote"); upsert(comp,"dim_componente","codigo")
    # Pedido é histórico; para evitar duplicidade, limpamos SOMENTE a dimensão de pedidos.
    conn.execute("DELETE FROM dim_pedido")
    if not ped.empty:
        ped=ped.copy(); ped["pedido"]=ped["pedido"].astype(str).str.replace(r"\.0$","",regex=True)
        cols=list(ped.columns); marks=",".join("?"*len(cols))
        for row in ped.itertuples(index=False,name=None):
            conn.execute(f"INSERT INTO dim_pedido ({','.join(cols)}) VALUES ({marks})",row)
    conn.commit(); conn.close()
    print(f"Importado: {len(prod)} produtos | {len(spec)} specs | {len(fis)} lotes | {len(comp)} componentes | {len(ped)} pedidos")
if __name__=="__main__": main()
