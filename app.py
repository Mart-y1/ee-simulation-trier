"""
Enerlyse EE-Simulation Trier
Berechnung des erneuerbaren Energiebedarfs für eine klimaneutrale Region
Basiert auf dem Excel-Modell „EEnergie Trier Neu"
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import base64

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="EE-Ausbaubedarf Trier | Enerlyse SARL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# STYLING
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    .stApp { background-color: #0e1117 !important; color: #e8eaf0 !important; }
    #MainMenu { visibility: hidden; }
    footer                         { display: none; }
    [data-testid="stDecoration"]   { display: none; }

    /* Desktop: Header komplett verstecken */
    @media (min-width: 769px) {
        header[data-testid="stHeader"] { display: none; }
        [data-testid="stToolbar"]      { display: none; }
    }
    /* Mobil: Header ausblenden (Button kommt via components.html) */
    @media (max-width: 768px) {
        header[data-testid="stHeader"] { display: none; }
        [data-testid="stToolbar"] { display: none; }
        .main .block-container { padding: 0.5rem 0.6rem 2rem !important; max-width: 100% !important; }
        .tool-header { padding: 12px 14px !important; flex-direction: column; align-items: flex-start !important; }
        .tool-header-text h1 { font-size: 15px !important; }
        .tool-header-text p  { font-size: 12px !important; }
        .tool-header-logo    { display: none; }
        .kpi-value { font-size: 18px !important; }
        .kpi-card  { padding: 8px 12px !important; min-height: 64px !important; }
        .kpi-label { font-size: 11px !important; }
        section[data-testid="stSidebar"] { width: 85vw !important; min-width: 260px !important; }
    }

    .tool-header {
        background: linear-gradient(135deg, #111111 0%, #2a2a2a 100%);
        padding: 22px 30px; border-radius: 12px; margin-bottom: 24px;
        display: flex; align-items: center; justify-content: space-between;
    }
    .tool-header-text h1, .tool-header-text p { color: #ffffff !important; }
    .tool-header-text h1 { font-size: 24px; margin: 0; font-weight: 700; }
    .tool-header-text p  { margin: 4px 0 0; font-size: 14px; opacity: 0.80; }
    .tool-header-logo img { max-height: 95px; width: auto; }

    .kpi-card {
        background: #1a1f2e !important;
        border-radius: 10px; padding: 16px 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.5);
        border-left: 5px solid #4da6e0; margin-bottom: 12px; min-height: 95px;
    }
    .kpi-value { font-size: 26px; font-weight: 700; color: #e8eaf0 !important; }
    .kpi-sub   { font-size: 13px; color: #7eb8d8 !important; margin-top: 2px; }
    .kpi-label { font-size: 11px; color: #9aa5b4 !important; margin-top: 3px; }
    .kpi-card.green  { border-left-color: #2ecc71; }
    .kpi-card.yellow { border-left-color: #f39c12; }
    .kpi-card.red    { border-left-color: #e74c3c; }
    .kpi-card.blue   { border-left-color: #4da6e0; }
    .kpi-card.purple { border-left-color: #9b59b6; }
    .kpi-card.teal   { border-left-color: #1abc9c; }
    .kpi-card.orange { border-left-color: #e67e22; }

    .section-h {
        font-size: 15px; font-weight: 700; color: #c8d8e8 !important;
        border-bottom: 2px solid #4da6e0; padding-bottom: 4px; margin: 18px 0 10px;
    }

    .info-box {
        background: #0d1f2d; border: 1px solid #2e6da4; border-radius: 8px;
        padding: 10px 14px; font-size: 12px; color: #7ec8e3 !important; margin: 6px 0;
    }
    .warn-box {
        background: #1f1208; border: 1px solid #d4700d; border-radius: 8px;
        padding: 10px 14px; font-size: 12px; color: #f0a060 !important; margin: 6px 0;
    }

    section[data-testid="stSidebar"] { background: #1a1f2e !important; }
    section[data-testid="stSidebar"] label { color: #c8d8e8 !important; }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #4da6e0 !important; font-size: 11px; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.5px;
        border-top: 1px solid #2a3a4a; padding-top: 10px; margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# KONSTANTEN & BASISWERTE (aus Excel „EEnergie Trier Neu", Referenz 2024)
# ══════════════════════════════════════════════════════════════════════════════

# Energiebedarf Ist-Zustand [MWh/a]
STROM_BASIS     = 584_421.5    # Direkter Strombedarf Trier
WAERME_BASIS    = 1_711_097.0  # Wärme gesamt (Heizwärme + Brauchwasser)
VERKEHR_BASIS   = 787_500.0    # Kraftstoffenergie Verkehr

# Technologieparameter (kalibriert an Excel-Ausgaben)
# Hinweis Wirkungsgrad-Überprüfung (Quellen: Fraunhofer ISE, NREL, IEA, DOE, Stand 2024):
#   ETA_P2H:     86 % ist Stack-Wirkungsgrad/Zukunftsziel; reale Systemeffizienz (inkl. Kompression) ~70–75 %
#   ETA_BZ:      50 % konservativ; moderne PEM-BZ erreichen 55–60 % elektrisch
#   ETA_P2CH4:   71 % leicht konservativ; aktueller Konsens 70–80 %, Empfehlung 75 %
#   ETA_BHKW_EL: 38 % korrekt; Recherche bestätigt 30–40 % für Gasmotoren
#   Speicher:    Batterie-Runtrip-Verluste (~8 % bei Li-Ion, RTE ~92 %) sind im Modell nicht abgebildet
#   Alle Werte bleiben zur Konsistenz mit Excel kalibriert – Änderung würde Excel-Abgleich aufbrechen
COP_WP          = 2.8          # Wärmepumpen-Arbeitszahl
ETA_P2CH4       = 0.7138       # Power-to-CH₄ Wirkungsgrad (Recherche: 70–80 %, Empfehlung 75 %)
ETA_P2L         = 0.4558       # Power-to-Liquid Wirkungsgrad
ETA_P2H         = 0.86         # Power-to-H₂ (Elektrolyse) – Stack-Wert/Zukunftsziel; System-η real ~70–75 %
ETA_BZ          = 0.50         # Brennstoffzelle elektrisch (Recherche: 45–60 %, Empfehlung 55 %)
ETA_BHKW_EL     = 0.38         # BHKW elektrisch (P2L-Pfad) – Recherche bestätigt ✓
ETA_BHKW2_EL    = 0.35         # BHKW elektrisch (H₂- und CH₄-Pfad, aus Excel-Abgleich)
ETA_P2L_LUFT    = 0.42         # Power-to-Liquid mit CO₂ aus Luft (Grundlagen-Blatt)

# Wärme-P2X-Mix (nicht-WP-Anteil): 60 % P2CH₄, 40 % P2Liquid (aus Excel)
P2CH4_W_ANT     = 0.60         # Anteil CH₄ am P2X-Wärme-Mix
P2L_W_ANT       = 0.40

# Faktor Strom / Einheit Verkehrskraftstoff (aus Excel, Grundlagen-Blatt)
# Formel: strom = verkehr × anteil × faktor
F_BATT      = 0.3889   # E-Auto Batterie:       η_ref=0.35 / η_BEV=0.90
F_H2_BZ     = 0.8140   # H₂ Brennstoffzelle:    η_ref=0.35 / (η_BZ=0.50 × η_P2H=0.86)
# Ottomotor-Pfade: strom = kraftstoff / η_P2X (Otto-Motorwirkungsgrad = wie Referenz)
F_H2_OTTO   = 1/0.86   # P2H₂ Otto:             1 / η_P2H  = 1.1628
# P2CH4 und P2L Otto: 1/ETA_P2CH4 und 1/ETA_P2L (direkt aus Konstanten berechnet)

# EE-Technologie (kalibriert an Lastprofil-Zeitreihe)
PV_H_EFF   = 894.4   # PV effektive Volllaststunden [h/a] (aus Trier-Zeitreihe)
WIND_H_EFF = 1583.1  # Wind effektive Volllaststunden [h/a]
F_PV_KM2   = 0.010   # PV Flächenbedarf [km²/MW]
F_WIND_KM2 = 0.034   # Wind Flächenbedarf [km²/MW]

# CO₂-Emissionsfaktoren [kg CO₂/MWh]
CO2_STROM   = 380.0  # Strommix Deutschland 2024 (ca. 380 g CO₂/kWh, UBA 2024)
CO2_GAS     = 228.0  # Erdgas
CO2_KFZ     = 297.0  # Kraftstoff
CO2_PV      =  50.0  # LCA PV-Strom
CO2_WIND    =  19.0  # LCA Windstrom

# Stadtdaten
FLAECHE_KM2  = 117.13
EINWOHNER    = 107_233
EINWOHNER_REF = EINWOHNER   # Referenz Trier für Skalierung

# Monatliche Ertragsfaktoren (Summe = 1.0, aus Grundlagen-Blatt)
PV_DIST   = [0.021, 0.039, 0.073, 0.107, 0.144, 0.149, 0.152, 0.132, 0.090, 0.053, 0.024, 0.016]
WIND_DIST = [0.129, 0.104, 0.097, 0.065, 0.048, 0.052, 0.054, 0.052, 0.075, 0.091, 0.107, 0.126]
MONATE    = ["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]
DAYS_M    = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

XLS_PATH = Path(__file__).parent / "data" / "EEnergie_Trier.xlsm"

# ══════════════════════════════════════════════════════════════════════════════
# ZEITREIHEN LADEN
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner="Lastprofil-Daten werden geladen…")
def load_timeseries(xls_path_str: str):
    xls_path = Path(xls_path_str)
    if not xls_path.exists():
        return None
    try:
        import openpyxl
        wb = openpyxl.load_workbook(str(xls_path), read_only=True, keep_vba=False, data_only=True)
        # Referenz-Installationsleistung aus Eingabe Matrix (C18=PV, E18=Wind)
        ws_em = wb["Eingabe Matrix"]
        ref_pv_mw   = float(ws_em["C18"].value or 2233.9)
        ref_wind_mw = float(ws_em["E18"].value or 558.5)
        ws = wb["Lastprofile"]
        rows = []
        for row in ws.iter_rows(min_row=12, values_only=True):
            if row[6] is not None and isinstance(row[7], (int, float)):
                rows.append({
                    "ts":          row[6],
                    "strom_mw":    float(row[7]  or 0),
                    "heizw_mw":    float(row[15] or 0),
                    "wp_mw":       float(row[18] or 0),
                    "verkehr_mw":  float(row[23] or 0),
                    "pv_mw_ref":   float(row[31] or 0),   # Spalte AF: PV-Erzeugung bei Ref.-Kapazität
                    "wind_mw_ref": float(row[33] or 0),   # Spalte AH: Wind-Erzeugung bei Ref.-Kapazität
                })
        wb.close()
        df = pd.DataFrame(rows)
        df["ts"]    = pd.to_datetime(df["ts"])
        df["month"] = df["ts"].dt.month
        df["week"]  = df["ts"].dt.isocalendar().week.astype(int)
        # Kapazitätsfaktoren (0…1): echtes Erzeugungsprofil normiert auf Referenzleistung
        df["pv_cf"]   = df["pv_mw_ref"]   / ref_pv_mw   if ref_pv_mw   > 0 else 0.0
        df["wind_cf"] = df["wind_mw_ref"]  / ref_wind_mw if ref_wind_mw > 0 else 0.0
        return df
    except Exception:
        return None


df_ts = load_timeseries(str(XLS_PATH))

# ══════════════════════════════════════════════════════════════════════════════
# SPEICHER-SIMULATION (aus Zeitreihe oder synthetisch)
# ══════════════════════════════════════════════════════════════════════════════
def storage_simulation(pv_mwh_annual, wind_mwh_annual, demand_mwh_annual,
                       storage_mwh, df_ts_scaled=None, storage_mw=None):
    """
    Simuliert Speicher über das Jahr (15-min oder monatlich).
    storage_mw: maximale Lade-/Entladeleistung [MW]; None = unbegrenzt
    Gibt zurück: residualdefizit [MWh], gen_ts (monatlich), dem_ts (monatlich)
    """
    if df_ts_scaled is not None and len(df_ts_scaled) > 0:
        # 15-min Simulation mit echten Zeitreihen
        dt = 0.25  # h pro Intervall
        n  = len(df_ts_scaled)
        max_pw = storage_mw * dt if storage_mw is not None else float("inf")  # MWh pro Intervall

        # Installierte Leistung aus Jahresenergien
        pv_mw   = pv_mwh_annual   / PV_H_EFF   if PV_H_EFF   > 0 else 0.0
        wind_mw = wind_mwh_annual / WIND_H_EFF if WIND_H_EFF > 0 else 0.0
        months = df_ts_scaled["month"].values
        # Echte Kapazitätsfaktoren nutzen wenn vorhanden, sonst monatliche Näherung (Fallback)
        if "pv_cf" in df_ts_scaled.columns and "wind_cf" in df_ts_scaled.columns:
            gen_mwh = (pv_mw * df_ts_scaled["pv_cf"].values
                       + wind_mw * df_ts_scaled["wind_cf"].values) * dt
        else:
            pv_monthly   = np.array([pv_mwh_annual   * PV_DIST[m-1]   / (DAYS_M[m-1] * 96) * 4 for m in months])
            wind_monthly = np.array([wind_mwh_annual * WIND_DIST[m-1] / (DAYS_M[m-1] * 96) * 4 for m in months])
            gen_mwh = (pv_monthly + wind_monthly) * dt
        dem_mwh  = df_ts_scaled["demand_mw"].values * dt

        soc = storage_mwh * 0.50
        defizit_total = 0.0
        demand_ts_m   = np.zeros(12)
        gen_ts_m      = np.zeros(12)
        defizit_ts_m  = np.zeros(12)
        soc_end_m     = np.zeros(12)

        for i in range(n):
            m = months[i] - 1
            bilanz = gen_mwh[i] - dem_mwh[i]
            if bilanz >= 0:
                charge = min(bilanz, max_pw)
                soc = min(soc + charge, storage_mwh)
            else:
                discharge  = min(-bilanz, soc, max_pw)
                soc       -= discharge
                defizit_total += (-bilanz - discharge)
            demand_ts_m[m] += dem_mwh[i]
            gen_ts_m[m]    += gen_mwh[i]
            if bilanz < 0:
                defizit_ts_m[m] += (-bilanz - discharge)
            soc_end_m[m] = soc

        return defizit_total, gen_ts_m, demand_ts_m, defizit_ts_m, soc_end_m

    else:
        # Monatliche Näherung
        soc = storage_mwh * 0.5
        defizit_total = 0.0
        gen_m = np.array([pv_mwh_annual * PV_DIST[m] + wind_mwh_annual * WIND_DIST[m] for m in range(12)])
        dem_m = np.array([demand_mwh_annual * DAYS_M[m] / 365 for m in range(12)])
        defizit_ts_m = np.zeros(12)
        soc_end_m    = np.zeros(12)

        for m in range(12):
            max_pw_m = storage_mw * DAYS_M[m] * 24 if storage_mw is not None else float("inf")
            bilanz = gen_m[m] - dem_m[m]
            if bilanz >= 0:
                charge = min(bilanz, max_pw_m)
                soc = min(soc + charge, storage_mwh)
            else:
                discharge  = min(-bilanz, soc, max_pw_m)
                soc       -= discharge
                defizit_total += (-bilanz - discharge)
                defizit_ts_m[m] = -bilanz - discharge
            soc_end_m[m] = soc

        return defizit_total, gen_m, dem_m, defizit_ts_m, soc_end_m


# ══════════════════════════════════════════════════════════════════════════════
# SZENARIO-BERECHNUNG
# ══════════════════════════════════════════════════════════════════════════════
def compute(red, wp_ant, ch4_w_ant, p2l_w_ant,
            batt_ant, h2bz_ant, ph2_ant, ch4m_ant, pl_ant,
            pv_cap_ratio, storage_mwh, storage_mw=None,
            pop_factor=1.0, flaeche_km2=FLAECHE_KM2):
    """
    Berechnet EE-Ausbaubedarf und Speicherbedarf für das Szenario.

    Eingaben:
      red         – Energiereduzierung [0…1]
      wp_ant      – Wärmepumpen-Anteil [0…1]  (wp + ch4_w + p2l_w = 1)
      ch4_w_ant   – P2CH₄-Anteil Wärme [0…1]
      p2l_w_ant   – P2Liquid-Anteil Wärme [0…1]
      batt_ant    – E-Auto-Anteil [0…1]        (batt + h2 + synth = 1)
      h2_ant      – H₂-Anteil Verkehr [0…1]
      synth_ant   – Synthetisch-Anteil Verkehr [0…1]
      pv_cap_ratio – PV-Kapazitätsanteil [0…1]
      storage_mwh  – Speicherkapazität [MWh]
    """
    f = 1.0 - red

    # ── Energiebedarf (skaliert) ──────────────────────────────────────────────
    strom  = STROM_BASIS   * f * pop_factor
    waerme = WAERME_BASIS  * f * pop_factor
    verk   = VERKEHR_BASIS * f * pop_factor

    # ── Strom für Wärme ───────────────────────────────────────────────────────
    st_wp   = waerme * wp_ant    / COP_WP
    st_ch4w = waerme * ch4_w_ant / ETA_P2CH4
    st_p2lw = waerme * p2l_w_ant / ETA_P2L
    st_p2x  = st_ch4w + st_p2lw
    st_waerme = st_wp + st_p2x

    # ── Strom für Verkehr (5 Pfade aus Excel) ────────────────────────────────
    st_batt   = verk * batt_ant  * F_BATT           # E-Auto Batterie
    st_h2bz   = verk * h2bz_ant  * F_H2_BZ          # H₂ Brennstoffzelle
    st_ph2    = verk * ph2_ant   * F_H2_OTTO         # P2H₂ Ottomotor
    st_ch4m   = verk * ch4m_ant  / ETA_P2CH4         # P2CH₄ Ottomotor
    st_pl     = verk * pl_ant    / ETA_P2L           # P2Liquid Ottomotor
    st_verk   = st_batt + st_h2bz + st_ph2 + st_ch4m + st_pl

    # ── Gesamtbedarf (direkt, ohne Backup-Speicher-Verluste) ─────────────────
    demand = strom + st_waerme + st_verk

    # ── PV- und Wind-Leistung (Goal-Seek-Replikation) ─────────────────────────
    # EE_annual = PV_MW × PV_H_EFF + Wind_MW × WIND_H_EFF = demand
    # Wind_MW = PV_MW × (1 - pv_cap_ratio) / pv_cap_ratio
    R = (1.0 - pv_cap_ratio) / pv_cap_ratio if pv_cap_ratio > 0 else 1e-9
    pv_mw   = demand / (PV_H_EFF + R * WIND_H_EFF)
    wind_mw = pv_mw * R
    pv_mwh  = pv_mw   * PV_H_EFF
    wind_mwh = wind_mw * WIND_H_EFF
    ee_direct = pv_mwh + wind_mwh   # ≈ demand

    # ── Speicher-Simulation ────────────────────────────────────────────────────
    df_scaled = None
    if df_ts is not None:
        # Skaliere Zeitreihen-Lastprofil
        base_demand_mw = (STROM_BASIS + WAERME_BASIS / COP_WP + VERKEHR_BASIS * F_BATT) / 8760
        # Compute scaled demand per timestep from actual profiles
        df_scaled = df_ts.copy()
        # Strom direkt: skaliere proportional zu f
        st_strom_factor  = strom / (STROM_BASIS if STROM_BASIS else 1)
        st_waerme_factor = st_waerme / (WAERME_BASIS / COP_WP * (WAERME_BASIS if WAERME_BASIS else 1) / WAERME_BASIS)
        # Einfache Skalierung: Gesamtprofil × (demand_neu / demand_alt)
        # Basis-Jahreswert aus Zeitreihe: Summe(15-min Strom) × 0.25h ≈ strom_basis
        sum_strom_ts = df_ts["strom_mw"].sum() * 0.25  # MWh
        scale = demand / (sum_strom_ts * (demand / strom) if strom > 0 else demand)
        df_scaled["demand_mw"] = df_ts["strom_mw"] * (demand / (STROM_BASIS if STROM_BASIS else 1))
        # Skaliere alle auf Gesamtbedarf
        sum_ts = df_scaled["demand_mw"].sum() * 0.25
        if sum_ts > 0:
            df_scaled["demand_mw"] *= demand / sum_ts

        defizit, gen_ts, dem_ts, defizit_ts_m, soc_end_m = storage_simulation(pv_mwh, wind_mwh, demand, storage_mwh, df_scaled, storage_mw)
    else:
        defizit, gen_ts, dem_ts, defizit_ts_m, soc_end_m = storage_simulation(pv_mwh, wind_mwh, demand, storage_mwh, storage_mw=storage_mw)

    # ── Speicherbedarf für vollständige Deckung ────────────────────────────────
    def min_storage_for_coverage(coverage=0.99):
        for sp in range(0, 100_001, 500):
            d, *_ = storage_simulation(pv_mwh, wind_mwh, demand, sp, storage_mw=storage_mw)
            if d / demand < (1 - coverage):
                return sp
        return None

    sp_99 = min_storage_for_coverage(0.99)

    # ── Rückverstromung (X-to-Power): Residualdefizit → P2X-Speicher → Kraftwerk ──
    # Strom (Überschuss) → H₂/CH₄/P2L speichern → Rückverstromung bei Defizit
    # 4 Pfade aus Excel (Eingabe Matrix Z18/Z20); jeder Pfad deckt ANTEIL DES DEFIZITS:
    #   35% H₂-BZ  | 25% H₂-BHKW | 25% P2CH₄-BHKW | 15% P2L-BHKW (CO₂ aus Luft)
    # Korrekte Formel: ee_backup = Defizit × Σ(Anteil_i / eta_i)  [harmonisches Mittel]
    eta_backup = 1 / (
        0.35 / (ETA_P2H * ETA_BZ)          +  # eta = 0.430
        0.25 / (ETA_P2H * ETA_BHKW2_EL)    +  # eta = 0.301
        0.25 / (ETA_P2CH4 * ETA_BHKW2_EL)  +  # eta = 0.250
        0.15 / (ETA_P2L_LUFT * ETA_BHKW_EL)   # eta = 0.160
    )
    ee_backup   = defizit / eta_backup if eta_backup > 0 else 0.0
    demand_mit_backup = demand + ee_backup
    # PV/Wind bei vollem Backup-Bedarf
    pv_mw_full   = demand_mit_backup / (PV_H_EFF + R * WIND_H_EFF)
    wind_mw_full = pv_mw_full * R

    # ── Fläche ────────────────────────────────────────────────────────────────
    f_pv    = pv_mw_full   * F_PV_KM2
    f_wind  = wind_mw_full * F_WIND_KM2
    f_tot   = f_pv + f_wind
    f_ant   = f_tot / flaeche_km2 * 100

    # ── CO₂ ───────────────────────────────────────────────────────────────────
    co2_st_h   = strom  * CO2_STROM / 1000
    co2_w_h    = waerme * CO2_GAS   / 1000
    co2_vk_h   = verk   * CO2_KFZ   / 1000
    co2_heute  = co2_st_h + co2_w_h + co2_vk_h

    lca_w       = (pv_mwh * CO2_PV + wind_mwh * CO2_WIND) / ee_direct if ee_direct > 0 else 0
    co2_ee      = demand_mit_backup * lca_w / 1000
    co2_st_ee   = strom * lca_w / 1000
    co2_w_ee    = st_waerme * lca_w / 1000
    co2_vk_ee   = st_verk   * lca_w / 1000
    co2_red     = (co2_heute - co2_ee) / co2_heute * 100 if co2_heute > 0 else 0

    # ── Monatliche Werte ──────────────────────────────────────────────────────
    # gen_ts: entweder aus Simulation oder monatlich
    # sicherstellen dass 12 Werte vorhanden
    if len(gen_ts) == 12:
        monthly_gen  = gen_ts
        monthly_dem  = dem_ts
    else:
        monthly_gen  = np.array([pv_mwh * PV_DIST[m] + wind_mwh * WIND_DIST[m] for m in range(12)])
        monthly_dem  = np.array([demand * DAYS_M[m] / 365 for m in range(12)])

    monthly_pv   = np.array([pv_mwh   * PV_DIST[m]   for m in range(12)])
    monthly_wind = np.array([wind_mwh * WIND_DIST[m]  for m in range(12)])

    return dict(
        red=red, f=f,
        strom=strom, waerme=waerme, verk=verk,
        st_wp=st_wp, st_p2x=st_p2x, st_waerme=st_waerme,
        st_batt=st_batt, st_h2bz=st_h2bz, st_ph2=st_ph2,
        st_ch4m=st_ch4m, st_pl=st_pl, st_verk=st_verk,
        demand=demand,
        pv_mw=pv_mw, wind_mw=wind_mw, pv_mwh=pv_mwh, wind_mwh=wind_mwh,
        pv_mw_full=pv_mw_full, wind_mw_full=wind_mw_full,
        demand_mit_backup=demand_mit_backup,
        ee_direct=ee_direct, ee_backup=ee_backup,
        defizit=defizit, sp_99=sp_99, storage_mwh=storage_mwh,
        eta_backup=eta_backup,
        f_pv=f_pv, f_wind=f_wind, f_tot=f_tot, f_ant=f_ant,
        co2_st_h=co2_st_h, co2_w_h=co2_w_h, co2_vk_h=co2_vk_h, co2_heute=co2_heute,
        co2_st_ee=co2_st_ee, co2_w_ee=co2_w_ee, co2_vk_ee=co2_vk_ee, co2_ee=co2_ee,
        co2_red=co2_red, lca_w=lca_w,
        monthly_pv=monthly_pv, monthly_wind=monthly_wind,
        monthly_gen=monthly_gen, monthly_dem=monthly_dem,
        monthly_deficit=defizit_ts_m,
        monthly_soc=soc_end_m,
        wp_ant=wp_ant, ch4_w_ant=ch4_w_ant, p2l_w_ant=p2l_w_ant,
        st_ch4w=st_ch4w, st_p2lw=st_p2lw,
        batt_ant=batt_ant, h2bz_ant=h2bz_ant, ph2_ant=ph2_ant,
        ch4m_ant=ch4m_ant, pl_ant=pl_ant,
        pv_cap_ratio=pv_cap_ratio,
        df_ts_scaled=df_scaled,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR – SZENARIO-PARAMETER
# ══════════════════════════════════════════════════════════════════════════════
def _logo_html():
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        data = base64.b64encode(logo_path.read_bytes()).decode()
        return (
            f'<div style="text-align:center;padding:10px 0 6px">'
            f'<img src="data:image/png;base64,{data}" '
            f'style="max-width:160px;width:80%;background:white;'
            f'border-radius:8px;padding:6px;" />'
            f'</div>'
        )
    return (
        "<div style='text-align:center;padding:8px 0 4px'>"
        "<span style='font-size:26px'>⚡</span><br>"
        "<span style='color:#4da6e0;font-weight:700;font-size:14px'>Enerlyse SARL</span>"
        "</div>"
    )

with st.sidebar:
    st.markdown("### 🏙️ STADT")
    einwohner = st.number_input(
        "Einwohnerzahl", min_value=10_000, max_value=5_000_000,
        value=EINWOHNER, step=1_000,
        help="Alle Energiebedarfswerte skalieren proportional zur Einwohnerzahl (Referenz: Trier 107.233).",
    )
    flaeche_km2_inp = st.number_input(
        "Stadtfläche [km²]", min_value=1.0, max_value=5_000.0,
        value=float(FLAECHE_KM2), step=0.5,
        help="Stadtfläche für Berechnung des EE-Flächenanteils.",
    )
    pop_factor = einwohner / EINWOHNER_REF
    st.markdown("---")

    st.markdown("### EFFIZIENZ & REDUKTION")
    red = st.slider(
        "Energiereduktion bis 2050 [%]", -30, 50, 0, 5,
        help="Negativ = Mehrverbrauch (Bevölkerungswachstum, KI-Rechenzentren etc.) ggü. 2024. Positiv = Einsparung.",
    ) / 100

    st.markdown("### ♨️ WÄRME")
    # WP: freier Slider; P2CH4: freier Slider (max = rem_w); P2L: automatisch
    wp_pct = st.slider("Wärmepumpe [%]", 0, 100, 75, 5,
                        key="_wp", help="COP 2,8 – effizienter Stromeinsatz.")
    rem_w = 100 - wp_pct
    # Session-State vor Slider-Aufruf clampen – sonst ignoriert Streamlit den value-Parameter
    if rem_w > 0:
        if "_ch4w" not in st.session_state:
            st.session_state["_ch4w"] = min(15, rem_w)
        elif st.session_state["_ch4w"] > rem_w:
            st.session_state["_ch4w"] = rem_w
        ch4_w_pct = st.slider("Power-to-CH₄ [%]", 0, rem_w, step=5,
                               key="_ch4w", help="Erdgas-Substitut via Methanisierung (η 71 %).")
    else:
        st.session_state["_ch4w"] = 0
        ch4_w_pct = 0
        st.markdown('<div class="info-box">P2CH₄: 0 % (WP deckt 100 %)</div>',
                    unsafe_allow_html=True)
    p2l_w_pct = rem_w - ch4_w_pct
    st.markdown(
        f'<div style="background:#12191f;border:1px solid #2a3a4a;border-radius:6px;'
        f'padding:8px 12px;margin:2px 0 8px;font-size:12px;color:#9aa5b4;">'
        f'🔒 Power-to-Liquid <span style="float:right;font-size:16px;'
        f'font-weight:700;color:#e8eaf0">{p2l_w_pct} %</span>'
        f'<br><span style="font-size:10px">= 100 − WP − P2CH₄ (automatisch)</span></div>',
        unsafe_allow_html=True,
    )
    wp_ant    = wp_pct    / 100
    ch4_w_ant = ch4_w_pct / 100
    p2l_w_ant = p2l_w_pct / 100

    st.markdown("### 🚗 MOBILITÄT")
    # 4 freie Slider, P2Liquid Otto = Residual (automatisch)

    def _clamp(key, default, max_val):
        if key not in st.session_state:
            st.session_state[key] = min(default, max_val)
        elif st.session_state[key] > max_val:
            st.session_state[key] = max_val

    batt_pct = st.slider("E-Auto (Batterie) [%]", 0, 100, 60, 5, key="_batt")
    rem_m = 100 - batt_pct

    if rem_m > 0:
        _clamp("_h2bz", 15, rem_m)
        h2bz_pct = st.slider("H₂ – Brennstoffzelle [%]", 0, rem_m, step=5,
                              key="_h2bz", help="H₂-BZ: η = P2H (86 %) × BZ (50 %) = 43 %")
    else:
        st.session_state["_h2bz"] = 0; h2bz_pct = 0
    rem_m2 = rem_m - h2bz_pct

    if rem_m2 > 0:
        _clamp("_ph2", 10, rem_m2)
        ph2_pct = st.slider("P2H₂ – Ottomotor [%]", 0, rem_m2, step=5,
                             key="_ph2", help="H₂ über Elektrolyse, verbrennt im Ottomotor (η 86 %)")
    else:
        st.session_state["_ph2"] = 0; ph2_pct = 0
    rem_m3 = rem_m2 - ph2_pct

    if rem_m3 > 0:
        _clamp("_pch4m", 10, rem_m3)
        ch4m_pct = st.slider("P2CH₄ – Ottomotor [%]", 0, rem_m3, step=5,
                              key="_pch4m", help="Synthet. Methan im Ottomotor (η 71 %)")
    else:
        st.session_state["_pch4m"] = 0; ch4m_pct = 0
    pl_pct = rem_m3 - ch4m_pct

    st.markdown(
        f'<div style="background:#12191f;border:1px solid #2a3a4a;border-radius:6px;'
        f'padding:8px 12px;margin:2px 0 8px;font-size:12px;color:#9aa5b4;">'
        f'🔒 P2Liquid – Ottomotor <span style="float:right;font-size:16px;'
        f'font-weight:700;color:#e8eaf0">{pl_pct} %</span>'
        f'<br><span style="font-size:10px">= 100 − Σ übrige (automatisch, η 46 %)</span></div>',
        unsafe_allow_html=True,
    )
    batt_ant  = batt_pct  / 100
    h2bz_ant  = h2bz_pct  / 100
    ph2_ant   = ph2_pct   / 100
    ch4m_ant  = ch4m_pct  / 100
    pl_ant    = pl_pct    / 100

    st.markdown("### ☀️💨 EE-TECHNOLOGIEMIX")
    pv_cap_pct = st.slider(
        "PV-Anteil an installierter Kapazität [%]", 40, 95, 80, 5,
        help="80 % PV / 20 % Wind entspricht dem Excel-Referenzfall.",
    )
    pv_cap_ratio = pv_cap_pct / 100

    st.markdown("### 🔋 LANGZEITSPEICHER")
    storage_mwh = st.slider(
        "Speicherkapazität [MWh]", 0, 20_000, 3_000, 500,
        help="Speicherbare Energiemenge (Batterie / P2X-Tank). Max. 20.000 MWh.",
    )
    storage_mw = st.slider(
        "Speicher-Leistung [MW]", 0, 700, 300, 25,
        help="Max. Lade- / Entladeleistung. 0 = Speicher deaktiviert.",
    )
    # Leistung 0 MW = Speicher komplett deaktiviert (kein Fluss möglich)
    # None = unbegrenzt (wird intern nie genutzt, da Slider min=0)
    storage_mw_val = storage_mw  # 0 → max_pw=0 → kein Laden/Entladen

    st.markdown("---")
    st.caption("Enerlyse SARL · Trier 2024 → klimaneutral")

components.html("""
<script>
(function() {
    var doc = window.parent.document;

    // Desktop: Sidebar per injiziertem Style immer offen halten
    if (!doc.getElementById('_sb_style')) {
        var s = doc.createElement('style');
        s.id = '_sb_style';
        s.textContent =
            '@media (min-width: 769px) {' +
            '  section[data-testid="stSidebar"] { transform: none !important; min-width: 320px !important; }' +
            '  [data-testid="stSidebarCollapseButton"] { display: none !important; }' +
            '  [data-testid="stSidebarCollapsedControl"] { display: none !important; }' +
            '  button[aria-label="Collapse sidebar"] { display: none !important; }' +
            '  button[aria-label="collapse sidebar"] { display: none !important; }' +
            '}';
        doc.head.appendChild(s);
    }

    // Mobil: Floating-Button direkt in parent body injizieren
    function injectMobileBtn() {
        if (doc.getElementById('_sb_btn')) return;
        var btn = doc.createElement('button');
        btn.id = '_sb_btn';
        btn.textContent = '☰ Eingaben';
        btn.style.cssText =
            'position:fixed;top:0;left:0;right:0;z-index:99999;' +
            'background:#4da6e0;color:#fff;border:none;' +
            'padding:14px 20px;font-size:16px;font-weight:700;' +
            'width:100%;text-align:left;cursor:pointer;' +
            'box-shadow:0 2px 8px rgba(0,0,0,0.4);';
        btn.onclick = function() {
            var sb = doc.querySelector('section[data-testid="stSidebar"]');
            if (!sb) return;
            var open = sb.style.transform === 'none' || sb.style.transform === '';
            if (open) {
                sb.style.transform = 'translateX(-110%)';
                btn.textContent = '☰ Eingaben';
            } else {
                sb.style.transform = 'none';
                btn.textContent = '✕ Schließen';
            }
        };
        doc.body.appendChild(btn);
        var main = doc.querySelector('.main');
        if (main) main.style.paddingTop = '52px';
    }

    if (window.innerWidth <= 768) {
        setTimeout(injectMobileBtn, 400);
    }
})();
</script>
""", height=0)

# ══════════════════════════════════════════════════════════════════════════════
# BERECHNUNG
# ══════════════════════════════════════════════════════════════════════════════
s = compute(red, wp_ant, ch4_w_ant, p2l_w_ant,
            batt_ant, h2bz_ant, ph2_ant, ch4m_ant, pl_ant,
            pv_cap_ratio, storage_mwh, storage_mw_val,
            pop_factor=pop_factor, flaeche_km2=flaeche_km2_inp)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
red_pct = int(red * 100)
_logo_b64 = ""
_lp = Path(__file__).parent / "logo.png"
if _lp.exists():
    _logo_b64 = base64.b64encode(_lp.read_bytes()).decode()
_logo_img = (
    f'<div class="tool-header-logo">'
    f'<img src="data:image/png;base64,{_logo_b64}" /></div>'
    if _logo_b64 else ""
)
st.markdown(f"""
<div class="tool-header">
    <div class="tool-header-text">
        <h1>⚡ EE-Ausbaubedarf – Klimaneutralitätspfad</h1>
        <p>Berechnung benötigter EE-Kapazitäten &nbsp;·&nbsp;
           Strom · Wärme · Verkehr &nbsp;·&nbsp;
           {'Reduktion ' + str(red_pct) + ' % ggü. 2024' if red_pct else 'Referenzfall 2024 ohne Einsparung'}
           &nbsp;·&nbsp; PV:Wind = {pv_cap_pct}:{100-pv_cap_pct} % (Kapazität)</p>
    </div>
    {_logo_img}
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Ausbaubedarf",
    "📈 Jahresverlauf & Speicher",
    "🔀 Energiefluss",
    "🌿 Klimabilanz",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 – AUSBAUBEDARF
# ─────────────────────────────────────────────────────────────────────────────
with tab1:

    def kpi(col, val, sub, label, color="blue"):
        col.markdown(
            f'<div class="kpi-card {color}">'
            f'<div class="kpi-value">{val}</div>'
            f'<div class="kpi-sub">{sub}</div>'
            f'<div class="kpi-label">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Hauptergebnis: PV und Wind
    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, f"{s['pv_mw_full']:,.0f} MW", "PV-Leistung (inkl. Backup)",
        f"Direktbedarf: {s['pv_mw']:,.0f} MW · Fläche: {s['f_pv']:.1f} km²", "yellow")
    kpi(c2, f"{s['wind_mw_full']:,.0f} MW", "Wind-Leistung (inkl. Backup)",
        f"Direktbedarf: {s['wind_mw']:,.0f} MW · Fläche: {s['f_wind']:.1f} km²", "teal")
    kpi(c3, f"{s['sp_99']:,} MWh" if s['sp_99'] else "< 500 MWh",
        "Speicher für 99 % Deckung",
        f"Aktuell: {storage_mwh:,} MWh / {storage_mw} MW → Defizit: {s['defizit']/1000:.0f} GWh/a", "blue")
    kpi(c4, f"{s['co2_red']:.0f} %", "CO₂-Reduktion",
        f"Heute: {s['co2_heute']:,.0f} t/a → EE: {s['co2_ee']:,.0f} t/a", "green")

    c5, c6, c7, c8 = st.columns(4)
    kpi(c5, f"{s['demand']/1000:,.0f} GWh", "Strombedarf gesamt",
        f"Strom {s['strom']/1000:.0f} + WP {s['st_wp']/1000:.0f} + P2X-W {s['st_p2x']/1000:.0f} + Verk {s['st_verk']/1000:.0f} GWh", "blue")
    kpi(c6, f"{s['demand_mit_backup']/1000:,.0f} GWh", "EE-Bedarf inkl. Rückverstromung (XtP)",
        f"XtP-Verluste: {s['ee_backup']/1000:.0f} GWh/a · η={s['eta_backup']:.2f} (4 Pfade: H₂-BZ / H₂-BHKW / CH₄-BHKW / P2L-BHKW)", "orange")
    kpi(c7, f"{s['f_tot']:.1f} km²", "Gesamtflächenbedarf EE",
        f"{s['f_ant']:.0f} % der Stadtfläche ({FLAECHE_KM2} km²)", "purple")
    kpi(c8, f"{s['defizit']/s['demand']*100:.0f} %", "Restdefizit nach Speicher",
        f"{s['defizit']/1000:.0f} GWh/a ungedeckt bei {storage_mwh:,} MWh Speicher", "red")

    # ── XtP Wirkungsgrad-Info ─────────────────────────────────────────────────
    eta_h2bz    = ETA_P2H * ETA_BZ
    eta_h2bhkw  = ETA_P2H * ETA_BHKW2_EL
    eta_ch4bhkw = ETA_P2CH4 * ETA_BHKW2_EL
    eta_p2lbhkw = ETA_P2L_LUFT * ETA_BHKW_EL
    st.markdown(
        f'<div class="info-box">'
        f'<b>Rückverstromung X-to-Power (XtP) – Wirkungsgradannahmen:</b> &nbsp;'
        f'Überschussstrom wird als H₂, CH₄ oder synthetisches Liquid gespeichert und bei Bedarf rückverstromt. &nbsp;'
        f'<b>35 %</b> H₂-Brennstoffzelle: η<sub>P2H</sub> {ETA_P2H:.0%} × η<sub>BZ</sub> {ETA_BZ:.0%} '
        f'= <b>η = {eta_h2bz:.0%}</b> &nbsp;|&nbsp; '
        f'<b>25 %</b> H₂-BHKW: η<sub>P2H</sub> {ETA_P2H:.0%} × η<sub>BHKW</sub> {ETA_BHKW2_EL:.0%} '
        f'= <b>η = {eta_h2bhkw:.0%}</b> &nbsp;|&nbsp; '
        f'<b>25 %</b> CH₄-BHKW: η<sub>P2CH4</sub> {ETA_P2CH4:.0%} × η<sub>BHKW</sub> {ETA_BHKW2_EL:.0%} '
        f'= <b>η = {eta_ch4bhkw:.0%}</b> &nbsp;|&nbsp; '
        f'<b>15 %</b> P2L-BHKW (CO₂ aus Luft): η<sub>P2L</sub> {ETA_P2L_LUFT:.0%} × η<sub>BHKW</sub> {ETA_BHKW_EL:.0%} '
        f'= <b>η = {eta_p2lbhkw:.0%}</b> &nbsp;|&nbsp; '
        f'Gesamt-η (harmonisch): <b>{s["eta_backup"]:.0%}</b> &nbsp;→&nbsp; '
        f'pro 1 GWh Defizit werden <b>{1/s["eta_backup"]:.1f} GWh</b> zusätzliche EE-Erzeugung benötigt.'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Strombedarf-Anstieg ───────────────────────────────────────────────────
    strom_heute   = STROM_BASIS * pop_factor       # nur Direktstrom heute [MWh], skaliert auf Einwohnerzahl
    strom_zukunft = s["demand_mit_backup"]        # gesamter EE-Bedarf Zukunft [MWh]
    strom_delta   = strom_zukunft - strom_heute
    strom_pct     = strom_delta / strom_heute * 100
    strom_faktor  = strom_zukunft / strom_heute

    st.markdown(
        f'<div style="background:linear-gradient(90deg,#1a1225 0%,#1a1f2e 100%);'
        f'border-left:5px solid #9b59b6;border-radius:10px;padding:16px 24px;margin:8px 0 4px;">'
        f'<span style="font-size:13px;font-weight:700;color:#c8a8e8;text-transform:uppercase;'
        f'letter-spacing:0.5px;">⚡ Strombedarf-Anstieg: Heute → Klimaneutral</span><br>'
        f'<span style="font-size:12px;color:#9aa5b4;margin-top:4px;display:block;">'
        f'Direkter Strombedarf heute: <b style="color:#e8eaf0">{strom_heute/1000:,.0f} GWh/a</b> &nbsp;→&nbsp; '
        f'Gesamter EE-Bedarf Zukunft: <b style="color:#e8eaf0">{strom_zukunft/1000:,.0f} GWh/a</b>'
        f'&emsp;|&emsp;'
        f'Anstieg: <b style="color:#f39c12;font-size:18px">+{strom_delta/1000:,.0f} GWh/a</b> '
        f'(<b style="color:#f39c12">+{strom_pct:.0f} %</b>)'
        f'&emsp;·&emsp;'
        f'Faktor: <b style="color:#9b59b6;font-size:18px">×{strom_faktor:.1f}</b>'
        f'&emsp;·&emsp;'
        f'<span style="font-size:11px">inkl. Wärme, Verkehr, XtP-Rückverstromungsverluste</span>'
        f'</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    col_left, col_right = st.columns([3, 2])

    # ── Energiebedarf-Aufschlüsselung ─────────────────────────────────────────
    with col_left:
        st.markdown('<div class="section-h">Strombedarf nach Sektoren und Pfaden</div>',
                    unsafe_allow_html=True)

        # Horizontale Balken – jede Komponente eigene Zeile, Skalierung unabhängig
        # → WP-Balken bleibt konstant breit wenn WP-Anteil unverändert
        kategorien = [
            "☀️💨 PV + Wind (Erzeugung)",
            "⚡ Strom direkt",
            "🌡️ Wärme – Wärmepumpe",
            "⚗️ Wärme – P2CH₄",
            "🛢️ Wärme – P2Liquid",
            "🔋 Verkehr – E-Auto (Batterie)",
            "💧 Verkehr – H₂ Brennstoffzelle",
            "💧 Verkehr – P2H₂ Ottomotor",
            "⚙️ Verkehr – P2CH₄ Ottomotor",
            "🛢️ Verkehr – P2Liquid Ottomotor",
            "♻️ Rückverstromung X-to-Power (XtP)",
        ]
        werte_h = [
            (s["pv_mwh"] + s["wind_mwh"]) / 1000,
            s["strom"] / 1000,
            s["st_wp"] / 1000,
            s["st_ch4w"] / 1000,
            s["st_p2lw"] / 1000,
            s["st_batt"] / 1000,
            s["st_h2bz"] / 1000,
            s["st_ph2"] / 1000,
            s["st_ch4m"] / 1000,
            s["st_pl"] / 1000,
            s["ee_backup"] / 1000,
        ]
        farben_h = ["#2ecc71",
                    "#4da6e0", "#e67e22", "#f39c12", "#c0392b",
                    "#27ae60", "#1abc9c", "#16a085", "#3498db", "#2980b9",
                    "#e74c3c"]

        fig_bed = go.Figure()
        for kat, w, c in zip(kategorien, werte_h, farben_h):
            if w is None:
                continue
            fig_bed.add_trace(go.Bar(
                name=kat,
                x=[w], y=[kat],
                orientation="h",
                marker_color=c,
                text=[f"<b>{w:,.0f} GWh</b>"],
                textposition="auto",
                textfont=dict(size=11, color="#e8eaf0"),
                hovertemplate=f"{kat}: %{{x:,.0f}} GWh<extra></extra>",
            ))
        # Gesamtlinie
        fig_bed.add_vline(
            x=s["demand_mit_backup"] / 1000,
            line_dash="dash", line_color="#f39c12", line_width=1.5,
            annotation_text=f"Gesamt inkl. Backup: {s['demand_mit_backup']/1000:,.0f} GWh",
            annotation_font_color="#f39c12", annotation_position="top",
        )
        fig_bed.update_layout(
            barmode="group", height=400,
            margin=dict(l=0, r=80, t=30, b=0),
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font=dict(color="#e8eaf0"),
            showlegend=False,
            xaxis=dict(title="GWh / Jahr", gridcolor="#2a3a4a"),
            yaxis=dict(gridcolor="#2a3a4a", autorange="reversed"),
        )
        st.plotly_chart(fig_bed, use_container_width=True)

    # ── Mix-Donuts ────────────────────────────────────────────────────────────
    with col_right:
        st.markdown('<div class="section-h">Technologiemix</div>', unsafe_allow_html=True)

        fig_wm = go.Figure(go.Pie(
            labels=["Wärmepumpe", "Power-to-CH₄", "Power-to-Liquid"],
            values=[s["wp_ant"], s["ch4_w_ant"], s["p2l_w_ant"]],
            hole=0.52,
            marker_colors=["#e67e22", "#3498db", "#9b59b6"],
            textinfo="label+percent", textfont_size=11,
        ))
        fig_wm.update_layout(
            title=dict(text="Wärme-Mix", font=dict(size=12, color="#c8d8e8"), x=0.5),
            height=200, margin=dict(l=0,r=0,t=28,b=0),
            paper_bgcolor="#0e1117", font=dict(color="#e8eaf0"), showlegend=False,
        )
        st.plotly_chart(fig_wm, use_container_width=True)

        fig_vm = go.Figure(go.Pie(
            labels=["E-Auto", "H₂-BZ", "P2H₂ Otto", "P2CH₄ Otto", "P2L Otto"],
            values=[s["batt_ant"], s["h2bz_ant"], s["ph2_ant"], s["ch4m_ant"], s["pl_ant"]],
            hole=0.52,
            marker_colors=["#27ae60", "#1abc9c", "#16a085", "#3498db", "#2980b9"],
            textinfo="label+percent", textfont_size=11,
        ))
        fig_vm.update_layout(
            title=dict(text="Verkehrs-Mix", font=dict(size=12, color="#c8d8e8"), x=0.5),
            height=200, margin=dict(l=0,r=0,t=28,b=0),
            paper_bgcolor="#0e1117", font=dict(color="#e8eaf0"), showlegend=False,
        )
        st.plotly_chart(fig_vm, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 – JAHRESVERLAUF & SPEICHER
# ─────────────────────────────────────────────────────────────────────════════
with tab2:
    st.markdown('<div class="section-h">Monatliche Erzeugung vs. Bedarf</div>',
                unsafe_allow_html=True)

    fig_j = go.Figure()
    fig_j.add_trace(go.Bar(
        name="PV-Erzeugung [GWh]", x=MONATE,
        y=[v/1000 for v in s["monthly_pv"]],
        marker_color="#f1c40f",
    ))
    fig_j.add_trace(go.Bar(
        name="Wind-Erzeugung [GWh]", x=MONATE,
        y=[v/1000 for v in s["monthly_wind"]],
        marker_color="#1abc9c",
    ))
    fig_j.add_trace(go.Scatter(
        name="Bedarf gesamt [GWh]", x=MONATE,
        y=[v/1000 for v in s["monthly_dem"]],
        mode="lines+markers", line=dict(color="#e74c3c", width=2.5, dash="dash"),
        marker=dict(size=6),
    ))
    # Surplus/Defizit
    bilanz_m = [g - d for g, d in zip(s["monthly_gen"], s["monthly_dem"])]
    surplus  = [max(0,  b/1000) for b in bilanz_m]
    defizit_m = [max(0, -b/1000) for b in bilanz_m]
    fig_j.add_trace(go.Bar(
        name="Überschuss (Speicher/P2X) [GWh]", x=MONATE, y=surplus,
        marker_color="rgba(46,204,113,0.35)", base=0,
        marker_line_width=0,
    ))
    fig_j.add_trace(go.Bar(
        name="Defizit (Backup nötig) [GWh]", x=MONATE, y=[-d for d in defizit_m],
        marker_color="rgba(231,76,60,0.35)", base=0,
    ))
    fig_j.update_layout(
        barmode="relative", height=380,
        margin=dict(l=0,r=0,t=10,b=0),
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font=dict(color="#e8eaf0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(size=11, color="#e8eaf0")),
        yaxis=dict(title="GWh / Monat", gridcolor="#2a3a4a"),
        xaxis=dict(gridcolor="#2a3a4a"),
    )
    st.plotly_chart(fig_j, use_container_width=True)

    st.markdown("---")

    if df_ts is not None:
        st.markdown('<div class="section-h">15-Minuten-Lastprofil – Wochenprofil</div>',
                    unsafe_allow_html=True)
        col_s, col_i = st.columns([2, 3])
        with col_s:
            week = st.slider("Kalenderwoche", 1, 52, 1)
        with col_i:
            st.markdown(
                '<div class="info-box">Referenzjahr 2015. '
                'Strom-Lastprofil skaliert auf aktuelles Szenario.</div>',
                unsafe_allow_html=True,
            )
        df_w = df_ts[df_ts["week"] == week].copy()
        if len(df_w) > 0:
            scale = s["demand"] / (STROM_BASIS if STROM_BASIS else 1)
            m_idx = df_w["ts"].dt.month.values[0] - 1
            pv_inst_full  = s["pv_mw_full"]
            wind_inst_full = s["wind_mw_full"]

            fig_wk = go.Figure()
            fig_wk.add_trace(go.Scatter(
                x=df_w["ts"], y=df_w["strom_mw"] * scale,
                name="Lastprofil Strom [MW]",
                line=dict(color="#e74c3c", width=1.5),
            ))
            # Echtes EE-Erzeugungsprofil wenn Kapazitätsfaktoren vorhanden
            if "pv_cf" in df_w.columns and "wind_cf" in df_w.columns:
                pv_gen_w    = df_w["pv_cf"]   * pv_inst_full
                wind_gen_w  = df_w["wind_cf"] * wind_inst_full
                fig_wk.add_trace(go.Scatter(
                    x=df_w["ts"], y=pv_gen_w + wind_gen_w,
                    name="EE-Erzeugung gesamt [MW]",
                    line=dict(color="#2ecc71", width=1.5),
                    fill="tozeroy", fillcolor="rgba(46,204,113,0.08)",
                ))
                fig_wk.add_trace(go.Scatter(
                    x=df_w["ts"], y=pv_gen_w,
                    name="PV [MW]", line=dict(color="#f1c40f", width=1, dash="dot"),
                ))
                fig_wk.add_trace(go.Scatter(
                    x=df_w["ts"], y=wind_gen_w,
                    name="Wind [MW]", line=dict(color="#1abc9c", width=1, dash="dot"),
                ))
            else:
                # Fallback: monatlicher Mittelwert als Linie
                pv_mw_week   = pv_inst_full  * PV_DIST[m_idx]   * 12
                wind_mw_week = wind_inst_full * WIND_DIST[m_idx] * 12
                fig_wk.add_hline(
                    y=pv_mw_week + wind_mw_week,
                    line_color="#2ecc71", line_width=1.5, line_dash="dot",
                    annotation_text=f"⌀ EE-Erzeugung Monat {MONATE[m_idx]}: {pv_mw_week+wind_mw_week:.0f} MW",
                    annotation_font_color="#2ecc71",
                )
            fig_wk.update_layout(
                height=340, margin=dict(l=0,r=0,t=10,b=0),
                plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
                font=dict(color="#e8eaf0"),
                legend=dict(orientation="h", y=1.05, x=0, font=dict(color="#e8eaf0")),
                yaxis=dict(title="Leistung [MW]", gridcolor="#2a3a4a"),
                xaxis=dict(gridcolor="#2a3a4a"),
            )
            st.plotly_chart(fig_wk, use_container_width=True)
    else:
        st.info(f"Excel-Datei nicht gefunden: `{XLS_PATH}`")

    # ── Speicher-Simulation Monatsverlauf ────────────────────────────────────
    st.markdown('<div class="section-h">Simulierter Speicher-SOC (State of Charge) – monatlich</div>',
                unsafe_allow_html=True)

    gen_m  = s["monthly_gen"]
    dem_m  = s["monthly_dem"]
    soc_m     = list(s["monthly_soc"])
    def_m_full = list(s["monthly_deficit"] / 1000)  # GWh

    fig_soc = make_subplots(rows=2, cols=1, shared_xaxes=True,
                             subplot_titles=["Speicher-Füllstand am Monatsende (SOC)", "Monatliches Restdefizit nach Speicher"])
    fig_soc.add_trace(go.Bar(
        name="SOC [MWh]", x=MONATE, y=soc_m,
        marker_color="#4da6e0",
    ), row=1, col=1)
    fig_soc.add_hline(
        y=storage_mwh, line_dash="dash", line_color="#9aa5b4",
        annotation_text="Max. Kapazität", annotation_font_color="#9aa5b4",
        row=1, col=1,
    )
    fig_soc.add_trace(go.Bar(
        name="Restdefizit [GWh]", x=MONATE, y=def_m_full,
        marker_color="#e74c3c",
    ), row=2, col=1)
    fig_soc.update_layout(
        height=380, margin=dict(l=0,r=0,t=30,b=0),
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font=dict(color="#e8eaf0"),
        legend=dict(orientation="h", y=1.05, x=0, font=dict(color="#e8eaf0")),
    )
    for ann in fig_soc.layout.annotations:
        ann.font.color = "#e8eaf0"
    fig_soc.update_yaxes(gridcolor="#2a3a4a")
    fig_soc.update_xaxes(gridcolor="#2a3a4a")
    st.plotly_chart(fig_soc, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 – ENERGIEFLUSS (SANKEY)
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-h">Energiefluss – Vom Bedarf zur benötigten EE-Kapazität</div>',
                unsafe_allow_html=True)
    st.caption("Alle Werte in GWh Strom-Äquivalent / Jahr. Thermische Endenergie = Elektrischer Input × Wirkungsgrad.")

    # Nodes:
    # 0 PV  1 Wind  2 Strom-direkt  3 WP  4 P2X-Wärme  5 E-Mobilität  6 Alt.Kraftstoff  7 Backup-P2X
    # 8 Haushalt/GHD  9 Wärme  10 Verkehr  11 Puffer/Überschuss

    ee = s["pv_mwh"] + s["wind_mwh"]
    pv_f  = s["pv_mwh"]  / ee if ee > 0 else 0.5
    wnd_f = s["wind_mwh"] / ee if ee > 0 else 0.5

    demands = {
        2: s["strom"],
        3: s["st_wp"],
        4: s["st_p2x"],
        5: s["st_batt"],
        6: s["st_h2bz"] + s["st_ph2"] + s["st_ch4m"] + s["st_pl"],
        7: s["ee_backup"],
    }

    src, tgt, val, lnk = [], [], [], []
    pc = "rgba(241,196,15,0.45)"
    wc = "rgba(26,188,156,0.45)"

    for ni, mv in demands.items():
        if mv > 1:
            src += [0, 1]; tgt += [ni, ni]
            val += [mv*pv_f/1000, mv*wnd_f/1000]
            lnk += [pc, wc]

    # Intermediate → Sink
    link_map = {
        2: (8, "rgba(77,166,224,0.45)"),
        3: (9, "rgba(230,126,34,0.45)"),
        4: (9, "rgba(155,89,182,0.45)"),
        5: (10, "rgba(46,204,113,0.45)"),
        6: (10, "rgba(52,152,219,0.45)"),
        7: (8,  "rgba(231,76,60,0.45)"),
    }
    for ni, (sink, c) in link_map.items():
        mv = demands.get(ni, 0)
        if mv > 1:
            src.append(ni); tgt.append(sink); val.append(mv/1000); lnk.append(c)

    node_labels = [
        f"☀️ PV\n{s['pv_mw_full']:,.0f} MW",
        f"💨 Wind\n{s['wind_mw_full']:,.0f} MW",
        "⚡ Strom direkt",
        "🌡️ Wärmepumpe",
        "⚗️ P2X Wärme\n(CH₄ + P2L)",
        "🔋 E-Mobilität",
        "💧 Alt. Kraftstoff\n(H₂ + Synth.)",
        "♻️ Rückverstromung\nX-to-Power (XtP)",
        "🏭 Haushalt/\nGHD/Industrie",
        "♨️ Gebäude-\nwärme",
        "🚗 Verkehr",
    ]
    node_colors = [
        "#f1c40f", "#1abc9c",
        "#4da6e0", "#e67e22", "#9b59b6", "#2ecc71", "#3498db", "#e74c3c",
        "#4da6e0", "#e67e22", "#2ecc71",
    ]

    fig_sk = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=20, thickness=22,
            line=dict(color="#1a1f2e", width=0.5),
            label=node_labels, color=node_colors,
            hovertemplate="%{label}<br>%{value:.1f} GWh<extra></extra>",
        ),
        link=dict(
            source=src, target=tgt, value=val, color=lnk,
            hovertemplate="%{source.label} → %{target.label}<br>%{value:.1f} GWh<extra></extra>",
        ),
    ))
    fig_sk.update_layout(
        height=520, margin=dict(l=0,r=0,t=10,b=0),
        paper_bgcolor="#0e1117", font=dict(color="#e8eaf0", size=12),
    )
    st.plotly_chart(fig_sk, use_container_width=True)

    # Detailtabelle
    st.markdown('<div class="section-h">Sektorübersicht</div>', unsafe_allow_html=True)
    tbl = {
        "Pfad": [
            "Strom direkt",
            "Wärme – Wärmepumpe", "Wärme – P2CH₄", "Wärme – P2Liquid",
            "Verkehr – E-Auto (Batterie)",
            "Verkehr – H₂ Brennstoffzelle",
            "Verkehr – P2H₂ Ottomotor",
            "Verkehr – P2CH₄ Ottomotor",
            "Verkehr – P2Liquid Ottomotor",
            "Rückverstromung X-to-Power (XtP)",
            "── GESAMT ──",
        ],
        "Endenergie [GWh/a]": [
            s["strom"],
            s["waerme"]*s["wp_ant"], s["waerme"]*s["ch4_w_ant"], s["waerme"]*s["p2l_w_ant"],
            s["verk"]*s["batt_ant"], s["verk"]*s["h2bz_ant"],
            s["verk"]*s["ph2_ant"], s["verk"]*s["ch4m_ant"], s["verk"]*s["pl_ant"],
            s["defizit"],
            s["demand"],
        ],
        "Strom benötigt [GWh/a]": [
            s["strom"], s["st_wp"], s["st_ch4w"], s["st_p2lw"],
            s["st_batt"], s["st_h2bz"], s["st_ph2"], s["st_ch4m"], s["st_pl"],
            s["ee_backup"],
            s["demand_mit_backup"],
        ],
    }
    df_tbl = pd.DataFrame(tbl)
    for col in ["Endenergie [GWh/a]", "Strom benötigt [GWh/a]"]:
        df_tbl[col] = (df_tbl[col] / 1000).map("{:,.0f}".format)
    st.dataframe(df_tbl, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 – KLIMABILANZ
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    col_co2, col_fl = st.columns(2)

    with col_co2:
        st.markdown('<div class="section-h">CO₂-Emissionen: Ist vs. EE-Klimaneutral</div>',
                    unsafe_allow_html=True)
        kats = ["Strom", "Wärme", "Verkehr", "Gesamt"]
        co2_h = [s["co2_st_h"], s["co2_w_h"], s["co2_vk_h"],
                 s["co2_st_h"]+s["co2_w_h"]+s["co2_vk_h"]]
        co2_e = [s["co2_st_ee"], s["co2_w_ee"], s["co2_vk_ee"], s["co2_ee"]]

        fig_co2 = go.Figure()
        fig_co2.add_trace(go.Bar(
            name="Ist-Zustand 2024", x=kats, y=co2_h,
            marker_color="#e74c3c",
            text=[f"{v:,.0f}" for v in co2_h], textposition="outside",
        ))
        fig_co2.add_trace(go.Bar(
            name="EE-Szenario (LCA)", x=kats, y=co2_e,
            marker_color="#2ecc71",
            text=[f"{v:,.0f}" for v in co2_e], textposition="outside",
        ))
        fig_co2.update_layout(
            barmode="group", height=380,
            margin=dict(l=0,r=0,t=10,b=40),
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font=dict(color="#e8eaf0"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="left", x=0, font=dict(color="#e8eaf0")),
            yaxis=dict(title="t CO₂/a", gridcolor="#2a3a4a"),
        )
        st.plotly_chart(fig_co2, use_container_width=True)
        st.markdown(
            f'<div class="info-box">Pro-Kopf: '
            f'<b style="color:#e74c3c">{s["co2_heute"]/EINWOHNER*1000:.0f} kg heute</b> → '
            f'<b style="color:#2ecc71">{s["co2_ee"]/EINWOHNER*1000:.0f} kg EE</b> '
            f'(−{s["co2_red"]:.0f} %, {EINWOHNER:,} Einwohner)</div>',
            unsafe_allow_html=True,
        )

    with col_fl:
        st.markdown('<div class="section-h">Flächenbedarf EE-Anlagen</div>',
                    unsafe_allow_html=True)
        fig_fl = go.Figure(go.Pie(
            labels=["PV-Anlagen", "Windkraft", "Restliche Stadtfläche"],
            values=[s["f_pv"], s["f_wind"], max(0, FLAECHE_KM2 - s["f_tot"])],
            hole=0.48,
            marker_colors=["#f1c40f", "#1abc9c", "#2c3e50"],
            texttemplate="%{label}<br>%{value:.1f} km² (%{percent})",
            textfont_size=11,
        ))
        fig_fl.update_layout(
            height=320, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="#0e1117", font=dict(color="#e8eaf0"), showlegend=False,
            annotations=[dict(text=f"{s['f_tot']:.1f} km²<br>EE-Fläche",
                              x=0.5, y=0.5, font_size=12, font_color="#e8eaf0", showarrow=False)],
        )
        st.plotly_chart(fig_fl, use_container_width=True)
        st.markdown(
            f'<div class="info-box">'
            f'<b>PV:</b> {s["f_pv"]:.1f} km² ({s["pv_mw_full"]:,.0f} MW) &nbsp;|&nbsp; '
            f'<b>Wind:</b> {s["f_wind"]:.1f} km² ({s["wind_mw_full"]:,.0f} MW)<br>'
            f'<b>Gesamt:</b> {s["f_tot"]:.1f} km² = <b>{s["f_ant"]:.0f} %</b> '
            f'der Stadtfläche Trier ({FLAECHE_KM2} km²)'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown('<div class="section-h">Vollständige Kennzahlen</div>', unsafe_allow_html=True)
    rows = [
        ("Strombedarf direkt", f"{s['strom']/1000:,.0f} GWh/a"),
        ("Strom für Wärmepumpen",      f"{s['st_wp']/1000:,.0f} GWh/a"),
        ("Strom für P2X-Wärme",        f"{s['st_p2x']/1000:,.0f} GWh/a"),
        ("Strom für E-Auto (Batterie)",     f"{s['st_batt']/1000:,.0f} GWh/a"),
        ("Strom für H₂-Brennstoffzelle",   f"{s['st_h2bz']/1000:,.0f} GWh/a"),
        ("Strom für P2H₂-Ottomotor",       f"{s['st_ph2']/1000:,.0f} GWh/a"),
        ("Strom für P2CH₄-Ottomotor",      f"{s['st_ch4m']/1000:,.0f} GWh/a"),
        ("Strom für P2Liquid-Ottomotor",   f"{s['st_pl']/1000:,.0f} GWh/a"),
        ("Direktbedarf EE gesamt",     f"{s['demand']/1000:,.0f} GWh/a"),
        ("Rückverstromung XtP (EE-Mehrbedarf)", f"{s['ee_backup']/1000:,.0f} GWh/a"),
        ("EE-Bedarf inkl. XtP",        f"{s['demand_mit_backup']/1000:,.0f} GWh/a"),
        ("─── EE-Erzeugung ───", ""),
        ("PV-Leistung (benötigt)",     f"{s['pv_mw_full']:,.0f} MW"),
        ("Wind-Leistung (benötigt)",   f"{s['wind_mw_full']:,.0f} MW"),
        ("PV-Jahreserzeugung",         f"{s['pv_mwh']/1000:,.0f} GWh/a"),
        ("Wind-Jahreserzeugung",       f"{s['wind_mwh']/1000:,.0f} GWh/a"),
        ("─── Speicher ───", ""),
        ("Speicherkapazität (vorgegeben)", f"{storage_mwh:,} MWh"),
        ("Speicher-Leistung (vorgegeben)", f"{storage_mw} MW" + (" (unbegrenzt)" if storage_mw == 0 else "")),
        ("Residualdefizit nach Speicher", f"{s['defizit']/1000:,.0f} GWh/a"),
        ("Speicher für 99 % Deckung",  f"{s['sp_99']:,} MWh" if s['sp_99'] else "< 500 MWh"),
        ("─── Strombedarf-Anstieg ───", ""),
        ("Direkter Strombedarf heute (2024)",  f"{STROM_BASIS/1000:,.0f} GWh/a"),
        ("Gesamter EE-Strombedarf Zukunft",    f"{s['demand_mit_backup']/1000:,.0f} GWh/a"),
        ("Anstieg absolut",                    f"+{(s['demand_mit_backup']-STROM_BASIS)/1000:,.0f} GWh/a"),
        ("Anstieg prozentual",                 f"+{(s['demand_mit_backup']-STROM_BASIS)/STROM_BASIS*100:.0f} %"),
        ("Multiplikationsfaktor",              f"×{s['demand_mit_backup']/STROM_BASIS:.1f}"),
        ("─── Fläche & CO₂ ───", ""),
        ("Flächenbedarf PV",           f"{s['f_pv']:.2f} km²"),
        ("Flächenbedarf Wind",         f"{s['f_wind']:.2f} km²"),
        ("Flächenbedarf gesamt",       f"{s['f_tot']:.2f} km² ({s['f_ant']:.0f} % von Trier)"),
        ("CO₂ Ist-Zustand",           f"{s['co2_heute']:,.0f} t CO₂/a"),
        ("CO₂ EE-Szenario (LCA)",     f"{s['co2_ee']:,.0f} t CO₂/a"),
        ("CO₂-Reduktion",             f"{s['co2_red']:.1f} %"),
    ]
    df_kenn = pd.DataFrame(rows, columns=["Kennzahl", "Wert"])
    st.dataframe(df_kenn, use_container_width=True, hide_index=True)
