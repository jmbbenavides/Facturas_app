import os
import shutil
from datetime import datetime

class Organizer:
    def __init__(self, base_dir="downloads"):
        self.base_dir = base_dir

    def organizar_archivo_desde_ruta(self, ruta_temporal, nombre_original, fecha_correo):
        # Crear estructura Año/Mes/Día
        anio = fecha_correo.strftime("%Y")
        mes = fecha_correo.strftime("%m")
        dia = fecha_correo.strftime("%d")
        
        carpeta_destino = os.path.join(self.base_dir, anio, mes, dia)
        os.makedirs(carpeta_destino, exist_ok=True)
            
        ruta_destino = os.path.join(carpeta_destino, nombre_original)
        
        # Mover archivo
        if os.path.exists(ruta_destino):
            # Si ya existe, añadir timestamp para evitar sobreescritura
            nombre_base, ext = os.path.splitext(nombre_original)
            ruta_destino = os.path.join(carpeta_destino, f"{nombre_base}_{datetime.now().strftime('%H%M%S')}{ext}")
            
        shutil.move(ruta_temporal, ruta_destino)
        return ruta_destino
