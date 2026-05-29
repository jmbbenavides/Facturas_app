import email
import imaplib
import os
import re
from datetime import datetime, timedelta
import uuid

class GmailReader:
    def __init__(self, email_user, email_pass):
        self.email_user = email_user
        self.email_pass = email_pass
        self.mail = None

    def connect(self):
        self.mail = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=20)
        self.mail.login(self.email_user, self.email_pass)
        return self.mail

    def disconnect(self):
        if self.mail:
            try:
                self.mail.logout()
            except:
                pass
            self.mail = None

    def _listar_buzones(self):
        status, data = self.mail.list()
        if status != "OK" or not data:
            return []

        buzones = []
        for linea in data:
            if not linea:
                continue
            try:
                texto = linea.decode("utf-8", errors="ignore")
            except Exception:
                texto = str(linea)

            match = re.search(r'"([^"]+)"\s*$', texto)
            if match:
                buzones.append(match.group(1))
            else:
                partes = texto.split()
                if partes:
                    buzones.append(partes[-1].strip('"'))

        return buzones

    def _buscar_buzon(self, nombre, buzones_disponibles):
        nombre_limpio = nombre.lower()
        if nombre in buzones_disponibles:
            return nombre

        equivalencias = {
            "all mail": ["all mail", "todos", "todo correo"],
            "spam": ["spam", "no deseado", "correos no deseados"],
            "promotions": ["promotions", "promociones", "promocion"]
        }

        for buzon in buzones_disponibles:
            buzon_lower = buzon.lower()
            if nombre_limpio == "inbox" and buzon_lower == "inbox":
                return buzon

            for clave, patrones in equivalencias.items():
                if clave in nombre_limpio:
                    for patron in patrones:
                        if patron in buzon_lower:
                            return buzon

        return nombre

    def buscar_y_descargar(self, carpetas, nit, nrc, fecha_desde, fecha_hasta, log_callback, thread_check, organizer):
        self.connect()
        archivos_descargados = 0
        correos_procesados = 0
        
        # Ampliar el rango para asegurar que capture hoy
        # Gmail a veces tiene desfases de zona horaria
        fecha_desde_str = (fecha_desde - timedelta(days=1)).strftime("%d-%b-%Y")
        fecha_hasta_str = (fecha_hasta + timedelta(days=1)).strftime("%d-%b-%Y")
        criterio_fecha = f'(SINCE {fecha_desde_str} BEFORE {fecha_hasta_str})'
        
        buzones_disponibles = self._listar_buzones()

        for carpeta in carpetas:
            carpeta_real = self._buscar_buzon(carpeta, buzones_disponibles)
            try:
                status, _ = self.mail.select(carpeta_real, readonly=True)
                if status != "OK":
                    status, _ = self.mail.select(f'"{carpeta_real}"', readonly=True)
                if status != "OK":
                    log_callback(f"⚠️ No se pudo abrir carpeta: {carpeta_real}")
                    continue

                status, mensajes = self.mail.search(None, criterio_fecha)
                if status != "OK":
                    log_callback(f"⚠️ Error de búsqueda en {carpeta_real}")
                    continue

                ids = mensajes[0].split()
                log_callback(f"📬 {carpeta_real}: encontrados {len(ids)} correos")
                
                for correo_id in ids:
                    if not thread_check(): break
                    
                    status, datos_correo = self.mail.fetch(correo_id, "(RFC822)")
                    mensaje = email.message_from_bytes(datos_correo[0][1])
                    fecha_correo = email.utils.parsedate_to_datetime(mensaje["date"])
                    
                    for parte in mensaje.walk():
                        nombre = parte.get_filename()
                        if not nombre or not nombre.endswith((".json", ".pdf")): continue
                        
                        # Guardar archivo temporal en downloads
                        os.makedirs("downloads", exist_ok=True)
                        ruta_temporal = os.path.join("downloads", f"{uuid.uuid4().hex[:8]}_{nombre}")
                        with open(ruta_temporal, "wb") as f:
                            f.write(parte.get_payload(decode=True))
                        
                        organizer.organizar_archivo_desde_ruta(ruta_temporal, nombre, fecha_correo)
                        archivos_descargados += 1
                        log_callback(f"💾 Guardado: {nombre}")
                    
                    correos_procesados += 1
                    
            except Exception as e:
                log_callback(f"⚠️ Error en {carpeta}: {str(e)}")
                            
        self.disconnect()
        return archivos_descargados, correos_procesados
