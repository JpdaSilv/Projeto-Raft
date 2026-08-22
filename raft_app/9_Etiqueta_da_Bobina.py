import streamlit as st
import qrcode
import io
from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from db_utils import carregar_bobinas_fisicas
from theme import aplicar_tema
from auth import exigir_login, mostrar_usuario_logado

st.set_page_config(page_title="Etiqueta da Bobina", page_icon="🏷️", layout="wide")
aplicar_tema()
exigir_login()
mostrar_usuario_logado()

st.title("🏷️ Etiqueta da Bobina")
st.caption("Gera um PDF pronto pra imprimir e colar na bobina física, com QR Code que leva direto pro Kardex dela.")

bobinas = carregar_bobinas_fisicas()
if bobinas.empty:
    st.warning("Nenhuma bobina cadastrada.")
    st.stop()

lote_label = st.selectbox(
    "Bobina (lote)",
    options=list(bobinas["lote"] + " — " + bobinas["desc_curta"].fillna("")),
)
lote = lote_label.split(" — ")[0]
info = bobinas[bobinas["lote"] == lote].iloc[0]

url_base = st.text_input(
    "URL base do app (pra montar o link do QR Code)",
    value="https://SEU-APP.streamlit.app",
    help="Troque pela URL real do seu app publicado. O QR vai apontar pra essa URL + o lote.",
)


def gerar_pdf_etiqueta(lote: str, info: dict, url_base: str) -> bytes:
    qr_texto = f"{url_base}/Kardex_da_Bobina?lote={lote}"
    qr_img = qrcode.make(qr_texto)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    pdf_buffer = io.BytesIO()
    largura, altura = A6
    c = canvas.Canvas(pdf_buffer, pagesize=A6)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(8 * mm, altura - 12 * mm, "RAFT — Setor Telha")

    c.setFont("Helvetica-Bold", 20)
    c.drawString(8 * mm, altura - 24 * mm, f"Lote: {lote}")

    c.setFont("Helvetica", 11)
    linhas = [
        f"Código: {info.get('codigo_spec') or '-'}",
        f"Descrição: {(info.get('desc_curta') or '-')[:35]}",
        f"Peso específico: {info.get('peso_especifico') or 0:.2f} kg/m",
        f"Local: {info.get('local_fisico') or '-'}",
    ]
    y = altura - 34 * mm
    for linha in linhas:
        c.drawString(8 * mm, y, linha)
        y -= 6 * mm

    from reportlab.lib.utils import ImageReader
    c.drawImage(ImageReader(qr_buffer), largura - 42 * mm, 6 * mm, width=32 * mm, height=32 * mm)

    c.setFont("Helvetica-Oblique", 7)
    c.drawString(8 * mm, 6 * mm, "Escaneie o QR Code para ver o histórico completo desta bobina.")

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer.read()


if st.button("Gerar etiqueta em PDF", type="primary"):
    pdf_bytes = gerar_pdf_etiqueta(lote, info.to_dict(), url_base)
    st.success("Etiqueta gerada.")
    st.download_button(
        "⬇️ Baixar PDF da etiqueta",
        data=pdf_bytes,
        file_name=f"etiqueta_{lote}.pdf",
        mime="application/pdf",
        type="primary",
    )
