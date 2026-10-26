import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo

# =========================================================
# CONFIGURACIÓN Y CATÁLOGOS DE PLANTA
# =========================================================
st.set_page_config(page_title="Liberación de Tarimas", page_icon="📦", layout="centered")

# Zona horaria oficial para Pachuca, Hidalgo
ZONA_HORARIA_MX = ZoneInfo("America/Mexico_City")

# Capacidad fija de piezas por pallet por modelo
CAPACIDAD_PALLET = {
    "107150": 20,
    "107453": 20,
    "107193": 19,
    "107638": 15,
    "107164": 25,
    "10130750": 20,
    "10130754": 25,
    "10130748": 20,
    "10130746": 15,
    "10130752": 19,
    "M0304": 20
}

INSPECTORES = [
    "Seleccionar...",
    "Eladio García",
    "Valeria Neria",
    "Sebastián Rosales",
    "Armando Rosales",
    "Alexis Hernández",
    "Itzel Juárez",
    "Berenice Hernández",
    "Otro"
]

# Códigos de defecto para última operación (16xx Fundición / 26xx Maquinado)
DEFECTOS_OP60 = {
    "1601": "Marca de pintura (Molde de fundición)",
    "1602": "Fracturas/Uniones",
    "1603": "Rechupes",
    "1604": "Falta de material",
    "1605": "Inclusión escoria",
    "1606": "Erosión",
    "1607": "Golpes",
    "1608": "Leyendas incompletas o faltantes",
    "1609": "Gas",
    "1610": "Inclusión de arena",
    "1611": "Exceso de material",
    "1612": "Esmerilado sin granallar",
    "2613": "Caída",
    "2614": "Piloto cerrado",
    "2615": "Piloto abierto",
    "2616": "Pista cerrada",
    "2617": "Pista abierta",
    "2618": "Ovalamiento / Conicidad",
    "2619": "Espesor de brida",
    "2620": "Ajuste por ingeniería",
    "2621": "Golpes / incrustación",
    "2622": "Marcaje de fecha juliana incorrecto",
    "2623": "Cinturón abierto",
    "2624": "Cinturón cerrado",
    "2642": "Runout",
    "1626": "Falla en balanceo por peso (sin corte)",
    "2627": "Falla en balanceo por peso (con corte)",
    "2628": "Profundidad de corte en balanceo",
    "2629": "Corte con escalón o mayor a 120°",
    "2630": "Doble corte en balanceo ≠ 180°",
    "2631": "Falla en ajuste",
    "2632": "Vibración / Rugosidad",
    "2633": "Barrenado incompleto",
    "2634": "Diámetro de ranura fuera de especificación",
    "2635": "Posición de barrenos NG",
    "2636": "Altura fuera de especificación",
    "2637": "Inserto roto",
    "2638": "Falla en chaflán",
    "2639": "Rayas en pista",
    "2640": "Rayas en brida",
    "2641": "Oxido",
    "2644": "Falla en balanceo TRU TURN",
    "2645": "Pieza sin estatus",
    "2646": "Falla en pintura"
}

def obtener_fecha_y_turno_auto():
    ahora = datetime.now(ZONA_HORARIA_MX)
    hora_actual = ahora.time()
    
    # REGLA DÍA OPERATIVO: De 00:00 a 08:59 hrs la fecha pertenece al día operativo anterior
    if hora_actual < dtime(9, 0):
        fecha_dt = ahora - timedelta(days=1)
    else:
        fecha_dt = ahora
        
    fecha_formateada = fecha_dt.strftime("%d/%m/%Y") # Formato DD/MM/YYYY
    
    # REGLA DE TURNO CON VENTANA DE TOLERANCIA
    if dtime(9, 0) <= hora_actual < dtime(17, 0):
        turno = "1"
    elif dtime(17, 0) <= hora_actual or hora_actual < dtime(0, 30):
        turno = "2"
    else:
        turno = "3"
        
    return fecha_formateada, turno

# =========================================================
# CONEXIÓN A GOOGLE SHEETS
# =========================================================
try:
    SPREADSHEET_ID_TARIMAS = st.secrets["SPREADSHEET_ID_TARIMAS"]
    gcp_data = st.secrets["GCP_SERVICE_ACCOUNT"]
    
    if isinstance(gcp_data, str):
        GCP_CREDS = json.loads(gcp_data)
    else:
        GCP_CREDS = dict(gcp_data)

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(GCP_CREDS, scopes=scopes)
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(SPREADSHEET_ID_TARIMAS).sheet1
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
    st.stop()

# =========================================================
# INTERFAZ DE USUARIO
# =========================================================
st.title("📦 Registro de Liberación de Tarimas")
st.caption("Captura rápida para inspectores de calidad")

# 1. INFORMACIÓN GENERAL
st.subheader("1. Información General")

col_insp, col_modo = st.columns(2)
with col_insp:
    inspector = st.selectbox("Inspector de Calidad", INSPECTORES)
    if inspector == "Otro":
        inspector = st.text_input("Escribe tu nombre:")

with col_modo:
    modo_tiempo = st.radio(
        "Modo Fecha y Turno:",
        ["⚡ Automático (Ahora)", "✏️ Manual (Extemporáneo)"],
        horizontal=True
    )

if modo_tiempo == "⚡ Automático (Ahora)":
    fecha_reg, turno_reg = obtener_fecha_y_turno_auto()
    st.info(f"📅 **Fecha Operativa:** `{fecha_reg}` | 🕒 **Turno Detectado:** `{turno_reg}`")
else:
    col_f, col_t = st.columns(2)
    with col_f:
        fecha_input = st.date_input(
            "Fecha de Inspección", 
            value=datetime.now(ZONA_HORARIA_MX),
            format="DD/MM/YYYY"
        )
        fecha_reg = fecha_input.strftime("%d/%m/%Y") # Formato DD/MM/YYYY
    with col_t:
        turno_reg = st.selectbox("Turno", ["1", "2", "3"])

st.divider()

# 2. SELECCIÓN DE MODELOS LIBERADOS
st.subheader("2. Selecciona los Números de Parte Inspeccionados")
modelos_seleccionados = st.multiselect(
    "Puedes elegir varios modelos a la vez:",
    options=list(CAPACIDAD_PALLET.keys()),
    placeholder="Haz clic aquí para seleccionar los números de parte..."
)

# 3. CAPTURA DETALLADA POR MODELO
registros_capturados = []

if modelos_seleccionados:
    st.divider()
    st.subheader("3. Conteo de Tarimas por Modelo")

    for modelo in modelos_seleccionados:
        cap_pzas = CAPACIDAD_PALLET[modelo]
        
        with st.expander(f"📌 **Modelo #{modelo}** ({cap_pzas} pzas/pallet)", expanded=True):
            col_t1, col_t2, col_t3 = st.columns(3)
            
            with col_t1:
                t_paso1 = st.number_input(
                    f"Tarimas Pasaron 1ra Rev. ({modelo})",
                    min_value=0, value=0, step=1, key=f"t1_{modelo}"
                )
            with col_t2:
                t_paso2 = st.number_input(
                    f"Tarimas Pasaron 2da Rev. ({modelo})",
                    min_value=0, value=0, step=1, key=f"t2_{modelo}"
                )
            with col_t3:
                t_rech = st.number_input(
                    f"Tarimas Rechazadas 1ra Rev. ({modelo})",
                    min_value=0, value=0, step=1, key=f"tr_{modelo}"
                )

            # Desglose de defectos para tarimas rechazadas
            codigos_defectos_list = []
            if t_rech > 0:
                st.warning(f"⚠️ Asigna el código de defecto para las **{t_rech}** tarima(s) rechazada(s):")
                for i in range(1, t_rech + 1):
                    cod_def = st.selectbox(
                        f"Código de Defecto - Tarima Rechazada #{i} ({modelo})",
                        options=[""] + list(DEFECTOS_OP60.keys()),
                        format_func=lambda x: f"{x} - {DEFECTOS_OP60[x]}" if x in DEFECTOS_OP60 else "Selecciona defecto...",
                        key=f"def_{modelo}_{i}"
                    )
                    codigos_defectos_list.append(cod_def)

            # 1. Generar fila para Aceptadas en 1ra Revisión
            if t_paso1 > 0:
                registros_capturados.append({
                    "Fecha": fecha_reg,
                    "Turno": turno_reg,
                    "Inspector": inspector,
                    "#Parte": modelo,
                    "Estatus": "1ra Revisión",
                    "Pzas_x_Pallet": cap_pzas,
                    "Tarimas": t_paso1,
                    "Total_Piezas": t_paso1 * cap_pzas,
                    "Descripcion_Defecto": "N/A",
                    "Cod_Defecto": "N/A"
                })

            # 2. Generar fila para Aceptadas en 2da Revisión
            if t_paso2 > 0:
                registros_capturados.append({
                    "Fecha": fecha_reg,
                    "Turno": turno_reg,
                    "Inspector": inspector,
                    "#Parte": modelo,
                    "Estatus": "2da Revisión",
                    "Pzas_x_Pallet": cap_pzas,
                    "Tarimas": t_paso2,
                    "Total_Piezas": t_paso2 * cap_pzas,
                    "Descripcion_Defecto": "N/A",
                    "Cod_Defecto": "N/A"
                })

            # 3. Generar UNA FILA INDIVIDUAL POR CADA TARIMA RECHAZADA
            if t_rech > 0:
                for cod in codigos_defectos_list:
                    cod_num = cod if cod else "Sin seleccionar"
                    desc_def = DEFECTOS_OP60.get(cod, "Sin seleccionar") if cod else "Sin seleccionar"
                    registros_capturados.append({
                        "Fecha": fecha_reg,
                        "Turno": turno_reg,
                        "Inspector": inspector,
                        "#Parte": modelo,
                        "Estatus": "Rechazado",
                        "Pzas_x_Pallet": cap_pzas,
                        "Tarimas": 1,
                        "Total_Piezas": cap_pzas,
                        "Descripcion_Defecto": desc_def,
                        "Cod_Defecto": cod_num
                    })

    # 4. RESUMEN Y GUARDADO
    st.divider()
    st.subheader("4. Confirmar y Registrar en Google Sheets")

    defectos_pendientes = any(
        r["Estatus"] == "Rechazado" and (r["Cod_Defecto"] == "Sin seleccionar" or r["Descripcion_Defecto"] == "Sin seleccionar")
        for r in registros_capturados
    )

    if inspector == "Seleccionar..." or not inspector.strip():
        st.error("⚠️ Por favor selecciona tu nombre de inspector en la Sección 1 antes de guardar.")
    elif defectos_pendientes:
        st.error("⚠️ Asigna el código de defecto para cada una de las tarimas rechazadas antes de enviar.")
    elif len(registros_capturados) == 0:
        st.info("💡 Ingresa al menos 1 tarima (pasada o rechazada) para poder realizar el registro.")
    else:
        df_resumen = pd.DataFrame(registros_capturados)
        st.dataframe(df_resumen, use_container_width=True)

        if st.button("🚀 Registrar Liberaciones", type="primary", use_container_width=True):
            try:
                filas_insertar = []
                for r in registros_capturados:
                    fila = [
                        r["Fecha"],
                        r["Turno"],
                        r["Inspector"],
                        r["#Parte"],
                        r["Estatus"],
                        r["Pzas_x_Pallet"],
                        r["Tarimas"],
                        r["Total_Piezas"],
                        r["Descripcion_Defecto"],
                        r["Cod_Defecto"]
                    ]
                    filas_insertar.append(fila)

                sheet.append_rows(filas_insertar)
                st.balloons()
                st.success("✅ ¡Registros guardados exitosamente en Google Sheets!")
            except Exception as e:
                st.error(f"Error al guardar los datos: {e}")
