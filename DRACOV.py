import streamlit as st
import math

st.set_page_config(page_title="DRACOV - Diabetic Retinopathy Calculator", layout="centered")

def snellen_to_logmar(x: float) -> float:
    if x <= 0:
        return 2.0
    return -math.log10(x)

def logmar_to_etdrs(x: float) -> float:
    return 85 - 50*x

def interpret_av_input(x: str) -> float:
    y = x.strip().lower()
    if y in ["cuenta dedos", "cd", "count fingers"]:
        return 0.01
    elif y in ["movimiento de manos", "mm", "hand motion"]:
        return 0.005
    try:
        a, b = y.split('/')
        return float(a) / float(b)
    except:
        return 0.0

def clasificar_hta(a: float, b: float) -> str:
    if a <= 0 or b <= 0:
        return "No válido"
    if a > 180 or b > 120:
        return "Crisis HTA"
    elif a >= 140 or b >= 90:
        return "HTA Estadio 2"
    elif (130 <= a <= 139) or (80 <= b <= 89):
        return "HTA Estadio 1"
    elif (120 <= a <= 129) and (b < 80):
        return "Elevada"
    else:
        return "Normal"

def calcular_riesgo_sangrado(a: int, b: int, c: float, d: str, e: str, f: str) -> float:
    g = 0.1
    g += 0.004 * max(0, a - 50)
    g += 0.003 * max(0, b - 10)
    g += 0.02  * max(0, c - 7)
    if d == "CKD 1":
        g += 0.01
    elif d == "CKD 2":
        g += 0.02
    elif d == "CKD 3":
        g += 0.03
    elif d == "CKD 4":
        g += 0.06
    elif d == "CKD 5":
        g += 0.10
    if "traccional" in e.lower():
        g += 0.05
    if "mixto" in e.lower():
        g += 0.07
    if "off" in e.lower():
        g += 0.05
    if f == "Elevada":
        g += 0.02
    elif f == "HTA Estadio 1":
        g += 0.05
    elif f == "HTA Estadio 2":
        g += 0.08
    elif f == "Crisis HTA":
        g += 0.12
    return min(max(g, 0), 1)

def calcular_riesgo_reintervencion(a: int, b: int, c: float, d: str, e: str, f: str) -> float:
    g = 0.05
    g += 0.002 * max(0, a - 50)
    g += 0.002 * max(0, b - 10)
    g += 0.015 * max(0, c - 7)
    if d == "CKD 1":
        g += 0.005
    elif d == "CKD 2":
        g += 0.01
    elif d == "CKD 3":
        g += 0.02
    elif d == "CKD 4":
        g += 0.04
    elif d == "CKD 5":
        g += 0.08
    if "traccional" in e.lower():
        g += 0.04
    if "mixto" in e.lower():
        g += 0.06
    if "off" in e.lower():
        g += 0.04
    if f == "Elevada":
        g += 0.02
    elif f == "HTA Estadio 1":
        g += 0.04
    elif f == "HTA Estadio 2":
        g += 0.07
    elif f == "Crisis HTA":
        g += 0.10
    return min(max(g, 0), 1)

def calcular_prob_mejoria_visual(a: float, b: str, c: str) -> dict:
    if a <= 0.05:
        x = 0.4
    elif a <= 0.1:
        x = 0.5
    elif a <= 0.5:
        x = 0.6
    else:
        x = 0.7
    if "traccional" in b.lower() or "mixto" in b.lower():
        x -= 0.05
    if "off" in b.lower():
        x -= 0.1
    if c == "HTA Estadio 1":
        x -= 0.03
    elif c == "HTA Estadio 2":
        x -= 0.05
    elif c == "Crisis HTA":
        x -= 0.1
    x = min(max(x, 0), 1)
    y = x * 0.8
    z = x * 0.5
    return {"≥1 línea": x, "≥2 líneas": min(max(y, 0), 1), "≥3 líneas": min(max(z, 0), 1)}

def calcular_prob_mejoria_visual_con_antiVEGF(a: float, b: str, c: str) -> dict:
    d = calcular_prob_mejoria_visual(a, b, c)
    e = {}
    for k, v in d.items():
        w = v + 0.08
        e[k] = min(max(w, 0), 1)
    return e

def recomendar_terapia_adicional(x: float) -> str:
    if x > 0.6:
        return "**Riesgo muy alto de sangrado**.\n- Recomendación: **PRP preoperatoria** (si tiempo disponible) y/o **anti-VEGF preqx** (Protocol S indica reducción de neovasos).\n- Optimizar control de HTA y glucemia antes de cirugía."
    elif x > 0.3:
        return "**Riesgo moderado de sangrado**.\n- Podría ser útil **PRP parcial** o **dosis de anti-VEGF** preqx según hallazgos y tiempo de espera.\n- Control estricto de factores sistémicos."
    else:
        return "**Riesgo bajo de sangrado**.\n- Cirugía programada con medidas estándar.\n- La PRP o anti-VEGF se pueden reservar según hallazgos intraoperatorios."

def calcular_prob_tamponade(a: int, b: int, c: float, d: str, e: str, f: str, g: float) -> dict:
    h = {"Solución (BSS)": 0.10,"Aire": 0.15,"SF6": 0.40,"C3F8": 0.25,"Silicón": 0.10}
    if "traccional" in e.lower() or "mixto" in e.lower():
        h["Silicón"] += 0.05
        h["SF6"] -= 0.03
        h["C3F8"] -= 0.02
    if "off" in e.lower():
        h["Silicón"] += 0.05
        h["SF6"] -= 0.03
        h["Aire"] -= 0.02
    if g > 0.5:
        h["Silicón"] += 0.05
        h["C3F8"] -= 0.03
        h["SF6"] -= 0.02
    if f in ["HTA Estadio 2", "Crisis HTA"]:
        h["Silicón"] += 0.03
        h["SF6"] -= 0.02
        h["C3F8"] -= 0.01
    if c > 9:
        h["Silicón"] += 0.03
        h["Aire"] -= 0.02
        h["Solución (BSS)"] -= 0.01
    for k in h:
        if h[k] < 0:
            h[k] = 0
    s = sum(h.values())
    if s > 0:
        for k in h:
            h[k] /= s
    else:
        h = {"Solución (BSS)": 0,"Aire": 0,"SF6": 0,"C3F8": 0,"Silicón": 1}
    return h

def main():
    st.title("DRACOV: Diabetic Retinopathy Advanced Calculator for Outcomes & Vision")
    st.caption("Prototipo de calculadora para estimar riesgos y pronósticos quirúrgicos en retinopatía diabética basada en evidencia.")
    st.markdown(
    """
    <div style="text-align: left; margin-top: -20px;">
        <span style="font-size: 10px; color: grey;">
            Creado por Luis Daniel García Arzate
        </span>
    </div>
    """,
    unsafe_allow_html=True
)
    st.write("**DRACOV** integra:\n- Factores sistémicos (Duración DM, HbA1c, HTA, IR).\n- Complicaciones retinianas (DR traccional/mixto, mácula ON/OFF).\n- Probabilidad de mejoría visual con/sin **anti-VEGF prequirúrgico**.\n- Estimación simplificada del **tipo de taponador** más probable.\n\n**Advertencia**: Los coeficientes son orientativos; no sustituyen un modelo estadístico validado ni el juicio clínico.")
    st.subheader("1. Factores sistémicos")
    c1, c2 = st.columns(2)
    with c1:
        A = st.number_input("Edad (años)", min_value=1, max_value=120, value=60)
        B = st.number_input("Duración de DM (años)", min_value=0, max_value=60, value=15)
        C = st.number_input("HbA1c (%)", min_value=4.0, max_value=14.0, value=8.0)
    with c2:
        P1 = st.number_input("PAS (mmHg)", min_value=0, max_value=300, value=130)
        P2 = st.number_input("PAD (mmHg)", min_value=0, max_value=200, value=85)
    F = clasificar_hta(P1, P2)
    st.write(f"**Clasificación HTA**: {F}")
    D = st.selectbox("Estadio de insuficiencia renal (CKD)",["Sin IR","CKD 1","CKD 2","CKD 3","CKD 4","CKD 5"],index=0)
    st.subheader("2. Patología ocular")
    E = st.selectbox("Desprendimiento de Retina (DR)",["Sin desprendimiento","Traccional (mácula ON)","Traccional (mácula OFF)","Mixto (mácula ON)","Mixto (mácula OFF)"],index=0)
    X = st.text_input("Agudeza Visual (ej. '20/200', 'Cuenta dedos', etc.)", value="20/200")
    v = interpret_av_input(X)
    if v == 0:
        st.warning("Formato no válido. Se usará 20/200 por defecto.")
        v = 0.1
    l = snellen_to_logmar(v)
    e = logmar_to_etdrs(l)
    st.write(f"**Snellen**: {v:.3f} | **logMAR**: {l:.2f} | **ETDRS**: {e:.1f} letras")
    if st.button("Calcular"):
        r_sang = calcular_riesgo_sangrado(A, B, C, D, E, F)
        r_reint = calcular_riesgo_reintervencion(A, B, C, D, E, F)
        p_sin = calcular_prob_mejoria_visual(v, E, F)
        p_con = calcular_prob_mejoria_visual_con_antiVEGF(v, E, F)
        reco = recomendar_terapia_adicional(r_sang)
        p_tamp = calcular_prob_tamponade(A, B, C, D, E, F, r_reint)
        st.subheader("Resultados de DRACOV")
        st.write(f"- **Riesgo de sangrado**: {r_sang*100:.1f}%")
        st.write(f"- **Riesgo de reintervención**: {r_reint*100:.1f}%")
        m1, m2 = st.columns(2)
        m1.markdown("### Sin Anti-VEGF preqx")
        m1.write(f"≥1 línea: {p_sin['≥1 línea']*100:.1f}%")
        m1.write(f"≥2 líneas: {p_sin['≥2 líneas']*100:.1f}%")
        m1.write(f"≥3 líneas: {p_sin['≥3 líneas']*100:.1f}%")
        m2.markdown("### Con Anti-VEGF preqx")
        m2.write(f"≥1 línea: {p_con['≥1 línea']*100:.1f}%")
        m2.write(f"≥2 líneas: {p_con['≥2 líneas']*100:.1f}%")
        m2.write(f"≥3 líneas: {p_con['≥3 líneas']*100:.1f}%")
        st.markdown(f"**Recomendación**:\n{reco}")
        st.subheader("Probabilidad de taponador más probable")
        for k, v2 in p_tamp.items():
            st.write(f"- {k}: {v2*100:.1f}%")
        st.info("**Nota**: Estos porcentajes son aproximaciones hipotéticas. La decisión real de usar anti-VEGF prequirúrgico (p. ej., ranibizumab, aflibercept, bevacizumab), PRP adicional o un gas/taponador específico (SF6, C3F8, silicón, etc.) debe basarse en protocolos validados, disponibilidad de tiempo, experiencia del cirujano y valoración integral de cada paciente.")
    st.write("---")
    st.subheader("Referencias")
    st.markdown("- **DRCR.net Protocol S**: *JAMA.* 2015;314(20):2137-2146")
    st.markdown("- **DRCR.net Protocol T**: *Ophthalmology.* 2015;122(10):2044-2052")
    st.markdown("- **Virgili G, et al.** Cochrane Database Syst Rev. 2022;1(1):CD008214")
    st.markdown("- **Gao L, et al.** *PLoS One.* 2019;14(1):e0210659")
    st.markdown("- **Wong TY, et al.** *Nat Rev Dis Primers.* 2016;2:16012")
    st.markdown("- **Gross JL, et al.** *Diabetes Care.* 2005;28(1):164-176")
    st.markdown("- **Wong D, et al.** *Br J Ophthalmol.* 2010;94(3):332-337")
    st.markdown("- **Bopp S, et al.** *Ophthalmologica.* 2019;241(5):267-277")

if __name__ == "__main__":
    main()
