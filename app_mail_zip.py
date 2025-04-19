import streamlit as st
from email.message import EmailMessage
import smtplib
import sounddevice as sd
import scipy.io.wavfile as wavfile
from scipy.io.wavfile import write as write_wav
import speech_recognition as sr
import matplotlib.pyplot as plt
import numpy as np
import os
import librosa
from streamlit_lottie import st_lottie
from pathlib import Path
from datetime import datetime
import datetime
import base64
import soundfile as sf
import threading
import queue
import wavio
import whisper
import zipfile
import io

import warnings
warnings.simplefilter("ignore", category=FutureWarning)
# Suprimir advertencias ValueWarning
warnings.simplefilter("ignore")


os.environ["STREAMLIT_DISABLE_WATCHDOG_WARNINGS"] = "true"
#sys.modules["torch._classes"] = None

st.set_page_config(page_title="App-Audio a Texto", page_icon="img/logo1.png", layout="centered",
                   initial_sidebar_state="expanded")

# --------------------------
# Cargar CSS personalizado
# --------------------------

#def apply_custom_style():
#    css_paths = ["assets/style.css", "./style.css"]  # Opciones de ubicación

#    for css_file in css_paths:
#        if os.path.exists(css_file):
#            with open(css_file) as f:
#                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
#            return  # Sale al encontrar uno válido
#
#    st.warning("No se encontró el archivo 'style.css' en ninguna ruta conocida.")

#apply_custom_style()

# Estilos con modo claro / oscuro 
def apply_custom_style(theme: str):
    css_file = f"assets/style_{theme}.css"
    if os.path.exists(css_file):
       with open(css_file, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"No se encontró el archivo de estilo: {css_file}")
        
#with open("assets/style.css", encoding="utf-8") as f:   
#    st.markdown(f"<style>{f.read()} </style>", unsafe_allow_html=True)     

# Selector de tema
st.sidebar.markdown("**Tema interfaz**")
selected_theme = st.sidebar.selectbox("Selecciona un tema:", ["dark", "light"], format_func=lambda x: "🌙 Suave" if x == "dark" else "🌞 Intenso")

# Aplicar tema
apply_custom_style(selected_theme)

st.header("App de Transcipción de Audio")

st.image("img/main-page.jpg", caption=None, width=50, use_column_width=None, clamp=False, channels="RGB",
         output_format="auto", use_container_width=True)

# ──────────────── VARIABLES DE ESTADO ──────────────── #
if "grabando" not in st.session_state:
    st.session_state.grabando = False
if "audio_grabado" not in st.session_state:
    st.session_state.audio_grabado = None
if "hilo_grabacion" not in st.session_state:
    st.session_state.hilo_grabacion = None
if "dispositivo_seleccionado" not in st.session_state:
    st.session_state.dispositivo_seleccionado = None
if "mensaje_estado" not in st.session_state:
    st.session_state.mensaje_estado = ""

reconocedor = sr.Recognizer()
estado_queue = queue.Queue()


# ──────────────── FUNCIONES ──────────────── #

def convertir_a_wav_temporal(archivo_audio):
    try:
        y, sr_librosa = librosa.load(archivo_audio, sr=44100, mono=True)
        wav_path = "audio_subido.wav"
        write_wav(wav_path, sr_librosa, (y * 32767).astype(np.int16))
        return wav_path
    except Exception as e:
        st.error(f"Error al convertir el archivo de audio: {e}")
        return None


def subir_y_transcribir(archivo_audio):
    if archivo_audio:
        ruta_wav = convertir_a_wav_temporal(archivo_audio)
        if not ruta_wav:
            return "No se pudo procesar el archivo de audio."
        try:
            with sr.AudioFile(ruta_wav) as fuente:
                audio = reconocedor.record(fuente)
                texto = reconocedor.recognize_google(audio, language="es-ES")
            os.remove(ruta_wav)
            return texto
        except sr.UnknownValueError:
            return "No se pudo reconocer el audio."
        except sr.RequestError as e:
            return f"Error al solicitar resultados; {e}"
        except Exception as e:
            return f"Ocurrió un error: {e}"
    return ""


def grabar_audio(duracion, device_index):
    st.session_state.grabando = True
    st.session_state.audio_grabado = None
    estado_queue.put("Grabando...")

    def grabar():
        fs = 44100
        try:
            grabacion = sd.rec(int(duracion * fs), samplerate=fs, channels=1, dtype='float32', device=device_index)
            sd.wait()
            st.session_state.audio_grabado = grabacion
            estado_queue.put("Grabación finalizada.")
        except Exception as e:
            estado_queue.put(f"[ERROR] Grabación falló: {e}")
        finally:
            st.session_state.grabando = False

    hilo = threading.Thread(target=grabar)
    hilo.start()
    st.session_state.hilo_grabacion = hilo


def detener_y_transcribir():
    if st.session_state.hilo_grabacion:
        st.session_state.hilo_grabacion.join()
        st.session_state.hilo_grabacion = None
        if st.session_state.audio_grabado is not None and len(st.session_state.audio_grabado) > 0:
            array_audio = np.array(st.session_state.audio_grabado)
            ruta_archivo_temporal = "audio_grabado.wav"
            sf.write(ruta_archivo_temporal, array_audio, 44100)

            try:
                with sr.AudioFile(ruta_archivo_temporal) as fuente:
                    audio_data = reconocedor.record(fuente)
                    texto = reconocedor.recognize_google(audio_data, language="es-ES")
                os.remove(ruta_archivo_temporal)
                return texto
            except sr.UnknownValueError:
                return "No se pudo reconocer el audio."
            except sr.RequestError as e:
                return f"Error al solicitar resultados; {e}"
            except Exception as e:
                return f"Ocurrió un error: {e}"
        else:
            return "No se grabó ningún audio."
    else:
        return "No se ha iniciado ninguna grabación."


def mostrar_dispositivos():
    dispositivos = sd.query_devices()
    st.write("Dispositivos disponibles:")
    for i, d in enumerate(dispositivos):
        if d['max_input_channels'] > 0:
            st.write(f"{i}: {d['name']}")


# ──────────────── INTERFAZ STREAMLIT ──────────────── #
st.subheader("Subir Audio y Transcribir", divider=True)

c1, c2 = st.columns(2, border=True, vertical_alignment="center")
with c1:
    st_lottie('https://lottie.host/d71ebc94-ead6-4aca-8dc8-0062336fde1f/X8PGsPl8vF.json', width=80)
with c2:
    st_lottie('https://lottie.host/ae0dbd3e-cc51-4872-a683-972232ba2e55/zzDvaHgUVx.json', width=80)

# subir un audio y hacer la transcripción ---------------------

with st.container(border=True):
    archivo_audio = st.file_uploader("Subir archivo de audio", type=["wav", "mp3", "ogg"],
                                     key="uploader_audio")

    if st.button("Subir y Transcribir", key="btn_subir_transcribir", disabled=st.session_state.grabando):
        st.audio(archivo_audio)
        if archivo_audio:
            with st.spinner("Transcribiendo audio subido..."):
                transcripcion = subir_y_transcribir(archivo_audio)
                if transcripcion:
                    st.text_area("Transcripción", value=transcripcion, height=150, key="text_area_transcripcion_1")
                    st.download_button(
                        label="Descargar Transcripción",
                        data=transcripcion.encode('utf-8'),
                        file_name="transcripcion.txt",
                        mime="text/plain",
                        key="download_transcripcion_1"
                    )

st.write("---")

# --------------------------
# inserccion de archivos gif
# --------------------------
def show_logo_uno():
    st.image("img/record.gif", caption=None, width=50, use_column_width=None, clamp=False, channels="RGB",
             output_format="auto", use_container_width=False)


def show_logo_dos():
    st.image("img/voice.gif", caption=None, width=50, use_column_width=None, clamp=False, channels="RGB",
             output_format="auto", use_container_width=False)

# --------------------------
# Interfaz
# --------------------------
col1, col2 = st.columns(2, border=True, vertical_alignment="center")
with col1:
    show_logo_uno()
with col2:
    show_logo_dos()

st.subheader("Grabación y Transcripción", divider=True)  # icon=":material/record_voice_over:"

# ---------- SESSION STATE ----------
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""

if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

if "historial" not in st.session_state:
    st.session_state.historial = []

# ---------- SELECCIÓN DE MICRÓFONO ----------
mic_devices = [device for device in sd.query_devices() if device['max_input_channels'] > 0]
mic_names = [f"{i}: {device['name']}" for i, device in enumerate(mic_devices)]

selected_mic_label = st.selectbox("Selecciona el micrófono de entrada", mic_names)
selected_mic_index = int(selected_mic_label.split(":")[0])
mic_info = sd.query_devices(selected_mic_index)
input_channels = mic_info['max_input_channels']

# ---------- PARÁMETROS DE GRABACIÓN ----------
custom_name = st.text_input("📛 Nombre para la grabación (opcional)", placeholder="Ej: Entrevista Juan")
st.warning("esta barra permite pre-establecer la duración del audio a grabar, si desea modificar la duración del audio a grabar mueva el punto rojo a los valores que Ud., considere apropiado")
duration = st.slider("Duración de la grabación (segundos)", 1, 30, 10)

# ---------- BOTÓN DE GRABACIÓN ----------
if st.button("Iniciar grabación", icon=":material/mic:"):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_filename = f"audio_{timestamp}.wav"
    nombre_grabacion = custom_name if custom_name else f"Grabación {timestamp}"

    st.info("Grabando... Hable ahora.")
    samplerate = 44100

    try:
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate,
                           channels=input_channels, dtype='int16', device=selected_mic_index)
        sd.wait()
        st.success("Grabación finalizada", icon=":material/check:")

        # Guardar audio en memoria
        wavio.write(audio_filename, recording, samplerate, sampwidth=2)
        with open(audio_filename, "rb") as audio_file:
            st.session_state.audio_bytes = audio_file.read()

        st.audio(st.session_state.audio_bytes, format="audio/wav")

        # Transcripción con Whisper
        with st.spinner("Transcribiendo con Whisper (modelo 'medium')..."):
            model = whisper.load_model("medium")
            result = model.transcribe(audio_filename, language="es")
            st.session_state.transcribed_text = result["text"]

        # Guardar en historial
        st.session_state.historial.append({
            "nombre": nombre_grabacion,
            "audio_bytes": st.session_state.audio_bytes,
            "texto": st.session_state.transcribed_text
        })

    except Exception as e:
        st.error(f"Ocurrió un error durante la grabación o transcripción: {e}")

# ---------- EDICIÓN Y DESCARGA ----------
if st.session_state.transcribed_text:
    st.subheader("Editar transcripción")
    st.warning("Primero debe descargar el archivo original, este archivo esta editado, si desea hacer alguna modificación, escriba luego de enter en el final del texto para que tome las correcciones realizadas, y presiones el boton de descargar el arhivo actualizado")
    edited_text = st.text_area("Transcripción:", value=st.session_state.transcribed_text, height=250, key="edited_text")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.session_state.audio_bytes:
            st.download_button(
                "Descargar audio (.wav)",
                st.session_state.audio_bytes,
                file_name="grabacion.wav",
                mime="audio/wav"
            )
    with col2:
        st.download_button(
            "Descargar transcripción (.txt)",
            data=edited_text,
            file_name="transcripcion.txt",
            mime="text/plain"
        )
    with col3:
        if st.button("Volver a grabar 🔁"):
            st.session_state.transcribed_text = ""
            st.session_state.audio_bytes = None

# ---------- HISTORIAL ----------
st.markdown("---")
st.subheader("Historial de grabaciones")

search_query = st.text_input("🔍 Buscar grabación por nombre")
historial_filtrado = [item for item in st.session_state.historial if search_query.lower() in item["nombre"].lower()]

if historial_filtrado:
    selected_item = st.selectbox("Selecciona una grabación", options=[item["nombre"] for item in historial_filtrado])

    for item in historial_filtrado:
        if item["nombre"] == selected_item:
            st.audio(item["audio_bytes"], format="audio/wav")
            st.text_area("Transcripción previa:", value=item["texto"], height=200, key=f"hist_{item['nombre']}")
            break
else:
    st.info("No se encontraron grabaciones con ese nombre.")

# ---------- DESCARGAR TODO COMO ZIP ----------
if st.session_state.historial:
    if st.button("📦 Descargar historial completo (.zip)"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for i, item in enumerate(st.session_state.historial):
                base_name = item["nombre"].replace(" ", "_")
                zip_file.writestr(f"{base_name}.wav", item["audio_bytes"])
                zip_file.writestr(f"{base_name}.txt", item["texto"])
        zip_buffer.seek(0)
        st.download_button(
            label="⬇️ Descargar ZIP",
            data=zip_buffer,
            file_name="historial_grabaciones.zip",
            mime="application/zip"
        )

# ---------- ENVIAR POR EMAIL ----------
st.markdown("---")
st.subheader("Enviar grabación por correo")

if historial_filtrado:
    selected_to_send = st.selectbox("Selecciona la grabación a enviar", options=[item["nombre"] for item in historial_filtrado])
    destinatario = st.text_input("✉️ Correo del destinatario")

    def enviar_por_email(destinatario, nombre, audio_bytes, texto):
        msg = EmailMessage()
        msg["Subject"] = f"Grabación: {nombre}"
        msg["From"] = "tu_correo@gmail.com"
        msg["To"] = destinatario
        msg.set_content("Adjunto encontrarás la grabación y la transcripción.")

        msg.add_attachment(audio_bytes, maintype="audio", subtype="wav", filename=f"{nombre}.wav")
        msg.add_attachment(texto.encode("utf-8"), maintype="text", subtype="plain", filename=f"{nombre}.txt")

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login("tu_correo@gmail.com", "tu_contraseña_app")
                smtp.send_message(msg)
            return True
        except Exception as e:
            return f"Error: {e}"

    if st.button("Enviar correo"):
        for item in historial_filtrado:
            if item["nombre"] == selected_to_send:
                resultado = enviar_por_email(destinatario, item["nombre"], item["audio_bytes"], item["texto"])
                if resultado is True:
                    st.success("Correo enviado correctamente " , icon=":material/done_all:")
                else:
                    st.error(f"Ocurrió un error al enviar: {resultado}")
                break
# --------------- footer -----------------------------
st.write("---")
with st.container():
    # st.write("---")
    st.write(
        "&copy; - derechos reservados -  2025 -  Walter Gómez - FullStack Developer - Data Science - Business Intelligence")
    # st.write("##")
    left, right = st.columns(2, gap='medium', vertical_alignment="bottom")
    with left:
        # st.write('##')
        st.link_button("Mi LinkedIn",
                       "https://www.linkedin.com/in/walter-gomez-fullstack-developer-datascience-businessintelligence-finanzas-python/",
                       use_container_width=False)
    with right:
        # st.write('##')
        st.link_button("Mi Porfolio", "https://walter-portfolio-animado.netlify.app/", use_container_width=False)
