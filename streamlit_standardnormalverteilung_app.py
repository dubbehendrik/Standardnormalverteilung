import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline, interp1d

st.set_page_config(layout="wide")

st.title("Vom Einzelstrahl zur Totalbeschichtung")

# --- Abschnitt 1: Datei Upload ---
st.subheader("1. Einzelstrahlprofil laden")

uploaded_file = st.file_uploader("Lade eine Excel-Datei hoch (Ort [mm], Schichtdicke [µm])", type=["xlsx"])

# Wenn die Datei gelöscht wird, Session State zurücksetzen
if uploaded_file is None and "df" in st.session_state:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

if uploaded_file and "df" not in st.session_state:
    df = pd.read_excel(uploaded_file)
    df = df.iloc[:, :2]  # Nur die ersten beiden Spalten verwenden
    df.columns = ['Ort_mm', 'Dicke_um']
    df = df.dropna().reset_index(drop=True)
    min_len = min(len(df['Ort_mm']), len(df['Dicke_um']))
    df = df.iloc[:min_len]
    st.session_state.df = df

# Wenn Daten vorhanden sind, geht es weiter
if "df" in st.session_state:
    df = st.session_state.df

    # Glättung unterhalb des Einzelstrahl-Plots konfigurieren
    st.markdown("**Glättung des Einzelstrahlprofils**")
    col_spline_slider, col_spline_input = st.columns([0.6, 0.4])

    # Initialisieren (nur wenn noch nicht vorhanden)
    if "spline_smoothness" not in st.session_state:
        st.session_state.spline_smoothness = 0.0
    if "spline_smoothness_input" not in st.session_state:
        st.session_state.spline_smoothness_input = 0.0

    # Synchronisationsfunktionen
    def sync_spline_slider():
        st.session_state.spline_smoothness_input = st.session_state.spline_smoothness

    def sync_spline_input():
        st.session_state.spline_smoothness = st.session_state.spline_smoothness_input

    # Darstellung
    col_spline_slider, col_spline_input = st.columns([0.6, 0.4])

    with col_spline_slider:
        st.slider("Glättungsfaktor s", min_value=0.0, max_value=20.0,
                  key="spline_smoothness", step=1.0, on_change=sync_spline_slider)

    with col_spline_input:
        st.number_input("Exakter Wert für s", min_value=0.0, max_value=20.0,
                        step=1.0, key="spline_smoothness_input", on_change=sync_spline_input)

    # Interpolation vorbereiten mit Glättung
    x_raw = df['Ort_mm'].values
    y_raw = df['Dicke_um'].values
    x_interp = np.arange(np.min(x_raw), np.max(x_raw), 1.0)
    spline = UnivariateSpline(x_raw, y_raw, s=st.session_state.spline_smoothness)
    y_interp = spline(x_interp)

    # h_max und Sb_50 berechnen
    h_max = np.max(y_interp)
    h_half = h_max / 2
    indices_half = np.where(y_interp >= h_half)[0]
    if len(indices_half) >= 2:
        sb_50 = x_interp[indices_half[-1]] - x_interp[indices_half[0]]
    else:
        sb_50 = np.nan

    # Einzelstrahlplot in 60% der Breite anzeigen
    col_plot, col_text = st.columns([0.6, 0.4])

    with col_plot:
        fig1, ax1 = plt.subplots()
        ax1.plot(x_interp, y_interp, 'k-', label='Interpoliertes Profil')
        ax1.plot(x_raw, y_raw, 'rD', label='Messpunkte')
        ax1.axhline(h_half, color='gray', linestyle='--', label=r'$0.5 \cdot h_{\mathrm{max}}$')
        if len(indices_half) >= 2:
            ax1.axvline(x_interp[indices_half[0]], color='blue', linestyle='--')
            ax1.axvline(x_interp[indices_half[-1]], color='blue', linestyle='--')
        ax1.set_xlabel('Position [mm]')
        ax1.set_ylabel('Schichtdicke [µm]')
        ax1.set_title('Einzelstrahlprofil mit Halbhöhenbreite')
        ax1.legend()
        st.pyplot(fig1)

    with col_text:
        st.latex(r"h_{\mathrm{max}} = " + f"{h_max:.2f} \\, \mu m")
        st.latex(r"Sb_{50} = " + f"{sb_50:.2f} \\, mm")


    # --- Abschnitt 2: Totalbeschichtung ---
    st.subheader("2. Übergang zur Totalbeschichtung")

    col1, col2 = st.columns(2)
    with col1:
        n_bahnen = st.number_input("Anzahl der Einzelstrahlen", min_value=1, max_value=100, value=15, key="n_bahnen")

    max_slider_value = sb_50  # Obergrenze bei ÜL = 0%
    exact_step = max((np.max(x_raw) - np.min(x_raw)) / 100, 0.01)

    if "preset_delta_y" in st.session_state:
        if "delta_y" not in st.session_state:
            st.session_state["delta_y"] = st.session_state["preset_delta_y"]
        if "delta_y_input" not in st.session_state:
            st.session_state["delta_y_input"] = st.session_state["preset_delta_y"]
        del st.session_state["preset_delta_y"]

    if "delta_y" not in st.session_state and not np.isnan(sb_50):
        st.session_state["delta_y"] = sb_50 / 2
    if "delta_y_input" not in st.session_state and not np.isnan(sb_50):
        st.session_state["delta_y_input"] = sb_50 / 2

    def sync_slider():
        st.session_state["delta_y"] = st.session_state["delta_y_input"]

    def sync_input():
        st.session_state["delta_y_input"] = st.session_state["delta_y"]

    col3, col4 = st.columns([0.6, 0.4])
    with col3:
        slider_val = st.slider("Bahnversatz Δy [mm]", min_value=0.1, max_value=float(max_slider_value),
                               value=st.session_state["delta_y"], key="delta_y", on_change=sync_input)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button(f"SET ÜL = 3 (67%)   - {sb_50/3:.2f} mm"):
                st.session_state["preset_delta_y"] = sb_50 / 3
                st.rerun()
        with col_btn2:
            if st.button(f"SET ÜL = 2 (50%)   - {sb_50/2:.2f} mm"):
                st.session_state["preset_delta_y"] = sb_50 / 2
                st.rerun()

    with col4:
        st.number_input("Exakter Bahnversatz Δy [mm]", min_value=0.1, max_value=float(max_slider_value),
                        step=exact_step, value=st.session_state["delta_y"], key="delta_y_input", on_change=sync_slider)

    delta_y = st.session_state["delta_y"]

    total_x_min = np.min(x_interp)
    total_x_max = np.max(x_interp) + (n_bahnen - 1) * delta_y
    x_total = np.arange(total_x_min, total_x_max, 1.0)
    y_total = np.zeros_like(x_total)

    for i in range(n_bahnen):
        shift = i * delta_y
        x_shifted = x_interp + shift
        y_shifted = spline(x_interp)
        y_total += interp1d(x_shifted, y_shifted, bounds_error=False, fill_value=0)(x_total)

    # h_ges automatisch bestimmen
    h_ges_auto = np.mean(y_total[y_total >= 0.95 * np.max(y_total)])
    h_max_total = float(np.max(y_total))
    h_step = h_max_total / 20

    # Initialisierung falls noch nicht vorhanden
    if "manual_h_ges" not in st.session_state:
        st.session_state.manual_h_ges = h_ges_auto
    if "manual_h_ges_input" not in st.session_state:
        st.session_state.manual_h_ges_input = h_ges_auto

    st.session_state.manual_h_ges = min(st.session_state.manual_h_ges, h_max_total)
    st.session_state.manual_h_ges_input = min(st.session_state.manual_h_ges_input, h_max_total)

    def sync_h_slider():
        st.session_state.manual_h_ges = st.session_state.manual_h_ges_input

    def sync_h_input():
        st.session_state.manual_h_ges_input = st.session_state.manual_h_ges

    auswahl = st.radio("Methode zur Ermittlung der Gesamtschichtdicke h_ges:",
                      [r"Automatisch ($y_{total} \geq 0.95 \cdot h_{max}$)", "Manuell"],
                      index=0)

    col_h1, col_h2 = st.columns([0.6, 0.4])
    with col_h1:
        st.slider(r"$h_{\mathrm{ges}}$ [µm]", min_value=0.0, max_value=h_max_total,
                  value=st.session_state.manual_h_ges,
                  key="manual_h_ges", on_change=sync_h_input, step=None)

    with col_h2:
        st.number_input("", min_value=0.0, max_value=h_max_total,
                        step=h_step, value=st.session_state.manual_h_ges,
                        key="manual_h_ges_input", on_change=sync_h_slider)

    if auswahl == "Manuell":
        h_ges = st.session_state.manual_h_ges
    else:
        h_ges = h_ges_auto

    # Plot
    col_plot2, col_text2 = st.columns([0.6, 0.4])

    with col_plot2:
        fig2, ax2 = plt.subplots()
        tab_colors = [plt.cm.get_cmap('hsv')(i / n_bahnen) for i in range(n_bahnen)]

        for i in range(n_bahnen):
            shift = i * delta_y
            x_shifted = x_interp + shift
            y_shifted = spline(x_interp)
            color = tab_colors[i]
            ax2.plot(x_shifted, y_shifted, color=color)
            if i < 2:
                x_rect = shift + x_interp[np.argmax(y_interp)] - sb_50 / 2
                ax2.add_patch(plt.Rectangle((x_rect, 0), sb_50, h_half, linewidth=0.5,
                                            edgecolor=color, facecolor=color, alpha=0.5))

        ax2.plot(x_total, y_total, 'k-', linewidth=2.5, label="Totalbeschichtung")
        ax2.axhline(h_ges, color='gray', linestyle='--', label=rf'$h_{{\mathrm{{ges}}}} = {h_ges:.2f}\,\mu m$')
        ax2.set_xlabel('Position [mm]')
        ax2.set_ylabel('Schichtdicke [µm]')
        ax2.set_title('Totalbeschichtung')
        ax2.legend(loc='upper right')
        st.pyplot(fig2)

    with col_text2:
        overl_percent = ((sb_50 - delta_y) / sb_50) * 100 if sb_50 else np.nan
        overl_dimless = sb_50 / delta_y if sb_50 else np.nan

        st.markdown(f"""
        <div style='font-family: monospace; font-size: 16px; line-height: 1.6;'>
        Überlappungsgrad ÜL [%]:&nbsp;&nbsp;&nbsp;&nbsp;{overl_percent:6.2f} %<br>
        Überlappungsgrad ÜL [-]:&nbsp;&nbsp;&nbsp;&nbsp;{overl_dimless:6.2f}<br>
        Mittlere Schichtdicke h<sub>ges</sub>:&nbsp;{h_ges:6.2f} µm
        </div>
        """, unsafe_allow_html=True)