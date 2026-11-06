"""
Dashboard - Ruta Descubriendo Saberes (Saber Pro)
Ejecutar localmente:  streamlit run app.py
"""
import io
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------------
# Configuración
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Ruta Descubriendo Saberes",
    page_icon="📊",
    layout="wide",
)

ARCHIVO_EXCEL = "Descubriendo Saberes.xlsx"  # debe estar junto a app.py
COLUMNAS = ["CODIGO", "CORREO", "PROGRAMA", "ESTADO"]
ORDEN_ESTADOS = [
    "Está en curso, pero no inicia",
    "No aparece en Curso",
    "Falta Completar",
]
COLORES = {
    "Está en curso, pero no inicia": "#F59E0B",  # ámbar
    "No aparece en Curso": "#EF4444",            # rojo
    "Falta Completar": "#3B82F6",                # azul
}
COLOR_TOTAL = "#0F766E"


def color_estado(estado: str) -> str:
    return COLORES.get(estado, "#6B7280")


# ----------------------------------------------------------------------------
# Estilos
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem;}
    .banner {
        background: linear-gradient(120deg, #0F766E 0%, #1D4ED8 100%);
        padding: 1.6rem 2rem; border-radius: 16px; color: #fff;
        margin-bottom: 1.4rem; box-shadow: 0 4px 16px rgba(0,0,0,.15);
    }
    .banner h1 {margin: 0; font-size: 2rem; color: #fff; padding: 0;}
    .banner p {margin: .4rem 0 0; opacity: .92; font-size: .95rem;}
    .card {
        background: #fff; border-radius: 14px; padding: 1rem 1.2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,.10);
        border-left: 7px solid var(--c); height: 100%;
    }
    .card .lbl {font-size: .85rem; color: #4B5563; min-height: 2.2em;}
    .card .val {font-size: 2.1rem; font-weight: 800; color: #111827; line-height: 1.2;}
    .card .pct {font-size: 1rem; font-weight: 700; color: var(--c);}
    h2, h3 {margin-top: 1.2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Carga y limpieza de datos
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando datos...")
def cargar_datos(contenido: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(contenido), dtype=str)
    df.columns = [str(c).strip().upper() for c in df.columns]

    faltantes = [c for c in COLUMNAS if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan las columnas: {', '.join(faltantes)}")

    df = df[COLUMNAS].fillna("")
    for col in COLUMNAS:
        df[col] = df[col].str.strip()

    df["CODIGO"] = df["CODIGO"].str.replace(r"\.0$", "", regex=True)
    df["CORREO"] = df["CORREO"].str.lower()
    df["PROGRAMA"] = df["PROGRAMA"].str.upper()  # programa en MAYÚSCULAS
    return df.reset_index(drop=True)


def obtener_contenido() -> bytes | None:
    """Lee el Excel del repositorio; si no existe, permite subirlo."""
    ruta = Path(__file__).parent / ARCHIVO_EXCEL
    if ruta.exists():
        return ruta.read_bytes()

    st.warning(f"No encontré «{ARCHIVO_EXCEL}» junto al script. Súbelo aquí:")
    subido = st.file_uploader("Archivo Excel", type=["xlsx", "xls"])
    return subido.getvalue() if subido else None


def a_excel(listado: pd.DataFrame, resumen: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        listado.to_excel(writer, index=False, sheet_name="Pendientes")
        resumen.to_excel(writer, sheet_name="Resumen por programa")
    return buffer.getvalue()


def tarjeta(etiqueta: str, valor: int, pct: float | None, color: str) -> str:
    pct_html = f'<div class="pct">{pct:.1f}% del total</div>' if pct is not None else ""
    return (
        f'<div class="card" style="--c:{color}">'
        f'<div class="lbl">{etiqueta}</div>'
        f'<div class="val">{valor:,}</div>{pct_html}</div>'
    )


# ----------------------------------------------------------------------------
# Encabezado
# ----------------------------------------------------------------------------
st.markdown(
    """
    <div class="banner">
        <h1>📊 Ruta Descubriendo Saberes</h1>
        <p>Seguimiento de estudiantes con la ruta pendiente por realizar o culminar ·
        Fortalecimiento de competencias Saber Pro · Registro de notas en Génesis ·
        Meta: noviembre 2026</p>
    </div>
    """,
    unsafe_allow_html=True,
)

contenido = obtener_contenido()
if contenido is None:
    st.stop()

try:
    df = cargar_datos(contenido)
except Exception as e:
    st.error(f"No pude leer el archivo: {e}")
    st.stop()

# Estados en orden lógico (+ cualquier otro que aparezca)
estados = [e for e in ORDEN_ESTADOS if e in df["ESTADO"].unique()]
estados += sorted(set(df["ESTADO"].unique()) - set(estados))

# ----------------------------------------------------------------------------
# Buscador por código
# ----------------------------------------------------------------------------
st.subheader("🔎 Buscar estudiante por código")
codigo = st.text_input(
    "Código estudiantil",
    placeholder="Escribe el código completo o parte de él",
).strip()

if codigo:
    res = df[df["CODIGO"].str.contains(codigo, case=False, regex=False)]
    if res.empty:
        st.info("No se encontró ningún estudiante con ese código.")
    else:
        st.success(f"{len(res)} resultado(s)")
        st.dataframe(res, use_container_width=True, hide_index=True)

st.divider()

# ----------------------------------------------------------------------------
# Filtros (barra lateral)
# ----------------------------------------------------------------------------
st.sidebar.header("🎛️ Filtros")
programas = sorted(df["PROGRAMA"].unique())
sel_programas = st.sidebar.multiselect("Programa", programas, default=programas)
sel_estados = st.sidebar.multiselect("Estado", estados, default=estados)

filtrado = df[df["PROGRAMA"].isin(sel_programas) & df["ESTADO"].isin(sel_estados)]
total = len(filtrado)

if total == 0:
    st.warning("No hay estudiantes con los filtros seleccionados.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Mostrando **{total:,}** de **{len(df):,}** estudiantes "
    f"({total / len(df) * 100:.1f}%)."
)

# ----------------------------------------------------------------------------
# Indicadores con porcentaje
# ----------------------------------------------------------------------------
st.subheader("Resumen general")
cols = st.columns(1 + len(estados))
cols[0].markdown(
    tarjeta("Total pendientes", total, 100.0, COLOR_TOTAL), unsafe_allow_html=True
)
for col, estado in zip(cols[1:], estados):
    n = int((filtrado["ESTADO"] == estado).sum())
    col.markdown(
        tarjeta(estado, n, n / total * 100, color_estado(estado)),
        unsafe_allow_html=True,
    )

st.write("")

# ----------------------------------------------------------------------------
# Gráficos con porcentajes
# ----------------------------------------------------------------------------
escala = alt.Scale(domain=estados, range=[color_estado(e) for e in estados])

g1, g2 = st.columns(2)

with g1:
    st.markdown("#### Estudiantes por estado")
    d_estado = (
        filtrado["ESTADO"].value_counts().reindex(estados).fillna(0).astype(int)
        .rename_axis("ESTADO").reset_index(name="N")
    )
    d_estado["PCT"] = d_estado["N"] / total * 100
    d_estado["ETIQUETA"] = d_estado.apply(
        lambda r: f"{r['N']:,} ({r['PCT']:.1f}%)", axis=1
    )
    base = alt.Chart(d_estado).encode(
        x=alt.X("ESTADO:N", sort=estados, title=None,
                axis=alt.Axis(labelAngle=0, labelLimit=140)),
        y=alt.Y("N:Q", title="Estudiantes"),
        color=alt.Color("ESTADO:N", scale=escala, legend=None),
        tooltip=["ESTADO", "N", alt.Tooltip("PCT:Q", format=".1f", title="% del total")],
    )
    barras = base.mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
    texto = base.mark_text(dy=-10, fontWeight="bold", fontSize=13).encode(
        text="ETIQUETA:N"
    )
    st.altair_chart((barras + texto).properties(height=340), use_container_width=True)

with g2:
    st.markdown("#### Estudiantes por programa")
    d_prog = (
        filtrado["PROGRAMA"].value_counts()
        .rename_axis("PROGRAMA").reset_index(name="N")
    )
    d_prog["PCT"] = d_prog["N"] / total * 100
    d_prog["ETIQUETA"] = d_prog.apply(
        lambda r: f"{r['N']:,} ({r['PCT']:.1f}%)", axis=1
    )
    base = alt.Chart(d_prog).encode(
        y=alt.Y("PROGRAMA:N", sort="-x", title=None, axis=alt.Axis(labelLimit=260)),
        x=alt.X("N:Q", title="Estudiantes"),
        tooltip=["PROGRAMA", "N", alt.Tooltip("PCT:Q", format=".1f", title="% del total")],
    )
    barras = base.mark_bar(color=COLOR_TOTAL, cornerRadiusTopRight=8,
                           cornerRadiusBottomRight=8)
    texto = base.mark_text(align="left", dx=5, fontWeight="bold").encode(
        text="ETIQUETA:N"
    )
    alto = max(340, 34 * len(d_prog))
    st.altair_chart((barras + texto).properties(height=alto), use_container_width=True)

# ----------------------------------------------------------------------------
# Tablas Programa × Estado (cantidad y porcentaje)
# ----------------------------------------------------------------------------
st.markdown("#### Programa × Estado")

cruce = (
    pd.crosstab(filtrado["PROGRAMA"], filtrado["ESTADO"])
    .reindex(columns=estados, fill_value=0)
)
cruce["TOTAL"] = cruce.sum(axis=1)
cruce = cruce.sort_values("TOTAL", ascending=False)

# Cantidad + % del total general
tabla_cant = cruce.copy()
tabla_cant["% DEL TOTAL"] = tabla_cant["TOTAL"] / total * 100

# % de cada estado dentro de cada programa (cada fila suma 100 %)
tabla_pct = cruce[estados].div(cruce["TOTAL"], axis=0) * 100

tab1, tab2 = st.tabs(["🔢 Cantidad", "📈 Porcentaje por programa"])

with tab1:
    st.dataframe(
        tabla_cant,
        use_container_width=True,
        column_config={
            "% DEL TOTAL": st.column_config.ProgressColumn(
                "% DEL TOTAL", format="%.1f%%", min_value=0, max_value=100
            ),
        },
    )

with tab2:
    st.caption("Distribución de los estados dentro de cada programa (cada fila suma 100 %).")
    st.dataframe(
        tabla_pct,
        use_container_width=True,
        column_config={
            e: st.column_config.ProgressColumn(
                e, format="%.1f%%", min_value=0, max_value=100
            )
            for e in estados
        },
    )

# ----------------------------------------------------------------------------
# Listado y descargas
# ----------------------------------------------------------------------------
st.subheader("📋 Listado de estudiantes")
st.dataframe(filtrado, use_container_width=True, hide_index=True)

resumen_excel = cruce.join(tabla_cant["% DEL TOTAL"].round(1))

d1, d2, _ = st.columns([1, 1, 3])
d1.download_button(
    "⬇️ Descargar Excel",
    data=a_excel(filtrado, resumen_excel),
    file_name="Descubriendo_Saberes_listado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
d2.download_button(
    "⬇️ Descargar CSV",
    data=filtrado.to_csv(index=False).encode("utf-8-sig"),
    file_name="Descubriendo_Saberes_listado.csv",
    mime="text/csv",
)
