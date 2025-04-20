import streamlit as st
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

import warnings
warnings.simplefilter("ignore", category=FutureWarning)
# Suprimir advertencias ValueWarning
warnings.simplefilter("ignore")

st.set_page_config(page_title="Transcibir-audio", page_icon="img/logo1.png", layout="centered",
                   initial_sidebar_state="collapsed")


# --------------------------
# Cargar CSS personalizado
# --------------------------
def apply_custom_style():
    css_file = "assets/style.css"
    try:
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"No se encontró el archivo de estilo: {css_file}", icon=":material/cancel:")

apply_custom_style()

# ------------------------------------------------------
#def local_css(file_name):
#    with open(file_name) as f:
#        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Intenta cargar desde carpeta 'assets' o raíz
#if os.path.exists("assets/style.css"):
#    local_css("assets/style.css")
#elif os.path.exists("assets/style.css"):
#    local_css("assets/style.css")
#else:#
#    st.warning("Archivo style.css no encontrado")

st.header(":orange[App de Transcipción de Audio]")

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
st.subheader(":orange[Subir Audio y Transcribir]", divider=True)

c1, c2 = st.columns(2, border=True, vertical_alignment="center")
with c1:
    st_lottie('https://lottie.host/d71ebc94-ead6-4aca-8dc8-0062336fde1f/X8PGsPl8vF.json', width=80)
with c2:
    st_lottie('https://lottie.host/ae0dbd3e-cc51-4872-a683-972232ba2e55/zzDvaHgUVx.json', width=80)

# subir un audio y hacer la transcripción ---------------------

with st.container(border=True):
    archivo_audio = st.file_uploader(":orange[Subir archivo de audio]", type=["wav", "mp3", "ogg"],
                                     key="uploader_audio")

    if st.button(":orange[Subir y Transcribir]", key="btn_subir_transcribir", disabled=st.session_state.grabando):
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

st.subheader(":orange[Grabación y Transcripción]", divider=True)  # icon=":material/record_voice_over:"

# Obtener dispositivos de entrada
mic_devices = [device for device in sd.query_devices() if device['max_input_channels'] > 0]
mic_names = [f"{i}: {device['name']}" for i, device in enumerate(mic_devices)]

# Selección de micrófono
selected_mic_label = st.selectbox("Selecciona el micrófono de entrada", mic_names)
selected_mic_index = int(selected_mic_label.split(":")[0])
mic_info = sd.query_devices(selected_mic_index)
input_channels = mic_info['max_input_channels']

# Duración
st.warning("esta barra permite pre-establecer la duración del audio a grabar, si desea modificar la duración del audio a grabar mueva el punto rojo a los valores que Ud., considere apropiado")
duration = st.slider("Duración de la grabación (segundos)", 1, 30, 10)

# Timestamp y archivos
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
audio_filename = f"audio_{timestamp}.wav"
text_filename = f"transcripcion_{timestamp}.txt"

# Estado de sesión
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""

if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

# Grabación
if st.button("Iniciar grabación", icon=":material/mic:"):
    samplerate = 44100
    st.info("Grabando... Hable ahora.")
    try:
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate,
                           channels=input_channels, dtype='int16', device=selected_mic_index)
        sd.wait()
        st.success("Grabación finalizada", icon=":material/check:")

        # Guardar y cargar audio en memoria
        wavio.write(audio_filename, recording, samplerate, sampwidth=2)
        with open(audio_filename, "rb") as audio_file:
            st.session_state.audio_bytes = audio_file.read()

        # Reproducir
        st.audio(st.session_state.audio_bytes, format="audio/wav")

        # Transcripción
        with st.spinner("Transcribiendo con Whisper (modelo 'medium')..."):
            model = whisper.load_model("medium")
            result = model.transcribe(audio_filename, language="es")
            st.session_state.transcribed_text = result["text"]

    except Exception as e:
        st.error(f"Ocurrió un error durante la grabación o transcripción: {e}")

# Mostrar transcripción si existe
if st.session_state.transcribed_text:
    st.subheader("Editar transcripción")
    st.warning("Este archivo esta editado, si desea hacer alguna modificación escribala luego de enter en el final del texto para que tome las correcciones realizadas, y posteriormente presiones el boton de descargar el arhivo")
    edited_text = st.text_area("Transcripción:", value=st.session_state.transcribed_text, height=250, key="edited_text")

    # ✅ Botones de descarga en columnas
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.audio_bytes:
            st.download_button(
                "Descargar audio (.wav)",
                st.session_state.audio_bytes,
                file_name=audio_filename,
                mime="audio/wav",
                key="download_audio"
            )
    with col2:
        st.download_button(
            "Descargar transcripción (.txt)",
            data=edited_text,
            file_name=text_filename,
            mime="text/plain",
            key="download_text"
        )
        
        
        
# --------------- footer -----------------------------
st.write("---")
with st.container():
    # st.write("---")
    st.write(
        ":orange[&copy; - derechos reservados -  2025 -  Walter Gómez - FullStack Developer - Data Science - Business Intelligence]:")
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
