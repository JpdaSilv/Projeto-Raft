import uuid
import pandas as pd
import streamlit as st
from db_utils import carregar_bobinas_fisicas, transaction, query_df, registrar_auditoria, clear_caches
from theme import aplicar_tema, page_header, section, kpi, alert, footer
from auth import exigir_perfil, mostrar_usuario_logado

aplicar_tema(); user=exigir_perfil("ALMOXARIFADO","ADMINISTRADOR"); mostrar_usuario_logado()
page_header("Importar TOTVS", "Faça a conferência antes de alterar o cadastro: arquivo → prévia → divergências → confirmação.", "GESTÃO", "IMPORTAÇÃO SEGURA", "📥")
section("1 • Selecionar arquivo", "Formato esperado: XLSX ou CSV")
up=st.file_uploader("Relatório TOTVS",type=["xlsx","csv"],label_visibility="collapsed")
if up:
    try:
        raw=pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
        aliases={"lote":["Lote","LOTE","lote"],"codigo_spec":["Código","Codigo","CÓDIGO","codigo"],"peso_totvs":["Peso Real","Peso","Peso TOTVS","peso_totvs","Saldo"],"local_fisico":["Local Físico","Local","local_fisico","Endereço"]}
        mapped={target:next((c for c in options if c in raw.columns),None) for target,options in aliases.items()}
        mapped={k:v for k,v in mapped.items() if v}
        if "lote" not in mapped or "peso_totvs" not in mapped:
            alert("O arquivo precisa conter pelo menos <b>Lote</b> e <b>Peso</b>.","danger"); st.stop()
        df=raw.rename(columns={v:k for k,v in mapped.items()})[list(mapped)]
        df["lote"]=df["lote"].astype(str).str.strip(); df["peso_totvs"]=pd.to_numeric(df["peso_totvs"],errors="coerce")
        df=df.dropna(subset=["lote","peso_totvs"]).drop_duplicates("lote",keep="last")
        atual=carregar_bobinas_fisicas()[["lote","peso_real","codigo_spec","local_fisico"]]
        diff=df.merge(atual,on="lote",how="left",suffixes=("_novo","_atual"))
        diff["tipo_diff"]=diff.apply(lambda r:"NOVO" if pd.isna(r["peso_real"]) else ("DIVERGENTE" if abs(float(r["peso_totvs"])-float(r["peso_real"] or 0))>.01 else "IGUAL"),axis=1)
        section("2 • Prévia e divergências", "Nada é gravado enquanto você não confirmar")
        a,b,c=st.columns(3)
        with a:kpi("Linhas válidas",f"{len(diff)}","após limpeza","blue")
        with b:kpi("Lotes novos",f"{int((diff.tipo_diff=='NOVO').sum())}","entrarão no cadastro","green")
        with c:kpi("Divergentes",f"{int((diff.tipo_diff=='DIVERGENTE').sum())}","exigem atenção","amber" if (diff.tipo_diff=='DIVERGENTE').any() else "green")
        st.dataframe(diff,use_container_width=True,hide_index=True)
        confirm=st.checkbox("Conferi a prévia e autorizo a aplicação desta importação.")
        if st.button("Aplicar importação",type="primary",disabled=not confirm):
            imp_id=str(uuid.uuid4())
            with transaction() as conn:
                conn.execute("INSERT INTO importacoes_totvs (id,arquivo_nome,linhas,novos,divergentes,status,usuario) VALUES (?,?,?,?,?,'APLICADA',?)",(imp_id,up.name,len(diff),int((diff.tipo_diff=='NOVO').sum()),int((diff.tipo_diff=='DIVERGENTE').sum()),user["nome"]))
                for _,row in diff.iterrows():
                    codigo=row.get("codigo_spec_novo"); codigo=row.get("codigo_spec_atual") if pd.isna(codigo) else codigo
                    local=row.get("local_fisico_novo"); local=row.get("local_fisico_atual") if pd.isna(local) else local
                    conn.execute("INSERT INTO snapshot_totvs (importacao_id,lote,codigo_spec,peso_totvs,local_fisico,arquivo_nome,usuario) VALUES (?,?,?,?,?,?,?)",(imp_id,row.lote,codigo,float(row.peso_totvs),local,up.name,user["nome"]))
                    if pd.isna(row.get("peso_real")):
                        conn.execute("INSERT INTO dim_bobina_fisica (lote,codigo_spec,local_fisico,peso_real,status) VALUES (?,?,?,?, 'ESTOQUE')",(row.lote,codigo,local,float(row.peso_totvs)))
                    else:
                        conn.execute("UPDATE dim_bobina_fisica SET peso_real=?,local_fisico=?,atualizado_em=datetime('now','localtime') WHERE lote=?",(float(row.peso_totvs),local,row.lote))
                    registrar_auditoria(conn,"importacoes_totvs",0,"IMPORTAR",user["nome"],valor_novo=f"{row.lote}: {row.peso_totvs} kg")
            clear_caches(); alert(f"Importação <b>{imp_id[:8]}</b> aplicada com sucesso.","success"); st.rerun()
    except Exception as e: st.error(f"Falha ao processar o arquivo: {e}")
section("Histórico de importações", "Snapshots preservam o que veio do TOTVS")
st.dataframe(query_df("SELECT id,arquivo_nome,linhas,novos,divergentes,status,criado_em,usuario FROM importacoes_totvs ORDER BY criado_em DESC LIMIT 20"),use_container_width=True,hide_index=True)
footer()
