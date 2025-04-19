import tkinter as tk
from tkinter import ttk, messagebox
from time import gmtime, strftime
import os
import threading
import speech_recognition as sr
import pyttsx3

# --- Variables globales ---
grabando = False
modo_oscuro = False

# --- Inicializar ventana ---
root = tk.Tk()
root.title("Copiador de Voz")
root.geometry("800x700")
style = ttk.Style()

# --- Inicializar motor de voz ---
engine = pyttsx3.init()
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)

def talk(text):
    engine.say(text)
    engine.runAndWait()

# --- Modo claro/oscuro ---
def toggle_modo():
    global modo_oscuro
    modo_oscuro = not modo_oscuro
    if modo_oscuro:
        root.config(bg="#2E2E2E")
        frame.config(bg="#2E2E2E")
        textoComentario.config(bg="#1E1E1E", fg="white", insertbackground="white")
        boton_escuchar.config(bg="#4CAF50", fg="white")
        boton_detener.config(bg="#f44336", fg="white")
        boton_guardar.config(bg="#2196F3", fg="white")
        boton_tema.config(text="Modo Claro")
    else:
        root.config(bg="white")
        frame.config(bg="white")
        textoComentario.config(bg="white", fg="black", insertbackground="black")
        boton_escuchar.config(bg="green", fg="white")
        boton_detener.config(bg="red", fg="white")
        boton_guardar.config(bg="blue", fg="white")
        boton_tema.config(text="Modo Oscuro")

# --- Reconocimiento de voz ---
listener = sr.Recognizer()
listener.pause_threshold = 0.8

def escuchar():
    global grabando
    grabando = True
    textoComentario.insert(tk.END, "Iniciando transcripción en vivo...\n")

    def grabar():
        with sr.Microphone() as source:
            listener.adjust_for_ambient_noise(source)
            while grabando:
                try:
                    audio = listener.listen(source, timeout=5, phrase_time_limit=5)
                    texto = listener.recognize_google(audio, language='es-ES')
                    textoComentario.insert(tk.END, f"{texto}\n")
                    textoComentario.see(tk.END)
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    textoComentario.insert(tk.END, "No se entendió el audio.\n")
                except Exception as e:
                    textoComentario.insert(tk.END, f"Error: {e}\n")
                    break

    threading.Thread(target=grabar).start()

def detener():
    global grabando
    grabando = False
    textoComentario.insert(tk.END, "Transcripción detenida.\n")

# --- Guardar archivo en Descargas ---
def guardar():
    nombre = nombre_archivo.get()
    if not nombre:
        messagebox.showwarning("Atención", "Debes ingresar un nombre para el archivo.")
        return
    
    contenido = textoComentario.get("1.0", tk.END)
    fecha = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
    nombre += ".txt"
    ruta = os.path.join(os.path.expanduser("~/Downloads"), nombre)

    try:
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(fecha + "\n")
            archivo.write(contenido)
        messagebox.showinfo("Guardado", f"Archivo guardado en: {ruta}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")

# --- Interfaz gráfica ---
frame = tk.Frame(root, bg="white")
frame.pack(pady=20)

tk.Label(frame, text="Audio a Texto", font=("Comic Sans MS", 30), bg="white", fg="steelblue").pack(pady=10)

tk.Label(frame, text="Digite nombre del archivo antes de descargar :", bg="white").pack(pady=5)
nombre_archivo = tk.Entry(frame, width=50)
nombre_archivo.pack(pady=5)

textoComentario = tk.Text(frame, width=70, height=10, wrap="word", font=("Arial", 12))
textoComentario.pack(pady=10)

scroll = tk.Scrollbar(frame, command=textoComentario.yview)
scroll.pack(side=tk.RIGHT, fill=tk.Y)
textoComentario.config(yscrollcommand=scroll.set)

boton_escuchar = tk.Button(frame, text="🎧 Empezar Transcripción", command=escuchar, bg="green", fg="white", width=25, height=2)
boton_escuchar.pack(pady=5)

boton_detener = tk.Button(frame, text="🛑 Detener Transcripción", command=detener, bg="red", fg="white", width=25, height=2)
boton_detener.pack(pady=5)

boton_guardar = tk.Button(frame, text="💾 Guardar Archivo", command=guardar, bg="blue", fg="white", width=25, height=2)
boton_guardar.pack(pady=5)

boton_tema = tk.Button(frame, text="Modo Oscuro", command=toggle_modo, bg="gray", fg="white", width=25, height=2)
boton_tema.pack(pady=10)

toggle_modo()  # Opcional: inicia en modo oscuro
root.mainloop()
