"""
Catálogo de Renta de Ropa Deportiva - Nochixtlán.
Este script genera una interfaz web para mostrar productos y vender vía WhatsApp.
"""
import streamlit as st
import pandas as pd
import os
import unicodedata
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="BOLD FIT - Nochixtlán",
    page_icon="👕",
    layout="wide"
)


# --- ESTILOS DE PAGINA WEB (SOLUCIÓN PANTALLA COMPLETA) ---
st.markdown("""
    <style>
    /* 1. Fondo y Base */
    .stApp { background-color: #0d0d0d; }
    
    /* 2. TARJETA BOLD FIT - Optimizada para no romper el zoom */
    .stColumn > div {
        background: rgba(30, 30, 30, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 20px;
        transition: all 0.3s ease;
        margin-bottom: 20px;
        /* IMPORTANTE: Estas líneas permiten que el zoom salga de la caja */
        contain: none !important;
        isolation: auto !important;
    }
    
    /* Efecto de brillo azul sin romper el zoom */
    .stColumn > div:hover {
        border-color: #00d4ff !important;
        box-shadow: 0px 0px 30px rgba(0, 212, 255, 0.3) !important;
    }

    /* 3. LIBERACIÓN TOTAL DEL VISOR DE IMAGEN */
    /* Forzamos al visor a ignorar a su "padre" y cubrir la pantalla */
    div[data-testid="stImageZoomView"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 99999999 !important;
        background-color: rgba(0, 0, 0, 0.98) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* 4. BOTÓN DE CERRAR (X) GIGANTE Y ROJO */
    /* Esto es para que en el celular sea muy fácil de tocar */
    button[aria-label="Close Screen"], 
    button[title="Close Screen"] {
        display: block !important;
        visibility: visible !important;
        position: fixed !important;
        z-index: 100000000 !important;
        background-color: #ff4b4b !important; /* Rojo intenso */
        color: white !important;
        border-radius: 50% !important;
        width: 70px !important;
        height: 70px !important;
        right: 30px !important;
        top: 30px !important;
        opacity: 1 !important;
        border: 3px solid white !important;
    }

    /* 5. Estilos de texto y botones */
    [data-testid="stMetricValue"] { color: #00d4ff !important; }
    .stButton>button {
        background-color: #25d366;
        color: white;
        font-weight: bold;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. FUNCIONES TÉCNICAS


def normalizar_columna(col):
    col = str(col).lower().strip()
    col = ''.join(c for c in unicodedata.normalize(
        'NFD', col) if unicodedata.category(c) != 'Mn')
    return col.replace(" ", "_")


@st.cache_data(ttl=60)
def cargar_datos():
    try:
        # Usamos la URL directamente del secreto
        url = st.secrets["gsheets_url"]

        # Conexión directa (esto suele saltarse el error 404)
        df = pd.read_csv(url)

        # Limpieza de columnas (como ya lo teníamos)
        df.columns = [normalizar_columna(c) for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error crítico de conexión: {e}")
        # Intento de respaldo local si falla la nube
        if os.path.exists("inventario.xlsx"):
            return pd.read_excel("inventario.xlsx")
        return pd.DataFrame()


df = cargar_datos()

# 4. BARRA LATERAL (LOGO + ADMIN + FILTROS)
if os.path.exists("fotos/logo_bueno.png"):
    st.sidebar.image("fotos/logo_bueno.png", use_container_width=True)

with st.sidebar.expander("🔐 Área Administrativa"):
    admin_password = st.text_input("Clave de Acceso:", type="password")

st.sidebar.title("Filtros de Búsqueda")

# 1. Inicialización segura
df_filtrado = df.copy() if not df.empty else pd.DataFrame()

if not df.empty:
    # --- BUSCADOR ---
    search = st.sidebar.text_input("🔍 Buscar:")
    if search:
        # Usamos .get() o verificamos existencia para evitar errores
        col_prod = 'producto' if 'producto' in df_filtrado.columns else df_filtrado.columns[0]
        df_filtrado = df_filtrado[df_filtrado[col_prod].astype(
            str).str.contains(search, case=False, na=False)]

    # --- FILTRO CATEGORÍA (CORREGIDO) ---
    if 'categoria' in df.columns:
        categorias = ["Todos"] + sorted(list(df['categoria'].unique()))
        cat_sel = st.sidebar.selectbox("Selecciona Categoría:", categorias)

        # CAMBIO CLAVE: Aquí es donde aplicamos el filtro al DataFrame
        if cat_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado['categoria'] == cat_sel]
    else:
        st.error("⚠️ No se encontró la columna 'categoria'. Revisa tu Google Sheets.")
        cat_sel = "Todos"

    # --- FILTRO TALLA (CON PROTECCIÓN) ---
    if 'talla' in df.columns:
        tallas = ["Todas"] + sorted(list(df['talla'].unique()))
        talla_sel = st.sidebar.selectbox("Talla:", tallas)
        if talla_sel != "Todas":
            df_filtrado = df_filtrado[df_filtrado['talla'] == talla_sel]
    else:
        st.warning("Columna 'talla' no detectada.")

    # --- FILTRO STOCK ---
    if 'stock' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['stock'] > 0]

# 5. CUERPO PRINCIPAL (Banner y Métricas)
if os.path.exists("fotos/banner.png"):
    st.image("fotos/banner.png", use_container_width=True)
else:
    st.title("👕 Catálogo BOLD FIT")

st.divider()

# Por esta (Mucho más segura):
if admin_password == st.secrets["admin_password"]:
    if not df.empty:
        st.markdown("### 📊 Resumen de Inventario BOLD FIT")
        c1, c2, c3 = st.columns(3)
        c1.metric("Modelos", len(df))
        c2.metric("Tendencia", df['categoria'].mode()[
                  0] if not df['categoria'].empty else "N/A")
        c3.metric("Stock Total", f"{int(df['stock'].sum())} pzs")
        st.divider()

st.write(f"Mostrando **{len(df_filtrado)}** productos en Nochixtlán.")

# 6. GRID DE PRODUCTOS (Optimizado y con Indentación Corregida)
if not df_filtrado.empty:
    productos = df_filtrado.reset_index()

    # Recorremos los productos de 3 en 3
    for i in range(0, len(productos), 3):
        cols = st.columns(3, gap="large")
        batch = productos.iloc[i:i+3]

        for j, (index, row) in enumerate(batch.iterrows()):
            # --- AQUÍ ESTABA EL ERROR DE ESPACIOS ---
            with cols[j]:
                with st.container():
                    # 1. Obtención de imágenes (Frente y Detalle)
                    img1 = row.get('nombre_imagen', 'default.png')
                    img2 = row.get('nombre_imagen_2', None)

                    r1 = os.path.join("fotos", str(img1))
                    r2 = os.path.join("fotos", str(img2)) if img2 else None

                    # 2. Lógica de visualización (Tabs automáticos)
                    if img2 and os.path.exists(r2):
                        tab1, tab2 = st.tabs(["📸 Frente", "🔍 Detalle"])
                        with tab1:
                            st.image(r1, width="stretch")
                        with tab2:
                            st.image(r2, width="stretch")
                    else:
                        if os.path.exists(r1):
                            st.image(r1, width="stretch")
                        else:
                            st.warning("🖼️ Foto pendiente")

                    # 3. Badge de Stock Bajo
                    stock = row.get('stock', 0)
                    if stock <= 2:
                        st.markdown(f'''<div style="background:rgba(255,75,75,0.2);color:#ff4b4b;padding:5px;
                                    border-radius:5px;font-size:0.8em;font-weight:bold;text-align:center;">
                                    🔥 ÚLTIMAS {int(stock)} PIEZAS</div>''', unsafe_allow_html=True)

                    # 4. Información del producto
                    st.markdown(f"### {row.get('producto', 'Sin Nombre')}")
                    st.write(f"**Precio:** ${row.get('precio', 0)} MXN")
                    st.caption(
                        f"Talla: {row.get('talla', 'N/A')} | {row.get('categoria', 'General')}")

                    # 5. Botón de WhatsApp
                    msg = f"Hola BOLD FIT, me interesa: {row.get('producto')} (Talla: {row.get('talla')})"
                    texto_url = msg.replace(' ', '%20')

                    # Enlaces para los dos números
                    link_wa1 = f"https://wa.me/529511198303?text={texto_url}"
                    link_wa2 = f"https://wa.me/529514720440?text={texto_url}"
                    # Creamos dos columnas pequeñas para los botones
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        st.link_button("🛍️ Pedir a Vendedor 1", link_wa1)
                    with col_btn2:
                        st.link_button("🛍️ Pedir a Vendedor 2", link_wa2)
else:
    st.info("No hay productos disponibles.")

# 7. PIE DE PÁGINA (RESTAURADO AL 100%)
st.divider()
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    st.markdown("### 🛡️ Compra Segura")
    st.caption("Entregas personales en Nochixtlán.")
    st.caption("Pagos contra entrega o transferencia.")

with col_f2:
    st.markdown("### 📞 Contacto")
    st.caption("WhatsApp: 951 119 8303")
    st.caption("Horario: 9:00 AM - 8:00 PM")

with col_f3:
    st.markdown("### 📱 Redes Sociales")
    st.markdown(
        "[Instagram BOLD FIT](https://www.instagram.com/bold_fit2024?igsh=NW9oMTg5ZXFtanRt)")

st.markdown("<br><center style='color:#555;'>© 2024 BOLD FIT - Ingeniería en Moda Deportiva</center>",
            unsafe_allow_html=True)
