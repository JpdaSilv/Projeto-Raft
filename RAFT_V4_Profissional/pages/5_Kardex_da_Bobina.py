import streamlit as st, pandas as pd
from db_utils import carregar_bobinas_fisicas, query_df
from theme import aplicar_tema, page_header, section, kpi, alert, footer
from auth import exigir_login, mostrar_usuario_logado
from page_runtime import run_page


def main():

    aplicar_tema(); exigir_login(); mostrar_usuario_logado()
    page_header("Kardex da bobina", "A história completa da bobina: consumo, pesagens e saldo estimado em ordem cronológica.", "ESTOQUE & RASTREABILIDADE", "QR READY", "📖")
    bob=carregar_bobinas_fisicas()
    if bob.empty: alert("Nenhuma bobina cadastrada.","warn"); st.stop()
    param=st.query_params.get("lote"); opcoes=bob.lote.tolist(); default=opcoes.index(param) if param in opcoes else 0
    lote=st.selectbox("Bobina / lote",opcoes,index=default)
    info=bob[bob.lote==lote].iloc[0]
    cons=query_df("SELECT id,data,criado_em,'CONSUMO' evento,pedido,produto_codigo,mt_produzida metragem,cons_bob peso_evento,usuario,status FROM fact_movimentacao WHERE bobina_lote=?",(lote,))
    pes=query_df("SELECT id,data,criado_em,'PESAGEM' evento,NULL pedido,NULL produto_codigo,NULL metragem,peso_atual peso_evento,usuario,NULL status FROM fact_controle_utilizacao WHERE bobina_lote=?",(lote,))
    eventos=pd.concat([cons,pes],ignore_index=True).sort_values("criado_em") if not cons.empty or not pes.empty else pd.DataFrame()
    total=float(cons.peso_evento.fillna(0).sum()) if not cons.empty else 0
    inicial=float(info.peso_real or 0); saldo=inicial-total
    section("Resumo físico", "Informações principais do lote selecionado")
    a,b,c,d,e=st.columns(5)
    with a: kpi("Especificação",info.codigo_spec or "—","cadastro","blue")
    with b: kpi("Peso específico",f"{float(info.peso_especifico or 0):.2f} kg/m","material","blue")
    with c: kpi("Peso inicial",f"{inicial:,.0f} kg","cadastro físico","blue")
    with d: kpi("Consumido",f"{total:,.1f} kg","apontamentos","amber")
    with e: kpi("Saldo estimado",f"{saldo:,.1f} kg","RAFT","green" if saldo>=0 else "red")
    section("Identificação", "Localização atual e referência da bobina")
    a,b,c=st.columns(3)
    a.info(f"**Lote**\n\n{lote}"); b.info(f"**Local**\n\n{info.local_fisico or 'Não informado'}"); c.info(f"**Nº Ref.**\n\n{info.n_ref or 'Não informado'}")
    section("Linha do tempo", "Cada evento altera ou documenta a história do lote")
    if eventos.empty: alert("Esta bobina ainda não possui eventos registrados.","info")
    else: st.dataframe(eventos,use_container_width=True,hide_index=True)
    footer()

run_page('5_Kardex_da_Bobina', main)
