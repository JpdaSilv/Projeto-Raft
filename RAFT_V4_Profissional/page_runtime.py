"""Runtime seguro para páginas do RAFT.
Evita que uma exceção de uma página derrube a experiência inteira.
"""
from __future__ import annotations
import html
import logging
import traceback
from datetime import datetime
import streamlit as st

logger = logging.getLogger("raft")

def run_page(page_name: str, render):
    try:
        render()
    except Exception as exc:
        error_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]
        logger.exception("Erro na página %s [%s]", page_name, error_id)
        st.error("Não foi possível carregar esta tela.")
        st.markdown(
            f"""
            <div class="raft-error-card">
              <div class="raft-error-title">Algo deu errado nesta página</div>
              <div class="raft-error-text">
                A operação foi interrompida com segurança. Nenhum dado deve ser
                gravado parcialmente por causa deste erro.
              </div>
              <div class="raft-error-id">Código: {html.escape(error_id)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Detalhes técnicos"):
            st.code("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
