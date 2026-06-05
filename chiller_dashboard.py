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
    xaxis=dict(gridcolor="#1e2d3d", zeroline=False, tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#1e2d3d", zeroline=False, tickfont=dict(size=10)),
    hovermode="x unified",
)
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

def metric_card(label, value, unit, delta=None, accent=ACCENT_BLUE):
    delta_html = ""
    if delta:
        cls = "delta-up" if delta > 0 else "delta-down"
        arrow = "▲" if delta > 0 else "▼"
        delta_html = f'<div class="metric-delta {cls}">{arrow} {abs(delta):.1f}% vs kemarin</div>'
    st.markdown(f"""
    <div class="metric-card" style="--accent:{accent}">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>
      {delta_html}
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
delta_T  = outside_temp - sp_chiller
ahu_avg  = (sp_ahu1 + sp_ahu2 + sp_ahu3 + sp_mau) / 4
load_est = 320 + delta_T * 8 + (24 - ahu_avg) * 12 + outside_rh * 0.8
cop_est  = round(max(2.8, 5.2 - delta_T * 0.12), 2)
power_est = round(load_est / cop_est, 1)

np.random.seed(42)
t, p_chiller5 = gen_time_series(base=160, noise=18, trend=-10)
_, p_chiller6  = gen_time_series(base=155, noise=16, trend= 5)
_, p_total     = gen_time_series(base=315, noise=28, trend=-5)
_, p_pred      = gen_time_series(base=power_est, noise=8, trend=-3)

rooms = {
    "Filling Room A": {"ahu":"AHU-1","load_pct":88,"temp":22.1,"status":"active","kw":84},
    "Filling Room B": {"ahu":"AHU-1","load_pct":72,"temp":22.4,"status":"active","kw":68},
    "Granulasi":      {"ahu":"AHU-2","load_pct":95,"temp":21.8,"status":"critical","kw":102},
    "Coating":        {"ahu":"AHU-2","load_pct":60,"temp":22.9,"status":"standby","kw":58},
    "QC Lab":         {"ahu":"AHU-3","load_pct":45,"temp":23.1,"status":"active","kw":41},
    "Blending":       {"ahu":"MAU",  "load_pct":30,"temp":23.5,"status":"idle","kw":24},
    "Packaging":      {"ahu":"MAU",  "load_pct":55,"temp":22.8,"status":"active","kw":49},
    "Warehouse":      {"ahu":"AHU-3","load_pct":20,"temp":24.2,"status":"idle","kw":16},
}

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
c1, c2, c3, c4, c5 = st.columns(5)
with c1: metric_card("Prediksi Konsumsi", f"{power_est:.0f}", "kW",   delta=2.3,  accent=ACCENT_BLUE)
with c2: metric_card("COP Chiller",       f"{cop_est}",       "",      delta=-0.8, accent=ACCENT_CYAN)
with c3: metric_card("Total Cooling Load",f"{load_est:.0f}",  "kW",   delta=4.1,  accent=ACCENT_AMBER)
with c4: metric_card("Suhu Luar",         f"{outside_temp}", "°C",   accent=ACCENT_RED)
with c5: metric_card("Setpoint Chiller",  f"{sp_chiller}",   "°C",   accent=ACCENT_GREEN)

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
            yaxis_title="kW", xaxis_title="Waktu")
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
        yaxis_title="kWh", xaxis_title="Waktu")
    st.markdown('<div class="chart-card"><div class="chart-title">Energi Kumulatif</div><div class="chart-subtitle">Total akumulasi energi hari ini (kWh)</div>', unsafe_allow_html=True)
    st.plotly_chart(fig_energy, use_container_width=True, config={"displayModeBar":False})
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────── TAB 2 ───────────────────────────────────────
with tab2:
    st.markdown('<div class="section-header">Status Ruangan & AHU</div>', unsafe_allow_html=True)

    cols = st.columns(4, gap="medium")
    for idx, (room, info) in enumerate(rooms.items()):
        col = cols[idx % 4]
        with col:
            badge_cls   = badge_map[info["status"]]
            badge_lbl   = badge_label[info["status"]]
            bar_color   = {"active":ACCENT_BLUE,"standby":ACCENT_GREEN,
                           "idle":"#4a6a8a","critical":ACCENT_RED}[info["status"]]
            load_pct    = info["load_pct"]
            st.markdown(f"""
            <div class="metric-card" style="--accent:{bar_color}; margin-bottom:12px;">
              <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
                <div style="font-size:13px; font-weight:500; color:#c8d8e8; line-height:1.3;">{room}</div>
                <span class="room-badge {badge_cls}">{badge_lbl}</span>
              </div>
              <div style="font-size:11px; color:#4a6a8a; margin-bottom:6px;">{info['ahu']} · {info['temp']}°C</div>
              <div style="background:#0f1923; border-radius:4px; height:6px; margin-bottom:8px;">
                <div style="background:{bar_color}; width:{load_pct}%; height:100%; border-radius:4px;"></div>
              </div>
              <div style="display:flex; justify-content:space-between; font-size:11px; color:#6a8aaa;">
                <span>Load: {load_pct}%</span>
                <span style="font-family:'DM Mono',monospace; color:#c8d8e8;">{info['kw']} kW</span>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Matriks AHU vs Ruangan</div>', unsafe_allow_html=True)

    ahu_groups = {}
    for room, info in rooms.items():
        ahu_groups.setdefault(info["ahu"], []).append((room, info["kw"], info["load_pct"]))

    ahu_names = list(ahu_groups.keys())
    ahu_totals = [sum(x[1] for x in v) for v in ahu_groups.values()]
    ahu_sp = [sp_ahu1, sp_ahu2, sp_ahu3, sp_mau]

    fig_ahu = go.Figure()
    for i, (ahu, grp) in enumerate(ahu_groups.items()):
        for room, kw, lp in grp:
            fig_ahu.add_trace(go.Bar(
                name=room, x=[ahu], y=[kw],
                marker_color=colors_donut[list(rooms.keys()).index(room)],
                hovertemplate=f"<b>{room}</b><br>{kw} kW ({lp}% load)<extra></extra>"
            ))
    fig_ahu.update_layout(**PLOT_LAYOUT, margin=_M, height=260,
        barmode="stack", yaxis_title="kW",
        showlegend=True, legend=dict(
            orientation="h", y=-0.2, x=0,
            font=dict(size=10), bgcolor="rgba(0,0,0,0)"
        ))
    st.markdown('<div class="chart-card"><div class="chart-title">Konsumsi per AHU (Stacked)</div><div class="chart-subtitle">Distribusi beban ruangan per unit AHU</div>', unsafe_allow_html=True)
    st.plotly_chart(fig_ahu, use_container_width=True, config={"displayModeBar":False})
    st.markdown("</div>", unsafe_allow_html=True)

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
            xaxis_title="Suhu Luar (°C)", yaxis_title="Prediksi Konsumsi (kW)")
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
            xaxis_title="Setpoint AHU (°C)", yaxis_title="Saving / Tambahan (kW)")
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
