import io
import pandas as pd
import streamlit as st

# ==========================================
# 0. CONFIGURACIÓN INICIAL (DEBE IR PRIMERO)
# ==========================================
st.set_page_config(
    page_title="Conciliación Fiscal SAT y Diagnóstico Financiero",
    layout="wide",
)

st.title("📊 Conciliación Fiscal SAT y Diagnóstico Financiero")
st.caption("Procesamiento automático desde XML / OneFacture")

# Inicialización de memoria (Session State)
if "ingresos_manuales" not in st.session_state:
    st.session_state.ingresos_manuales = []

if "gastos_manuales" not in st.session_state:
    st.session_state.gastos_manuales = []

# ==========================================
# FUNCIONES CALLBACK PARA GUARDAR Y LIMPIAR
# ==========================================
def guardar_ingreso_callback():
    periodo = st.session_state.get("periodo_sel", "")
    monto = st.session_state.get("ing_monto", 0.0)
    if monto > 0:
        st.session_state.ingresos_manuales.append({
            "Periodo": periodo,
            "Subtotal": float(monto),
            "IVA": float(monto * 0.16),
            "Total": float(monto * 1.16),
        })
        st.session_state["ing_monto"] = 0.0
        st.toast(f"✅ Ingreso guardado en {periodo}")

def guardar_gasto_callback():
    periodo = st.session_state.get("periodo_sel", "")
    monto = st.session_state.get("gasto_monto", 0.0)
    rfc = st.session_state.get("gasto_rfc", "").strip().upper()

    if monto > 0 and rfc:
        sub_c = float(monto / 1.16)
        iva_c = float(sub_c * 0.16)
        st.session_state.gastos_manuales.append({
            "Periodo": periodo,
            "RFC": rfc,
            "Nombre": "COMBUSTIBLE (MANUAL)",
            "Subtotal": sub_c,
            "IVA": iva_c,
            "Total": float(monto),
        })
        st.session_state["gasto_monto"] = 0.0
        st.session_state["gasto_rfc"] = ""
        st.toast(f"✅ Gasto guardado en {periodo}")

# ==========================================
# CREACIÓN DE PESTAÑAS PRINCIPALES DE LA APP
# ==========================================
tab_mensual, tab_anual = st.tabs(["📊 Módulo Mensual / Bimestral", "📅 Módulo Declaración Anual"])

with tab_mensual:
    # ==========================================
    # 1. CARGA DE ARCHIVOS DE ONEFACTURE
    # ==========================================
    st.subheader("📁 Cargar Reportes de OneFacture")
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        st.markdown("**Archivos Obligatorios (Facturas)**")
        file_emi_f = st.file_uploader("Facturas EMITIDAS (F.xlsx) *", type=["xlsx"], key="file_emi_f")
        file_rec_f = st.file_uploader("Facturas RECIBIDAS (F.xlsx) *", type=["xlsx"], key="file_rec_f")

    with col_f2:
        st.markdown("**Archivos Opcionales (Complementos de Pago)**")
        file_emi_p = st.file_uploader("Pagos EMITIDOS / REPs (P.xlsx) (Opcional)", type=["xlsx"], key="file_emi_p")
        file_rec_p = st.file_uploader("Pagos RECIBIDOS / REPs (P.xlsx) (Opcional)", type=["xlsx"], key="file_rec_p")

    if file_emi_f:
        st.session_state["df_emi_f_raw"] = pd.read_excel(file_emi_f)
    if file_rec_f:
        st.session_state["df_rec_f_raw"] = pd.read_excel(file_rec_f)
    if file_emi_p:
        st.session_state["df_emi_p_raw"] = pd.read_excel(file_emi_p)
    if file_rec_p:
        st.session_state["df_rec_p_raw"] = pd.read_excel(file_rec_p)

    # ==========================================
    # 2. PANEL LATERAL: CONFIGURACIÓN BÁSICA Y CONTROLES
    # ==========================================
    with st.sidebar:
        st.header("⚙ Selección del Período")

        regimen = st.selectbox(
            "Régimen Fiscal",
            [
                "612 - Actividad Empresarial y Profesional (Mensual)",
                "626 - RESICO Persona Física (Mensual)",
                "621 - RIF - Reg. de Incorporación Fiscal (Bimestral)",
                "601 - General Persona Moral (Mensual)",
                "606 - Arrendamiento (Mensual)",
            ],
        )

        es_bimestral = "Bimestral" in regimen or "RIF" in regimen

        periodo_sel = st.selectbox(
            "Período a Declarar",
            [
                "Todos los meses", "Enero", "Febrero", "Marzo", "Abril", "Mayo",
                "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ] if not es_bimestral else [
                "Bimestre 1 (Ene-Feb)", "Bimestre 2 (Mar-Abr)", "Bimestre 3 (May-Jun)",
                "Bimestre 4 (Jul-Ago)", "Bimestre 5 (Sep-Oct)", "Bimestre 6 (Nov-Dic)"
            ],
            key="periodo_sel",
        )

        st.divider()
        st.header("➕ Captura Manual")
        st.caption(f"Los registros se aplicarán al período: **{periodo_sel}**")

        if periodo_sel == "Todos los meses":
            st.warning("⚠️ Para realizar capturas manuales, selecciona un mes o bimestre específico arriba.")
        else:
            with st.expander("📥 Agregar Ingreso Manual", expanded=False):
                st.number_input(f"Monto Ingreso para {periodo_sel} ($)", min_value=0.0, step=100.0, key="ing_monto")
                st.button("➕ Guardar Ingreso", use_container_width=True, on_click=guardar_ingreso_callback)

            with st.expander("⛽ Agregar Gasto Combustible", expanded=False):
                st.text_input("RFC del Proveedor", key="gasto_rfc")
                st.number_input(f"Monto Total Gasto para {periodo_sel} ($)", min_value=0.0, step=100.0, key="gasto_monto")

                rfc_actual = st.session_state.get("gasto_rfc", "").strip()
                if not rfc_actual:
                    st.caption("⚠️ Escribe el RFC del proveedor para poder guardar.")

                st.button("➕ Guardar Gasto", use_container_width=True, on_click=guardar_gasto_callback)

        if st.session_state.ingresos_manuales or st.session_state.gastos_manuales:
            if st.button("🗑️ Borrar Registros Manuales", type="secondary", use_container_width=True):
                st.session_state.ingresos_manuales = []
                st.session_state.gastos_manuales = []
                st.rerun()

    # ==========================================
    # 3. PROCESAMIENTO DE DATOS MENSUALES
    # ==========================================
    if "df_emi_f_raw" in st.session_state and "df_rec_f_raw" in st.session_state:
        df_emi_f = st.session_state["df_emi_f_raw"].copy()
        df_rec_f = st.session_state["df_rec_f_raw"].copy()

        df_emi_p = st.session_state.get("df_emi_p_raw", pd.DataFrame()).copy()
        df_rec_p = st.session_state.get("df_rec_p_raw", pd.DataFrame()).copy()

        df_emi_f = df_emi_f[df_emi_f["Estado"] == "VIGENTE"] if "Estado" in df_emi_f.columns else df_emi_f
        df_rec_f = df_rec_f[df_rec_f["Estado"] == "VIGENTE"] if "Estado" in df_rec_f.columns else df_rec_f

        if not df_emi_p.empty and "Estado" in df_emi_p.columns:
            df_emi_p = df_emi_p[df_emi_p["Estado"] == "VIGENTE"]
        if not df_rec_p.empty and "Estado" in df_rec_p.columns:
            df_rec_p = df_rec_p[df_rec_p["Estado"] == "VIGENTE"]

        meses_dict = {
            "Enero": [1], "Febrero": [2], "Marzo": [3], "Abril": [4], "Mayo": [5], "Junio": [6],
            "Julio": [7], "Agosto": [8], "Septiembre": [9], "Octubre": [10], "Noviembre": [11], "Diciembre": [12],
            "Bimestre 1 (Ene-Feb)": [1, 2], "Bimestre 2 (Mar-Abr)": [3, 4], "Bimestre 3 (May-Jun)": [5, 6],
            "Bimestre 4 (Jul-Ago)": [7, 8], "Bimestre 5 (Sep-Oct)": [9, 10], "Bimestre 6 (Nov-Dic)": [11, 12],
        }

        if periodo_sel != "Todos los meses":
            num_meses = meses_dict[periodo_sel]
            df_emi_f["Fecha emision"] = pd.to_datetime(df_emi_f["Fecha emision"], errors="coerce")
            df_emi_f = df_emi_f[df_emi_f["Fecha emision"].dt.month.isin(num_meses)]

            df_rec_f["Fecha emision"] = pd.to_datetime(df_rec_f["Fecha emision"], errors="coerce")
            df_rec_f = df_rec_f[df_rec_f["Fecha emision"].dt.month.isin(num_meses)]

            if not df_emi_p.empty and "Fecha pago" in df_emi_p.columns:
                df_emi_p["Fecha pago"] = pd.to_datetime(df_emi_p["Fecha pago"], errors="coerce")
                df_emi_p = df_emi_p[df_emi_p["Fecha pago"].dt.month.isin(num_meses)]

            if not df_rec_p.empty and "Fecha pago" in df_rec_p.columns:
                df_rec_p["Fecha pago"] = pd.to_datetime(df_rec_p["Fecha pago"], errors="coerce")
                df_rec_p = df_rec_p[df_rec_p["Fecha pago"].dt.month.isin(num_meses)]

        # ==========================================
        # 4. CÁLCULO DE INGRESOS
        # ==========================================
        emi_pue = df_emi_f[
            (df_emi_f["Metodo pago"].astype(str).str.startswith("PUE"))
            & (df_emi_f["Tipo"].astype(str).str.startswith("I"))
        ]

        col_desc_emi = next((c for c in emi_pue.columns if "descuento" in c.lower()), None)
        desc_emi_pue = float(emi_pue[col_desc_emi].fillna(0).sum()) if col_desc_emi else 0.0

        sub_emi_bruto = float(emi_pue["SubTotal"].sum())
        sub_emi_pue = sub_emi_bruto - desc_emi_pue
        iva_emi_pue = float(emi_pue["IVA Trasladado 16%"].sum()) if "IVA Trasladado 16%" in emi_pue.columns else 0.0
        cant_emi_pue = len(emi_pue)

        if not df_emi_p.empty:
            total_emi_rep = float(df_emi_p["Monto"].dropna().sum()) if "Monto" in df_emi_p.columns else 0.0
            iva_emi_rep = float(df_emi_p["TrasladosImpuestoIVA16 - pago"].dropna().sum()) if "TrasladosImpuestoIVA16 - pago" in df_emi_p.columns else 0.0
            sub_emi_rep = iva_emi_rep / 0.16 if iva_emi_rep > 0 else 0.0
            cant_emi_rep = len(df_emi_p)
        else:
            total_emi_rep, sub_emi_rep, iva_emi_rep, cant_emi_rep = 0.0, 0.0, 0.0, 0

        emi_egresos = df_emi_f[df_emi_f["Tipo"].astype(str).str.startswith("E")]
        sub_emi_egreso = float(emi_egresos["SubTotal"].sum())
        iva_emi_egreso = float(emi_egresos["IVA Trasladado 16%"].sum()) if "IVA Trasladado 16%" in emi_egresos.columns else 0.0
        cant_emi_egreso = len(emi_egresos)

        ing_manuales_filtrados = [
            i for i in st.session_state.ingresos_manuales
            if periodo_sel == "Todos los meses" or i["Periodo"] == periodo_sel
        ]
        sub_ing_man = float(sum(i["Subtotal"] for i in ing_manuales_filtrados))
        iva_ing_man = float(sum(i["IVA"] for i in ing_manuales_filtrados))
        cant_ing_man = len(ing_manuales_filtrados)

        subtotal_ingresos_xml = (sub_emi_pue + sub_emi_rep + sub_ing_man) - sub_emi_egreso
        iva_causado_xml = (iva_emi_pue + iva_emi_rep + iva_ing_man) - iva_emi_egreso
        total_ingresos_xml_banco = subtotal_ingresos_xml + iva_causado_xml
        total_cant_ingresos = cant_emi_pue + cant_emi_rep + cant_emi_egreso + cant_ing_man

        # ==========================================
        # 5. GASTOS: TRATAMIENTO (PUE + PPD CON REPS)
        # ==========================================
        df_rec_f_i = df_rec_f[df_rec_f["Tipo"].astype(str).str.startswith("I")].copy()

        if not df_rec_f_i.empty:
            col_desc_rec = next((c for c in df_rec_f_i.columns if "descuento" in c.lower()), None)
            desc_rec_pue_16 = float(df_rec_f_i[col_desc_rec].fillna(0).sum()) if col_desc_rec else 0.0

            col_iva_rec_16 = next((c for c in df_rec_f_i.columns if "iva trasladado 16%" in c.lower() or "iva 16%" in c.lower()), None)
            
            rec_pue_16 = df_rec_f_i[
                (df_rec_f_i["Metodo pago"].astype(str).str.startswith("PUE")) &
                (df_rec_f_i[col_iva_rec_16].fillna(0) > 0 if col_iva_rec_16 else False)
            ].copy()
            
            if not rec_pue_16.empty and col_iva_rec_16:
                rec_pue_16["_iva_monto"] = pd.to_numeric(rec_pue_16[col_iva_rec_16], errors="coerce").fillna(0)
                sub_rec_pue_16 = float((rec_pue_16["_iva_monto"] / 0.16).sum())
                iva_rec_pue_16 = float(rec_pue_16["_iva_monto"].sum())
            else:
                sub_rec_pue_16, iva_rec_pue_16 = 0.0, 0.0
            cant_rec_pue_16 = len(rec_pue_16)

            # --- CÁLCULO DE COMBUSTIBLES (PUE + REPs DE COMBUSTIBLES) ---
            def es_gasto_combustible(r):
                txt = ""
                for col in ["ClaveProdServ", "Conceptos", "Descripcion", "Concepto"]:
                    if col in r and pd.notna(r[col]):
                        txt += str(r[col]) + " "
                txt = txt.upper()
                return "1510" in txt or "COMBUSTIBLE" in txt or "GASOLINA" in txt or "DIESEL" in txt

            mask_comb = df_rec_f_i.apply(es_gasto_combustible, axis=1)
            rec_pue_comb = df_rec_f_i[mask_comb & df_rec_f_i["Metodo pago"].fillna("").astype(str).str.lower().str.strip().str.startswith("pue")].copy()
            
            if not rec_pue_comb.empty:
                sub_comb_pue = float((pd.to_numeric(rec_pue_comb["Total"], errors="coerce").fillna(0) / 1.16).sum())
                iva_comb_pue = float(sub_comb_pue * 0.16)
                total_comb_pue = float(rec_pue_comb["Total"].fillna(0).sum())
                cant_comb_pue = len(rec_pue_comb)
            else:
                sub_comb_pue, iva_comb_pue, total_comb_pue, cant_comb_pue = 0.0, 0.0, 0.0, 0

            # Incluir REPs que correspondan a facturas de combustibles (PPD pagados en el periodo)
            sub_comb_rep, iva_comb_rep, total_comb_rep, cant_comb_rep = 0.0, 0.0, 0.0, 0
            if "df_rec_p_raw" in st.session_state and not st.session_state["df_rec_p_raw"].empty:
                df_rec_p_raw_full = st.session_state["df_rec_p_raw"].copy()
                if "Estado" in df_rec_p_raw_full.columns:
                    df_rec_p_raw_full = df_rec_p_raw_full[df_rec_p_raw_full["Estado"] == "VIGENTE"]
                
                if periodo_sel != "Todos los meses" and "Fecha pago" in df_rec_p_raw_full.columns:
                    df_rec_p_raw_full["Fecha pago"] = pd.to_datetime(df_rec_p_raw_full["Fecha pago"], errors="coerce")
                    df_rec_p_raw_full = df_rec_p_raw_full[df_rec_p_raw_full["Fecha pago"].dt.month.isin(num_meses)]

                df_rec_f_raw_all = st.session_state["df_rec_f_raw"].copy()
                mask_comb_global = df_rec_f_raw_all.apply(es_gasto_combustible, axis=1)
                df_comb_global = df_rec_f_raw_all[mask_comb_global].copy()

                col_id_rel = next((c for c in df_rec_p_raw_full.columns if "idpago" in c.lower() or "docto" in c.lower() or "uuid" in c.lower() and "relacionado" in c.lower()), None)
                col_imp_pagado = next((c for c in df_rec_p_raw_full.columns if "impago" in c.lower() or "importepagado" in c.lower() or "monto" in c.lower()), None)
                col_uuid_factura = "UUID" if "UUID" in df_comb_global.columns else None

                if col_id_rel and col_imp_pagado and col_uuid_factura and not df_comb_global.empty:
                    pagos_por_factura = df_rec_p_raw_full.groupby(col_id_rel)[col_imp_pagado].sum().reset_index()
                    comb_pagados = pd.merge(
                        df_comb_global,
                        pagos_por_factura,
                        left_on=col_uuid_factura,
                        right_on=col_id_rel,
                        how="inner"
                    )
                    if not comb_pagados.empty:
                        total_comb_rep = float(pd.to_numeric(comb_pagados[col_imp_pagado], errors="coerce").fillna(0).sum())
                        sub_comb_rep = float(total_comb_rep / 1.16)
                        iva_comb_rep = float(sub_comb_rep * 0.16)
                        cant_comb_rep = len(comb_pagados)

            gastos_manuales_filtrados = [
                g for g in st.session_state.gastos_manuales
                if periodo_sel == "Todos los meses" or g["Periodo"] == periodo_sel
            ]
            total_comb_man = float(sum(g["Total"] for g in gastos_manuales_filtrados))
            sub_comb_man = float(sum(g["Subtotal"] for g in gastos_manuales_filtrados))
            iva_comb_man = float(sum(g["IVA"] for g in gastos_manuales_filtrados))
            cant_comb_man = len(gastos_manuales_filtrados)

            sub_comb = sub_comb_pue + sub_comb_rep + sub_comb_man
            iva_comb_real = iva_comb_pue + iva_comb_rep + iva_comb_man
            total_comb = total_comb_pue + total_comb_rep + total_comb_man
            cant_rec_comb = cant_comb_pue + cant_comb_rep + cant_comb_man

            col_tasa_0 = next((c for c in df_rec_f_i.columns if "0%" in c.lower() or "tasa 0" in c.lower()), None)
            col_exento = next((c for c in df_rec_f_i.columns if "exento" in c.lower()), None)

            rec_pue_0_directo = df_rec_f_i[(df_rec_f_i[col_tasa_0].fillna(0) > 0)] if col_tasa_0 else pd.DataFrame()
            sub_rec_pue_0 = float(pd.to_numeric(rec_pue_0_directo["SubTotal"], errors="coerce").fillna(0).sum()) if not rec_pue_0_directo.empty else 0.0
            cant_rec_pue_0 = len(rec_pue_0_directo)
            if not rec_pue_0_directo.empty:
                rec_pue_0_directo["_sub_neto"] = pd.to_numeric(rec_pue_0_directo["SubTotal"], errors="coerce").fillna(0)

            rec_pue_exento = df_rec_f_i[(df_rec_f_i[col_exento].fillna(0) > 0)] if col_exento else pd.DataFrame()
            sub_rec_pue_exento = float(pd.to_numeric(rec_pue_exento["SubTotal"], errors="coerce").fillna(0).sum()) if not rec_pue_exento.empty else 0.0
            cant_rec_pue_exento = len(rec_pue_exento)
            if not rec_pue_exento.empty:
                rec_pue_exento["_sub_neto"] = pd.to_numeric(rec_pue_exento["SubTotal"], errors="coerce").fillna(0)
        else:
            desc_rec_pue_16 = 0.0
            sub_rec_pue_16, iva_rec_pue_16, cant_rec_pue_16 = 0.0, 0.0, 0
            sub_comb, iva_comb_real, total_comb, cant_rec_comb = 0.0, 0.0, 0.0, 0
            sub_rec_pue_0, cant_rec_pue_0 = 0.0, 0
            sub_rec_pue_exento, cant_rec_pue_exento = 0.0, 0
            rec_pue_16, rec_pue_0_directo, rec_pue_exento = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        if not df_rec_p.empty:
            total_rec_rep = float(df_rec_p["Monto"].dropna().sum()) if "Monto" in df_rec_p.columns else 0.0
            iva_rec_rep = float(df_rec_p["TrasladosImpuestoIVA16 - pago"].dropna().sum()) if "TrasladosImpuestoIVA16 - pago" in df_rec_p.columns else 0.0
            sub_rec_rep = iva_rec_rep / 0.16 if iva_rec_rep > 0 else 0.0
            cant_rec_rep = len(df_rec_p)
        else:
            total_rec_rep, sub_rec_rep, iva_rec_rep, cant_rec_rep = 0.0, 0.0, 0.0, 0

        rec_egresos = df_rec_f[df_rec_f["Tipo"].astype(str).str.startswith("E")].copy()
        sub_rec_egreso = float(rec_egresos["SubTotal"].sum()) if not rec_egresos.empty else 0.0
        iva_rec_egreso = float(rec_egresos["IVA Trasladado 16%"].sum()) if not rec_egresos.empty and "IVA Trasladado 16%" in rec_egresos.columns else 0.0
        total_rec_egreso = sub_rec_egreso + iva_rec_egreso
        cant_rec_egreso = len(rec_egresos)

        subtotal_gastos_16 = (sub_rec_pue_16 + sub_comb + sub_rec_rep) - sub_rec_egreso
        iva_acreditable = (iva_rec_pue_16 + iva_comb_real + iva_rec_rep) - iva_rec_egreso

        subtotal_gastos = subtotal_gastos_16 + sub_rec_pue_0 + sub_rec_pue_exento
        total_gastos_banco = subtotal_gastos + iva_acreditable
        total_cant_gastos = cant_rec_pue_16 + cant_rec_pue_0 + cant_rec_pue_exento + cant_rec_comb + cant_rec_rep + cant_rec_egreso
        subtotal_gastos_16_diot = sub_rec_pue_16 + sub_comb + sub_rec_rep - sub_rec_egreso

        # ==========================================
        # 6. PÚBLICO EN GENERAL Y MÉTRICAS
        # ==========================================
        diferencia_banco = total_ingresos_xml_banco - total_gastos_banco

        if diferencia_banco < 0:
            faltante_pg_total = abs(diferencia_banco)
            faltante_pg_sub = faltante_pg_total / 1.16
            faltante_pg_iva = faltante_pg_sub * 0.16
        else:
            faltante_pg_total, faltante_pg_sub, faltante_pg_iva = 0.0, 0.0, 0.0

        subtotal_ingresos_totales = subtotal_ingresos_xml + faltante_pg_sub
        iva_causado_total = iva_causado_xml + faltante_pg_iva
        total_ingresos_consolidados = subtotal_ingresos_totales + iva_causado_total

        st.divider()
        st.subheader(f"📌 Resumen Conciliado — [{periodo_sel.upper()}] — {regimen}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingresos Totales (Base ISR)", f"${subtotal_ingresos_totales:,.2f}")
        c2.metric("Gastos Totales (Base ISR)", f"${subtotal_gastos:,.2f}")

        iva_neto = iva_causado_total - iva_acreditable
        c3.metric("IVA Causado Total", f"${iva_causado_total:,.2f}")
        c4.metric(
            "IVA Acreditable Real",
            f"${iva_acreditable:,.2f}",
            delta=(f"${abs(iva_neto):,.2f} {'A Pagar' if iva_neto > 0 else 'A Favor'}"),
            delta_color="inverse" if iva_neto > 0 else "normal",
        )

        # ==========================================
        # 7. DIAGNÓSTICO ESTRATÉGICO DE CIERRE
        # ==========================================
        st.divider()
        st.subheader("🎯 Diagnóstico Estratégico de Cierre")

        if diferencia_banco < 0:
            st.error("🚨 **DIAGNÓSTICO AUTOMÁTICO: TE FALTAN INGRESOS POR FACTURAR (PÚBLICO EN GENERAL)**")
            st.markdown(f"""
            Tus gastos pagados (**${total_gastos_banco:,.2f} MXN**) superan a tus ingresos XML nominativos (**${total_ingresos_xml_banco:,.2f} MXN**).
            * • **TOTAL NETO A FACTURAR (Entrada a Banco):** **${faltante_pg_total:,.2f} MXN**
            * • **SUBTOTAL A FACTURAR (Base ISR):** **${faltante_pg_sub:,.2f} MXN**
            * • **IVA TRASLADADO (16%):** **${faltante_pg_iva:,.2f} MXN**
            """)
        elif diferencia_banco > 0:
            disponible_gastar_total = diferencia_banco
            disponible_gastar_sub = disponible_gastar_total / 1.16
            iva_gastos_potencial = disponible_gastar_sub * 0.16

            st.warning("⚠ **DIAGNÓSTICO AUTOMÁTICO: TE FALTAN GASTOS / DEDUCCIONES**")
            st.markdown(f"""
            Tus ingresos cobrados superan a tus gastos pagados. Tienes una utilidad temporal en banco de **${disponible_gastar_total:,.2f} MXN**.
            * • **TOTAL NETO MÁXIMO A DESEMBOLSAR EN BANCO:** **${disponible_gastar_total:,.2f} MXN**
            * • **SUBTOTAL MÁXIMO DEDUCIBLE (Base ISR):** **${disponible_gastar_sub:,.2f} MXN**
            * • **IVA ACREDITABLE A GENERAR:** **${iva_gastos_potencial:,.2f} MXN**
            """)
        else:
            st.success("✅ **BALANCE PERFECTO:** Tus ingresos y gastos están totalmente amarrados.")

        # ==========================================
        # 8. DESGLOSE GENERAL DETALLADO (CUADRADO CON LA DIOT)
        # ==========================================
        st.divider()
        st.subheader("📑 Desglose General de Operaciones y Impuestos")

        tabla_desglose = pd.DataFrame([
            {
                "Concepto": "1. Facturas Emitidas PUE + Manuales",
                "No. Facturas": cant_emi_pue + cant_ing_man,
                "Subtotal (Base ISR)": f"${(sub_emi_pue + sub_ing_man):,.2f}",
                "Descuentos": f"${desc_emi_pue:,.2f}",
                "IVA (Exacto XML)": f"${(iva_emi_pue + iva_ing_man):,.2f}",
                "Total (Neto Banco)": f"${((sub_emi_pue + iva_emi_pue) + (sub_ing_man + iva_ing_man)):,.2f}",
            },
            {
                "Concepto": "2. Pagos Recibidos / REPs Emitidos (P)",
                "No. Facturas": cant_emi_rep,
                "Subtotal (Base ISR)": f"${sub_emi_rep:,.2f}",
                "Descuentos": "$0.00",
                "IVA (Exacto XML)": f"${iva_emi_rep:,.2f}",
                "Total (Neto Banco)": f"${total_emi_rep:,.2f}",
            },
            {
                "Concepto": "3. (-) Egresos / Notas de Crédito Emitidas (E)",
                "No. Facturas": cant_emi_egreso,
                "Subtotal (Base ISR)": f"-${sub_emi_egreso:,.2f}",
                "Descuentos": "$0.00",
                "IVA (Exacto XML)": f"-${iva_emi_egreso:,.2f}",
                "Total (Neto Banco)": f"-${(sub_emi_egreso + iva_emi_egreso):,.2f}",
            },
            {
                "Concepto": "4. Ventas Público en General (Calculado) Necesarias",
                "No. Facturas": 0,
                "Subtotal (Base ISR)": f"${faltante_pg_sub:,.2f}",
                "Descuentos": "$0.00",
                "IVA (Exacto XML)": f"${faltante_pg_iva:,.2f}",
                "Total (Neto Banco)": f"${faltante_pg_total:,.2f}",
            },
            {
                "Concepto": "✅ TOTAL INGRESOS CONSOLIDADOS",
                "No. Facturas": total_cant_ingresos,
                "Subtotal (Base ISR)": f"${subtotal_ingresos_totales:,.2f}",
                "Descuentos": f"${desc_emi_pue:,.2f}",
                "IVA (Exacto XML)": f"${iva_causado_total:,.2f}",
                "Total (Neto Banco)": f"${total_ingresos_consolidados:,.2f}",
            },
            {
                "Concepto": "5. Gastos Generales Recibidos PUE (Tasa 16%)",
                "No. Facturas": cant_rec_pue_16,
                "Subtotal (Base ISR)": f"${sub_rec_pue_16:,.2f}",
                "Descuentos": f"${desc_rec_pue_16:,.2f}",
                "IVA (Exacto XML)": f"${iva_rec_pue_16:,.2f}",
                "Total (Neto Banco)": f"${(sub_rec_pue_16 + iva_rec_pue_16):,.2f}",
            },
            {
                "Concepto": "5a. Gastos Generales Recibidos PUE (Tasa 0%)",
                "No. Facturas": cant_rec_pue_0,
                "Subtotal (Base ISR)": f"${sub_rec_pue_0:,.2f}",
                "Descuentos": "$0.00",
                "IVA (Exacto XML)": "$0.00",
                "Total (Neto Banco)": f"${sub_rec_pue_0:,.2f}",
            },
            {
                "Concepto": "5b. Gastos Generales Recibidos PUE (Exento)",
                "No. Facturas": cant_rec_pue_exento,
                "Subtotal (Base ISR)": f"${sub_rec_pue_exento:,.2f}",
                "Descuentos": "$0.00",
                "IVA (Exacto XML)": "$0.00",
                "Total (Neto Banco)": f"${sub_rec_pue_exento:,.2f}",
            },
            {
                "Concepto": "6. Combustibles (XML PUE + REPs PPD + Manuales)",
                "No. Facturas": cant_rec_comb,
                "Subtotal (Base ISR)": f"${sub_comb:,.2f}",
                "Descuentos": "$0.00",
                "IVA (Exacto XML)": f"${iva_comb_real:,.2f}",
                "Total (Neto Banco)": f"${total_comb:,.2f}",
            },
            {
                "Concepto": "7. Pagos Realizados / REPs Recibidos (P)",
                "No. Facturas": cant_rec_rep,
                "Subtotal (Base ISR)": f"${sub_rec_rep:,.2f}",
                "Descuentos": "$0.00",
                "IVA (Exacto XML)": f"${iva_rec_rep:,.2f}",
                "Total (Neto Banco)": f"${total_rec_rep:,.2f}",
            },
            {
                "Concepto": "8. (-) Egresos / Notas de Crédito Recibidas (E)",
                "No. Facturas": cant_rec_egreso,
                "Subtotal (Base ISR)": f"-${sub_rec_egreso:,.2f}",
                "Descuentos": "$0.00",
                "IVA (Exacto XML)": f"-${iva_rec_egreso:,.2f}",
                "Total (Neto Banco)": f"-${total_rec_egreso:,.2f}",
            },
            {
                "Concepto": "📊 TOTAL GASTOS CONSOLIDADOS (BRUTO)",
                "No. Facturas": (
                    cant_rec_pue_16
                    + cant_rec_pue_0
                    + cant_rec_pue_exento
                    + cant_rec_comb
                    + cant_rec_rep
                ),
                "Subtotal (Base ISR)": (
                    f"${(sub_rec_pue_16 + sub_rec_pue_0 + sub_rec_pue_exento + sub_comb + sub_rec_rep):,.2f}"
                ),
                "Descuentos": f"${desc_rec_pue_16:,.2f}",
                "IVA (Exacto XML)": (
                    f"${(iva_rec_pue_16 + iva_comb_real + iva_rec_rep):,.2f}"
                ),
                "Total (Neto Banco)": (
                    f"${((sub_rec_pue_16 + iva_rec_pue_16) + sub_rec_pue_0 + sub_rec_pue_exento + total_comb + total_rec_rep):,.2f}"
                ),
            },
            {
                "Concepto": "✅ TOTAL GASTOS CONSOLIDADOS (ISR)",
                "No. Facturas": total_cant_gastos,
                "Subtotal (Base ISR)": f"${subtotal_gastos:,.2f}",
                "Descuentos": f"${desc_rec_pue_16:,.2f}",
                "IVA (Exacto XML)": f"${iva_acreditable:,.2f}",
                "Total (Neto Banco)": f"${total_gastos_banco:,.2f}",
            },
            {
                "Concepto": "🏛️ TOTALES PARA DECLARACION (IVA)",
                "No. Facturas": (
                    cant_rec_pue_16
                    + cant_rec_comb
                    + cant_rec_rep
                    + cant_rec_egreso
                ),
                "Subtotal (Base ISR)": f"${subtotal_gastos_16_diot:,.2f}",
                "Descuentos": f"${desc_rec_pue_16:,.2f}",
                "IVA (Exacto XML)": f"${iva_acreditable:,.2f}",
                "Total (Neto Banco)": (
                    f"${(subtotal_gastos_16_diot + iva_acreditable):,.2f}"
                ),
            },
        ])

        tabla_desglose["No. Facturas"] = (
            pd.to_numeric(tabla_desglose["No. Facturas"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

        st.table(tabla_desglose)

        def convertir_desglose_a_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Desglose Operaciones", index=False)
            return output.getvalue()

        excel_desglose = convertir_desglose_a_excel(tabla_desglose)

        st.download_button(
            label="📊 Descargar Desglose General en Excel",
            data=excel_desglose,
            file_name="desglose_general_operaciones.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # ==========================================
        # 9. REPORTE DIOT (16%)
        # ==========================================
        st.divider()
        st.subheader("📋 Reporte Concentrado para la DIOT (Agrupado por RFC)")

        col_rfc_emisor = next(
            (
                c
                for c in df_rec_f.columns
                if "rfc" in c.lower() and "emisor" in c.lower()
            ),
            "RfcEmisor",
        )
        col_nom_emisor = next(
            (
                c
                for c in df_rec_f.columns
                if ("nombre" in c.lower() or "razon" in c.lower())
                and "emisor" in c.lower()
            ),
            "NombreEmisor",
        )

        if not rec_pue_16.empty:
            diot_gral = rec_pue_16[[col_rfc_emisor, col_nom_emisor]].copy()
            diot_gral["IVA_16"] = rec_pue_16["_iva_monto"]
            diot_gral["SubTotal"] = diot_gral["IVA_16"] / 0.16
            diot_gral["Total"] = diot_gral["SubTotal"] + diot_gral["IVA_16"]
        else:
            diot_gral = pd.DataFrame(
                columns=[
                    col_rfc_emisor,
                    col_nom_emisor,
                    "SubTotal",
                    "IVA_16",
                    "Total",
                ]
            )

        # REPs de combustibles para la DIOT mensual
        diot_comb_rep = pd.DataFrame()
        if "df_rec_p_raw" in st.session_state and not st.session_state["df_rec_p_raw"].empty:
            df_rec_p_raw_full = st.session_state["df_rec_p_raw"].copy()
            if "Estado" in df_rec_p_raw_full.columns:
                df_rec_p_raw_full = df_rec_p_raw_full[df_rec_p_raw_full["Estado"] == "VIGENTE"]
            if periodo_sel != "Todos los meses" and "Fecha pago" in df_rec_p_raw_full.columns:
                df_rec_p_raw_full["Fecha pago"] = pd.to_datetime(df_rec_p_raw_full["Fecha pago"], errors="coerce")
                df_rec_p_raw_full = df_rec_p_raw_full[df_rec_p_raw_full["Fecha pago"].dt.month.isin(num_meses)]
            
            df_rec_f_raw_all = st.session_state["df_rec_f_raw"].copy()
            mask_comb_global = df_rec_f_raw_all.apply(es_gasto_combustible, axis=1)
            df_comb_global = df_rec_f_raw_all[mask_comb_global].copy()

            col_id_rel = next((c for c in df_rec_p_raw_full.columns if "idpago" in c.lower() or "docto" in c.lower() or "uuid" in c.lower() and "relacionado" in c.lower()), None)
            col_imp_pagado = next((c for c in df_rec_p_raw_full.columns if "impago" in c.lower() or "importepagado" in c.lower() or "monto" in c.lower()), None)
            col_uuid_factura = "UUID" if "UUID" in df_comb_global.columns else None

            if col_id_rel and col_imp_pagado and col_uuid_factura and not df_comb_global.empty:
                pagos_por_factura = df_rec_p_raw_full.groupby(col_id_rel)[col_imp_pagado].sum().reset_index()
                comb_pagados_diot = pd.merge(
                    df_comb_global,
                    pagos_por_factura,
                    left_on=col_uuid_factura,
                    right_on=col_id_rel,
                    how="inner"
                )
                if not comb_pagados_diot.empty:
                    diot_comb_rep = comb_pagados_diot[[col_rfc_emisor, col_nom_emisor, col_imp_pagado]].copy()
                    diot_comb_rep.rename(columns={col_imp_pagado: "Total"}, inplace=True)
                    diot_comb_rep["SubTotal"] = diot_comb_rep["Total"] / 1.16
                    diot_comb_rep["IVA_16"] = diot_comb_rep["SubTotal"] * 0.16
                    diot_comb_rep["SubTotal"] = diot_comb_rep["IVA_16"] / 0.16

        if not rec_pue_comb.empty:
            diot_comb = rec_pue_comb[
                [col_rfc_emisor, col_nom_emisor, "Total"]
            ].copy()
            diot_comb["SubTotal"] = diot_comb["Total"] / 1.16
            diot_comb["IVA_16"] = diot_comb["SubTotal"] * 0.16
            diot_comb["SubTotal"] = diot_comb["IVA_16"] / 0.16
        else:
            diot_comb = pd.DataFrame(
                columns=[
                    col_rfc_emisor,
                    col_nom_emisor,
                    "SubTotal",
                    "IVA_16",
                    "Total",
                ]
            )

        if gastos_manuales_filtrados:
            diot_man = pd.DataFrame(gastos_manuales_filtrados)
            diot_man = diot_man.rename(
                columns={"RFC": col_rfc_emisor, "Nombre": col_nom_emisor}
            )
            diot_man["IVA_16"] = diot_man["IVA"]
            diot_man["SubTotal"] = diot_man["IVA_16"] / 0.16
            diot_man["Total"] = diot_man["SubTotal"] + diot_man["IVA_16"]
            diot_man = diot_man[
                [col_rfc_emisor, col_nom_emisor, "SubTotal", "IVA_16", "Total"]
            ]
        else:
            diot_man = pd.DataFrame(
                columns=[
                    col_rfc_emisor,
                    col_nom_emisor,
                    "SubTotal",
                    "IVA_16",
                    "Total",
                ]
            )

        if not df_rec_p.empty:
            col_rfc_p = next(
                (
                    c
                    for c in df_rec_p.columns
                    if "rfc" in c.lower() and "emisor" in c.lower()
                ),
                col_rfc_emisor,
            )
            col_nom_p = next(
                (
                    c
                    for c in df_rec_p.columns
                    if ("nombre" in c.lower() or "razon" in c.lower())
                    and "emisor" in c.lower()
                ),
                col_nom_emisor,
            )

            diot_p = pd.DataFrame()
            if "TrasladosImpuestoIVA16 - pago" in df_rec_p.columns:
                diot_p[col_rfc_emisor] = df_rec_p[col_rfc_p]
                diot_p[col_nom_emisor] = df_rec_p[col_nom_p]
                diot_p["IVA_16"] = (
                    pd.to_numeric(
                        df_rec_p["TrasladosImpuestoIVA16 - pago"], errors="coerce"
                    )
                    .fillna(0)
                )
                diot_p = diot_p[diot_p["IVA_16"] > 0].copy()
                diot_p["SubTotal"] = diot_p["IVA_16"] / 0.16
                diot_p["Total"] = (
                    df_rec_p["Monto"]
                    if "Monto" in df_rec_p.columns
                    else (diot_p["SubTotal"] + diot_p["IVA_16"])
                )
        else:
            diot_p = pd.DataFrame(
                columns=[
                    col_rfc_emisor,
                    col_nom_emisor,
                    "SubTotal",
                    "IVA_16",
                    "Total",
                ]
            )

        if not rec_egresos.empty:
            diot_egr = rec_egresos[[col_rfc_emisor, col_nom_emisor]].copy()
            diot_egr["IVA_16"] = (
                rec_egresos["IVA Trasladado 16%"].fillna(0)
                if "IVA Trasladado 16%" in rec_egresos.columns
                else 0.0
            )
            diot_egr = diot_egr[diot_egr["IVA_16"] > 0].copy()
            diot_egr["SubTotal"] = diot_egr["IVA_16"] / 0.16
            diot_egr["Total"] = diot_egr["SubTotal"] + diot_egr["IVA_16"]

            diot_egr["SubTotal"] = -diot_egr["SubTotal"]
            diot_egr["IVA_16"] = -diot_egr["IVA_16"]
            diot_egr["Total"] = -diot_egr["Total"]
        else:
            diot_egr = pd.DataFrame(
                columns=[
                    col_rfc_emisor,
                    col_nom_emisor,
                    "SubTotal",
                    "IVA_16",
                    "Total",
                ]
            )

        df_diot_consolidado = pd.concat(
            [diot_gral, diot_comb, diot_comb_rep, diot_man, diot_p, diot_egr], ignore_index=True
        )

        if not df_diot_consolidado.empty:
            tabla_diot = df_diot_consolidado.groupby(
                [col_rfc_emisor, col_nom_emisor], as_index=False
            ).agg({
                "Total": ["count", "sum"],
                "SubTotal": "sum",
                "IVA_16": "sum",
            })

            tabla_diot.columns = [
                "RFC Proveedor",
                "Nombre / Razón Social",
                "Número de Facturas",
                "Total Pagado",
                "Subtotal (Base IVA 16%)",
                "IVA 16%",
            ]
            tabla_diot = tabla_diot[[
                "RFC Proveedor",
                "Nombre / Razón Social",
                "Número de Facturas",
                "Subtotal (Base IVA 16%)",
                "IVA 16%",
                "Total Pagado",
            ]]

            tabla_diot_display = tabla_diot.copy()
            tabla_diot_display["Subtotal (Base IVA 16%)"] = tabla_diot_display[
                "Subtotal (Base IVA 16%)"
            ].apply(lambda x: f"${x:,.2f}")
            tabla_diot_display["IVA 16%"] = tabla_diot_display["IVA 16%"].apply(
                lambda x: f"${x:,.2f}"
            )
            tabla_diot_display["Total Pagado"] = tabla_diot_display[
                "Total Pagado"
            ].apply(lambda x: f"${x:,.2f}")

            st.dataframe(tabla_diot_display, use_container_width=True)

            def convertir_a_excel(df):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="DIOT")
                return output.getvalue()

            excel_data = convertir_a_excel(tabla_diot)
            st.download_button(
                label="📥 Descargar Reporte DIOT en Excel",
                data=excel_data,
                file_name="tabla_diot.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info(
                "No hay gastos gravados con IVA al 16% registrados en este período"
                " para generar la DIOT."
            )

        # ==========================================
        # 10. REPORTE INDEPENDIENTE: TASA 0% Y EXENTOS
        # ==========================================
        st.divider()
        st.subheader("📋 Reporte de Gastos Tasa 0% y Exentos (Agrupado por RFC)")

        lista_ceros_exentos = []

        if not rec_pue_0_directo.empty:
            df_0 = rec_pue_0_directo[[col_rfc_emisor, col_nom_emisor, "_sub_neto", "Total"]].copy()
            df_0["Tipo Tasa"] = "Tasa 0%"
            df_0["SubTotal"] = df_0["_sub_neto"]
            lista_ceros_exentos.append(df_0[[col_rfc_emisor, col_nom_emisor, "Tipo Tasa", "SubTotal", "Total"]])

        if not rec_pue_exento.empty:
            df_ex = rec_pue_exento[[col_rfc_emisor, col_nom_emisor, "_sub_neto", "Total"]].copy()
            df_ex["Tipo Tasa"] = "Exento"
            df_ex["SubTotal"] = df_ex["_sub_neto"]
            lista_ceros_exentos.append(df_ex[[col_rfc_emisor, col_nom_emisor, "Tipo Tasa", "SubTotal", "Total"]])

        if lista_ceros_exentos:
            df_0_ex_consolidado = pd.concat(lista_ceros_exentos, ignore_index=True)

            tabla_0_ex = df_0_ex_consolidado.groupby(
                [col_rfc_emisor, col_nom_emisor, "Tipo Tasa"], as_index=False
            ).agg(
                Num_Facturas=("Total", "count"),
                Subtotal_Monto=("SubTotal", "sum")
            )

            tabla_0_ex.columns = [
                "RFC Proveedor",
                "Nombre / Razón Social",
                "Tipo de Tasa",
                "Número de Facturas",
                "Subtotal / Monto Total",
            ]

            tabla_0_ex_display = tabla_0_ex.copy()
            tabla_0_ex_display["Subtotal / Monto Total"] = tabla_0_ex_display["Subtotal / Monto Total"].apply(lambda x: f"${x:,.2f}")

            st.dataframe(tabla_0_ex_display, use_container_width=True)

            def convertir_0_ex_a_excel(df):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Tasa 0 y Exentos")
                return output.getvalue()

            excel_0_ex_data = convertir_0_ex_a_excel(tabla_0_ex)

            st.download_button(
                label="📥 Descargar Reporte Tasa 0% y Exentos en Excel",
                data=excel_0_ex_data,
                file_name="reporte_tasa_cero_exentos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info("No hay gastos registrados con Tasa 0% o Exentos en este período.")

    else:
        st.info("Carga las Facturas EMITIDAS y RECIBIDAS (archivos obligatorios) para comenzar el análisis mensual.")

with tab_anual:
    st.header("📅 Módulo de Declaración Anual - Personas Físicas")
    st.caption("Consolidación fiscal estricta: PUE directos + PPD validados y efectivamente pagados mediante REP.")

    if "df_emi_f_raw" in st.session_state and "df_rec_f_raw" in st.session_state:
        st.success("✅ ¡Datos del ejercicio cargados correctamente!")

        df_anual_emi = st.session_state["df_emi_f_raw"].copy()
        df_anual_rec = st.session_state["df_rec_f_raw"].copy()

        if "Estado" in df_anual_emi.columns:
            df_anual_emi = df_anual_emi[df_anual_emi["Estado"] == "VIGENTE"]
        if "Estado" in df_anual_rec.columns:
            df_anual_rec = df_anual_rec[df_anual_rec["Estado"] == "VIGENTE"]

        # ==========================================
        # 1. CÁLCULOS ANUALES DE INGRESOS
        # ==========================================
        emi_pue_anual = df_anual_emi[
            (df_anual_emi["Metodo pago"].astype(str).str.startswith("PUE"))
            & (df_anual_emi["Tipo"].astype(str).str.startswith("I"))
        ]
        sub_anual_ingresos = float(emi_pue_anual["SubTotal"].sum())
        iva_anual_ingresos = float(emi_pue_anual["IVA Trasladado 16%"].sum()) if "IVA Trasladado 16%" in emi_pue_anual.columns else 0.0

        if "df_emi_p_raw" in st.session_state and not st.session_state["df_emi_p_raw"].empty:
            df_anual_emi_p = st.session_state["df_emi_p_raw"].copy()
            if "Estado" in df_anual_emi_p.columns:
                df_anual_emi_p = df_anual_emi_p[df_anual_emi_p["Estado"] == "VIGENTE"]
            iva_rep_anual = float(df_anual_emi_p["TrasladosImpuestoIVA16 - pago"].dropna().sum()) if "TrasladosImpuestoIVA16 - pago" in df_anual_emi_p.columns else 0.0
            sub_rep_anual = iva_rep_anual / 0.16 if iva_rep_anual > 0 else 0.0
            sub_anual_ingresos += sub_rep_anual
            iva_anual_ingresos += iva_rep_anual

        # ==========================================
        # 2. FUNCIÓN DE CLASIFICACIÓN SAT ANUAL
        # ==========================================
        def clasificar_y_tratar_gasto_anual(row):
            texto_completo = ""
            for col in ["ClaveProdServ", "Conceptos", "Descripcion", "Concepto"]:
                if col in row and pd.notna(row[col]):
                    texto_completo += str(row[col]) + " "
            texto_completo = texto_completo.upper()

            if "ALMACEN" in texto_completo or "MERCANCIA" in texto_completo or "INVENTARIO" in texto_completo or "SUMINISTROS" in texto_completo or "MATERIALES" in texto_completo:
                rubro = "Almacén / Mercancías / Insumos"
            elif "1510" in texto_completo or "COMBUSTIBLE" in texto_completo or "GASOLINA" in texto_completo or "DIESEL" in texto_completo:
                rubro = "Combustibles y lubricantes"
            elif "HONORARIOS" in texto_completo or "SERVICIOS PROFESIONALES" in texto_completo:
                rubro = "Honorarios"
            elif "ARRENDAMIENTO" in texto_completo or "RENTA" in texto_completo:
                rubro = "Uso o goce temporal de bienes (Rentas)"
            elif "RESTAURANT" in texto_completo or "ALIMENTOS" in texto_completo or "CONSUMO" in texto_completo:
                rubro = "Consumo en restaurantes"
            else:
                rubro = "Gastos generales"

            es_combustible = "1510" in texto_completo or "COMBUSTIBLE" in texto_completo or "GASOLINA" in texto_completo or "DIESEL" in texto_completo
            total_val = float(row["Total"]) if "Total" in row and pd.notna(row["Total"]) else 0.0
            sub_val = float(row["SubTotal"]) if "SubTotal" in row and pd.notna(row["SubTotal"]) else 0.0

            if es_combustible and total_val > 0:
                sub_calculado = total_val / 1.16
                iva_calculado = sub_calculado * 0.16
            else:
                sub_calculado = sub_val
                col_iva_rec = next((c for c in row.index if "iva trasladado 16%" in c.lower() or "iva 16%" in c.lower()), None)
                iva_calculado = float(row[col_iva_rec]) if col_iva_rec and pd.notna(row[col_iva_rec]) else 0.0

            return pd.Series([sub_calculado, iva_calculado, rubro])

        df_anual_rec_i = df_anual_rec[df_anual_rec["Tipo"].astype(str).str.startswith("I")].copy()
        df_anual_rec_i[["_sub_calculado", "_iva_calculado", "Rubro_SAT"]] = df_anual_rec_i.apply(clasificar_y_tratar_gasto_anual, axis=1)

        pue_gastos = df_anual_rec_i[
            df_anual_rec_i["Metodo pago"].astype(str).str.startswith("PUE")
        ].copy()

        ppd_gastos = df_anual_rec_i[
            df_anual_rec_i["Metodo pago"].astype(str).str.startswith("PPD")
        ].copy()

        lista_gastos_efectivos = [pue_gastos]

        if "df_rec_p_raw" in st.session_state and not st.session_state["df_rec_p_raw"].empty:
            df_rec_p = st.session_state["df_rec_p_raw"].copy()
            if "Estado" in df_rec_p.columns:
                df_rec_p = df_rec_p[df_rec_p["Estado"] == "VIGENTE"]

            col_id_rel = next((c for c in df_rec_p.columns if "idpago" in c.lower() or "docto" in c.lower() or "uuid" in c.lower() and "relacionado" in c.lower()), None)
            col_imp_pagado = next((c for c in df_rec_p.columns if "impago" in c.lower() or "importepagado" in c.lower() or "monto" in c.lower()), None)
            col_uuid_factura = "UUID" if "UUID" in df_anual_rec_i.columns else None

            if col_id_rel and col_imp_pagado and col_uuid_factura:
                pagos_por_factura = df_rec_p.groupby(col_id_rel)[col_imp_pagado].sum().reset_index()
                
                ppd_pagadas = pd.merge(
                    ppd_gastos, 
                    pagos_por_factura, 
                    left_on=col_uuid_factura, 
                    right_on=col_id_rel, 
                    how="inner"
                )

                if not ppd_pagadas.empty:
                    if "Total" in ppd_pagadas.columns:
                        ppd_pagadas["Factor_Pagado"] = pd.to_numeric(ppd_pagadas[col_imp_pagado], errors="coerce") / pd.to_numeric(ppd_pagadas["Total"], errors="coerce").replace(0, 1)
                        ppd_pagadas["Factor_Pagado"] = ppd_pagadas["Factor_Pagado"].clip(upper=1.0)
                        
                        ppd_pagadas["_sub_calculado"] = ppd_pagadas["_sub_calculado"] * ppd_pagadas["Factor_Pagado"]
                        ppd_pagadas["_iva_calculado"] = ppd_pagadas["_iva_calculado"] * ppd_pagadas["Factor_Pagado"]
                        ppd_pagadas["Total"] = ppd_pagadas[col_imp_pagado]

                    lista_gastos_efectivos.append(ppd_pagadas)

        rec_efectivo_anual = pd.concat(lista_gastos_efectivos, ignore_index=True) if lista_gastos_efectivos else pue_gastos
        sub_anual_gastos = float(rec_efectivo_anual["_sub_calculado"].sum())

        # ==========================================
        # 3. MÉTRICAS Y RESULTADOS ANUALES
        # ==========================================
        st.divider()
        st.subheader("📊 Balance Consolidado del Ejercicio Anual")

        ac1, ac2, ac3 = st.columns(3)
        ac1.metric("Ingresos Acumulables Anuales", f"${sub_anual_ingresos:,.2f}")
        ac2.metric("Deducciones Autorizadas (Efectivamente Pagadas)", f"${sub_anual_gastos:,.2f}")
        utilidad_anual = sub_anual_ingresos - sub_anual_gastos
        ac3.metric(
            "Utilidad Fiscal Anual", 
            f"${utilidad_anual:,.2f}", 
            delta=("Utilidad Gravable" if utilidad_anual >= 0 else "Pérdida Fiscal"),
            delta_color="normal" if utilidad_anual >= 0 else "inverse"
        )

        # ==========================================
        # 4. TABLA RESUMEN POR RUBRO SAT
        # ==========================================
        st.divider()
        st.subheader("📑 Deducciones Autorizadas Agrupadas por Rubro del SAT")

        if not rec_efectivo_anual.empty:
            resumen_rubros_sat = rec_efectivo_anual.groupby("Rubro_SAT").agg(
                No_Comprobantes=("_sub_calculado", "count"),
                Subtotal_Deducible=("_sub_calculado", "sum"),
                IVA_Asociado=("_iva_calculado", "sum")
            ).reset_index()

            resumen_rubros_sat = resumen_rubros_sat.sort_values(by="Subtotal_Deducible", ascending=False)
            st.table(resumen_rubros_sat)

            st.subheader("🔍 Depuración de Deducciones por Rubro SAT")
            cat_seleccionada = st.selectbox("Selecciona la categoría para revisar los comprobantes:", resumen_rubros_sat["Rubro_SAT"].tolist())

            df_detalle_cat = rec_efectivo_anual[rec_efectivo_anual["Rubro_SAT"] == cat_seleccionada]
            st.dataframe(df_detalle_cat, use_container_width=True)

            csv_anual = resumen_rubros_sat.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Reporte Anual de Deducciones (CSV)",
                data=csv_anual,
                file_name="deducciones_autorizadas_anuales.csv",
                mime="text/csv",
            )
        else:
            st.info("No se encontraron registros de gastos válidos o pagados para este ejercicio.")

    else:
        st.warning("⚠️ Por favor carga primero tus archivos en el **Módulo Mensual**.")

st.markdown("---")
st.caption("💻 **Sistema de Declaraciones + Onefacture** | Diseñado y desarrollado por **Alam E.T.N.**")