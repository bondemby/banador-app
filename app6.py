import streamlit as st
from PIL import Image, ImageEnhance
import numpy as np
import os

st.set_page_config(page_title="Bañadores IA", layout="wide")

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

# Mostrar selector gráfico
st.sidebar.header("Selecciona modelo")
modelo_idx = st.sidebar.selectbox("Modelo", range(len(modelos)), format_func=lambda i: modelos[i])

modelo_path = os.path.join(MODELOS_DIR, modelos[modelo_idx])
mascara_path = os.path.join(MASCARAS_DIR, mascaras[modelo_idx])

modelo_img = Image.open(modelo_path).convert("RGB")
mascara_img = Image.open(mascara_path).convert("L").resize(modelo_img.size)

# Cargar patrón
st.sidebar.markdown("### Sube un patrón")
patron_file = st.sidebar.file_uploader("Imagen del patrón", type=["jpg", "jpeg", "png"])

# Sliders
st.sidebar.markdown("### Ajustes visuales")
sombra = st.sidebar.slider("Sombras", 0.5, 1.25, DEFAULT_VALUES["Sombras"], step=0.05)
color_boost = st.sidebar.slider("Color Boost", 0.5, 5.0, DEFAULT_VALUES["Color Boost"], step=0.25)
contraste = st.sidebar.slider("Contraste", 0.5, 4.0, DEFAULT_VALUES["Contraste"], step=0.25)
repeticion = st.sidebar.slider("Tamaño patrón", 1, 10, DEFAULT_VALUES["Tamaño patrón"])

# Botón reset
if st.sidebar.button("🔄 Reset valores"):
    st.experimental_rerun()

# Aplicación del patrón
def aplicar_patron(modelo, mascara, patron, sombras, boost, contrast, tile_scale):
    modelo_np = np.array(modelo).astype(np.float32)
    mascara_np = np.array(mascara) / 255.0

    # Crear patrón en mosaico
    patron = patron.resize((modelo.width // tile_scale, modelo.height // tile_scale))
    mosaico = Image.new("RGB", modelo.size)
    for x in range(0, modelo.width, patron.width):
        for y in range(0, modelo.height, patron.height):
            mosaico.paste(patron, (x, y))
    mosaico = mosaico.crop((0, 0, modelo.width, modelo.height))

    # Ajustes visuales
    mosaico = ImageEnhance.Color(mosaico).enhance(boost)
    mosaico = ImageEnhance.Contrast(mosaico).enhance(contrast)
    mosaico_np = np.array(mosaico).astype(np.float32)

    # Combinar
    out_np = modelo_np * (1 - mascara_np[..., None] * sombras) + mosaico_np * (mascara_np[..., None])
    out_np = np.clip(out_np, 0, 255).astype(np.uint8)
    return Image.fromarray(out_np)

# Mostrar resultado
st.markdown("## Resultado")
if patron_file:
    patron_img = Image.open(patron_file).convert("RGB")
    resultado = aplicar_patron(modelo_img, mascara_img, patron_img, sombra, color_boost, contraste, repeticion)
    st.image(resultado, use_container_width=True)
else:
    st.image(modelo_img, caption="Esperando patrón...", use_container_width=True)