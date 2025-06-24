import streamlit as st
from PIL import Image, ImageEnhance
import numpy as np
import io

def aplicar_patron_con_sombras_y_color(img_base, img_mask, img_pattern, alpha, color_boost, curva_contraste, scale_factor):
    img_mask = img_mask.resize(img_base.size)

    # Ajustar tamaño del patrón según el factor de escala
    pattern_width = max(8, int(img_base.size[0] / scale_factor))
    pattern_height = max(8, int(img_base.size[1] / scale_factor))
    pattern_resized = img_pattern.resize((pattern_width, pattern_height))

    pattern_mosaic = Image.new("RGB", img_base.size)
    for y in range(0, img_base.size[1], pattern_resized.height):
        for x in range(0, img_base.size[0], pattern_resized.width):
            pattern_mosaic.paste(pattern_resized, (x, y))

    pattern_mosaic = ImageEnhance.Brightness(pattern_mosaic).enhance(1.1)
    pattern_mosaic = ImageEnhance.Contrast(pattern_mosaic).enhance(1.1)

    base_np = np.array(img_base).astype(np.float32) / 255.0
    mask_np = np.array(img_mask.convert("L")).astype(np.float32) / 255.0
    pattern_np = np.array(pattern_mosaic).astype(np.float32) / 255.0

    # Obtener mapa de luz en escala de grises de la imagen base
    gray_np = np.mean(base_np, axis=2)
    light_map = np.stack([gray_np]*3, axis=2)
    adjusted_light_map = (1 - alpha) + alpha * light_map

    # Aplicar iluminación y color boost al patrón
    blended_pattern = pattern_np * adjusted_light_map
    enhanced_pattern = np.clip(blended_pattern ** (1 / color_boost), 0, 1)

    # Aplicar curva de contraste solo al patrón mejorado
    contrasted_pattern = 0.5 + curva_contraste * (enhanced_pattern - 0.5)
    contrasted_pattern = np.clip(contrasted_pattern, 0, 1)

    # Aplicar solo dentro de la máscara
    mask_rgb = np.stack([mask_np]*3, axis=2)
    banador_np = contrasted_pattern * mask_rgb
    fondo_np = base_np * (1 - mask_rgb)
    result_np = fondo_np + banador_np

    result_img = Image.fromarray((np.clip(result_np, 0, 1) * 255).astype(np.uint8))

    return result_img

# Interfaz Streamlit
st.title("🩳 Aplicador Avanzado (efectos solo en el bañador)")
st.markdown("Aplica sombras, color y contraste sólo en la zona del bañador usando la máscara. También puedes escalar el patrón.")

col1, col2, col3 = st.columns(3)
with col1:
    base_file = st.file_uploader("Imagen base", type=["jpg", "jpeg", "png"])
with col2:
    mask_file = st.file_uploader("Máscara (blanco y negro o con transparencia)", type=["png", "jpg", "jpeg"])
with col3:
    pattern_file = st.file_uploader("Patrón", type=["jpg", "jpeg", "png"])

# Valores por defecto
default_alpha = 0.8
default_color_boost = 1.75
default_curva_contraste = 2.5
default_scale_factor = 2

# Botón para resetear
if st.button("🔁 Resetear valores a defecto"):
    st.session_state["alpha"] = default_alpha
    st.session_state["color_boost"] = default_color_boost
    st.session_state["curva_contraste"] = default_curva_contraste
    st.session_state["scale_factor"] = default_scale_factor

alpha = st.slider("Sombras (0 = sin sombras, 1.25 = sombras marcadas)", 0.0, 1.25, st.session_state.get("alpha", default_alpha), 0.01, key="alpha")
color_boost = st.slider("Color Boost (viveza)", 0.8, 3.0, st.session_state.get("color_boost", default_color_boost), 0.05, key="color_boost")
curva_contraste = st.slider("Contraste final (solo en el bañador)", 0.5, 4.0, st.session_state.get("curva_contraste", default_curva_contraste), 0.05, key="curva_contraste")
scale_factor = st.slider("Tamaño del patrón (1 = grande, 10 = pequeño)", 1, 10, st.session_state.get("scale_factor", default_scale_factor), 1, key="scale_factor")

if base_file and mask_file and pattern_file:
    img_base = Image.open(base_file).convert("RGB")
    img_mask = Image.open(mask_file)
    img_pattern = Image.open(pattern_file).convert("RGB")

    resultado = aplicar_patron_con_sombras_y_color(img_base, img_mask, img_pattern, alpha, color_boost, curva_contraste, scale_factor)

    st.subheader("Resultado")
    st.image(resultado, use_container_width=True)

    buf = io.BytesIO()
    resultado.save(buf, format="PNG")
    byte_im = buf.getvalue()
    st.download_button("Descargar imagen", data=byte_im, file_name="banador_resultado.png", mime="image/png")