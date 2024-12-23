import streamlit as st
import math

# -------------------------------------------------------------------------
# 1) Ajuste de página (para evitar errores de Streamlit):
# -------------------------------------------------------------------------
st.set_page_config(page_title="DRACOV - Diabetic Retinopathy Calculator", layout="centered")

# -------------------------------------------------------------------------
# 2) Definiciones y funciones de soporte
# -------------------------------------------------------------------------

def snellen_to_logmar(snellen_fraction: float) -> float:
    """
    Convierte un valor de fracción Snellen (p. ej., 0.5 para 20/40) a logMAR,
    usando la fórmula aproximada: logMAR = -log10(snellen_fraction).
    """
    if snellen_fraction <= 0:
        return 2.0
    return -math.log10(snellen_fraction)

def logmar_to_etdrs(logmar: float) -> float:
    """
    Aproximación de logMAR a letras ETDRS: ETDRS ≈ 85 - 50*logmar
    """
    return 85 - 50*logmar

def interpret_av_input(av_input: str) -> float:
    """
    Interpreta la agudeza visual en formato '20/200', 'Cuenta dedos', 'mm', etc.
    Retorna un valor float (fracción Snellen aprox).
    """
    av_str = av_input.strip().lower()
    if av_str in ["cuenta dedos", "cd", "count fingers"]:
        return 0.01  # ~20/2000
    elif av_str in ["movimiento de manos", "mm", "hand motion"]:
        return 0.005  # ~20/4000
    try:
        num, den = av_str.split('/')
        return float(num) / float(den)
    except:
        return 0.0

def clasificar_hta(pas: float, pad: float) -> str:
    """
    Clasificación simple de HTA (Normal, Elevada, Estadio 1, Estadio 2, Crisis)
    """
    if pas <= 0 or pad <= 0:
        return "No válido"
    if pas > 180 or pad > 120:
        return "Crisis HTA"
    elif pas >= 140 or pad >= 90:
        return "HTA Estadio 2"
    elif (130 <= pas <= 139) or (80 <= pad <= 89):
        return "HTA Estadio 1"
    elif (120 <= pas <= 129) and (pad < 80):
        return "Elevada"
    else:
        return "Normal"

# -------------------------------------------------------------------------
# 3) Funciones de cálculo (Lógica principal)
# -------------------------------------------------------------------------

def calcular_riesgo_sangrado(
    edad: int, 
    duracion_dm: int, 
    hba1c: float,
    estadio_renal: str, 
    tipo_dr: str,
    hta_stage: str
) -> float:
    """
    Calcula riesgo de sangrado intra/postoperatorio, inspirándose en:
    - DRCR.net, Cochrane, etc.
    """
    base = 0.1
    base += 0.004 * max(0, edad - 50)
    base += 0.003 * max(0, duracion_dm - 10)
    base += 0.02  * max(0, hba1c - 7)

    if estadio_renal == "CKD 1":
        base += 0.01
    elif estadio_renal == "CKD 2":
        base += 0.02
    elif estadio_renal == "CKD 3":
        base += 0.03
    elif estadio_renal == "CKD 4":
        base += 0.06
    elif estadio_renal == "CKD 5":
        base += 0.10

    # DR traccional/mixto => más riesgo
    if "traccional" in tipo_dr.lower():
        base += 0.05
    if "mixto" in tipo_dr.lower():
        base += 0.07
    if "off" in tipo_dr.lower():
        base += 0.05

    # HTA
    if hta_stage == "Elevada":
        base += 0.02
    elif hta_stage == "HTA Estadio 1":
        base += 0.05
    elif hta_stage == "HTA Estadio 2":
        base += 0.08
    elif hta_stage == "Crisis HTA":
        base += 0.12

    return min(max(base, 0), 1)

def calcular_riesgo_reintervencion(
    edad: int, 
    duracion_dm: int, 
    hba1c: float,
    estadio_renal: str, 
    tipo_dr: str,
    hta_stage: str
) -> float:
    """
    Calcula riesgo de reintervención (segunda vitrectomía, etc.).
    """
    base = 0.05
    base += 0.002 * max(0, edad - 50)
    base += 0.002 * max(0, duracion_dm - 10)
    base += 0.015 * max(0, hba1c - 7)

    if estadio_renal == "CKD 1":
        base += 0.005
    elif estadio_renal == "CKD 2":
        base += 0.01
    elif estadio_renal == "CKD 3":
        base += 0.02
    elif estadio_renal == "CKD 4":
        base += 0.04
    elif estadio_renal == "CKD 5":
        base += 0.08

    if "traccional" in tipo_dr.lower():
        base += 0.04
    if "mixto" in tipo_dr.lower():
        base += 0.06
    if "off" in tipo_dr.lower():
        base += 0.04

    if hta_stage == "Elevada":
        base += 0.02
    elif hta_stage == "HTA Estadio 1":
        base += 0.04
    elif hta_stage == "HTA Estadio 2":
        base += 0.07
    elif hta_stage == "Crisis HTA":
        base += 0.10

    return min(max(base, 0), 1)

def calcular_prob_mejoria_visual(
    av_snellen: float, 
    tipo_dr: str, 
    hta_stage: str
) -> dict:
    """
    Prob. de ganar ≥1, ≥2, ≥3 líneas "sin" anti-VEGF preqx.
    """
    if av_snellen <= 0.05:
        base_1l = 0.4
    elif av_snellen <= 0.1:
        base_1l = 0.5
    elif av_snellen <= 0.5:
        base_1l = 0.6
    else:
        base_1l = 0.7

    # Ajustes por DR complicado y mácula OFF
    if "traccional" in tipo_dr.lower() or "mixto" in tipo_dr.lower():
        base_1l -= 0.05
    if "off" in tipo_dr.lower():
        base_1l -= 0.1

    # Ajuste por HTA
    if hta_stage == "HTA Estadio 1":
        base_1l -= 0.03
    elif hta_stage == "HTA Estadio 2":
        base_1l -= 0.05
    elif hta_stage == "Crisis HTA":
        base_1l -= 0.1

    base_1l = min(max(base_1l, 0), 1)
    base_2l = base_1l * 0.8
    base_3l = base_1l * 0.5

    return {
        "≥1 línea": base_1l,
        "≥2 líneas": min(max(base_2l, 0), 1),
        "≥3 líneas": min(max(base_3l, 0), 1),
    }

def calcular_prob_mejoria_visual_con_antiVEGF(
    av_snellen: float, 
    tipo_dr: str,
    hta_stage: str
) -> dict:
    """
    Prob. de ganar ≥1, ≥2, ≥3 líneas "con" anti-VEGF preqx.
    
    Inspirado en DRCR.net Protocol S, Protocol T, y metanálisis
    (p. ej. Gao L, 2019) que sugieren una ligera mayor ganancia 
    visual si se reduce la actividad neovascular previa a la cirugía.
    """
    # Primero, calculamos la prob "base" sin anti-VEGF
    base_dict = calcular_prob_mejoria_visual(av_snellen, tipo_dr, hta_stage)
    
    # Asumimos que el anti-VEGF preqx aumenta la prob. en un rango ~5-10%.
    # Para simplificar, añadimos +0.08 (8%) a cada escenario.
    dict_con_anti = {}
    for key, val in base_dict.items():
        mejorado = val + 0.08  # +8% de ganancia
        dict_con_anti[key] = min(max(mejorado, 0), 1)
    
    return dict_con_anti

def recomendar_terapia_adicional(riesgo_sangrado: float) -> str:
    """
    Recomienda PRP y/o anti-VEGF en función del riesgo de sangrado.
    """
    if riesgo_sangrado > 0.6:
        return (
            "**Riesgo muy alto de sangrado**.\n"
            "- Recomendación: **PRP preoperatoria** (si tiempo disponible) y/o "
            "**anti-VEGF preqx** (Protocol S indica reducción de neovasos). \n"
            "- Optimizar control de HTA y glucemia antes de cirugía."
        )
    elif riesgo_sangrado > 0.3:
        return (
            "**Riesgo moderado de sangrado**.\n"
            "- Podría ser útil **PRP parcial** o **dosis de anti-VEGF** preqx "
            "según hallazgos y tiempo de espera.\n"
            "- Control estricto de factores sistémicos."
        )
    else:
        return (
            "**Riesgo bajo de sangrado**.\n"
            "- Cirugía programada con medidas estándar.\n"
            "- La PRP o anti-VEGF se pueden reservar según hallazgos intraoperatorios."
        )

# -------------------------------------------------------------------------
# 4) DRACOV: Lógica principal (Calculadora)
# -------------------------------------------------------------------------
def main():
    st.title("DRACOV: Diabetic Retinopathy Advanced Calculator for Outcomes & Vision")
    st.caption("Prototipo de calculadora para estimar riesgos y pronósticos en retinopatía diabética basada en evidencia.")

    st.write("""
**DRACOV** integra:
- Factores sistémicos (Duración DM, HbA1c, HTA, IR).
- Complicaciones retinianas (DR traccional/mixto, mácula ON/OFF).
- Opcional: Efecto del **anti-VEGF prequirúrgico** en la probabilidad de mejoría visual.

**Advertencia**: Los coeficientes son orientativos; no sustituyen un modelo estadístico validado ni el juicio clínico.
""")

    # Entradas
    st.subheader("1. Factores sistémicos")
    colA, colB = st.columns(2)
    with colA:
        edad = st.number_input("Edad (años)", min_value=1, max_value=120, value=60)
        duracion_dm = st.number_input("Duración de DM (años)", min_value=0, max_value=60, value=15)
        hba1c = st.number_input("HbA1c (%)", min_value=4.0, max_value=14.0, value=8.0)

    with colB:
        pas = st.number_input("PAS (mmHg)", min_value=0, max_value=300, value=130)
        pad = st.number_input("PAD (mmHg)", min_value=0, max_value=200, value=85)
    
    hta_stage = clasificar_hta(pas, pad)
    st.write(f"**Clasificación HTA**: {hta_stage}")

    estadio_renal = st.selectbox(
        "Estadio de insuficiencia renal (CKD)",
        ["Sin IR", "CKD 1", "CKD 2", "CKD 3", "CKD 4", "CKD 5"],
        index=0
    )

    st.subheader("2. Patología ocular")
    tipo_dr = st.selectbox(
        "Desprendimiento de Retina (DR)",
        [
            "Sin desprendimiento",
            "Traccional (mácula ON)",
            "Traccional (mácula OFF)",
            "Mixto (mácula ON)",
            "Mixto (mácula OFF)"
        ],
        index=0
    )

    av_in = st.text_input("Agudeza Visual (ej. '20/200', 'Cuenta dedos', etc.)", value="20/200")
    snellen_value = interpret_av_input(av_in)
    if snellen_value == 0:
        st.warning("Formato no válido. Se usará 20/200 por defecto.")
        snellen_value = 0.1

    logmar_val = snellen_to_logmar(snellen_value)
    etdrs_val = logmar_to_etdrs(logmar_val)
    st.write(f"**Snellen**: {snellen_value:.3f} | **logMAR**: {logmar_val:.2f} | **ETDRS**: {etdrs_val:.1f} letras")

    # Botón para calcular
    if st.button("Calcular"):
        # Calcular riesgo de sangrado
        riesgo_sang = calcular_riesgo_sangrado(
            edad, duracion_dm, hba1c,
            estadio_renal, tipo_dr,
            hta_stage
        )
        # Calcular riesgo reinterv
        riesgo_reint = calcular_riesgo_reintervencion(
            edad, duracion_dm, hba1c,
            estadio_renal, tipo_dr,
            hta_stage
        )
        # Probabilidad de mejoría SIN antiVEGF
        prob_sin = calcular_prob_mejoria_visual(
            snellen_value, tipo_dr, hta_stage
        )
        # Probabilidad de mejoría CON antiVEGF preqx
        prob_con = calcular_prob_mejoria_visual_con_antiVEGF(
            snellen_value, tipo_dr, hta_stage
        )
        # Recomendación final
        recomendacion_final = recomendar_terapia_adicional(riesgo_sang)

        st.subheader("Resultados de DRACOV")

        st.write(f"- **Riesgo de sangrado**: {riesgo_sang*100:.1f}%")
        st.write(f"- **Riesgo de reintervención**: {riesgo_reint*100:.1f}%")

        # Mostrar en dos columnas la comparación con vs sin antiVEGF
        col1, col2 = st.columns(2)
        col1.markdown("### Sin Anti-VEGF preqx")
        col1.write(f"≥1 línea: {prob_sin['≥1 línea']*100:.1f}%")
        col1.write(f"≥2 líneas: {prob_sin['≥2 líneas']*100:.1f}%")
        col1.write(f"≥3 líneas: {prob_sin['≥3 líneas']*100:.1f}%")

        col2.markdown("### Con Anti-VEGF preqx")
        col2.write(f"≥1 línea: {prob_con['≥1 línea']*100:.1f}%")
        col2.write(f"≥2 líneas: {prob_con['≥2 líneas']*100:.1f}%")
        col2.write(f"≥3 líneas: {prob_con['≥3 líneas']*100:.1f}%")

        st.markdown(f"**Recomendación**:\n{recomendacion_final}")

        st.info("""
**Nota**: Estos porcentajes son aproximaciones hipotéticas. 
La decisión real de usar anti-VEGF prequirúrgico (p. ej., ranibizumab, aflibercept o bevacizumab)
o PRP adicional debe basarse en protocolos específicos, disponibilidad de tiempo
y valoración clínica integral.
""")

    st.write("---")
    st.subheader("Referencias (Evidencia de Alta Calidad)")
    st.markdown("""
- **DRCR.net Protocol S**: *JAMA.* 2015;314(20):2137-2146  
- **DRCR.net Protocol T**: *Ophthalmology.* 2015;122(10):2044-2052  
- **Virgili G, et al.** “Surgical interventions for vitreous haemorrhage in people with diabetic retinopathy.” 
  *Cochrane Database Syst Rev.* 2022;1(1):CD008214  
- **Gao L, et al.** “Efficacy and Safety of Intravitreal Ranibizumab Versus Panretinal Photocoagulation in Proliferative Diabetic Retinopathy.” 
  *PLoS One.* 2019;14(1):e0210659  
- **Wong TY, et al.** “Diabetic retinopathy.” *Nat Rev Dis Primers.* 2016;2:16012  
- **Gross JL, et al.** “Diabetic nephropathy: diagnosis, prevention, and treatment.” 
  *Diabetes Care.* 2005;28(1):164-176
""")


# -------------------------------------------------------------------------
# 5) Ejecución (entry point)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    main()