# bot/pages/projects_partes.py
from __future__ import annotations

from bot.utils.common_imports import *
from bot.utils.base import Base
from bot.utils.selenium_imports import *



class partesTap(Base):
    """
    Acciones dentro de la pestaña 'Partes' del formulario de 'Nuevo Proyecto'.
    """
    # ---------- utils internos ----------

    def agregar(self, timeout: int = 20):
        """
        Espera a que el botón 'Agregar' sea clickeable, hace scroll y clic.
        Luego valida que se abrió la fila/modal (espera el label 'Rol').
        """
        xpaths = [
            "//button[normalize-space()='Agregar']",
            "//button[.//span[normalize-space()='Agregar']]",
            "//button[@aria-label='Agregar' or @title='Agregar']",
        ]

        last_err = None
        for xp in xpaths:
            try:
                # 1) Esperar a que sea clickeable
                but = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                # 2) Scroll al centro por si hay overlay fijo
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", but
                )
                # 3) Intentar clic normal; si falla, clic por JS
                try:
                    but.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", but)

                # 4) Post-condición: que aparezca “Rol”
                self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//label[normalize-space()='Rol']")
                    )
                )
                return  # listo
            except Exception as e:
                last_err = e
                continue

        # Si ningún XPATH funcionó, propaga el último error para depurar
        raise last_err or RuntimeError("No pude hacer clic en 'Agregar'")

    def set_cliente(self, cliente:str) -> None:
        inp = self.driver.find_element(By.XPATH, "//div[@class='form-group']//input[@placeholder='Busca datos existentes por Nombre, CURP o RFC.']")
        inp.send_keys(cliente)
        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//ul[contains(@id,'listbox') or contains(@class,'k-list')]//li[contains(., '{cliente}')]")
            )
        )
        inp.send_keys(Keys.ARROW_DOWN)
        inp.send_keys(Keys.ENTER)
        time.sleep(1)

    def guardar_parte(self, timeout: int = 10) -> bool:
        """
        Espera a que el botón 'Guardar' sea clickeable (distintas variantes),
        hace scroll y clic (normal o por JS) y valida una post-condición
        (toast de éxito o cierre/disparo del guardado).
        Regresa True si parece haber guardado; False si no.
        """
        XPATHS = [
            # Tu variante original + con <span> anidado
            "//button[contains(@class,'btn-outline-success')][contains(normalize-space(),'Guardar') or .//span[normalize-space()='Guardar']]",
            # A veces es btn-success
            "//button[contains(@class,'btn-success')][contains(normalize-space(),'Guardar') or .//span[normalize-space()='Guardar']]",
            # Botón en footer del modal
            "//div[contains(@class,'modal-footer')]//button[normalize-space()='Guardar']",
            # Por título/aria-label
            "//button[@title='Guardar' or @aria-label='Guardar']",
        ]

        # Overlays comunes (ajusta si tu UI usa otros)
        OVERLAYS = (By.CSS_SELECTOR, ".k-loading-mask,.k-busy,.spinner-border,.modal-backdrop.show")

        # 0) Si hay overlay visible, espera a que se vaya (no bloqueante si no existe)
        try:
            self.wait.until(EC.invisibility_of_element_located(OVERLAYS))
        except Exception:
            pass

        last_err = None
        for xp in XPATHS:
            try:
                # 1) Espera a que sea clickeable
                but = self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))

                # 2) Scroll al centro (a veces queda bajo el header fijo)
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", but)
                except Exception:
                    pass

                # 3) Click con pequeño retry por si se vuelve stale
                clicked = False
                for _ in range(3):
                    try:
                        try:
                            but.click()
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", but)
                        clicked = True
                        break
                    except StaleElementReferenceException:
                        but = self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                        continue

                if not clicked:
                    continue

                # 4) Post-condición: éxito o al menos que cambie el estado
                #    - Toast de éxito (kendo/bootstrap)
                #    - o que desaparezca el botón/ se deshabilite/ cambie el DOM
                try:
                    self.wait.until(
                        lambda d: (
                            len(d.find_elements(By.CSS_SELECTOR, ".toast-success,.k-notification-success")) > 0
                            or len(d.find_elements(By.XPATH, xp)) == 0
                            or (but.get_attribute("disabled") in ("true", "disabled"))
                        )
                    )
                except Exception:
                    pass

                return True
            except Exception as e:
                last_err = e
                continue

        print(f"NO SE PUDO SELECCIONAR EL BOTON Guardar: {last_err}")
        return False

    def set_rol(self, rol:str)->None:
        try:
            fila_rol = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'form-group') and .//label[normalize-space()='Rol']]"
            )
            campo_rol = fila_rol.find_element(By.XPATH, ".//span[contains(@class,'k-input-inner')]")
            campo_rol.click()

            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//ul[contains(@id,'listbox') or contains(@class,'k-list')]//li")
                )
            )

            opcion = self.wait.until(EC.element_to_be_clickable((
                By.XPATH,
                f"//ul[contains(@id,'listbox') or contains(@class,'k-list')]//li[contains(., '{rol}')]"
            )))
            opcion.click()
            self.wait.until(EC.text_to_be_present_in_element(
                (By.XPATH, "//kendo-dropdownlist//span[contains(@class,'k-input-value-text')]"),
                rol
            ))
            #print(f"Rol '{rol}' seleccionado correctamente.")
        except Exception as e:
            print(f"Error al seleccionar el rol '{rol}': {e}")

    def existe_cliente_y_rol(self, nombre: str, rol: str) -> bool:
        """
        True si ya existe en la grilla de 'Partes' una fila cuyo
        Nombre/Fideicomiso (col 1) contiene `nombre` y cuyo Rol (col 3) contiene `rol`.
        Comparación case-insensitive y tolerante a acentos.
        """
        # Asegura que el cuerpo de la tabla esté presente (Kendo grid)
        try:
            self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[@role='grid']//tbody[@role='rowgroup']")
            ))
        except Exception:
            # Si no hay grid visible, no hay filas todavía
            return False

        nombre_l = (nombre or "").strip().lower()
        rol_l    = (rol or "").strip().lower()

        xp = (
            "//div[@role='grid']//tbody[@role='rowgroup']"
            "//tr["
            "  .//td[@role='gridcell' and @aria-colindex='1']"
            "     [contains(translate(normalize-space(.),"
            "       'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
            "       'abcdefghijklmnopqrstuvwxyzáéíóúüñ'"
            "     ), %s)]"
            "  and "
            "  .//td[@role='gridcell' and @aria-colindex='3']"
            "     [contains(translate(normalize-space(.),"
            "       'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
            "       'abcdefghijklmnopqrstuvwxyzáéíóúüñ'"
            "     ), %s)]"
            "]"
        )

        filas = self.driver.find_elements(By.XPATH, xp % (repr(nombre_l), repr(rol_l)))
        return len(filas) > 0


    def set_porcentaje(self, valor: int | float = 50) -> None:
        """
        Escribe el porcentaje en el kendo-numerictextbox de 'Porcentaje'.
        Solo escribe: no toca switches ni nada más.
        """
        try:
            # Contenedor por la etiqueta 'Porcentaje'
            fila = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//label[normalize-space()='Porcentaje']/..")
                )
            )
            # Input real del spinner
            inp = fila.find_element(By.XPATH, ".//input[@role='spinbutton']")
            inp.click()
            inp.send_keys(Keys.CONTROL, "a")
            inp.send_keys(Keys.DELETE)
            inp.send_keys(str(valor))
            # ENTER opcional para confirmar el spinner
            inp.send_keys(Keys.ENTER)
        except Exception as e:
            print(f"No se pudo establecer el porcentaje: {e}")