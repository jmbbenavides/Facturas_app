import json
import os
import re
import shutil
from datetime import datetime

try:
    import PyPDF2
except Exception:
    PyPDF2 = None


class Organizer:
    def __init__(self, base_dir="downloads"):
        self.base_dir = base_dir

    def _try_parse_date(self, text):
        if not text or not isinstance(text, str):
            return None

        # Common date patterns
        patterns = [
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{2}/\d{2}/\d{4})",
            r"(\d{2}-\d{2}-\d{4})",
            r"(\d{4}/\d{2}/\d{2})",
        ]

        for pat in patterns:
            m = re.search(pat, text)
            if m:
                s = m.group(1)
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                    try:
                        dt = datetime.strptime(s, fmt)
                        return dt
                    except Exception:
                        continue

        # Try ISO datetime strings
        iso = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", text)
        if iso:
            try:
                return datetime.fromisoformat(iso.group(1))
            except Exception:
                pass

        return None

    def _extract_date_from_json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Recursively search for keys that likely contain dates
            date_key_terms = ("fecha", "date", "emision", "issue", "fec", "emi")
            stack = [data]
            while stack:
                node = stack.pop()
                if isinstance(node, dict):
                    for k, v in node.items():
                        key_low = str(k).lower()
                        if any(term in key_low for term in date_key_terms):
                            dt = self._try_parse_date(str(v))
                            if dt:
                                return dt
                        if isinstance(v, (dict, list)):
                            stack.append(v)
                elif isinstance(node, list):
                    for it in node:
                        if isinstance(it, (dict, list)):
                            stack.append(it)
                        else:
                            dt = self._try_parse_date(str(it))
                            if dt:
                                return dt

            # Fallback: parse any string-like value in the JSON if key-based search fails
            stack = [data]
            while stack:
                node = stack.pop()
                if isinstance(node, dict):
                    for v in node.values():
                        if isinstance(v, (dict, list)):
                            stack.append(v)
                        else:
                            dt = self._try_parse_date(str(v))
                            if dt:
                                return dt
                elif isinstance(node, list):
                    for it in node:
                        if isinstance(it, (dict, list)):
                            stack.append(it)
                        else:
                            dt = self._try_parse_date(str(it))
                            if dt:
                                return dt
        except Exception:
            return None
        return None

    def _extract_date_from_pdf(self, path):
        if PyPDF2 is None:
            return None
        try:
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = []
                for p in reader.pages[:3]:
                    try:
                        text.append(p.extract_text() or "")
                    except Exception:
                        continue
                txt = "\n".join(text)
                return self._try_parse_date(txt)
        except Exception:
            return None

    def organizar_archivo_desde_ruta(
        self, ruta_temporal, nombre_original, fecha_correo, log_callback=None
    ):
        # Intentar extraer fecha desde el contenido del archivo (JSON o PDF)
        ext = os.path.splitext(nombre_original)[1].lower()
        fecha_extraida = None
        if ext == ".json":
            fecha_extraida = self._extract_date_from_json(ruta_temporal)
        elif ext == ".pdf":
            fecha_extraida = self._extract_date_from_pdf(ruta_temporal)

        # Normalizar fechas a hora local (sin tzinfo) para evitar desfaces de día
        def _to_local_naive(dt):
            if dt is None:
                return None
            try:
                if hasattr(dt, "tzinfo") and dt.tzinfo is not None:
                    return dt.astimezone().replace(tzinfo=None)
                return dt
            except Exception:
                return dt

        fecha_extraida = _to_local_naive(fecha_extraida)
        fecha_correo = _to_local_naive(fecha_correo)

        # Usar fecha extraída si existe, si no, usar la fecha del correo
        fecha_usar = fecha_extraida or fecha_correo or datetime.now()

        # Log de depuración si se proporciona callback
        try:
            if log_callback:
                log_callback(f"🔎 Archivo: {nombre_original}")
                log_callback(f"    Fecha del correo: {fecha_correo}")
                log_callback(f"    Fecha extraída: {fecha_extraida}")
                log_callback(f"    Fecha usada para ordenar: {fecha_usar}")
        except Exception:
            pass

        anio = fecha_usar.strftime("%Y")
        mes = fecha_usar.strftime("%m")
        dia = fecha_usar.strftime("%d")

        carpeta_destino = os.path.join(self.base_dir, anio, mes, dia)
        os.makedirs(carpeta_destino, exist_ok=True)

        ruta_destino = os.path.join(carpeta_destino, nombre_original)

        # Evitar sobreescritura
        if os.path.exists(ruta_destino):
            nombre_base, ext = os.path.splitext(nombre_original)
            ruta_destino = os.path.join(
                carpeta_destino,
                f"{nombre_base}_{datetime.now().strftime('%H%M%S')}{ext}",
            )

        shutil.move(ruta_temporal, ruta_destino)
        return ruta_destino, fecha_usar
