"""Identidade visual do RAFT V4."""
import html
import streamlit as st

CSS = r"""
<style>
:root{
  --raft-bg:#08111f;
  --raft-panel:#0e1a2b;
  --raft-panel-2:#122137;
  --raft-border:#1d314a;
  --raft-border-soft:#15263b;
  --raft-text:#f4f8ff;
  --raft-muted:#91a3b8;
  --raft-blue:#2f80ed;
  --raft-blue-2:#60a5fa;
  --raft-green:#22c55e;
  --raft-amber:#f59e0b;
  --raft-red:#ef4444;
}
.stApp{background:linear-gradient(180deg,#07101d 0%,#0a1422 48%,#091321 100%);}
.block-container{max-width:1480px;padding:1.5rem 2rem 3rem;}
[data-testid="stSidebar"]{background:#07101c;border-right:1px solid var(--raft-border);}
[data-testid="stSidebar"] > div:first-child{padding-top:1rem;}
h1,h2,h3{letter-spacing:-.025em;}
.stButton>button,.stDownloadButton>button{
  border-radius:10px;border:1px solid #284362;font-weight:700;
  transition:.15s ease;min-height:40px;
}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:#4d8edb;transform:translateY(-1px);}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div,
textarea,input{border-radius:9px!important;}
.raft-brand{display:flex;align-items:center;gap:12px;padding:8px 4px 18px;}
.raft-brand-mark{width:40px;height:40px;display:grid;place-items:center;border-radius:12px;
 background:linear-gradient(135deg,#1d4ed8,#2563eb);box-shadow:0 8px 24px rgba(37,99,235,.25);}
.raft-brand-title{font-size:18px;font-weight:900;letter-spacing:.08em;}
.raft-brand-sub{font-size:10px;color:#71849b;text-transform:uppercase;letter-spacing:.12em;margin-top:2px;}
.raft-page-head{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;
 padding:4px 0 22px;border-bottom:1px solid var(--raft-border-soft);margin-bottom:22px;}
.raft-kicker{font-size:10px;font-weight:900;color:#60a5fa;letter-spacing:.15em;text-transform:uppercase;margin-bottom:6px;}
.raft-title{font-size:31px;font-weight:900;line-height:1.05;color:var(--raft-text);}
.raft-subtitle{font-size:13px;color:var(--raft-muted);margin-top:8px;max-width:900px;line-height:1.5;}
.raft-head-chip{padding:7px 11px;border-radius:999px;background:#0d2138;border:1px solid #21466e;
 color:#9dccff;font-size:10px;font-weight:900;white-space:nowrap;}
.raft-section{margin:25px 0 11px;}
.raft-section-title{font-size:17px;font-weight:850;color:#edf5ff;}
.raft-section-desc{font-size:12px;color:#71849b;margin-top:3px;}
.raft-kpi{min-height:105px;padding:16px 17px;border-radius:14px;background:linear-gradient(145deg,#101e30,#0d1827);
 border:1px solid var(--raft-border);box-shadow:0 8px 25px rgba(0,0,0,.12);}
.raft-kpi.blue{border-top:2px solid #2f80ed}.raft-kpi.green{border-top:2px solid #22c55e}
.raft-kpi.amber{border-top:2px solid #f59e0b}.raft-kpi.red{border-top:2px solid #ef4444}
.raft-kpi-label{font-size:10px;text-transform:uppercase;letter-spacing:.09em;color:#7f93aa;font-weight:850;}
.raft-kpi-value{font-size:24px;font-weight:900;letter-spacing:-.025em;margin-top:7px;color:#f7fbff;}
.raft-kpi-meta{font-size:11px;color:#71849b;margin-top:3px;}
.raft-card{background:#0e1a2b;border:1px solid var(--raft-border);border-radius:14px;}
.raft-status{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:999px;font-size:10px;font-weight:900;border:1px solid transparent;}
.raft-status.ok{color:#86efac;background:#0b2114;border-color:#164a2a}
.raft-status.warn{color:#fcd34d;background:#241b08;border-color:#59430e}
.raft-status.bad{color:#fca5a5;background:#2a0e10;border-color:#5a2025}
.raft-status.info{color:#7dd3fc;background:#082033;border-color:#12496c}
.raft-status.neutral{color:#cbd5e1;background:#141b25;border-color:#303c4d}
.raft-alert{border-radius:12px;padding:12px 14px;border:1px solid;margin:9px 0;font-size:13px;line-height:1.45;}
.raft-alert.info{background:#0a1d2d;border-color:#164a6c;color:#bae6fd}
.raft-alert.warn{background:#241a07;border-color:#5a430d;color:#fde68a}
.raft-alert.danger{background:#290d0f;border-color:#5d2026;color:#fecaca}
.raft-alert.success{background:#0b2014;border-color:#18552e;color:#bbf7d0}
.raft-login-wrap{max-width:980px;margin:7vh auto 0}.raft-login-card{background:linear-gradient(145deg,#101e31,#0b1625);border:1px solid #29405d;border-radius:22px;padding:34px;box-shadow:0 25px 70px rgba(0,0,0,.28)}.raft-login-badge{display:inline-flex;padding:6px 10px;border-radius:999px;background:#0c2035;border:1px solid #164b70;color:#7dd3fc;font-size:10px;font-weight:900}.raft-footer{margin-top:42px;padding-top:15px;border-top:1px solid var(--raft-border-soft);
 color:#627184;font-size:10px;display:flex;justify-content:space-between;}
.raft-error-card{margin-top:10px;padding:18px;border:1px solid #63313a;border-radius:14px;background:#1b1015;}
.raft-error-title{font-size:16px;font-weight:850;color:#fecaca;}
.raft-error-text{font-size:12px;color:#caaeb3;margin-top:5px;}
.raft-error-id{font:11px monospace;color:#8ca0b6;margin-top:12px;}
</style>
"""

def aplicar_tema():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("<meta name='color-scheme' content='dark'>", unsafe_allow_html=True)

def brand_sidebar():
    st.sidebar.markdown("""
    <div class='raft-brand'>
      <div class='raft-brand-mark'>🏭</div>
      <div><div class='raft-brand-title'>RAFT</div><div class='raft-brand-sub'>Controle Industrial • V4</div></div>
    </div>
    """, unsafe_allow_html=True)

def page_header(title, subtitle="", kicker="OPERAÇÃO", chip=None, icon=None):
    title_text = f"{icon} {title}" if icon else title
    chip_html = f"<div class='raft-head-chip'>{html.escape(str(chip))}</div>" if chip else ""
    st.markdown(
        f"<div class='raft-page-head'><div><div class='raft-kicker'>{html.escape(str(kicker))}</div>"
        f"<div class='raft-title'>{html.escape(str(title_text))}</div>"
        f"<div class='raft-subtitle'>{html.escape(str(subtitle))}</div></div>{chip_html}</div>",
        unsafe_allow_html=True,
    )

def section(title, description=""):
    st.markdown(
        f"<div class='raft-section'><div class='raft-section-title'>{html.escape(str(title))}</div>"
        f"{f'<div class=\"raft-section-desc\">{html.escape(str(description))}</div>' if description else ''}</div>",
        unsafe_allow_html=True,
    )

def kpi(label, value, meta="", tone="blue"):
    tone = tone if tone in {"blue","green","amber","red"} else "blue"
    st.markdown(
        f"<div class='raft-kpi {tone}'><div class='raft-kpi-label'>{html.escape(str(label))}</div>"
        f"<div class='raft-kpi-value'>{html.escape(str(value))}</div>"
        f"<div class='raft-kpi-meta'>{html.escape(str(meta))}</div></div>",
        unsafe_allow_html=True,
    )

def status(text, tone="neutral"):
    tone = tone if tone in {"ok","warn","bad","info","neutral"} else "neutral"
    return f"<span class='raft-status {tone}'>{html.escape(str(text))}</span>"

def alert(message, tone="info"):
    tone = tone if tone in {"info","warn","danger","success"} else "info"
    st.markdown(f"<div class='raft-alert {tone}'>{message}</div>", unsafe_allow_html=True)

def footer():
    st.markdown("<div class='raft-footer'><span>RAFT • Controle Industrial</span><span>V4 • Operação • Rastreabilidade • Gestão</span></div>", unsafe_allow_html=True)
