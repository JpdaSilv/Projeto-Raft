import io, urllib.parse
import qrcode
from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import streamlit as st
from config import APP_NAME
from db_utils import carregar_bobinas_fisicas
from theme import aplicar_tema, page_header, section, kpi, alert, footer
from auth import exigir_login, mostrar_usuario_logado

aplicar_tema(); exigir_login(); mostrar_usuario_logado()
page_header("Etiqueta da bobina", "Gere uma etiqueta A6 com identificação física e QR Code para abrir o Kardex.", "ESTOQUE & RASTREABILIDADE", "A6 • QR CODE", "🏷️")
bob=carregar_bobinas_fisicas()
if bob.empty: alert("Nenhuma bobina cadastrada.","warn"); st.stop()
lote=st.selectbox("Bobina / lote",bob.lote.tolist()); info=bob[bob.lote==lote].iloc[0]
section("Prévia da identificação", "Confira os dados antes de gerar o PDF")
a,b,c=st.columns(3)
with a:kpi("Lote",lote,"identificador físico","blue")
with b:kpi("Peso",f"{float(info.peso_real or 0):,.0f} kg","cadastro","green")
with c:kpi("Local",info.local_fisico or "Não informado","posição","amber" if not info.local_fisico else "blue")
base=st.text_input("URL base do app", "https://SEU-APP.streamlit.app", help="Em produção, use a URL pública real do RAFT.")
if st.button("Gerar etiqueta em PDF",type="primary"):
    url=f"{base.rstrip('/')}/kardex?lote={urllib.parse.quote(lote)}"
    qr=qrcode.make(url); qb=io.BytesIO(); qr.save(qb,"PNG"); qb.seek(0)
    out=io.BytesIO(); w,h=A6; c=canvas.Canvas(out,pagesize=A6)
    c.setFont("Helvetica-Bold",11); c.drawString(8*mm,h-10*mm,APP_NAME)
    c.setFont("Helvetica-Bold",18); c.drawString(8*mm,h-21*mm,f"LOTE {lote}")
    c.setFont("Helvetica",9)
    lines=[f"Código: {info.codigo_spec or '-'}",f"Descrição: {(info.desc_curta or '-')[:34]}",f"Peso específico: {float(info.peso_especifico or 0):.3f} kg/m",f"Peso cadastrado: {float(info.peso_real or 0):.1f} kg",f"Local: {info.local_fisico or '-'}",f"Nº Ref.: {info.n_ref or '-'}"]
    y=h-32*mm
    for line in lines: c.drawString(8*mm,y,line); y-=6*mm
    c.drawImage(ImageReader(qb),w-48*mm,8*mm,width=39*mm,height=39*mm)
    c.setFont("Helvetica-Oblique",7); c.drawString(8*mm,9*mm,"Escaneie para abrir o Kardex.")
    c.save(); out.seek(0)
    st.download_button("Baixar etiqueta PDF",out.read(),f"etiqueta_{lote}.pdf","application/pdf",type="primary")
footer()
