"""Sistema visual compartilhado do RAFT.

O objetivo é dar às telas a mesma linguagem visual de um ERP industrial:
hierarquia forte, estados operacionais claros e pouco ruído.
"""
import streamlit as st

CSS = r"""
<style>
:root {
  --raft-primary:#2563EB;
  --raft-primary-2:#1D4ED8;
  --raft-cyan:#38BDF8;
  --raft-bg:#080B10;
  --raft-surface:#0F141C;
  --raft-surface-2:#141B25;
  --raft-surface-3:#1A2330;
  --raft-border:#263244;
  --raft-border-soft:#1B2532;
  --raft-text:#F4F7FB;
  --raft-muted:#91A0B2;
  --raft-success:#22C55E;
  --raft-warning:#F59E0B;
  --raft-danger:#EF4444;
  --raft-info:#38BDF8;
}
#MainMenu, footer {visibility:hidden;}
header[data-testid="stHeader"] {background:rgba(8,11,16,.88); backdrop-filter:blur(14px);}
.block-container {padding-top:1.2rem; padding-bottom:3.5rem; max-width:1540px;}
body {background:var(--raft-bg);}

/* Sidebar */
section[data-testid="stSidebar"] {
  background:linear-gradient(180deg,#0A0F16 0%,#080B10 100%);
  border-right:1px solid var(--raft-border-soft);
}
section[data-testid="stSidebar"] > div {padding-top:1rem;}
section[data-testid="stSidebar"] button {border-radius:10px;}
section[data-testid="stSidebar"] [data-testid="stPageLink"] a {
  border-radius:10px; margin:2px 0; transition:.18s ease;
}
section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
  background:#141D29;
}

/* Typography */
h1 {font-size:2.05rem!important; letter-spacing:-.035em; line-height:1.12!important;}
h2 {font-size:1.38rem!important; letter-spacing:-.02em;}
h3 {font-size:1.05rem!important;}
p, label, div {font-variant-numeric:tabular-nums;}

/* Inputs */
div[data-baseweb="select"] > div, input, textarea {
  border-radius:10px!important;
  background-color:#111722!important;
  border-color:#2A3748!important;
}
div[data-baseweb="select"] > div:focus-within, input:focus, textarea:focus {
  border-color:var(--raft-primary)!important;
  box-shadow:0 0 0 1px var(--raft-primary)!important;
}
button[kind="primary"], button[kind="primaryFormSubmit"] {
  background:linear-gradient(135deg,var(--raft-primary),var(--raft-primary-2))!important;
  border:0!important; font-weight:700!important; border-radius:10px!important;
}
button[kind="primary"]:hover {filter:brightness(1.08);}

/* Native metrics */
div[data-testid="stMetric"] {
  background:linear-gradient(145deg,#131B26,#0E141C);
  border:1px solid var(--raft-border);
  border-radius:14px;
  padding:16px 18px;
  box-shadow:0 10px 28px rgba(0,0,0,.15);
}
div[data-testid="stMetricLabel"] {color:var(--raft-muted);}
div[data-testid="stMetricValue"] {font-size:1.55rem; font-weight:760;}

/* Containers / cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background:linear-gradient(145deg,rgba(20,28,39,.96),rgba(13,18,25,.96));
  border-color:var(--raft-border)!important;
  border-radius:14px!important;
}
hr {border-color:var(--raft-border-soft)!important; margin:1.35rem 0!important;}

/* Dataframes */
div[data-testid="stDataFrame"] {
  border:1px solid var(--raft-border)!important;
  border-radius:12px!important;
  overflow:hidden;
}

/* Tabs */
button[data-baseweb="tab"] {font-weight:700;}
button[data-baseweb="tab"][aria-selected="true"] {color:#60A5FA;}

/* Custom RAFT components */
.raft-brand {display:flex;align-items:center;gap:11px;margin:0 0 22px 2px;}
.raft-brand-mark {width:38px;height:38px;border-radius:11px;display:grid;place-items:center;background:linear-gradient(135deg,#2563EB,#0EA5E9);box-shadow:0 8px 22px rgba(37,99,235,.28);font-size:20px;}
.raft-brand-title {font-size:18px;font-weight:800;letter-spacing:-.02em;}
.raft-brand-sub {font-size:11px;color:var(--raft-muted);margin-top:1px;}

.raft-page-head {display:flex;justify-content:space-between;align-items:flex-start;gap:24px;margin-bottom:22px;}
.raft-kicker {font-size:11px;text-transform:uppercase;letter-spacing:.14em;color:#60A5FA;font-weight:800;margin-bottom:7px;}
.raft-title {font-size:34px;font-weight:820;letter-spacing:-.045em;line-height:1.08;color:var(--raft-text);}
.raft-subtitle {color:var(--raft-muted);font-size:14px;margin-top:7px;max-width:850px;line-height:1.5;}
.raft-head-chip {padding:8px 12px;border:1px solid var(--raft-border);background:#101722;border-radius:999px;color:#B9C5D4;font-size:12px;white-space:nowrap;}

.raft-section {display:flex;align-items:center;justify-content:space-between;gap:16px;margin:25px 0 12px;}
.raft-section-title {font-size:17px;font-weight:780;letter-spacing:-.02em;}
.raft-section-desc {font-size:12px;color:var(--raft-muted);}

.raft-kpi {height:100%;background:linear-gradient(145deg,#141C27,#0F151E);border:1px solid var(--raft-border);border-radius:15px;padding:16px 17px;box-shadow:0 10px 28px rgba(0,0,0,.14);}
.raft-kpi-label {font-size:11px;color:#9BA9BA;text-transform:uppercase;letter-spacing:.08em;font-weight:760;}
.raft-kpi-value {font-size:25px;font-weight:820;letter-spacing:-.035em;margin-top:7px;}
.raft-kpi-meta {font-size:11px;color:#77879A;margin-top:5px;}
.raft-kpi.blue {border-top:2px solid #3B82F6;}
.raft-kpi.green {border-top:2px solid #22C55E;}
.raft-kpi.amber {border-top:2px solid #F59E0B;}
.raft-kpi.red {border-top:2px solid #EF4444;}

.raft-card {background:linear-gradient(145deg,#121923,#0D131B);border:1px solid var(--raft-border);border-radius:15px;padding:18px 19px;}
.raft-card-title {font-size:14px;font-weight:780;}
.raft-card-muted {color:var(--raft-muted);font-size:12px;line-height:1.45;}

.raft-status {display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:999px;font-size:11px;font-weight:800;border:1px solid transparent;}
.raft-status.ok {color:#86EFAC;background:#0B2114;border-color:#164A2A;}
.raft-status.warn {color:#FCD34D;background:#241B08;border-color:#59430E;}
.raft-status.bad {color:#FCA5A5;background:#2A0E10;border-color:#5A2025;}
.raft-status.info {color:#7DD3FC;background:#082033;border-color:#12496C;}
.raft-status.neutral {color:#CBD5E1;background:#141B25;border-color:#303C4D;}

.raft-alert {border-radius:12px;padding:12px 14px;border:1px solid;margin:8px 0;font-size:13px;line-height:1.45;}
.raft-alert.info {background:#0A1D2D;border-color:#164A6C;color:#BAE6FD;}
.raft-alert.warn {background:#241A07;border-color:#5A430D;color:#FDE68A;}
.raft-alert.danger {background:#290D0F;border-color:#5D2026;color:#FECACA;}
.raft-alert.success {background:#0B2014;border-color:#18552E;color:#BBF7D0;}

.raft-timeline {position:relative;margin:4px 0 0 8px;padding-left:24px;border-left:1px solid #2B394B;}
.raft-timeline-item {position:relative;padding:0 0 18px 10px;}
.raft-timeline-dot {position:absolute;left:-31px;top:3px;width:12px;height:12px;border-radius:50%;background:#2563EB;border:3px solid #0B1017;box-shadow:0 0 0 1px #3569AE;}
.raft-timeline-time {font-size:11px;color:#738398;}
.raft-timeline-main {font-size:13px;font-weight:700;margin-top:2px;}
.raft-timeline-meta {font-size:11px;color:#93A1B2;margin-top:3px;}

.raft-footer {margin-top:36px;padding-top:15px;border-top:1px solid var(--raft-border-soft);color:#627184;font-size:11px;display:flex;justify-content:space-between;}

/* Login */
.raft-login-wrap {max-width:1020px;margin:8vh auto 0;}
.raft-login-card {background:linear-gradient(145deg,#121A25,#0D131B);border:1px solid #293648;border-radius:22px;padding:34px;box-shadow:0 30px 80px rgba(0,0,0,.35);}
.raft-login-badge {display:inline-flex;padding:6px 10px;border-radius:999px;background:#0C2035;border:1px solid #164B70;color:#7DD3FC;font-size:11px;font-weight:800;}
</style>
"""

def aplicar_tema():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("<meta name='color-scheme' content='dark'>", unsafe_allow_html=True)

def brand_sidebar():
    st.sidebar.markdown("""
    <div class='raft-brand'>
      <div class='raft-brand-mark'>🏭</div>
      <div><div class='raft-brand-title'>RAFT</div><div class='raft-brand-sub'>Controle Industrial</div></div>
    </div>
    """, unsafe_allow_html=True)

def page_header(title, subtitle="", kicker="OPERAÇÃO", chip=None, icon=None):
    title_text = f"{icon} {title}" if icon else title
    chip_html = f"<div class='raft-head-chip'>{chip}</div>" if chip else ""
    st.markdown(f"""
    <div class='raft-page-head'>
      <div><div class='raft-kicker'>{kicker}</div><div class='raft-title'>{title_text}</div>
      <div class='raft-subtitle'>{subtitle}</div></div>{chip_html}
    </div>
    """, unsafe_allow_html=True)

def section(title, description=""):
    desc = f"<div class='raft-section-desc'>{description}</div>" if description else ""
    st.markdown(f"<div class='raft-section'><div class='raft-section-title'>{title}</div>{desc}</div>", unsafe_allow_html=True)

def kpi(label, value, meta="", tone="blue"):
    st.markdown(f"""<div class='raft-kpi {tone}'>
      <div class='raft-kpi-label'>{label}</div><div class='raft-kpi-value'>{value}</div>
      <div class='raft-kpi-meta'>{meta}</div>
    </div>""", unsafe_allow_html=True)

def status(text, tone="neutral"):
    return f"<span class='raft-status {tone}'>{text}</span>"

def alert(message, tone="info"):
    st.markdown(f"<div class='raft-alert {tone}'>{message}</div>", unsafe_allow_html=True)

def footer():
    st.markdown("<div class='raft-footer'><span>RAFT • Controle Industrial</span><span>Operação • Rastreabilidade • Gestão</span></div>", unsafe_allow_html=True)
