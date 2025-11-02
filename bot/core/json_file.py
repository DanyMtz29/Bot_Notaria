# bot/core/faltantes_json.py
from __future__ import annotations
from pathlib import Path
import json, os, tempfile
from typing import Any



class json_file:
    # def __init__(self, path):
    #     self.CACHE_DIR = path
    #     self.FILE = self.CACHE_DIR / "Faltantes.json"
    def set_path(self, path:str) -> None:
        self.FILE = Path(path) / "Faltantes.json"
    def get_path(self):
        return self.FILE
    # ---------------- Utilidades base ----------------
    def _atomic_write(self,path: Path, text: str) -> None:
        """Escritura atómica para evitar archivos corruptos."""
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=path.name, dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp, path)  # move/replace atómico
        finally:
            try:
                os.remove(tmp)
            except FileNotFoundError:
                pass

    def exists(self) -> bool:
        """¿Existe bot/_cache_bot/Faltantes.json?"""
        return self.FILE.exists()

    def load(self,default: Any = None) -> Any:
        """
        Lee el JSON y regresa su contenido (dict/list/lo que sea).
        Si no existe, regresa 'default' (por defecto un dict vacío).
        Si está corrupto, lo renombra a *.bad.json y regresa 'default'.
        """
        if not self.exists():
            return {} if default is None else default
        try:
            with self.FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # respaldo del archivo corrupto
            self.FILE.rename(self.FILE.with_suffix(".bad.json"))
            return {} if default is None else default

    def save(self, obj: Any) -> None:
        """Guarda el objeto como JSON con indentación bonita."""
        self._atomic_write(self.FILE, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))

    def ensure(self, default: Any = None) -> Any:
        """
        Asegura que exista el archivo; si no, lo crea con 'default' (o {}).
        Regresa el contenido actual.
        """
        if not self.exists():
            data = {} if default is None else default
            self.save(data)
            return data
        return self.load(default)

    # --------------- Operaciones comunes ---------------
    def set_key(self, key: str, value: Any) -> dict:
        """Crea/actualiza una clave de nivel superior y guarda."""
        data = self.load({})
        data[key] = value
        self.save(data)
        return data

    def delete_key(self, key: str) -> dict:
        """Elimina una clave de nivel superior si existe y guarda."""
        data = self.load({})
        if key in data:
            del data[key]
            self.save(data)
        return data

    def list_append(self, key: str, value: Any) -> dict:
        """Asegura que 'key' sea lista, agrega 'value' y guarda."""
        data = self.load({})
        lst = data.setdefault(key, [])
        if not isinstance(lst, list):
            raise TypeError(f"'{key}' no es una lista en Faltantes.json")
        lst.append(value)
        self.save(data)
        return data

    def list_remove(self, key: str, predicate_or_value: Any) -> dict:
        """
        Elimina de la lista en 'key':
        - Si pasas un valor, quita la primera coincidencia.
        - Si pasas una función, filtra todos los que cumplan el predicado.
        """
        data = self.load({})
        lst = data.get(key, [])
        if not isinstance(lst, list):
            return data

        if callable(predicate_or_value):
            lst[:] = [x for x in lst if not predicate_or_value(x)]
        else:
            try:
                lst.remove(predicate_or_value)
            except ValueError:
                pass
        self.save(data)
        return data
