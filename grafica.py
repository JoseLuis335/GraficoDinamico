import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.graph_objects as go
import plotly.express as px
import random


# Configurar estilo de Seaborn
sns.set_theme(style="white")

# Cargar datos
ruta_archivo = 'Resumen_Cartera_Morosidad.xlsx'
dfs = {
    "TOTAL CARTERA_resumen": pd.read_excel(ruta_archivo, sheet_name="TOTAL CARTERA_resumen"),
    "PRIMERA COMPRA_resumen": pd.read_excel(ruta_archivo, sheet_name="PRIMERA COMPRA_resumen"),
    "RECOMPRA_resumen": pd.read_excel(ruta_archivo, sheet_name="RECOMPRA_resumen")
}

# Expandir el ancho de la aplicación en Streamlit
st.set_page_config(layout="wide")
# Colores personalizados para cada negocio
# Colores específicos y sus variantes para cada negocio


colores_negocios_variantes = {
    "EL BODEGON": ["#FF0000", "#FF6666", "#FF9999"],  # Variantes de rojo
    "LA MARINA": ["#00FF00", "#66FF66", "#99FF99"],   # Variantes de verde
    "PROGRESSA": ["#800080", "#B266B2", "#D9B3D9"]    # Variantes de morado
}


def crear_grafico_dispersión_multiple(hojas_seleccionadas, negocios_seleccionados, departamento, plazo_meses, eje_x, ejes_y):
    # Verificar que al menos un negocio esté seleccionado
    if not negocios_seleccionados:
        st.warning("Por favor, selecciona al menos un negocio para generar el gráfico.")
        return
    
    # Combinar los datos de las hojas seleccionadas
    df_combined = pd.concat([dfs[hoja] for hoja in hojas_seleccionadas], ignore_index=True)
    
    # Filtrar los datos por negocios, departamento y plazo
    df_filtrado = df_combined[df_combined["NEGOCIO"].isin(negocios_seleccionados)]
    if departamento != "Todos":
        df_filtrado = df_filtrado[df_filtrado["DEPARTAMENTO / PRODUCTO"].isin(departamento)]
    if plazo_meses != "Todos":
        df_filtrado = df_filtrado[df_filtrado["PLAZO MESES"] == plazo_meses]
    # Calcular promedio ponderado si se selecciona "Todos" los departamentos
    if plazo_meses == "Todos":
        # Columnas base de agrupación
        columnas_agrupacion = ['NEGOCIO', 'DEPARTAMENTO / PRODUCTO', 'ID DEPTO', 'TASA', 'RETAIL/PF/MKP','MARGEN']
        
        # Verificar si "MARGEN" existe en el DataFrame
        # Asegurarte de que "MARGEN" exista
        df_filtrado['MARGEN'] = df_filtrado['MARGEN'].fillna(0)
        df_filtrado = df_filtrado[df_filtrado['%USGAAP 90 PONDERADO'] >= 0.3]
  
            # Filtrar por el umbral de CARTERA CAPITAL TOTAL y condiciones adicionales
        df_filtrado = df_filtrado[df_filtrado["CARTERA CAPITAL TOTAL"] > 0]
        df_filtrado = df_filtrado[df_filtrado["TASA"] == "CON TASA"]
        df_filtrado = df_filtrado[~df_filtrado["ID DEPTO"].astype(str).str.match(r"^6\d{4}$")]
        df_filtrado = df_filtrado.dropna(subset=[eje_x] + ejes_y)
        df_filtrado = df_filtrado[(df_filtrado[eje_x] != 0)] 
        
        # Agrupación y cálculo
        df_filtrado = (
            df_filtrado.groupby(columnas_agrupacion)
            .apply(lambda x: pd.Series({
                'CARTERA CAPITAL TOTAL': x['CARTERA CAPITAL TOTAL'].sum(),
                'TASA ACTIVA PONDERADA': (x['TASA ACTIVA PONDERADA'] * x['CARTERA CAPITAL TOTAL']).sum() / x['CARTERA CAPITAL TOTAL'].sum(),
                '$ USGAAP 60 TOTAL': x['$ USGAAP 60 TOTAL'].sum(),
                '$ USGAAP 90 TOTAL': x['$ USGAAP 90 TOTAL'].sum(),
                '%USGAAP 60 PONDERADO': (x['%USGAAP 60 PONDERADO'] * x['CARTERA CAPITAL TOTAL']).sum() / x['CARTERA CAPITAL TOTAL'].sum(),
                '%USGAAP 90 PONDERADO': (x['%USGAAP 90 PONDERADO'] * x['CARTERA CAPITAL TOTAL']).sum() / x['CARTERA CAPITAL TOTAL'].sum(),
                'RRR': (x['RRR'] * x['CARTERA CAPITAL TOTAL']).sum() / x['CARTERA CAPITAL TOTAL'].sum(),
                'RRR (con margen)': (x['RRR (con margen)'] * x['CARTERA CAPITAL TOTAL']).sum() / x['CARTERA CAPITAL TOTAL'].sum()
            }))
            .reset_index(drop=False)
        )
           

    
    # Crear gráfico de dispersión interactivo con múltiples trazas
    fig = go.Figure()
    
    # Agregar una traza por cada negocio y cada eje Y seleccionado
    for negocio in negocios_seleccionados:
        for i, eje_y in enumerate(ejes_y):
            color_index = i % len(colores_negocios_variantes[negocio])  # Seleccionar un color basado en el índice
            color = colores_negocios_variantes[negocio][color_index]    # Asignar el color según el negocio y su variante

            df_filtrado_var = df_filtrado[(df_filtrado["NEGOCIO"] == negocio) & (df_filtrado[eje_y] != 0)]  # Filtrar valores cero en el eje Y actual
            # Crear un texto para el hover con la información adicional
            hover_text = (
                "Departamento/Producto: " + df_filtrado_var["DEPARTAMENTO / PRODUCTO"].astype(str) + "<br>" +
                "Cartera Capital Total: $" + df_filtrado_var["CARTERA CAPITAL TOTAL"].apply(lambda x: f"{x:,.2f}") + "<br>" +
                 #"Morosidad: " + df_filtrado_var["%USGAAP 90 PONDERADO"].apply(lambda x: f"{x:,.2f}")+ "%" +
                df_filtrado_var.apply(
        lambda row: f"{eje_x}: {row[eje_x]:,.2f}<br>{eje_y}: {row[eje_y]:,.2f}",
        axis=1)
                )
            # Calcular el rango de valores para CARTERA CAPITAL TOTAL
            min_size = 5
            max_size = 50
            
            # Normalizar el tamaño de los círculos entre min_size y max_size
            df_filtrado_var['scaled_size'] = (
                (df_filtrado_var['CARTERA CAPITAL TOTAL'] - df_filtrado_var['CARTERA CAPITAL TOTAL'].min()) /
                (df_filtrado_var['CARTERA CAPITAL TOTAL'].max() - df_filtrado_var['CARTERA CAPITAL TOTAL'].min())
            ) * (max_size - min_size) + min_size
            
            # Usar el tamaño escalado para los marcadores
            fig.add_trace(go.Scatter(
                x=df_filtrado_var[eje_x],
                y=df_filtrado_var[eje_y],
                mode='markers+text',
                hovertext=hover_text,  # Agregar el texto para hover
                marker=dict(size=df_filtrado_var['scaled_size'], opacity=1, color=color, line=dict(width=1, color='DarkSlateGrey')),
                text=df_filtrado_var["DEPARTAMENTO / PRODUCTO"],
                name=f"{negocio} - {eje_y}",  # Nombre del eje Y actual incluyendo el negocio
                textfont=dict(size=6),
                textposition='middle right',
                showlegend=False  # Mantener la entrada en la leyenda
            ))
           # Crear un trace adicional con tamaño fijo SOLO para la leyenda
            fig.add_trace(go.Scatter(
                x=[None],  # Punto "ficticio" fuera del gráfico
                y=[None],
                mode='markers',
                marker=dict(
                    size=10,  # Tamaño fijo para la leyenda
                    color=color,
                    line=dict(width=1, color='DarkSlateGrey')
                ),
                name=f"{negocio} - {eje_y}",  # Texto que aparece en la leyenda
                showlegend=True  # Mostrarlo solo en la leyenda
            ))
         
            
    # Configuración del diseño
    fig.update_layout(
       title={
        "text": f"Gráfico de dispersión para {', '.join(negocios_seleccionados)} - {plazo_meses} meses" 
                if plazo_meses != "Todos" 
                else f"Gráfico de dispersión para {', '.join(negocios_seleccionados)} - Todos los periodos",
        "x": 0.40,  # Centra el título horizontalmente
        "y": 0.98,  # Ajusta la posición vertical (más cerca o lejos del gráfico)
        "xanchor": "center",  # Asegura que el título esté anclado en el centro
        "yanchor": "top",  # Asegura que se mida desde la parte superior
    },
        xaxis_title=eje_x,
        yaxis_title=" | ".join(ejes_y),
   

        plot_bgcolor='rgba(240, 240, 240, 1)',  # Color de fondo de la malla
        #paper_bgcolor='rgba(255, 255, 255, 1)',  # Color del fondo general
        margin=dict(t=10, b=2),  # Reduce margen superior e inferior
        legend_title="Variables del eje Y",
        height=600,
    )
    
    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig)
    if not df_filtrado.empty:
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar datos filtrados",
            data=csv,
            file_name="datos_filtrados.csv",
            mime="text/csv"
        )




# Función para crear el gráfico combinado de barras y línea
# Función para crear el gráfico combinado de barras y línea
def crear_grafico_barras_linea(df, negocio, plazo_meses):
    # Filtrar los datos por negocio
    df_filtrado = df[df["NEGOCIO"] == negocio]

    # Filtrar por plazo de meses o agrupar todos los plazos
    if plazo_meses != "Todos":
        df_filtrado = df_filtrado[df_filtrado["PLAZO MESES"] == plazo_meses]
    else:
        # Agrupar los datos cuando se selecciona "Todos"
        columnas_agrupacion = ['DEPARTAMENTO / PRODUCTO']

        # Verificar si "MARGEN" existe y reemplazar valores nulos con 0
        df_filtrado['MARGEN'] = df_filtrado['MARGEN'].fillna(0)
        
        # Aplicar filtros adicionales
        df_filtrado = df_filtrado[df_filtrado['%USGAAP 90 PONDERADO'] >= 0.3]
        df_filtrado = df_filtrado[df_filtrado["CARTERA CAPITAL TOTAL"] > 0]
        df_filtrado = df_filtrado[df_filtrado["TASA"] == "CON TASA"]
        df_filtrado = df_filtrado[~df_filtrado["ID DEPTO"].astype(str).str.match(r"^6\\d{4}$")]

        # Agrupar los datos y calcular promedios ponderados
        df_filtrado = (
            df_filtrado.groupby(columnas_agrupacion)
            .apply(lambda x: pd.Series({
                'CARTERA CAPITAL TOTAL': x['CARTERA CAPITAL TOTAL'].sum(),
                'TASA ACTIVA PONDERADA': (x['TASA ACTIVA PONDERADA'] * x['CARTERA CAPITAL TOTAL']).sum() / x['CARTERA CAPITAL TOTAL'].sum(),
                '$ USGAAP 60 TOTAL': x['$ USGAAP 60 TOTAL'].sum(),
                '$ USGAAP 90 TOTAL': x['$ USGAAP 90 TOTAL'].sum(),
                '%USGAAP 60 PONDERADO': (x['%USGAAP 60 PONDERADO'] * x['CARTERA CAPITAL TOTAL']).sum() / x['CARTERA CAPITAL TOTAL'].sum(),
                '%USGAAP 90 PONDERADO': (x['%USGAAP 90 PONDERADO'] * x['CARTERA CAPITAL TOTAL']).sum() / x['CARTERA CAPITAL TOTAL'].sum(),
                'RRR': (x['RRR'] * x['CARTERA CAPITAL TOTAL']).sum() / x['CARTERA CAPITAL TOTAL'].sum(),
                'RRR (con margen)': (x['RRR (con margen)'] * x['CARTERA CAPITAL TOTAL']).sum() / x['CARTERA CAPITAL TOTAL'].sum()
            }))
            .reset_index(drop=False)
        )

    # Filtrar los datos por umbral de CARTERA CAPITAL TOTAL
    df_filtrado = df_filtrado[df_filtrado["CARTERA CAPITAL TOTAL"] >= 100000]
    df_filtrado = df_filtrado.dropna(subset=["RRR", "%USGAAP 90 PONDERADO"])
    df_filtrado = df_filtrado[df_filtrado["RRR"] != 0]
    df_filtrado = df_filtrado.sort_values(by='RRR', ascending=False)

    # Crear gráfico de barras y línea en plotly
    fig = go.Figure()

    # Gráfico de barras para RRR
    fig.add_trace(go.Bar(
        x=df_filtrado['DEPARTAMENTO / PRODUCTO'],
        y=df_filtrado['RRR'],
        name='RRR',
        marker_color='blue',
        text=[f"{rrr:.1f}x" for rrr in df_filtrado['RRR']],  # Mostrar valores en cada barra
        textposition='outside'
    ))

    # Gráfico de línea para %USGAAP 90 PONDERADO
    fig.add_trace(go.Scatter(
        x=df_filtrado['DEPARTAMENTO / PRODUCTO'],
        y=df_filtrado['%USGAAP 90 PONDERADO'],
        name='%USGAAP 90 PONDERADO',
        mode='lines+markers',
        marker=dict(color='red'),
        line=dict(width=2)
    ))

    # Configuración del diseño
    fig.update_layout(
        #title=f"Gráfico de barras y línea para {negocio} - {plazo_meses} meses" if plazo_meses != "Todos" else f"Gráfico de barras y línea para {negocio} - Todos los periodos",
        xaxis_title="Departamento / Producto",
        margin=dict(t=10, b=10),
        yaxis_title="RRR",
        yaxis2=dict(
            title="%USGAAP 90 PONDERADO",
            overlaying='y',
            side='right'
        ),
        legend=dict(title="Indicadores"),
        height=700
    )

    fig.update_traces(textfont_size=10)
    fig.update_xaxes(tickangle=80)

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig)





# Título de la aplicación
#st.title("Análisis de RRR y Morosidad")

# Widgets para el gráfico de dispersión
#st.header("Gráfico de Dispersión")
# Crear columnas para la disposición
col_filtros, col_graficos = st.columns([1, 6])
# Inicializa valores predeterminados en session_state
# Inicializa valores en session_state
if "hojas_seleccionadas_disp" not in st.session_state:
    st.session_state["hojas_seleccionadas_disp"] = ["TOTAL CARTERA_resumen"]
if "negocios_disp" not in st.session_state:
    st.session_state["negocios_disp"] = ["EL BODEGON"]
if "plazo_meses_disp" not in st.session_state:
    st.session_state["plazo_meses_disp"] = "Todos"
if "departamentos_seleccionados" not in st.session_state:
    st.session_state["departamentos_seleccionados"] = ["Todos"]

# Función para manejar actualizaciones de filtros
def actualizar_filtro(key, value):
    st.session_state[key] = value

# Filtros de selección en la columna de filtros
with col_filtros:
    st.empty()  # Espacio vertical
    
    # Selección de hojas
    hojas_seleccionadas_disp = st.multiselect(
        "Selecciona las hojas:",
        list(dfs.keys()),
        default=st.session_state["hojas_seleccionadas_disp"],
        on_change=actualizar_filtro,
        args=("hojas_seleccionadas_disp", st.session_state["hojas_seleccionadas_disp"])
    )

    # Selección de negocios
    negocios_disp = st.multiselect(
        "Selecciona los negocios:",
        options=list(colores_negocios_variantes.keys()),
        default=st.session_state["negocios_disp"],
        on_change=actualizar_filtro,
        args=("negocios_disp", st.session_state["negocios_disp"])
    )
    
    # Selección de plazo
    plazo_meses_disp = st.selectbox(
        "Selecciona el plazo:",
        options=["Todos"] + list(range(1, 60)),
        index=0 if st.session_state["plazo_meses_disp"] == "Todos" else st.session_state["plazo_meses_disp"],
        on_change=actualizar_filtro,
        args=("plazo_meses_disp", st.session_state["plazo_meses_disp"])
    )
    
    # Filtro dinámico de departamentos
    if hojas_seleccionadas_disp and negocios_disp:
        df_seleccionado = pd.concat([dfs[hoja] for hoja in hojas_seleccionadas_disp], ignore_index=True)
        df_filtrado_por_negocio = df_seleccionado[df_seleccionado["NEGOCIO"].isin(negocios_disp)]
        df_filtrado_por_negocio = df_filtrado_por_negocio[df_filtrado_por_negocio["CARTERA CAPITAL TOTAL"] >= 550000]
        df_filtrado_por_negocio = df_filtrado_por_negocio[df_filtrado_por_negocio["TASA"] == "CON TASA"]
        departamentos_filtrados = df_filtrado_por_negocio["DEPARTAMENTO / PRODUCTO"].unique()

        departamentos_seleccionados = st.multiselect(
            "Selecciona los departamentos:",
            options=["Todos"] + sorted(departamentos_filtrados),
            default=st.session_state["departamentos_seleccionados"],
            on_change=actualizar_filtro,
            args=("departamentos_seleccionados", st.session_state["departamentos_seleccionados"])
        )
    else:
        departamentos_seleccionados = ["Todos"]
        st.session_state["departamentos_seleccionados"] = departamentos_seleccionados
    
    # Determina el valor final del filtro de departamentos
    if "Todos" in departamentos_seleccionados:
        departamento_disp = "Todos"
    else:
        departamento_disp = departamentos_seleccionados

    # Selección de ejes
    opciones_columnas = ["%USGAAP 90 PONDERADO", "%USGAAP 60 PONDERADO", "RRR", "RRR (con margen)", "MARGEN", "TASA ACTIVA PONDERADA"]
    eje_x = st.selectbox(
        "Selecciona la variable para el Eje X:",
        opciones_columnas
    )
    ejes_y = st.multiselect(
        "Selecciona las variables para el Eje Y:",
        opciones_columnas,
        default=["RRR"]
    )

# Mostrar gráfico de dispersión
with col_graficos:
    if ejes_y:
        crear_grafico_dispersión_multiple(hojas_seleccionadas_disp, negocios_disp, departamento_disp, plazo_meses_disp, eje_x, ejes_y)
    else:
        st.warning("Por favor, selecciona al menos una variable para el eje Y.")
          
# Widgets para el gráfico de barras y línea
#st.header("Gráfico de Barras y Línea")
hoja_seleccionada_barras = st.selectbox("Selecciona la hoja:", list(dfs.keys()))

# Carga directamente el DataFrame sin usar pd.concat
df_barras = dfs[hoja_seleccionada_barras]
negocios_barras = dfs["TOTAL CARTERA_resumen"]["NEGOCIO"].unique()
negocio_barras = st.selectbox("Selecciona el negocio:", negocios_barras)
plazo_meses_barras = st.selectbox("Selecciona el plazo (en meses):", options=["Todos"] + list(range(1, 25)), index=1)


#df_barras = pd.concat([dfs[hoja] for hoja in hojas_seleccionadas_barras], ignore_index=True)

# Mostrar gráfico de barras y línea
crear_grafico_barras_linea(df_barras, negocio_barras, plazo_meses_barras)
