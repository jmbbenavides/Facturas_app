import email
import imaplib
import json
import os
import re
import threading
from datetime import datetime

import customtkinter as ctk
from tkcalendar import DateEntry

# Importar módulos personalizados
from modules.gmail_reader import GmailReader
from modules.organizer import Organizer

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"
thread_activo = None

def agregar_log(mensaje):
    hora = datetime.now().strftime("%H:%M:%S")
    log_text.insert("end", f"[{hora}] {mensaje}\n")
    log_text.see("end")

def limpiar_texto(texto):
    return re.sub(r"[^0-9]", "", texto)

# -------------------------
# FUNCIONES
# -------------------------

def guardar_config():
    datos = {
        "email": entry_email.get(),
        "password": entry_password.get(),
        "nit": entry_nit.get(),
        "nrc": entry_nrc.get(),
    }
    with open(CONFIG_FILE, "w") as archivo:
        json.dump(datos, archivo, indent=4)
    agregar_log("✅ Configuración guardada correctamente")
    estado.configure(text="✅ Configuración guardada", text_color="lightgreen")

def cargar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as archivo:
            datos = json.load(archivo)
        entry_email.insert(0, datos.get("email", ""))
        entry_password.insert(0, datos.get("password", ""))
        entry_nit.insert(0, datos.get("nit", ""))
        entry_nrc.insert(0, datos.get("nrc", ""))
        agregar_log("✅ Configuración cargada desde archivo")
        estado.configure(text="✅ Configuración cargada", text_color="lightgreen")

def editar_datos():
    entry_email.configure(state="normal")
    entry_password.configure(state="normal")
    entry_nit.configure(state="normal")
    entry_nrc.configure(state="normal")
    agregar_log("✏️ Modo edición activado")
    estado.configure(text="✏️ Modo edición activado", text_color="orange")

def conectar_gmail():
    estado.configure(text="🔄 Conectando...", text_color="orange")
    app.update()
    email_user = entry_email.get()
    email_pass = entry_password.get()
    try:
        agregar_log("Conectando a Gmail...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=10)
        agregar_log("Servidor Gmail conectado")
        mail.login(email_user, email_pass)
        agregar_log("Login exitoso")
        estado.configure(text="✅ Conexión Gmail exitosa", text_color="lightgreen")
        mail.logout()
    except Exception as e:
        agregar_log(f"❌ Error: {str(e)}")
        estado.configure(text="❌ Error Gmail", text_color="red")

def leer_correos_thread(email_user, email_pass, nit_busqueda, nrc_busqueda, fecha_desde, fecha_hasta):
    global thread_activo
    reader = GmailReader(email_user, email_pass)
    organizer = Organizer()
    try:
        agregar_log("📧 Iniciando proceso...")
        
        # Parámetros necesarios para el nuevo método
        carpetas = ["INBOX", "[Gmail]/All Mail", "[Gmail]/Spam", "[Gmail]/Promotions"]
        
        archivos_descargados, correos_procesados = reader.buscar_y_descargar(
            carpetas, nit_busqueda, nrc_busqueda, fecha_desde, fecha_hasta, 
            agregar_log, lambda: thread_activo is not None, organizer
        )

        agregar_log(f"📊 ========== RESUMEN ==========")
        agregar_log(f"✅ Correos procesados: {correos_procesados}")
        agregar_log(f"💾 Archivos descargados y organizados: {archivos_descargados}")
        estado.configure(text=f"✅ Listo: {archivos_descargados} archivos", text_color="lightgreen")

    except Exception as e:
        agregar_log(f"❌ Error: {str(e)}")
        estado.configure(text="❌ Error Gmail", text_color="red")
    finally:
        thread_activo = None
        btn_leer.configure(text="📬 Leer Correos y Facturas")

def leer_correos():
    global thread_activo
    if thread_activo is not None:
        thread_activo = None
        agregar_log("🛑 Cancelando búsqueda...")
        estado.configure(text="⏹️ Búsqueda cancelada", text_color="orange")
        btn_leer.configure(text="📬 Leer Correos y Facturas")
        return

    estado.configure(text="📬 Leyendo correos...", text_color="orange")
    btn_leer.configure(text="⏹️ Cancelar")
    app.update()

    email_user = entry_email.get()
    email_pass = entry_password.get()
    nit_busqueda = limpiar_texto(entry_nit.get())
    nrc_busqueda = limpiar_texto(entry_nrc.get())
    fecha_desde = calendar_desde.get_date()
    fecha_hasta = calendar_hasta.get_date()

    thread_activo = True
    hilo = threading.Thread(
        target=leer_correos_thread,
        args=(email_user, email_pass, nit_busqueda, nrc_busqueda, fecha_desde, fecha_hasta),
        daemon=True,
    )
    hilo.start()

# -------------------------
# VENTANA
# -------------------------
app = ctk.CTk()
app.geometry("1380x860")
app.minsize(1200, 720)
app.title("Facturas App")
app.configure(fg_color="#121417")

header_frame = ctk.CTkFrame(app, corner_radius=0, fg_color="#0f1320")
header_frame.pack(fill="x", pady=(0, 5))

header_title = ctk.CTkLabel(
    header_frame,
    text="Facturas App",
    font=("Arial", 30, "bold"),
    text_color="#ffffff"
)
header_title.grid(row=0, column=0, padx=30, pady=(20, 5), sticky="w")

header_subtitle = ctk.CTkLabel(
    header_frame,
    text="Gestión inteligente de facturas y archivos desde tus correos Gmail",
    font=("Arial", 14),
    text_color="#c3c9d9"
)
header_subtitle.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")

main_frame = ctk.CTkFrame(app, corner_radius=25, fg_color="#14192e")
main_frame.pack(fill="both", expand=True, padx=20, pady=10)
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=1)

# Panel izquierdo
left_container = ctk.CTkFrame(main_frame, corner_radius=20, fg_color="#191f35", width=580)
left_container.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")
left_container.grid_rowconfigure(0, weight=1)
left_container.grid_propagate(False)

left_scroll = ctk.CTkScrollableFrame(left_container, corner_radius=20, fg_color="#191f35")
left_scroll.pack(fill="both", expand=True, padx=10, pady=10)
left_scroll.grid_columnconfigure(0, weight=1)

section_label = ctk.CTkLabel(
    left_scroll,
    text="🛠️ Configuración",
    font=("Arial", 20, "bold"),
    anchor="w"
)
section_label.pack(fill="x", padx=20, pady=(20, 10))

info_label = ctk.CTkLabel(
    left_scroll,
    text="Completa tus datos de correo y filtra por fecha para encontrar tus facturas rápido.",
    font=("Arial", 12),
    text_color="#b0b8d0",
    wraplength=340,
    justify="left"
)
info_label.pack(fill="x", padx=20, pady=(0, 20))

fields_frame = ctk.CTkFrame(left_scroll, corner_radius=20, fg_color="#12172a", border_width=1, border_color="#2f3a57")
fields_frame.pack(fill="x", padx=20, pady=(0, 20))
fields_frame.grid_columnconfigure(0, weight=1)

entry_email = ctk.CTkEntry(fields_frame, width=440, placeholder_text="tu@gmail.com")
entry_email.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
entry_password = ctk.CTkEntry(fields_frame, width=440, show="*", placeholder_text="Contraseña App")
entry_password.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
entry_nit = ctk.CTkEntry(fields_frame, width=440, placeholder_text="NIT")
entry_nit.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
entry_nrc = ctk.CTkEntry(fields_frame, width=440, placeholder_text="NRC")
entry_nrc.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")

calendar_frame = ctk.CTkFrame(left_scroll, corner_radius=24, fg_color="#12172a", border_width=1, border_color="#2f3a57")
calendar_frame.pack(fill="x", padx=20, pady=(0, 20))
calendar_frame.grid_columnconfigure(0, weight=1)
calendar_frame.grid_columnconfigure(1, weight=1)

fecha_desde_label = ctk.CTkLabel(calendar_frame, text="Desde", font=("Arial", 13, "bold"), text_color="#e3ebff")
fecha_desde_label.grid(row=0, column=0, padx=(20, 10), pady=(22, 5), sticky="w")
fecha_hasta_label = ctk.CTkLabel(calendar_frame, text="Hasta", font=("Arial", 13, "bold"), text_color="#e3ebff")
fecha_hasta_label.grid(row=0, column=1, padx=(10, 20), pady=(22, 5), sticky="w")

calendar_desde = DateEntry(
    calendar_frame,
    width=34,
    font=("Arial", 12),
    date_pattern="dd/mm/yyyy",
    background="#0f1522",
    foreground="#ffffff",
    borderwidth=0,
    relief="flat",
    selectbackground="#2e8cff",
    selectforeground="#ffffff"
)
calendar_desde.grid(row=1, column=0, padx=(20, 10), pady=(0, 22), sticky="ew")
calendar_hasta = DateEntry(
    calendar_frame,
    width=34,
    font=("Arial", 12),
    date_pattern="dd/mm/yyyy",
    background="#0f1522",
    foreground="#ffffff",
    borderwidth=0,
    relief="flat",
    selectbackground="#2e8cff",
    selectforeground="#ffffff"
)
calendar_hasta.grid(row=1, column=1, padx=(10, 20), pady=(0, 22), sticky="ew")

actions_frame = ctk.CTkFrame(left_scroll, corner_radius=20, fg_color="#12172a", border_width=1, border_color="#2f3a57")
actions_frame.pack(fill="x", padx=20, pady=(0, 20))

actions_frame.grid_columnconfigure(0, weight=1)

actions_frame.grid_rowconfigure((0, 1), weight=1)

btn_leer = ctk.CTkButton(
    actions_frame,
    text="📬 Leer Correos",
    command=leer_correos,
    height=56,
    corner_radius=20,
    fg_color="#2e8cff",
    hover_color="#1f6bdb"
)
btn_leer.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

btn_guardar = ctk.CTkButton(
    actions_frame,
    text="💾 Guardar configuración",
    command=guardar_config,
    height=56,
    corner_radius=20,
    fg_color="#2fae82",
    hover_color="#24946f"
)
btn_guardar.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")

estado = ctk.CTkLabel(
    left_scroll,
    text="✅ Sistema iniciado",
    font=("Arial", 13, "bold"),
    text_color="#7ed957"
)
estado.pack(anchor="w", padx=20, pady=(0, 20))

# Panel derecho
right_container = ctk.CTkFrame(main_frame, corner_radius=20, fg_color="#191f35")
right_container.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
right_container.grid_rowconfigure(1, weight=1)

log_title = ctk.CTkLabel(
    right_container,
    text="📋 Registro de actividad",
    font=("Arial", 18, "bold"),
    anchor="w"
)
log_title.pack(fill="x", padx=20, pady=(20, 10))

log_text = ctk.CTkTextbox(
    right_container,
    width=560,
    font=("Courier", 11),
    fg_color="#12172a",
    corner_radius=18,
    border_width=1,
    border_color="#2f3a57"
)
log_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

cargar_config()
app.mainloop()
