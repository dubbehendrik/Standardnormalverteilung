import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ========== Seiteneinstellungen ==========
st.set_page_config(page_title="Standardnormalverteilung Bereichswahrscheinlichkeit", layout="centered")

# Logo (optional einfügen)
st.image("HSE-Logo.jpg", width=1000)

# ========== Titel ==========
st.title("Berechnung der Bereichswahrscheinlichkeit unter der Standardnormalverteilung")

# ========== Beschreibung und Formeln ==========
st.markdown("""
Die App berechnet die **Bereichswahrscheinlichkeit** unter der Standardnormalverteilung (SNV).  
Dabei wird die Fläche unter der Dichtefunktion \\( \\varphi_z(z) \\) zwischen zwei Grenzen \\( a \\) und \\( b \\) bestimmt:

\\[
\\varphi_z(z) = \\frac{1}{\\sqrt{2\\pi}} \\cdot e^{-\\frac{z^2}{2}}
\\]

Die zugehörige **Verteilungsfunktion** (Stammfunktion der Dichte) lautet:

\\[
\\Phi_z(z) = \\int_{-\\infty}^{z} \\varphi_z(u) \\; du
\\]

Die Wahrscheinlichkeit im Intervall \\( [a, b] \\) ergibt sich dann zu:

\\[
P(a \\leq Z \\leq b) = \\Phi_z(b) - \\Phi_z(a)
\\]

Nutze den Schieberegler oder die Eingabefelder, um die Grenzen \\( a \\) und \\( b \\) zu setzen.
""")

# ========== Vorbereitungen ==========
randWert = 6
dSchritt = 0.001
x = np.arange(-randWert, randWert, dSchritt)
phi = (2 * np.pi) ** -0.5 * np.exp(-0.5 * x**2)

# Approximierte Verteilungsfunktion
cumprob = np.cumsum(phi) * dSchritt
Phi = dict(zip(x, cumprob))

# Standardwerte
if "a" not in st.session_state: st.session_state.a = -1.96
if "b" not in st.session_state: st.session_state.b = 1.96

# ========== Plots ==========
a = st.session_state.a
b = st.session_state.b

# Intervall für Integration
a_idx = np.searchsorted(x, a)
b_idx = np.searchsorted(x, b)
z_slice = x[a_idx:b_idx]
p_slice = phi[a_idx:b_idx]

# Wahrscheinlichkeit berechnen
prob = np.trapz(p_slice, x=z_slice)
phi_a = np.trapz(phi[:a_idx], x=x[:a_idx])
phi_b = np.trapz(phi[:b_idx], x=x[:b_idx])

col1, col2 = st.columns(2)

# Plot 1: Dichtefunktion
with col1:
    fig1, ax1 = plt.subplots()
    ax1.plot(x, phi, color="blue", lw=2)
    ax1.fill_between(x, phi, 0, where=(x >= a) & (x <= b), color="green", alpha=0.3)
    ax1.set_xlabel("z")
    ax1.set_ylabel(r"$\varphi_{z}(z)$")
    ax1.set_title("Dichtefunktion")
    ax1.axvline(a, color="gray", linestyle="--")
    ax1.axvline(b, color="gray", linestyle="--")
    st.pyplot(fig1)
    st.latex(f"P({a:.2f} \\leq Z \\leq {b:.2f}) = {prob:.4f}")

# Plot 2: Verteilungsfunktion
with col2:
    fig2, ax2 = plt.subplots()
    ax2.plot(x, cumprob, color="blue", lw=2)
    ax2.set_ylim(-0.05, 1.05)
    ax2.set_xlabel("z")
    ax2.set_ylabel(r"$\Phi_{z}(z)$")
    ax2.set_title("Verteilungsfunktion")
    ax2.axvline(a, color="green", linestyle="--")
    ax2.axvline(b, color="green", linestyle="--")
    ax2.plot(a, phi_a, 'go')
    ax2.plot(b, phi_b, 'go')
    ax2.text(a, phi_a + 0.03, f"{phi_a:.4f}", ha='center')
    ax2.text(b, phi_b + 0.03, f"{phi_b:.4f}", ha='center')
    st.pyplot(fig2)
    st.latex(f"\\Phi({b:.2f}) - \\Phi({a:.2f}) = {phi_b:.4f} - {phi_a:.4f} = {prob:.4f}")

# ========== Interaktiver Bereichs-Slider ==========
st.subheader("Intervallauswahl")

a_new, b_new = st.slider("Wähle den Bereich [a, b]", min_value=-6.0, max_value=6.0, value=(a, b), step=0.01)

# Wenn Slider verändert wurde → Session aktualisieren
if (a_new != a) or (b_new != b):
    st.session_state.a = a_new
    st.session_state.b = b_new

# ========== Eingabefelder für genaue Werte ==========
col_a, col_b = st.columns(2)
with col_a:
    a_input = st.number_input("Untere Grenze a (genau)", value=a_new, step=0.01, key="input_a")
with col_b:
    b_input = st.number_input("Obere Grenze b (genau)", value=b_new, step=0.01, key="input_b")

# Synchronisation: wenn Eingabe geändert → Session-State + Slider updaten
if a_input != a_new or b_input != b_new:
    st.session_state.a = a_input
    st.session_state.b = b_input

# ========== Bug Report / Feature Request ==========
st.markdown("---")
st.markdown("### Fehler gefunden oder Idee?")
st.markdown(
    "👉 [Bug melden](https://github.com/dein-repo/issues/new?template=bug_report.md) &nbsp;&nbsp;&nbsp;"
    "🚀 [Feature vorschlagen](https://github.com/dein-repo/issues/new?template=feature_request.md)"
)

# ========== Disclaimer ==========
st.markdown("---")
st.markdown("""
<div style='font-size: 0.9em; color: gray'>
Diese Anwendung dient ausschließlich zu Lehr- und Demonstrationszwecken.  
Alle Berechnungen erfolgen ohne Gewähr. Keine kommerzielle Nutzung erlaubt.
</div>
""", unsafe_allow_html=True)
