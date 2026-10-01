import os
import time
import glob
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image
import streamlit as st
from gtts import gTTS
from deep_translator import GoogleTranslator

# ---------- Configuración del Sitio ----------
st.set_page_config(
    page_title="LingoScan | OCR & Voice",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Estilos Personalizados Renovados (Tema Slate/Indigo Moderno) ----------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    :root {
        --bg-main: #FAFAFA;
        --bg-sidebar: #0F172A;
        --accent-color: #6366F1;
        --accent-hover: #4F46E5;
        --text-dark: #1E293B;
        --text-muted: #64748B;
        --card-bg: #FFFFFF;
    }

    .stApp {
        background-color: var(--bg-main) !important;
        color: var(--text-dark);
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Estilos de la barra lateral (Modo Oscuro Elegante) */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
    }

    section[data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }

    /* Encabezado Principal Banner */
    .hero-container {
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white !important;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.3);
    }

    .hero-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(8px);
        padding: 0.3rem 0.8rem;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0.8rem;
    }

    .hero-title {
        font-size: 2.3rem;
        font-weight: 700;
        margin: 0;
        color: #FFFFFF !important;
        line-height: 1.2;
    }

    .hero-subtitle {
        font-size: 1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
        color: #E0E7FF !important;
        max-width: 600px;
    }

    /* Estilos de Tarjetas / Contenedores */
    .custom-card {
        background: var(--card-bg);
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }

    .card-title {
        font-weight: 700;
        font-size: 1rem;
        color: var(--accent-color) !important;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }

    /* Botón Principal */
    .stButton>button {
        border-radius: 10px !important;
        border: none !important;
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
    }

    textarea, input {
        border-radius: 10px !important;
        border: 1px solid #CBD5E1 !important;
    }

    div[data-testid="stNotification"] {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Mapeos de Idiomas y Configuración de Voces ----------
IDIOMAS = {
    "Español": "es",
    "Inglés": "en",
    "Italiano": "it",
    "Francés": "fr",
    "Alemán": "de",
    "Japonés": "ja",
    "Coreano": "ko",
    "Chino (Simplificado)": "zh-CN",
    "Bengalí": "bn"
}

ACENTOS = {
    "Global / Estándar": "com",
    "Latinoamérica (MX)": "com.mx",
    "Reino Unido (UK)": "co.uk",
    "Estados Unidos (US)": "com",
    "Canadá": "ca",
    "Australia": "com.au",
    "Irlanda": "ie",
    "Sudáfrica": "co.za",
    "India": "co.in"
}

# ---------- Limpieza Interna de Cache de Audio ----------
def autolimpieza_temporales(dias=7):
    if not os.path.exists("temp"):
        os.makedirs("temp")
    archivos = glob.glob("temp/*.mp3")
    ahora = time.time()
    limite = dias * 86400
    for f in archivos:
        if os.stat(f).st_mtime < ahora - limite:
            try:
                os.remove(f)
            except OSError:
                pass

autolimpieza_temporales(7)

def procesar_traduccion_voz(src_lang, dest_lang, texto, acento):
    # Traducción mediante deep-translator
    texto_traducido = GoogleTranslator(source=src_lang, target=dest_lang).translate(texto)
    
    # Generación de voz con gTTS
    gtts_lang = dest_lang.lower()
    tts = gTTS(texto_traducido, lang=gtts_lang, tld=acento, slow=False)
    
    prefijo = re.sub(r'[^a-zA-Z0-9]', '', texto[:12]).strip() or "voice_note"
    nombre_archivo = f"{prefijo}_{int(time.time())}.mp3"
    ruta_archivo = os.path.join("temp", nombre_archivo)
    tts.save(ruta_archivo)
    return ruta_archivo, texto_traducido

# ---------- Encabezado (Hero Section) ----------
st.markdown("""
    <div class="hero-container">
        <span class="hero-badge">🚀 LingoScan v2.0</span>
        <h1 class="hero-title">Reconocimiento Óptico y Locución Inteligente</h1>
        <p class="hero-subtitle">Transforma imágenes con texto escrito en archivos de voz multilingües al instante de manera rápida y precisa.</p>
    </div>
""", unsafe_allow_html=True)

# ---------- Menú Lateral (Panel de Control) ----------
with st.sidebar:
    if os.path.exists("traductor2.png"):
        st.image("traductor2.png", width=130)
    
    st.markdown("## ⚙️ Panel de Control")
    st.markdown("---")
    
    st.markdown("### 📥 Entrada de Imagen")
    metodo = st.radio(
        "Método de captura:",
        ("📂 Subir archivo", "📸 Captura con cámara"),
        help="Elige entre subir un documento guardado o usar la cámara en vivo."
    )
    
    st.markdown("---")
    st.markdown("### 🎨 Ajustes Visuales")
    aplicar_filtro = st.toggle("Invertir Contraste (Fondo Oscuro)", help="Actívalo si el texto de la imagen es blanco o de color claro.")
    
    st.markdown("---")
    st.markdown("### 🌐 Opciones de Idioma")
    in_lang_name = st.selectbox("Idioma en la imagen:", list(IDIOMAS.keys()), index=0)
    out_lang_name = st.selectbox("Traducir al idioma:", list(IDIOMAS.keys()), index=1)
    accent_name = st.selectbox("Acento de la voz:", list(ACENTOS.keys()), index=0)
    
    display_output_text = st.checkbox("Mostrar transcripción de traducción", value=True)

# ---------- Captura / Carga de la Imagen ----------
img_rgb = None

if metodo == "📸 Captura con cámara":
    img_buffer = st.camera_input("Apunta tu cámara hacia el texto:")
    if img_buffer is not None:
        bytes_data = img_buffer.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        if aplicar_filtro:
            cv2_img = cv2.bitwise_not(cv2_img)
        img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
else:
    uploaded_file = st.file_uploader("Arrastra tu documento o haz clic para subir:", type=["png", "jpg", "jpeg", "webp"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        img_np = np.array(image)
        
        if len(img_np.shape) == 3 and img_np.shape[2] == 4:
            img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB)
            
        if aplicar_filtro:
            img_np = cv2.bitwise_not(img_np)
            
        img_rgb = img_np

# ---------- Procesamiento Principal y Resultados ----------
if img_rgb is not None:
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown('<div class="card-title">🖼️ Vista Previa del Documento</div>', unsafe_allow_html=True)
        st.image(img_rgb, use_container_width=True)
        
    with col2:
        st.markdown('<div class="card-title">🔍 Lectura OCR de Texto</div>', unsafe_allow_html=True)
        
        try:
            with st.spinner("Escaneando el contenido de la imagen..."):
                ocr_lang_code = IDIOMAS[in_lang_name]
                tess_lang = "chi_sim" if ocr_lang_code == "zh-CN" else ocr_lang_code
                
                texto_extraido = pytesseract.image_to_string(img_rgb, lang=tess_lang)

            if texto_extraido.strip():
                st.text_area(
                    label="Texto extraído (editable):",
                    value=texto_extraido,
                    height=160,
                    help="Puedes corregir faltas de ortografía o símbolos antes de traducir."
                )
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("✨ Procesar Traducción y Sintetizar Voz"):
                    with st.spinner("Traduciendo el texto y generando la locución..."):
                        audio_path, texto_traducido = procesar_traduccion_voz(
                            IDIOMAS[in_lang_name],
                            IDIOMAS[out_lang_name],
                            texto_extraido,
                            ACENTOS[accent_name]
                        )
                        
                        st.balloons() # Efecto visual de éxito
                        
                        st.markdown("### 🔊 Reproductor de Audio")
                        with open(audio_path, "rb") as audio_file:
                            st.audio(audio_file.read(), format="audio/mp3", start_time=0)
                            
                        if display_output_text:
                            st.markdown("### 📄 Resultado de la Traducción")
                            st.info(texto_traducido)
            else:
                st.warning("⚠️ No pudimos detectar caracteres legibles en esta imagen. Prueba ajustando la iluminación o usando el interruptor de contraste en la barra lateral.")

        except pytesseract.TesseractNotFoundError:
            st.error("❌ El motor Tesseract OCR no está configurado en este servidor.")
        except Exception as e:
            st.error(f"Se ha detectado un error técnico: {e}")

else:
    st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem; color: #64748B;">
            <h3>👋 ¡Todo listo para empezar!</h3>
            <p>Selecciona una opción en el panel lateral para cargar una imagen o tomar una foto.</p>
        </div>
    """, unsafe_allow_html=True)
