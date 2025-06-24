import streamlit as st
from PIL import Image, ImageEnhance
import numpy as np
import os

# Configuración de página con sidebar siempre visible
st.set_page_config(page_title="Bañadores IA", layout="wide", initial_sidebar_state="expanded")

# CSS para fijar altura de imagen
st.markdown("""
    <style>
    img {
        max-height: 500px !important;
        height: auto;
    }
    </style>
""", unsafe_allow_html=True)

# Directorios
MODELOS_DIR = "modelos"
MASCARAS_DIR = "mascaras"

# Valores por defecto
DEFAULT_VALUES = {
    "Sombras": 0.8,
    "Color Boost": 1.75,
    "Contraste": 2.5,
    "Tamaño patrón": 2,
}

# Cargar modelos predefinidos
modelos = sorted([f for f in os.listdir(MODELOS_DIR) if f.endswith(('.jpg', '.png'))])
mascaras = sorted([f for f in os.listdir(MASCARAS_DIR) if f.endswith(('.png'))])

# Selector gráfico de modelos
st.sidebar.header("Selecciona modelo")
modelo_idx = st.sidebar.selectbox("Modelo", range(len(modelos)), format_func=lambda i: modelos[i])

modelo_path = os.path.join(MODELOS_DIR, modelos[modelo_idx])
mascara_path = os.path.join(MASCARAS_DIR, mascaras[modelo_idx])

modelo_img = Image.open(modelo_path).convert("RGB")
mascara_img = Image.open(mascara_path).convert("L").resize(modelo_img.size)

# Subir patrón
st.sidebar.markdown("### Sube un patrón")
patron_file = st.sidebar.file_uploader("Imagen del patrón", type=["jpg", "jpeg", "png"])

# Estado para resetear
if "reset" not in st.session_state:
    st.session_state.reset = False

if st.sidebar.button("🔄 Reset valores"):
    st.session_state.reset = True

# Sliders con rangos de app5.py
sombra = st.sidebar.slider(
    "Sombras (0 = sin sombras, 1.25 = sombras marcadas)", 0.0, 1.25,
    value=DEFAULT_VALUES["Sombras"] if st.session_state.reset else st.session_state.get("sombra", DEFAULT_VALUES["Sombras"]),
    step=0.01, key="sombra"
)

color_boost = st.sidebar.slider(
    "Color Boost (viveza)", 0.8, 3.0,
    value=DEFAULT_VALUES["Color Boost"] if st.session_state.reset else st.session_state.get("color_boost", DEFAULT_VALUES["Color Boost"]),
    step=0.05, key="color_boost"
)

contraste = st.sidebar.slider(
    "Contraste final (solo en el bañador)", 0.5, 4.0,
    value=DEFAULT_VALUES["Contraste"] if st.session_state.reset else st.session_state.get("contraste", DEFAULT_VALUES["Contraste"]),
    step=0.05, key="contraste"
)

repeticion = st.sidebar.slider(
    "Tamaño del patrón (1 = grande, 10 = pequeño)", 1, 10,
    value=DEFAULT_VALUES["Tamaño patrón"] if st.session_state.reset else st.session_state.get("repeticion", DEFAULT_VALUES["Tamaño patrón"]),
    step=1, key="repeticion"
)

# Reset de bandera
if st.session_state.reset:
    st.session_state.reset = False

# Función para aplicar patrón
def aplicar_patron(modelo, mascara, patron, sombras, boost, contrast, tile_scale):
    modelo_np = np.array(modelo).astype(np.float32) / 255.0
    mascara_np = np.array(mascara).astype(np.float32) / 255.0

    pattern_width = max(8, int(modelo.size[0] / tile_scale))
    pattern_height = max(8, int(modelo.size[1] / tile_scale))
    patron_resized = patron.resize((pattern_width, pattern_height))

    patron_mosaic = Image.new("RGB", modelo.size)
    for y in range(0, modelo.size[1], patron_resized.height):
        for x in range(0, modelo.size[0], patron_resized.width):
            patron_mosaic.paste(patron_resized, (x, y))
    patron_mosaic = patron_mosaic.crop((0, 0, modelo.size[0], modelo.size[1]))

    patron_mosaic = ImageEnhance.Brightness(patron_mosaic).enhance(1.1)
    patron_mosaic = ImageEnhance.Contrast(patron_mosaic).enhance(1.1)

    patron_np = np.array(patron_mosaic).astype(np.float32) / 255.0

    gray_np = np.mean(modelo_np, axis=2)
    light_map = np.stack([gray_np]*3, axis=2)
    adjusted_light_map = (1 - sombras) + sombras * light_map
    blended_pattern = patron_np * adjusted_light_map
    enhanced_pattern = np.clip(blended_pattern ** (1 / boost), 0, 1)

    contrasted_pattern = 0.5 + contrast * (enhanced_pattern - 0.5)
    contrasted_pattern = np.clip(contrasted_pattern, 0, 1)

    mask_rgb = np.stack([mascara_np]*3, axis=2)
    banador_np = contrasted_pattern * mask_rgb
    fondo_np = modelo_np * (1 - mask_rgb)
    result_np = fondo_np + banador_np

    result_img = Image.fromarray((np.clip(result_np, 0, 1) * 255).astype(np.uint8))
    return result_img

# Mostrar resultado
st.markdown("## Resultado")
if patron_file:
    patron_img = Image.open(patron_file).convert("RGB")
    resultado = aplicar_patron(modelo_img, mascara_img, patron_img, sombra, color_boost, contraste, repeticion)
    st.image(resultado, use_column_width=True)
else:
    st.image(modelo_img, caption="Esperando patrón...", use_column_width=True)
