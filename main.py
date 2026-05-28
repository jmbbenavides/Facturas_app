import imaplib
import json
import os
from datetime import datetime
import email
import re

import customtkinter as ctk
from tkcalendar import DateEntry

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"


def agregar_log(mensaje):

    hora = datetime.now().strftime("%H:%M:%S")

    log_text.insert("end", f"[{hora}] {mensaje}\n")

    log_text.see("end")

def limpiar_texto(texto):

    return re.sub(
        r'[^0-9]',
        '',
        texto
    )

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

    estado.configure(text="Configuración guardada correctamente")


def cargar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as archivo:
            datos = json.load(archivo)

        entry_email.insert(0, datos.get("email", ""))
        entry_password.insert(0, datos.get("password", ""))
        entry_nit.insert(0, datos.get("nit", ""))
        entry_nrc.insert(0, datos.get("nrc", ""))

        estado.configure(text="Configuración cargada")


def editar_datos():

    entry_email.configure(state="normal")
    entry_password.configure(state="normal")
    entry_nit.configure(state="normal")
    entry_nrc.configure(state="normal")

    estado.configure(text="Modo edición activado")


def conectar_gmail():

    estado.configure(text="Conectando...")
    left_frame.update()

    email_user = entry_email.get()
    email_pass = entry_password.get()

    try:
        agregar_log("Conectando a Gmail...")

        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=10)

        agregar_log("Servidor Gmail conectado")

        mail.login(email_user, email_pass)

        agregar_log("Login exitoso")

        estado.configure(text="Conexión Gmail exitosa")

        mail.logout()

    except Exception as e:
        agregar_log(f"Error: {str(e)}")

        estado.configure(text="Error Gmail")


def leer_correos():

    estado.configure(text="Leyendo correos...")
    left_frame.update()

    email_user = entry_email.get()
    email_pass = entry_password.get()

    try:
        agregar_log("Conectando a Gmail...")

        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)

        mail.login(email_user, email_pass)

        agregar_log("Login exitoso")

        mail.select("inbox")

        agregar_log("Inbox abierto")

        fecha_desde = datetime.strptime(calendar_desde.get(), "%d/%m/%Y").strftime(
            "%d-%b-%Y"
        )

        fecha_hasta = datetime.strptime(calendar_hasta.get(), "%d/%m/%Y").strftime(
            "%d-%b-%Y"
        )

        status, mensajes = mail.search(
            None, f'(SINCE "{fecha_desde}" BEFORE "{fecha_hasta}")'
        )

        lista_ids = mensajes[0].split()

        cantidad = len(lista_ids)

        agregar_log(f"Correos encontrados: {cantidad}")
        
        for correo_id in lista_ids:

            status, datos_correo = mail.fetch(
                correo_id,
                "(RFC822)"
            )

            raw_email = datos_correo[0][1]

            mensaje = email.message_from_bytes(raw_email)

            asunto = mensaje["subject"]

            agregar_log(f"Asunto: {asunto}")

            # -------------------------
            # RECORRER PARTES DEL CORREO
            # -------------------------

            for parte in mensaje.walk():

                nombre_archivo = parte.get_filename()

                # -------------------------
                # JSON
                # -------------------------

                if nombre_archivo and nombre_archivo.endswith(".json"):

                    agregar_log(
                        f"JSON encontrado: {nombre_archivo}"
                    )

                    contenido = parte.get_payload(
                        decode=True
                    )

                    texto_json = contenido.decode(
                        "utf-8"
                    )

                    nit_busqueda = limpiar_texto(
                        entry_nit.get()
                    )

                    nrc_busqueda = limpiar_texto(
                        entry_nrc.get()
                    )

                    texto_limpio = limpiar_texto(
                        texto_json
                    )

                    if nit_busqueda in texto_limpio:

                        agregar_log(
                            f"NIT encontrado en {nombre_archivo}"
                        )

                    if nrc_busqueda in texto_limpio:

                        agregar_log(
                            f"NRC encontrado en {nombre_archivo}"
                        )

        mail.logout()

    except Exception as e:
        agregar_log(f"Error: {str(e)}")

        estado.configure(text="Error leyendo correos")


# -------------------------
# VENTANA
# -------------------------

app = ctk.CTk()

app.geometry("900x700")
app.title("Facturas App")

main_frame = ctk.CTkFrame(app)

main_frame.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=20
)

main_frame.pack(fill="both", expand=True, padx=20, pady=20)

left_frame = ctk.CTkFrame(main_frame)

left_frame.grid(
    row=1,
    column=0,
    padx=10,
    pady=10,
    sticky="n"
)


right_frame = ctk.CTkFrame(main_frame)

right_frame.grid(
    row=1,
    column=1,
    padx=10,
    pady=10,
    sticky="n"
)

# -------------------------
# TITULO
# -------------------------

titulo = ctk.CTkLabel(
    main_frame,
    text="Sistema de Facturas",
    font=("Arial", 28)
)

titulo.grid(
    row=0,
    column=0,
    columnspan=2,
    pady=20
)

# -------------------------
# EMAIL
# -------------------------

label_email = ctk.CTkLabel(left_frame, text="Correo Gmail")
label_email.pack()

entry_email = ctk.CTkEntry(left_frame, width=400)
entry_email.pack(pady=5)

# -------------------------
# PASSWORD
# -------------------------

label_password = ctk.CTkLabel(left_frame, text="Contraseña de Aplicación")
label_password.pack()

entry_password = ctk.CTkEntry(left_frame, width=400, show="*")
entry_password.pack(pady=5)

# -------------------------
# NIT
# -------------------------

label_nit = ctk.CTkLabel(left_frame, text="NIT Receptor")
label_nit.pack()

entry_nit = ctk.CTkEntry(left_frame, width=400)
entry_nit.pack(pady=5)

# -------------------------
# NRC
# -------------------------

label_nrc = ctk.CTkLabel(left_frame, text="NRC Receptor")
label_nrc.pack()

entry_nrc = ctk.CTkEntry(left_frame, width=400)
entry_nrc.pack(pady=5)

# -------------------------
# FECHA DESDE
# -------------------------

label_desde = ctk.CTkLabel(left_frame   , text="Fecha Desde")

label_desde.pack()

calendar_desde = DateEntry(
    left_frame,
    width=20,
    background="blue",
    foreground="white",
    borderwidth=2,
    date_pattern="dd/mm/yyyy",
)

calendar_desde.pack(pady=5)

# -------------------------
# FECHA HASTA
# -------------------------

label_hasta = ctk.CTkLabel(left_frame, text="Fecha Hasta")

label_hasta.pack()

calendar_hasta = DateEntry(
    left_frame,
    width=20,
    background="blue",
    foreground="white",
    borderwidth=2,
    date_pattern="dd/mm/yyyy",
)

calendar_hasta.pack(pady=5)
# -------------------------
# BOTONES
# -------------------------

btn_guardar = ctk.CTkButton(
    left_frame, text="Guardar Configuración", command=guardar_config
)

btn_guardar.pack(pady=10)

btn_editar = ctk.CTkButton(left_frame, text="Editar Datos", command=editar_datos)

btn_editar.pack(pady=5)

btn_conectar = ctk.CTkButton(left_frame, text="Probar Gmail", command=conectar_gmail)

btn_conectar.pack(pady=5)


btn_leer = ctk.CTkButton(left_frame, text="Leer Correos", command=leer_correos)

btn_leer.pack(pady=5)

# -------------------------
# ESTADO
# -------------------------

estado = ctk.CTkLabel(left_frame, text="Sistema iniciado")

estado.pack(pady=20)

# -------------------------
# LOGS
# -------------------------

log_text = ctk.CTkTextbox(right_frame, width=450, height=600)

log_text.pack(pady=10)

# -------------------------
# CARGAR CONFIG
# -------------------------

cargar_config()

# -------------------------
# LOOP
# -------------------------

app.mainloop()
