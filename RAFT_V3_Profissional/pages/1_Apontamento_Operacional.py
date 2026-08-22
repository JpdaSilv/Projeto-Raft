import streamlit as st
from db_utils import carregar_pedidos, carregar_bobinas_fisicas, query_df
from theme import aplicar_tema, page_header, section, kpi, alert, footer, status
from auth import exigir_login, mostrar_usuario_logado
from services import criar_apontamento

aplicar_tema(); user=exigir_login(); mostrar_usuario_logado()
page_header("Novo apontamento", "Registre a produção com o mínimo de digitação. O RAFT deriva cliente, produto e consumo automaticamente.", "OPERAÇÃO", "FLUXO: OPERADOR → PCP", "📝")

pedidos=carregar_pedidos(); bobinas=carregar_bobinas_fisicas()
if pedidos.empty or bobinas.empty:
    alert("Cadastre ou importe pedidos e bobinas antes de iniciar a produção.", "warn"); st.stop()

pedido_nums=pedidos["pedido"].drop_duplicates().tolist()
pedido=st.selectbox("Pedido", pedido_nums, format_func=lambda x:f"Pedido {x}")
itens=pedidos[pedidos.pedido==pedido].copy()
if len(itens)>1:
    idx=st.selectbox("Item do pedido", itens.index, format_func=lambda i:f"OP {itens.loc[i,'op'] or '-'}  •  {itens.loc[i,'produto_codigo']}  •  {float(itens.loc[i,'metragem'] or 0):.2f} m")
    item=itens.loc[idx].to_dict()
else: item=itens.iloc[0].to_dict()

section("Contexto do pedido", "Dados preenchidos a partir da carteira cadastrada")
a,b,c=st.columns(3)
with a: kpi("Cliente", str(item.get("cliente") or "—")[:34], "pedido selecionado", "blue")
with b: kpi("Produto", str(item.get("produto_codigo") or "—"), "item de produção", "blue")
with c: kpi("Metragem planejada", f"{float(item.get('metragem') or 0):,.2f} m", f"OP {item.get('op') or 'não informada'}", "green")

section("Material e produção", "Selecione a bobina física e informe apenas o que aconteceu na linha")
lote_labels=(bobinas["lote"]+" — "+bobinas["desc_curta"].fillna("")).tolist()
lote_label=st.selectbox("Lote da bobina", lote_labels)
lote=lote_label.split(" — ",1)[0]
bob=bobinas[bobinas.lote==lote].iloc[0]
pe=float(bob.peso_especifico or 0)

x,y=st.columns([1.4,1])
with x: mt=st.number_input("Metragem produzida (m)",min_value=0.01,step=0.1,format="%.2f")
with y: tipo=st.radio("Tipo de produção",["PRODUÇÃO","2°","SUCATA"],horizontal=True)

consumo=pe*mt
saldo=float(bob.peso_real or 0)-float(query_df("SELECT COALESCE(SUM(cons_bob),0) s FROM fact_movimentacao WHERE bobina_lote=? AND status<>'CANCELADO'",(lote,)).iloc[0].s)
a,b,c=st.columns(3)
with a: kpi("Peso específico",f"{pe:.3f} kg/m","cadastro da especificação","blue")
with b: kpi("Consumo calculado",f"{consumo:.2f} kg","sem digitação manual","amber")
with c: kpi("Saldo RAFT",f"{saldo-consumo:.1f} kg","após este apontamento","green" if saldo-consumo>=0 else "red")

if mt>float(item.get("metragem") or 0)*1.10: alert("A metragem está mais de <b>10% acima</b> do planejado. Confira o pedido antes de enviar.","warn")
if saldo-consumo<0: alert("Este lançamento levaria o saldo estimado da bobina para <b>negativo</b>. Revise a bobina ou a metragem.","danger")

with st.form("apontamento"):
    confirmar=st.checkbox("Confirmei pedido, lote, tipo e metragem.")
    enviar=st.form_submit_button("Enviar para validação do PCP",type="primary",use_container_width=True)
if enviar:
    if not confirmar: st.error("Confirme os dados antes de enviar.")
    else:
        try:
            rid,cons=criar_apontamento(item,lote,tipo,mt,user["nome"])
            alert(f"Apontamento <b>#{rid}</b> enviado ao PCP. Consumo calculado: <b>{cons:.2f} kg</b>.","success")
            st.rerun()
        except Exception as e: st.error(str(e))
footer()
