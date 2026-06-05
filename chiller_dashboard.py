import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import random

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Chiller Prediction Dashboard",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0f1923;
    border-right: 1px solid #1e2d3d;
}
[data-testid="stSidebar"] * {
    color: #c8d8e8 !important;
}
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stSelectbox label {
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #6a8aaa !important;
    font-weight: 500;
}
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] {
    padding-top: 4px;
}

/* ── Main area ── */
[data-testid="stAppViewContainer"] > .main {
    background: #080f17;
}
.block-container {
    padding: 1.5rem 2rem;
}

/* ── Metric cards ── */
.metric-card {
    background: #111c28;
    border: 1px solid #1e2d3d;
    border-radius: 12px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: var(--accent);
    border-radius: 0 2px 2px 0;
}
.metric-label {
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4a6a8a;
    margin-bottom: 8px;
    font-weight: 500;
}
.metric-value {
    font-size: 28px;
    font-weight: 600;
    color: #e8f0f8;
    line-height: 1;
    font-family: 'DM Mono', monospace;
}
.metric-unit {
    font-size: 13px;
    color: #4a6a8a;
    margin-left: 4px;
    font-weight: 400;
}
.metric-delta {
    font-size: 12px;
    margin-top: 8px;
    font-weight: 500;
}
.delta-up { color: #f87171; }
.delta-down { color: #34d399; }

/* ── Section headers ── */
.section-header {
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #4a6a8a;
    padding: 0 0 12px;
    border-bottom: 1px solid #1e2d3d;
    margin-bottom: 20px;
}

/* ── Room status badges ── */
.room-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.05em;
}
.badge-active   { background: #0d3326; color: #34d399; border: 1px solid #1a5240; }
.badge-standby  { background: #1a2a14; color: #86efac; border: 1px solid #2a4a24; }
.badge-idle     { background: #1e2d3d; color: #6a8aaa; border: 1px solid #2a3d50; }
.badge-critical { background: #3d1414; color: #f87171; border: 1px solid #5a2020; }

/* ── Chart containers ── */
.chart-card {
    background: #111c28;
    border: 1px solid #1e2d3d;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}
.chart-title {
    font-size: 13px;
    font-weight: 500;
    color: #c8d8e8;
    margin-bottom: 4px;
}
.chart-subtitle {
    font-size: 11px;
    color: #4a6a8a;
    margin-bottom: 16px;
}

/* ── Stremlit overrides ── */
h1, h2, h3 { color: #e8f0f8 !important; }
p { color: #8aa8c8; }
.stMetric { background: transparent; }
div[data-testid="stMetricValue"] { color: #e8f0f8; font-family: 'DM Mono', monospace; }
div[data-testid="stMetricLabel"] { color: #4a6a8a; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; }
.stAlert { border-radius: 8px; }

/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0f1923;
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #1e2d3d;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    color: #4a6a8a;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.04em;
}
.stTabs [aria-selected="true"] {
    background: #1e3a5a;
    color: #7ab8f0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Helpers ──────────────────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#8aa8c8", size=11),
    hovermode="x unified",
)
# Default axis styling — pass explicitly per chart to avoid duplicate-kwarg errors
_AX = dict(gridcolor="#1e2d3d", zeroline=False, tickfont=dict(size=10))
_L = dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10), orientation="h",
          yanchor="bottom", y=1.01, xanchor="left", x=0)
# Default margin applied separately so individual charts can override without conflict
_M = dict(l=0, r=0, t=10, b=0)

ACCENT_BLUE    = "#3b82f6"
ACCENT_CYAN    = "#22d3ee"
ACCENT_GREEN   = "#34d399"
ACCENT_AMBER   = "#fbbf24"
ACCENT_RED     = "#f87171"
ACCENT_PURPLE  = "#a78bfa"

def metric_card(label, value, unit, delta=None, accent=ACCENT_BLUE,
                sublabel=None, subvalue=None, subunit="", badge=None, badge_color=None):
    delta_html = ""
    if delta is not None:
        cls = "delta-up" if delta > 0 else "delta-down"
        arrow = "▲" if delta > 0 else "▼"
        delta_html = f'<div class="metric-delta {cls}">{arrow} {abs(delta):.1f}% vs kemarin</div>'
    sub_html = ""
    if sublabel and subvalue is not None:
        sub_html = f'<div style="margin-top:8px;padding-top:8px;border-top:1px solid #1e2d3d;font-size:10px;color:#4a6a8a;">{sublabel}<span style="font-family:DM Mono,monospace;color:#c8d8e8;margin-left:6px;">{subvalue}<span style="font-size:9px;color:#4a6a8a;margin-left:2px;">{subunit}</span></span></div>'
    badge_html = ""
    if badge:
        bc = badge_color or accent
        badge_html = f'<div style="margin-top:8px;display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;background:{bc}22;color:{bc};border:1px solid {bc}55;">{badge}</div>'
    st.markdown(f"""
    <div class="metric-card" style="--accent:{accent}">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>
      {delta_html}{badge_html}{sub_html}
    </div>""", unsafe_allow_html=True)

def gen_time_series(hours=24, base=100, noise=15, trend=0):
    t = pd.date_range("2025-07-18 00:00", periods=hours*4, freq="15min")
    vals = base + trend * np.arange(len(t)) / len(t)
    vals += noise * np.sin(np.linspace(0, 4*np.pi, len(t)))
    vals += np.random.normal(0, noise*0.3, len(t))
    return t, np.clip(vals, 0, None)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 16px 0 24px; border-bottom: 1px solid #1e2d3d; margin-bottom: 20px;">
      <div style="font-size: 18px; font-weight: 600; color: #e8f0f8; letter-spacing: -0.02em;">❄️ ChillerPred</div>
      <div style="font-size: 11px; color: #4a6a8a; margin-top: 2px; letter-spacing: 0.05em; text-transform: uppercase;">Sistem Prediksi Energi</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Setpoint Chiller**")
    sp_chiller = st.slider("Chiller Setpoint (°C)", 5.0, 9.0, 7.0, 0.1, format="%.1f°C")

    st.markdown("---")
    st.markdown("**Setpoint AHU**")
    sp_ahu1 = st.slider("AHU 1 (°C)", 20.0, 26.0, 22.0, 0.5, format="%.1f°C")
    sp_ahu2 = st.slider("AHU 2 (°C)", 20.0, 26.0, 22.0, 0.5, format="%.1f°C")
    sp_ahu3 = st.slider("AHU 3 (°C)", 20.0, 26.0, 23.0, 0.5, format="%.1f°C")
    sp_mau  = st.slider("MAU (°C)",   20.0, 26.0, 22.0, 0.5, format="%.1f°C")

    st.markdown("---")
    st.markdown("**Kondisi Luar Gedung**")
    outside_temp = st.slider("Suhu Luar (°C)", 28.0, 38.0, 31.1, 0.1, format="%.1f°C")
    outside_rh   = st.slider("RH Luar (%)",    50,   95,   67,   1,   format="%d%%")

    st.markdown("---")
    st.markdown("**Jadwal**")
    hari = st.selectbox("Hari", ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu"])
    periode = st.selectbox("Periode Waktu", ["00:00–04:00","04:00–08:00","08:00–12:00","12:00–16:00","16:00–20:00","20:00–24:00"])

    st.markdown("---")
    sim_name = st.selectbox("Pilih Simulasi", [
        "Simulasi 1 – Chiller 5 & 6 (18 Juli)",
        "Simulasi 2 – Chiller 3 & 4 (20 Juli)",
        "Simulasi 3 – Full Load (22 Juli)",
    ])

# ── Derived values ────────────────────────────────────────────────────────────
delta_T   = outside_temp - sp_chiller
ahu_avg   = (sp_ahu1 + sp_ahu2 + sp_ahu3 + sp_mau) / 4
load_est  = 320 + delta_T * 8 + (24 - ahu_avg) * 12 + outside_rh * 0.8
cop_est   = round(max(2.8, 5.2 - delta_T * 0.12), 2)
power_est = round(load_est / cop_est, 1)

# ── Extended KPI calculations ─────────────────────────────────────────────────
# Avg kWh/day: assume 20-hr operational, vary with load
op_hours       = 20
kwh_per_day    = round(power_est * op_hours, 0)          # kWh/day
kwh_per_month  = round(kwh_per_day * 26 / 1000, 1)       # MWh/month (26 working days)

# RLA (Rated Load Ampere) estimation
# Chiller rated ~800A FLA at full load; RLA = FLA * load_factor
chiller_fla    = 800  # A per chiller
load_factor    = min(power_est / 400, 1.0)               # 400 kW = full load 1 chiller
rla_per_chiller = round(chiller_fla * load_factor, 0)
avg_rla_pct    = round(load_factor * 100, 1)

# Evaporator Leaving Water Temperature (ELT)
# ELT ≈ setpoint chiller + small approach (0.5-1.5°C depending on load)
approach_temp  = 0.5 + load_factor * 1.0
elt            = round(sp_chiller + approach_temp, 1)

# Chiller recommendation: 1 chiller up to ~380 kW, 2 chillers above
if power_est <= 380:
    chiller_rec     = "1 Chiller"
    chiller_rec_color = ACCENT_GREEN
    chiller_rec_icon  = "❄️"
else:
    chiller_rec     = "2 Chiller"
    chiller_rec_color = ACCENT_AMBER
    chiller_rec_icon  = "❄️❄️"

# Load factor for 2-chiller scenario
if power_est > 380:
    load_factor_each = min(power_est / 800, 1.0)
    rla_per_chiller  = round(chiller_fla * load_factor_each, 0)
    avg_rla_pct      = round(load_factor_each * 100, 1)

np.random.seed(42)
t, p_chiller5 = gen_time_series(base=160, noise=18, trend=-10)
_, p_chiller6  = gen_time_series(base=155, noise=16, trend= 5)
_, p_total     = gen_time_series(base=315, noise=28, trend=-5)
_, p_pred      = gen_time_series(base=power_est, noise=8, trend=-3)

rooms = {
    "Filling Room A": {"ahu":"AHU-1","load_pct":88,"temp":22.1,"rh":58,"status":"active","kw":84},
    "Filling Room B": {"ahu":"AHU-1","load_pct":72,"temp":22.4,"rh":63,"status":"active","kw":68},
    "Granulasi":      {"ahu":"AHU-2","load_pct":95,"temp":21.8,"rh":71,"status":"critical","kw":102},
    "Coating":        {"ahu":"AHU-2","load_pct":60,"temp":22.9,"rh":65,"status":"standby","kw":58},
    "QC Lab":         {"ahu":"AHU-3","load_pct":45,"temp":23.1,"rh":60,"status":"active","kw":41},
    "Blending":       {"ahu":"MAU",  "load_pct":30,"temp":23.5,"rh":68,"status":"idle","kw":24},
    "Packaging":      {"ahu":"MAU",  "load_pct":55,"temp":22.8,"rh":74,"status":"active","kw":49},
    "Warehouse":      {"ahu":"AHU-3","load_pct":20,"temp":26.2,"rh":72,"status":"idle","kw":16},
}
TEMP_LIMIT = 25.0
RH_LIMIT   = 70

badge_map = {"active":"badge-active","standby":"badge-standby","idle":"badge-idle","critical":"badge-critical"}
badge_label = {"active":"Produksi","standby":"Standby","idle":"Idle","critical":"High Load"}

# ═══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════════════════════
col_h1, col_h2, col_h3 = st.columns([3,1,1])
with col_h1:
    st.markdown(f"## Prediksi Konsumsi Chiller")
    st.markdown(f"<p style='margin-top:-10px;font-size:12px;color:#4a6a8a;'>{sim_name} · Diperbarui {datetime.now().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)
with col_h2:
    now_str = datetime.now().strftime("%d %b %Y")
    st.markdown(f"<div style='text-align:right;padding-top:8px;font-size:12px;color:#4a6a8a;'>{now_str}</div>", unsafe_allow_html=True)
with col_h3:
    st.markdown(f"<div style='text-align:right;padding-top:8px;font-size:12px;color:#4a6a8a;'>Periode: {periode}</div>", unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
#  KPI CARDS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Ringkasan Prediksi</div>', unsafe_allow_html=True)

# Row 1 – 6 cards
r1c1, r1c2, r1c3, r1c4, r1c5, r1c6 = st.columns(6)
with r1c1:
    metric_card("Rata-rata Konsumsi", f"{kwh_per_day:,.0f}", "kWh/hari",
                delta=2.3, accent=ACCENT_BLUE,
                sublabel="Bulan ini", subvalue=f"{kwh_per_month}", subunit="MWh")
with r1c2:
    metric_card("COP Chiller", f"{cop_est}", "",
                delta=-0.8, accent=ACCENT_CYAN,
                sublabel="Kondisi", subvalue="Optimal" if cop_est >= 3.5 else "Perlu cek",
                subunit="")
with r1c3:
    metric_card("Rekomendasi", chiller_rec_icon, "",
                accent=chiller_rec_color,
                badge=chiller_rec, badge_color=chiller_rec_color,
                sublabel="Est. beban", subvalue=f"{power_est:.0f}", subunit="kW")
with r1c4:
    metric_card("Prediksi RLA", f"{avg_rla_pct}", "%",
                accent=ACCENT_AMBER,
                sublabel="Per chiller", subvalue=f"{rla_per_chiller:.0f}", subunit="A")
with r1c5:
    metric_card("ELT Evaporator", f"{elt}", "°C",
                accent=ACCENT_PURPLE,
                sublabel="Setpoint", subvalue=f"{sp_chiller}", subunit="°C")
with r1c6:
    metric_card("Total Cooling Load", f"{load_est:.0f}", "kW",
                delta=4.1, accent=ACCENT_RED,
                sublabel="Suhu luar", subvalue=f"{outside_temp}", subunit="°C")

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["📊  Power & Energi", "🏭  Status Ruangan", "🔮  Analisis Prediksi"])

# ─────────────────────────────── TAB 1 ───────────────────────────────────────
with tab1:
    col_l, col_r = st.columns([3, 2], gap="medium")

    with col_l:
        # Stacked area chart – power usage
        fig_power = go.Figure()
        fig_power.add_trace(go.Scatter(
            x=t, y=p_chiller5, name="Chiller 5",
            fill="tozeroy", mode="lines",
            line=dict(color=ACCENT_BLUE, width=1.5),
            fillcolor="rgba(59,130,246,0.15)"
        ))
        fig_power.add_trace(go.Scatter(
            x=t, y=p_chiller6, name="Chiller 6",
            fill="tonexty", mode="lines",
            line=dict(color=ACCENT_CYAN, width=1.5),
            fillcolor="rgba(34,211,238,0.12)"
        ))
        fig_power.add_trace(go.Scatter(
            x=t, y=p_pred, name="Prediksi",
            mode="lines", line=dict(color=ACCENT_AMBER, width=2, dash="dash"),
        ))
        fig_power.update_layout(**PLOT_LAYOUT, margin=_M, legend=_L, height=260,
            xaxis={**_AX}, yaxis={**_AX, "title":"kW"}, xaxis_title="Waktu")
        st.markdown('<div class="chart-card"><div class="chart-title">Power Usage – Chiller 5 & 6</div><div class="chart-subtitle">Konsumsi aktual vs prediksi (kW)</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_power, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        # Energy donut
        room_kws = [v["kw"] for v in rooms.values()]
        room_names = list(rooms.keys())
        colors_donut = [ACCENT_BLUE, ACCENT_CYAN, ACCENT_GREEN, ACCENT_AMBER,
                        ACCENT_RED, ACCENT_PURPLE, "#ec4899", "#f97316"]
        fig_donut = go.Figure(go.Pie(
            labels=room_names, values=room_kws,
            hole=0.62,
            marker=dict(colors=colors_donut, line=dict(color="#080f17", width=2)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} kW (%{percent})<extra></extra>"
        ))
        fig_donut.add_annotation(
            text=f"<b>{sum(room_kws)}</b><br><span style='font-size:10px'>kW Total</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#e8f0f8", size=18)
        )
        fig_donut.update_layout(**PLOT_LAYOUT, height=260, showlegend=False,
            margin=dict(l=0,r=0,t=0,b=0))
        st.markdown('<div class="chart-card"><div class="chart-title">Distribusi Beban per Ruangan</div><div class="chart-subtitle">Proporsi konsumsi cooling (kW)</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

    # Bottom: energy cumulative
    energy_kwh = np.cumsum(p_total * 0.25 / 1000)
    fig_energy = go.Figure()
    fig_energy.add_trace(go.Scatter(
        x=t, y=energy_kwh, name="Energi Kumulatif",
        mode="lines", fill="tozeroy",
        line=dict(color=ACCENT_GREEN, width=2),
        fillcolor="rgba(52,211,153,0.10)"
    ))
    fig_energy.update_layout(**PLOT_LAYOUT, margin=_M, legend=_L, height=180,
        xaxis={**_AX}, yaxis={**_AX, "title":"kWh"}, xaxis_title="Waktu")
    st.markdown('<div class="chart-card"><div class="chart-title">Energi Kumulatif</div><div class="chart-subtitle">Total akumulasi energi hari ini (kWh)</div>', unsafe_allow_html=True)
    st.plotly_chart(fig_energy, use_container_width=True, config={"displayModeBar":False})
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Tren RLA, ELT, ELP, Total Konsumsi ──────────────────────────────────
    st.markdown('<div class="section-header" style="margin-top:8px;">Tren Prediksi – RLA · ELT · ELP · Total Konsumsi</div>', unsafe_allow_html=True)

    # Generate time-series for each parameter
    np.random.seed(7)
    # RLA % – follows load pattern, moderate noise
    _, p_rla_raw = gen_time_series(base=avg_rla_pct, noise=4, trend=-2)
    p_rla = np.clip(p_rla_raw, 40, 105)

    # ELT – Evaporator Leaving Temperature (°C)
    # Inversely related to load: heavier load → slightly higher ELT
    elt_base = sp_chiller + 0.5 + load_factor * 1.0
    _, p_elt_raw = gen_time_series(base=elt_base, noise=0.4, trend=0.2)
    p_elt = np.clip(p_elt_raw, sp_chiller - 0.5, sp_chiller + 3.0)

    # ELP – Evaporator Leaving Pressure (kPa)
    # Saturation pressure at ELT for R-134a approx: P(kPa) = 101.3 * exp(0.065 * (T - 5))
    p_elp = np.array([round(101.3 * np.exp(0.065 * (t_val - 5)), 1) for t_val in p_elt])
    p_elp += np.random.normal(0, 1.2, len(p_elp))
    p_elp = np.clip(p_elp, 85, 145)

    # Total konsumsi (kW) – sum of both chillers
    p_total_kw = p_chiller5 + p_chiller6

    # ── 2-column layout for 4 charts ──
    col_t1, col_t2 = st.columns(2, gap="medium")

    with col_t1:
        # Chart A – RLA Trend
        rla_limit = 100
        fig_rla = go.Figure()
        fig_rla.add_trace(go.Scatter(
            x=t, y=p_rla, name="RLA Chiller 5",
            mode="lines", line=dict(color=ACCENT_AMBER, width=1.8),
            fill="tozeroy", fillcolor="rgba(251,191,36,0.08)"
        ))
        # RLA limit line
        fig_rla.add_hline(y=rla_limit, line_color=ACCENT_RED, line_dash="dot", line_width=1.5,
            annotation_text="Batas RLA 100%", annotation_font_color=ACCENT_RED,
            annotation_font_size=10, annotation_position="top right")
        # Warning zone fill
        fig_rla.add_hrect(y0=90, y1=105, fillcolor="rgba(248,113,113,0.05)",
            line_width=0, annotation_text="⚠ Warning zone",
            annotation_font_size=9, annotation_font_color="#f87171")
        fig_rla.update_layout(**PLOT_LAYOUT, margin=_M, legend=_L, height=210,
            xaxis={**_AX, "title":"Waktu"},
            yaxis={**_AX, "title":"RLA (%)", "range":[40, 110]})
        st.markdown('<div class="chart-card"><div class="chart-title">Tren RLA Chiller</div><div class="chart-subtitle">Prediksi % Rated Load Ampere · batas 100%</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_rla, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

        # Chart C – ELP Trend
        elp_low_limit  = 90.0   # kPa
        elp_high_limit = 130.0  # kPa
        fig_elp = go.Figure()
        fig_elp.add_trace(go.Scatter(
            x=t, y=p_elp, name="ELP",
            mode="lines", line=dict(color=ACCENT_CYAN, width=1.8),
            fill="tozeroy", fillcolor="rgba(34,211,238,0.07)"
        ))
        fig_elp.add_hline(y=elp_high_limit, line_color=ACCENT_RED, line_dash="dot", line_width=1.5,
            annotation_text=f"Batas atas {elp_high_limit} kPa",
            annotation_font_color=ACCENT_RED, annotation_font_size=10,
            annotation_position="top right")
        fig_elp.add_hline(y=elp_low_limit, line_color=ACCENT_AMBER, line_dash="dot", line_width=1.5,
            annotation_text=f"Batas bawah {elp_low_limit} kPa",
            annotation_font_color=ACCENT_AMBER, annotation_font_size=10,
            annotation_position="bottom right")
        fig_elp.update_layout(**PLOT_LAYOUT, margin=_M, legend=_L, height=210,
            xaxis={**_AX, "title":"Waktu"},
            yaxis={**_AX, "title":"Tekanan (kPa)", "range":[75, 150]})
        st.markdown('<div class="chart-card"><div class="chart-title">Tren Evaporator Leaving Pressure (ELP)</div><div class="chart-subtitle">Prediksi tekanan refrigeran keluar evaporator (kPa) · R-134a</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_elp, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_t2:
        # Chart B – ELT Trend
        elt_limit = sp_chiller + 2.5
        fig_elt = go.Figure()
        fig_elt.add_trace(go.Scatter(
            x=t, y=p_elt, name="ELT",
            mode="lines", line=dict(color=ACCENT_PURPLE, width=1.8),
            fill="tozeroy", fillcolor="rgba(167,139,250,0.08)"
        ))
        fig_elt.add_hline(y=elt_limit, line_color=ACCENT_RED, line_dash="dot", line_width=1.5,
            annotation_text=f"Batas ELT {elt_limit:.1f}°C",
            annotation_font_color=ACCENT_RED, annotation_font_size=10,
            annotation_position="top right")
        fig_elt.add_hline(y=sp_chiller, line_color=ACCENT_GREEN, line_dash="dot", line_width=1,
            annotation_text=f"Setpoint {sp_chiller}°C",
            annotation_font_color=ACCENT_GREEN, annotation_font_size=10,
            annotation_position="bottom right")
        fig_elt.update_layout(**PLOT_LAYOUT, margin=_M, legend=_L, height=210,
            xaxis={**_AX, "title":"Waktu"},
            yaxis={**_AX, "title":"Suhu (°C)", "range":[sp_chiller - 1, sp_chiller + 4]})
        st.markdown('<div class="chart-card"><div class="chart-title">Tren Evaporator Leaving Temperature (ELT)</div><div class="chart-subtitle">Prediksi suhu air keluar evaporator (°C)</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_elt, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

        # Chart D – Total Konsumsi kW
        fig_totalkw = go.Figure()
        fig_totalkw.add_trace(go.Scatter(
            x=t, y=p_chiller5, name="Chiller 5",
            mode="lines", stackgroup="one",
            line=dict(color=ACCENT_BLUE, width=0),
            fillcolor="rgba(59,130,246,0.5)"
        ))
        fig_totalkw.add_trace(go.Scatter(
            x=t, y=p_chiller6, name="Chiller 6",
            mode="lines", stackgroup="one",
            line=dict(color=ACCENT_CYAN, width=0),
            fillcolor="rgba(34,211,238,0.5)"
        ))
        fig_totalkw.add_trace(go.Scatter(
            x=t, y=p_pred * (1 + load_factor * 0.3), name="Prediksi Total",
            mode="lines", line=dict(color=ACCENT_AMBER, width=2, dash="dash")
        ))
        fig_totalkw.update_layout(**PLOT_LAYOUT, margin=_M, legend=_L, height=210,
            xaxis={**_AX, "title":"Waktu"},
            yaxis={**_AX, "title":"kW"})
        st.markdown('<div class="chart-card"><div class="chart-title">Total Konsumsi Chiller (Stacked)</div><div class="chart-subtitle">Chiller 5 + Chiller 6 aktual vs prediksi total (kW)</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_totalkw, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────── TAB 2 ───────────────────────────────────────
with tab2:
    st.markdown('<div class="section-header">Status Ruangan & AHU</div>', unsafe_allow_html=True)

    cols = st.columns(4, gap="medium")
    for idx, (room, info) in enumerate(rooms.items()):
        col = cols[idx % 4]
        with col:
            badge_cls  = badge_map[info["status"]]
            badge_lbl  = badge_label[info["status"]]
            bar_color  = {"active":ACCENT_BLUE,"standby":ACCENT_GREEN,
                          "idle":"#4a6a8a","critical":ACCENT_RED}[info["status"]]
            temp       = info["temp"]
            rh         = info["rh"]
            kw         = info["kw"]
            ahu        = info["ahu"]

            # Bar widths (capped at 100%)
            temp_pct   = min(temp / TEMP_LIMIT * 100, 100)
            rh_pct     = min(rh   / RH_LIMIT   * 100, 100)

            # Exceed limit → red, else colour by status
            temp_color = ACCENT_RED if temp > TEMP_LIMIT else ACCENT_BLUE
            rh_color   = ACCENT_RED if rh   > RH_LIMIT   else ACCENT_CYAN

            temp_warn  = " ⚠" if temp > TEMP_LIMIT else ""
            rh_warn    = " ⚠" if rh   > RH_LIMIT   else ""

            # Limit marker position (always at 100% of bar width = the limit line)
            st.markdown(f"""
            <div class="metric-card" style="--accent:{bar_color}; margin-bottom:12px;">
              <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                <div style="font-size:13px; font-weight:500; color:#c8d8e8; line-height:1.3;">{room}</div>
                <span class="room-badge {badge_cls}">{badge_lbl}</span>
              </div>
              <div style="font-size:10px; color:#4a6a8a; margin-bottom:10px;">{ahu} &nbsp;·&nbsp; <span style="font-family:'DM Mono',monospace;">{kw} kW</span></div>

              <!-- Suhu bar -->
              <div style="margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; font-size:10px; margin-bottom:3px;">
                  <span style="color:#6a8aaa;">🌡 Suhu</span>
                  <span style="font-family:'DM Mono',monospace; color:{temp_color};">{temp}°C{temp_warn}</span>
                </div>
                <div style="position:relative; background:#0f1923; border-radius:4px; height:7px;">
                  <div style="background:{temp_color}; width:{temp_pct:.1f}%; height:100%; border-radius:4px; transition:width 0.4s;"></div>
                  <!-- limit marker at 100% = 25°C -->
                  <div style="position:absolute; top:-2px; right:0; width:2px; height:11px; background:#fbbf24; border-radius:1px;"></div>
                </div>
                <div style="font-size:9px; color:#3a5a7a; text-align:right; margin-top:1px;">batas 25°C</div>
              </div>

              <!-- RH bar -->
              <div>
                <div style="display:flex; justify-content:space-between; font-size:10px; margin-bottom:3px;">
                  <span style="color:#6a8aaa;">💧 RH</span>
                  <span style="font-family:'DM Mono',monospace; color:{rh_color};">{rh}%{rh_warn}</span>
                </div>
                <div style="position:relative; background:#0f1923; border-radius:4px; height:7px;">
                  <div style="background:{rh_color}; width:{rh_pct:.1f}%; height:100%; border-radius:4px; transition:width 0.4s;"></div>
                  <div style="position:absolute; top:-2px; right:0; width:2px; height:11px; background:#fbbf24; border-radius:1px;"></div>
                </div>
                <div style="font-size:9px; color:#3a5a7a; text-align:right; margin-top:1px;">batas 70%</div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Lini Produksi – Supply Air Flow & Konsumsi AHU</div>', unsafe_allow_html=True)

    # ── Supply Air Flow data per AHU (CMH) ──────────────────────────────────
    ahu_airflow = {
        "AHU-1": {"flow": 18500, "sp": sp_ahu1, "rooms": []},
        "AHU-2": {"flow": 24200, "sp": sp_ahu2, "rooms": []},
        "AHU-3": {"flow": 11800, "sp": sp_ahu3, "rooms": []},
        "MAU":   {"flow": 15600, "sp": sp_mau,  "rooms": []},
    }
    for room, info in rooms.items():
        ahu_airflow[info["ahu"]]["rooms"].append({
            "name": room, "kw": info["kw"], "load_pct": info["load_pct"],
            "temp": info["temp"], "rh": info["rh"]
        })

    # Sort AHU by air flow descending (highest supply first)
    sorted_ahus = sorted(ahu_airflow.items(), key=lambda x: x[1]["flow"], reverse=True)
    max_flow = sorted_ahus[0][1]["flow"]

    col_lini, col_flow = st.columns([3, 2], gap="medium")

    with col_lini:
        # Horizontal grouped bar: Lini (rooms) grouped by AHU, sorted by airflow
        fig_lini = go.Figure()
        room_colors = {r: colors_donut[i] for i, r in enumerate(rooms.keys())}
        for ahu_name, ahu_data in sorted_ahus:
            for rm in ahu_data["rooms"]:
                fig_lini.add_trace(go.Bar(
                    name=rm["name"],
                    y=[f"{ahu_name}  ({ahu_data['flow']:,} CMH)"],
                    x=[rm["kw"]],
                    orientation="h",
                    marker_color=room_colors[rm["name"]],
                    hovertemplate=(
                        f"<b>{rm['name']}</b><br>"
                        f"AHU: {ahu_name}<br>"
                        f"Konsumsi: {rm['kw']} kW<br>"
                        f"Load: {rm['load_pct']}%<br>"
                        f"Suhu: {rm['temp']}°C | RH: {rm['rh']}%<extra></extra>"
                    )
                ))
        fig_lini.update_layout(
            **PLOT_LAYOUT,
            margin=dict(l=0, r=0, t=10, b=40),
            height=280,
            barmode="stack",
            xaxis={**_AX, "title":"Konsumsi (kW)"},
            showlegend=True,
            legend=dict(orientation="h", y=-0.18, x=0,
                        font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
            yaxis=dict(gridcolor="#1e2d3d", zeroline=False,
                       tickfont=dict(size=10), autorange="reversed"),
        )
        st.markdown('<div class="chart-card"><div class="chart-title">Konsumsi per Lini – Diurutkan Supply Air Flow Tertinggi</div><div class="chart-subtitle">AHU dengan flow terbesar di atas · klik legend untuk filter ruangan</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_lini, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_flow:
        # Supply Air Flow gauge bars per AHU
        ahu_names_sorted  = [a for a, _ in sorted_ahus]
        ahu_flows_sorted  = [d["flow"]  for _, d in sorted_ahus]
        ahu_totalkw       = [sum(r["kw"] for r in d["rooms"]) for _, d in sorted_ahus]
        flow_colors = [ACCENT_CYAN, ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE]

        fig_flow = make_subplots(rows=1, cols=1)
        fig_flow.add_trace(go.Bar(
            name="Supply Air Flow",
            x=ahu_names_sorted,
            y=ahu_flows_sorted,
            marker_color=flow_colors,
            text=[f"{f:,} CMH" for f in ahu_flows_sorted],
            textposition="outside",
            textfont=dict(size=10, color="#8aa8c8"),
            hovertemplate="<b>%{x}</b><br>Air Flow: %{y:,} CMH<extra></extra>"
        ))
        # Overlay line for total kW
        fig_flow.add_trace(go.Scatter(
            name="Total kW",
            x=ahu_names_sorted,
            y=ahu_totalkw,
            mode="lines+markers+text",
            yaxis="y2",
            line=dict(color=ACCENT_AMBER, width=2),
            marker=dict(size=7, color=ACCENT_AMBER),
            text=[f"{k} kW" for k in ahu_totalkw],
            textposition="top center",
            textfont=dict(size=10, color=ACCENT_AMBER),
            hovertemplate="<b>%{x}</b><br>Total kW: %{y}<extra></extra>"
        ))
        fig_flow.update_layout(
            **PLOT_LAYOUT,
            margin=dict(l=0, r=40, t=30, b=10),
            height=280,
            xaxis={**_AX},
            yaxis=dict(gridcolor="#1e2d3d", zeroline=False,
                       tickfont=dict(size=10), title="Air Flow (CMH)"),
            yaxis2=dict(overlaying="y", side="right", showgrid=False,
                        tickfont=dict(size=10, color=ACCENT_AMBER),
                        title=dict(text="kW", font=dict(color=ACCENT_AMBER))),
            showlegend=True,
            legend=dict(orientation="h", y=1.08, x=0,
                        font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
            barmode="group",
        )
        st.markdown('<div class="chart-card"><div class="chart-title">Supply Air Flow per AHU</div><div class="chart-subtitle">Volume udara (CMH) vs total konsumsi (kW)</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_flow, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

        # Summary table: AHU ranked by airflow
        flow_df_data = {
            "AHU":      ahu_names_sorted,
            "Flow (CMH)":[f"{f:,}" for f in ahu_flows_sorted],
            "kW Total": ahu_totalkw,
            "SP (°C)":  [round(d["sp"],1) for _,d in sorted_ahus],
            "Ruangan":  [len(d["rooms"]) for _,d in sorted_ahus],
        }
        st.dataframe(pd.DataFrame(flow_df_data), use_container_width=True, hide_index=True,
            column_config={
                "AHU":       st.column_config.TextColumn(width="small"),
                "Flow (CMH)":st.column_config.TextColumn(width="medium"),
                "kW Total":  st.column_config.NumberColumn(width="small"),
                "SP (°C)":   st.column_config.NumberColumn(width="small"),
                "Ruangan":   st.column_config.NumberColumn(width="small"),
            })

# ─────────────────────────────── TAB 3 ───────────────────────────────────────
with tab3:
    st.markdown('<div class="section-header">Analisis Sensitivitas & Prediksi</div>', unsafe_allow_html=True)

    col_pred1, col_pred2 = st.columns([2, 1], gap="medium")

    with col_pred1:
        # Sensitivity: suhu luar vs konsumsi
        temp_range = np.linspace(28, 38, 30)
        pred_vals = [320 + (T - sp_chiller) * 8 + (24 - ahu_avg) * 12 + outside_rh * 0.8
                     for T in temp_range]
        pred_cop  = [max(2.8, 5.2 - (T - sp_chiller) * 0.12) for T in temp_range]
        pred_kw   = [p / c for p, c in zip(pred_vals, pred_cop)]

        fig_sens = go.Figure()
        fig_sens.add_trace(go.Scatter(
            x=temp_range, y=pred_kw, name="Prediksi kW",
            mode="lines", line=dict(color=ACCENT_BLUE, width=2),
            fill="tozeroy", fillcolor="rgba(59,130,246,0.08)"
        ))
        fig_sens.add_vline(x=outside_temp, line_color=ACCENT_AMBER, line_dash="dash",
            annotation_text=f"  Saat ini: {outside_temp}°C", annotation_font_color=ACCENT_AMBER)
        fig_sens.update_layout(**PLOT_LAYOUT, margin=_M, legend=_L, height=240,
            xaxis={**_AX}, yaxis={**_AX})
        st.markdown('<div class="chart-card"><div class="chart-title">Sensitivitas: Suhu Luar vs Konsumsi Chiller</div><div class="chart-subtitle">Dampak perubahan suhu ambient terhadap prediksi kW</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_sens, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

        # Setpoint AHU vs saving
        sp_range = np.linspace(20, 26, 20)
        saving   = [(s - ahu_avg) * 12 * (-1) for s in sp_range]
        fig_sp = go.Figure()
        fig_sp.add_trace(go.Bar(
            x=[f"{s:.1f}°C" for s in sp_range], y=saving,
            marker_color=[ACCENT_GREEN if s >= 0 else ACCENT_RED for s in saving],
            hovertemplate="Setpoint: %{x}<br>Saving: %{y:.1f} kW<extra></extra>"
        ))
        fig_sp.update_layout(**PLOT_LAYOUT, margin=_M, legend=_L, height=200,
            xaxis={**_AX}, yaxis={**_AX})
        st.markdown('<div class="chart-card"><div class="chart-title">Potensi Penghematan: Setpoint AHU</div><div class="chart-subtitle">Perubahan setpoint AHU vs estimasi penghematan energi</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_sp, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_pred2:
        # Gauge – COP
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=cop_est,
            delta={"reference": 3.8, "valueformat": ".2f"},
            title={"text": "COP Chiller", "font": {"color": "#8aa8c8", "size": 13}},
            number={"font": {"color": "#e8f0f8", "family": "DM Mono"}, "valueformat": ".2f"},
            gauge={
                "axis": {"range": [2, 6], "tickcolor": "#4a6a8a", "tickfont": {"size": 9}},
                "bar": {"color": ACCENT_CYAN, "thickness": 0.25},
                "bgcolor": "#0f1923",
                "bordercolor": "#1e2d3d",
                "steps": [
                    {"range": [2, 3],   "color": "#3d1414"},
                    {"range": [3, 4.5], "color": "#0d3326"},
                    {"range": [4.5, 6], "color": "#0c2a18"},
                ],
                "threshold": {"line": {"color": ACCENT_GREEN, "width": 2}, "value": 4.5}
            }
        ))
        fig_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font_color="#8aa8c8",
            height=220, margin=dict(l=20,r=20,t=40,b=20)
        )
        st.markdown('<div class="chart-card"><div class="chart-title">COP Real-time</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

        # Summary prediction table
        pred_data = {
            "Parameter": ["Cooling Load", "Power Chiller", "COP", "∆T Luar-SP", "Avg AHU SP"],
            "Nilai":     [f"{load_est:.0f} kW", f"{power_est:.0f} kW",
                          str(cop_est), f"{delta_T:.1f}°C", f"{ahu_avg:.1f}°C"],
        }
        df_pred = pd.DataFrame(pred_data)
        st.markdown('<div class="chart-card"><div class="chart-title">Ringkasan Parameter</div>', unsafe_allow_html=True)
        st.dataframe(
            df_pred, use_container_width=True, hide_index=True,
            column_config={
                "Parameter": st.column_config.TextColumn("Parameter", width="medium"),
                "Nilai":     st.column_config.TextColumn("Nilai",     width="small"),
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # Rekomendasi
        recs = []
        if cop_est < 3.5:
            recs.append(("🔴", "COP rendah — cek kondensor & evaporator"))
        if delta_T > 26:
            recs.append(("🟡", "∆T tinggi — pertimbangkan naikkan setpoint AHU"))
        if power_est > 370:
            recs.append(("🔴", "Konsumsi tinggi — evaluasi jadwal produksi"))
        if not recs:
            recs.append(("🟢", "Semua parameter dalam kondisi optimal"))

        st.markdown('<div class="chart-card"><div class="chart-title">Rekomendasi Operasional</div>', unsafe_allow_html=True)
        for icon, msg in recs:
            st.markdown(f"<div style='font-size:12px;color:#c8d8e8;padding:6px 0;border-bottom:1px solid #1e2d3d;'>{icon} {msg}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ─ Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='margin-top:24px; padding-top:16px; border-top:1px solid #1e2d3d;
     font-size:11px; color:#2a4a6a; text-align:center; letter-spacing:0.05em;'>
  ChillerPred v1.0 · Sistem Prediksi Konsumsi Energi Berbasis AHU & Produksi Ruangan
</div>""", unsafe_allow_html=True)
