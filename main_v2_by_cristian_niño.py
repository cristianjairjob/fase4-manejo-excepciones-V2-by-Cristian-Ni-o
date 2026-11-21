# ============================================================
# Sistema de Inventario - Fase 4: Manejo de excepciones
# Curso: Programación 213023 - UNAD
# ============================================================

import json  # Módulo para guardar y leer datos en formato JSON
import os    # Módulo para comprobar si un archivo existe

ARCHIVO = "inventario.json"  # Nombre del archivo donde se guardan los datos


# ---------- EXCEPCIONES PERSONALIZADAS ----------

class InventarioError(Exception):
    """Excepción base de la que heredan todos los errores del sistema."""


class ProductoInvalidoError(InventarioError):
    """Se lanza cuando los datos de un producto no son válidos."""


class ProductoNoEncontradoError(InventarioError):
    """Se lanza cuando se busca un código que no existe."""


class StockInsuficienteError(InventarioError):
    """Se lanza cuando se intenta vender más unidades de las disponibles."""


# ---------- CLASE PRODUCTO ----------

class Producto:
    """Representa un producto del inventario."""

    def __init__(self, codigo, nombre, precio, cantidad):
        # Validamos que el código sea texto y no esté vacío
        if not isinstance(codigo, str) or not codigo.strip():
            raise ProductoInvalidoError("El código no puede estar vacío.")
        # Validamos que el nombre no esté vacío
        if not isinstance(nombre, str) or not nombre.strip():
            raise ProductoInvalidoError("El nombre no puede estar vacío.")
        # Validamos que el precio sea numérico y positivo
        if not isinstance(precio, (int, float)) or precio <= 0:
            raise ProductoInvalidoError("El precio debe ser un número mayor a 0.")
        # Validamos que la cantidad sea entera y no negativa
        if not isinstance(cantidad, int) or cantidad < 0:
            raise ProductoInvalidoError("La cantidad debe ser un entero mayor o igual a 0.")

        self.codigo = codigo.strip()   # Guardamos el código sin espacios sobrantes
        self.nombre = nombre.strip()   # Guardamos el nombre sin espacios sobrantes
        self.precio = precio           # Guardamos el precio
        self.cantidad = cantidad       # Guardamos la cantidad disponible

    def vender(self, unidades):
        """Descuenta unidades del stock si hay suficientes."""
        # Validamos que las unidades sean un entero positivo
        if not isinstance(unidades, int) or unidades <= 0:
            raise ProductoInvalidoError("Las unidades deben ser un entero mayor a 0.")
        # Si piden más de lo que hay, lanzamos el error personalizado
        if unidades > self.cantidad:
            raise StockInsuficienteError(
                f"Stock insuficiente de '{self.nombre}': hay {self.cantidad}, pidió {unidades}."
            )
        self.cantidad -= unidades  # Restamos las unidades vendidas

    def a_diccionario(self):
        """Convierte el producto en diccionario para guardarlo en JSON."""
        return {"codigo": self.codigo, "nombre": self.nombre,
                "precio": self.precio, "cantidad": self.cantidad}

    def __str__(self):
        # Texto con el que se muestra el producto al imprimirlo
        return f"[{self.codigo}] {self.nombre} - ${self.precio:,.0f} - Stock: {self.cantidad}"


# ---------- CLASE INVENTARIO ----------

class Inventario:
    """Administra la colección de productos."""

    def __init__(self):
        self.productos = {}  # Diccionario: clave = código, valor = Producto

    def agregar(self, producto):
        # Evitamos códigos duplicados
        if producto.codigo in self.productos:
            raise ProductoInvalidoError(f"Ya existe un producto con el código {producto.codigo}.")
        self.productos[producto.codigo] = producto  # Lo guardamos en el diccionario

    def buscar(self, codigo):
        # Intentamos obtener el producto; si no existe, lanzamos error propio
        try:
            return self.productos[codigo]
        except KeyError:
            raise ProductoNoEncontradoError(f"No existe el producto con código {codigo}.")

    def vender(self, codigo, unidades):
        producto = self.buscar(codigo)  # Puede lanzar ProductoNoEncontradoError
        producto.vender(unidades)       # Puede lanzar StockInsuficienteError
        return producto.precio * unidades  # Devuelve el total de la venta

    def listar(self):
        return list(self.productos.values())  # Lista con todos los productos

    def guardar(self):
        """Guarda el inventario en un archivo JSON."""
        try:
            with open(ARCHIVO, "w", encoding="utf-8") as f:  # Abrimos para escribir
                json.dump([p.a_diccionario() for p in self.productos.values()],
                          f, indent=4, ensure_ascii=False)
        except OSError as e:  # Errores de disco, permisos, etc.
            raise InventarioError(f"No se pudo guardar el archivo: {e}")

    def cargar(self):
        """Carga el inventario desde el archivo JSON, si existe."""
        if not os.path.exists(ARCHIVO):  # Si no existe, empezamos vacío
            return
        try:
            with open(ARCHIVO, "r", encoding="utf-8") as f:  # Abrimos para leer
                datos = json.load(f)  # Convertimos el JSON a lista de diccionarios
            for d in datos:  # Recreamos cada producto
                self.agregar(Producto(d["codigo"], d["nombre"], d["precio"], d["cantidad"]))
        except json.JSONDecodeError:  # El archivo está dañado
            raise InventarioError("El archivo de inventario está dañado.")
        except KeyError as e:  # Falta algún campo en el JSON
            raise InventarioError(f"Al archivo le falta el campo {e}.")
        except OSError as e:  # Error al leer el archivo
            raise InventarioError(f"No se pudo leer el archivo: {e}")


# ---------- FUNCIONES AUXILIARES DE ENTRADA ----------

def leer_entero(mensaje):
    """Pide un entero y repite hasta que el usuario escriba uno válido."""
    while True:
        try:
            return int(input(mensaje))  # Intenta convertir a entero
        except ValueError:              # Si no es número, avisa y repite
            print("Error: ingrese un número entero válido.")


def leer_decimal(mensaje):
    """Pide un número decimal y repite hasta que sea válido."""
    while True:
        try:
            return float(input(mensaje))  # Intenta convertir a decimal
        except ValueError:
            print("Error: ingrese un número válido.")


# ---------- PROGRAMA PRINCIPAL ----------

def mostrar_menu():
    print("\n===== INVENTARIO =====")
    print("1. Agregar producto")
    print("2. Listar productos")
    print("3. Buscar producto")
    print("4. Vender producto")
    print("5. Guardar y salir")


def main():
    inventario = Inventario()  # Creamos el inventario vacío
    try:
        inventario.cargar()    # Intentamos cargar datos guardados
        print("Datos cargados correctamente.")
    except InventarioError as e:
        print(f"Aviso: {e}. Se inicia con inventario vacío.")

    while True:  # Bucle del menú
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()
        try:
            if opcion == "1":
                codigo = input("Código: ")
                nombre = input("Nombre: ")
                precio = leer_decimal("Precio: ")
                cantidad = leer_entero("Cantidad: ")
                inventario.agregar(Producto(codigo, nombre, precio, cantidad))
                print("Producto agregado.")
            elif opcion == "2":
                productos = inventario.listar()
                if not productos:
                    print("El inventario está vacío.")
                for p in productos:
                    print(p)
            elif opcion == "3":
                print(inventario.buscar(input("Código a buscar: ").strip()))
            elif opcion == "4":
                codigo = input("Código a vender: ").strip()
                unidades = leer_entero("Unidades: ")
                total = inventario.vender(codigo, unidades)
                print(f"Venta realizada. Total: ${total:,.0f}")
            elif opcion == "5":
                inventario.guardar()  # Guardamos antes de salir
                print("Datos guardados. ¡Hasta pronto!")
                break  # Salimos del bucle
            else:
                print("Opción no válida.")
        except InventarioError as e:  # Captura todos nuestros errores personalizados
            print(f"Error: {e}")
        except KeyboardInterrupt:     # El usuario presionó Ctrl+C
            print("\nInterrumpido. Guardando datos...")
            inventario.guardar()
            break
        except Exception as e:        # Cualquier otro error inesperado
            print(f"Error inesperado: {e}")
        finally:
            pass  # Aquí se podrían liberar recursos; se ejecuta siempre


# ============================================================
# INICIO DEL APORTE ADICIONAL - CRISTIAN NINO
# Version 2 - Reposicion de existencias y bitacora
# Creado por: Cristian Niño
# ============================================================
# El codigo anterior y el arranque original situado al final pertenecen
# al archivo main.py del companero. Se conservan sin editar ninguna linea.
# Esta ampliacion reutiliza las clases originales y agrega funcionalidades;
# no corrige las validaciones ni los problemas del programa base.
# Las reposiciones se hacen en memoria. La opcion 5 guarda inventario.json.
# La bitacora registra reposiciones, sus rechazos y el guardado desde la V2;
# no registra todas las operaciones de la version original.

from collections import deque  # Permite consultar solo los ultimos registros.
from datetime import datetime  # Obtiene la fecha, hora y zona horaria del equipo.
from pathlib import Path  # Representa la ruta del archivo de bitacora.
from typing import Optional, Union  # Describe los tipos de los parametros nuevos.


# ---------- BLOQUE NUEVO 1 - CREADO POR: Cristian Niño ----------

class ReposicionInvalidaError(InventarioError):
    """Representa datos incorrectos al intentar reponer existencias."""


class BitacoraError(InventarioError):
    """Representa un problema al escribir o consultar la nueva bitacora."""


class BitacoraReposiciones:
    """Registra eventos de la ampliacion como una linea JSON por evento."""

    def __init__(self, ruta: Union[str, Path] = "reposiciones_cristian.log"):
        self.ruta = Path(ruta)  # La ruta relativa parte de la carpeta de ejecucion.

    def registrar(self, evento: str, detalle: str) -> None:
        """Agrega un evento sin borrar los registros de sesiones anteriores."""
        registro = {
            "fecha": datetime.now().astimezone().isoformat(timespec="seconds"),
            "autor_aporte": "Cristian Niño",
            "evento": evento,
            "detalle": detalle,
        }
        # JSON escapa los saltos de linea de la entrada para no falsear registros.
        linea = json.dumps(registro, ensure_ascii=False)
        try:
            with self.ruta.open("a", encoding="utf-8") as archivo:
                archivo.write(linea + "\n")  # El contexto cierra y vacia el archivo.
        except (OSError, UnicodeError) as error:
            # El encadenamiento conserva la causa tecnica del fallo de escritura.
            raise BitacoraError(
                f"No se pudo escribir la bitacora '{self.ruta}': {error}"
            ) from error

    def leer_ultimos(self, limite: int = 20) -> list:
        """Devuelve hasta 20 eventos, por defecto, del mas antiguo al mas reciente."""
        if type(limite) is not int or limite <= 0:
            raise BitacoraError("El limite de consulta debe ser un entero positivo.")
        try:
            with self.ruta.open("r", encoding="utf-8") as archivo:
                # Solo se conservan las ultimas lineas no vacias en memoria.
                lineas = deque((linea for linea in archivo if linea.strip()), maxlen=limite)
        except FileNotFoundError:
            return []  # Es normal que aun no exista un historial al iniciar.
        except (OSError, UnicodeError) as error:
            raise BitacoraError(f"No se pudo leer la bitacora: {error}") from error

        registros = []
        try:
            for linea in lineas:
                registro = json.loads(linea)
                # Se comprueba el formato antes de mostrar el archivo al usuario.
                campos = ("fecha", "autor_aporte", "evento", "detalle")
                if not isinstance(registro, dict) or any(
                    not isinstance(registro.get(campo), str) for campo in campos
                ):
                    raise ValueError("El registro no tiene el formato esperado.")
                registros.append(registro)
        except (ValueError, TypeError) as error:
            raise BitacoraError(
                "La bitacora contiene un registro ilegible. No se ha modificado el archivo."
            ) from error
        return registros


# ---------- BLOQUE NUEVO 2 - CREADO POR: Cristian Niño ----------

class InventarioV2(Inventario):
    """Hereda el inventario original y agrega reposicion sin reescribir sus metodos."""

    def __init__(self, bitacora: Optional[BitacoraReposiciones] = None):
        super().__init__()  # Conserva el diccionario y los metodos de Inventario.
        self.bitacora = bitacora if bitacora is not None else BitacoraReposiciones()

    @staticmethod
    def _validar_unidades_reposicion(unidades: Union[int, str]) -> int:
        """Acepta un entero positivo o el texto que lo representa, sin redondear."""
        if isinstance(unidades, str):
            try:
                cantidad = int(unidades.strip())
            except ValueError as error:
                # Se encadena el error de conversion con una excepcion del negocio.
                raise ReposicionInvalidaError(
                    "Las unidades de reposicion deben ser un entero mayor a 0."
                ) from error
        elif type(unidades) is int:
            cantidad = unidades  # No se aceptan bool ni valores decimales como 5.0.
        else:
            raise ReposicionInvalidaError(
                "Las unidades de reposicion deben ser un entero mayor a 0."
            )
        if cantidad <= 0:
            raise ReposicionInvalidaError(
                "Las unidades de reposicion deben ser un entero mayor a 0."
            )
        return cantidad

    def _registrar_rechazo(self, codigo, unidades, error: InventarioError) -> None:
        """Registra el rechazo, o informa ambos problemas si tambien falla el log."""
        detalle = f"Codigo={codigo!r}; unidades={unidades!r}; motivo={error}"
        try:
            self.bitacora.registrar("ERROR_REPOSICION", detalle)
        except BitacoraError as fallo_bitacora:
            # No se comunica un registro exitoso cuando no fue posible escribirlo.
            raise BitacoraError(
                f"{error} Ademas, el error no se pudo registrar: {fallo_bitacora}"
            ) from error

    def reponer(self, codigo: str, unidades: Union[int, str]) -> dict:
        """Aumenta el stock de un producto existente y registra el cambio en memoria.

        No guarda automaticamente inventario.json: se usa la opcion 5 del menu.
        Si falla la escritura de la bitacora, se restaura el stock anterior.
        """
        try:
            if not isinstance(codigo, str) or not codigo.strip():
                raise ReposicionInvalidaError("El codigo de reposicion no puede estar vacio.")
            codigo = codigo.strip()
            cantidad = self._validar_unidades_reposicion(unidades)
            producto = self.buscar(codigo)  # Reutiliza el metodo original, sin cambios.
            if type(producto.cantidad) is not int or producto.cantidad < 0:
                raise ReposicionInvalidaError(
                    "El stock actual no es un entero valido. No se realizo la reposicion."
                )
        except InventarioError as error:
            # No se toca el stock cuando una comprobacion rechaza la operacion.
            self._registrar_rechazo(codigo, unidades, error)
            raise

        anterior = producto.cantidad
        nuevo = anterior + cantidad
        producto.cantidad = nuevo  # Se modifica solo la cantidad del producto elegido.
        detalle = (
            f"Codigo={producto.codigo}; producto={producto.nombre}; unidades={cantidad}; "
            f"stock_anterior={anterior}; stock_nuevo={nuevo}; "
            "cambio en memoria, pendiente de guardar con la opcion 5."
        )
        try:
            self.bitacora.registrar("REPOSICION", detalle)
        except BitacoraError:
            producto.cantidad = anterior  # Evita un cambio de stock sin su registro.
            raise
        else:
            return {
                "codigo": producto.codigo,
                "nombre": producto.nombre,
                "unidades": cantidad,
                "stock_anterior": anterior,
                "stock_nuevo": nuevo,
            }


# ---------- BLOQUE NUEVO 3 - CREADO POR: Cristian Niño ----------

def mostrar_menu_v2() -> None:
    """Conserva las cinco opciones originales y presenta dos opciones adicionales."""
    print("\nVersion 2 - Aporte de Cristian Niño")
    mostrar_menu()  # Se llama al menu del companero; no se modifica su funcion.
    print("6. Reponer existencias - Cristian Niño")
    print("7. Consultar bitacora de reposiciones - Cristian Niño")


def mostrar_bitacora_v2(bitacora: BitacoraReposiciones) -> None:
    """Muestra la fecha, el evento y el detalle de los ultimos 20 registros."""
    registros = bitacora.leer_ultimos()
    print("\n===== BITACORA DE LA AMPLIACION =====")
    if not registros:
        print("Todavia no hay registros en la bitacora.")
        return
    for registro in registros:
        print(f"\n{registro['fecha']} | {registro['evento']}")
        print(registro["detalle"])
    print(f"\nArchivo: {bitacora.ruta.resolve()}")


def guardar_v2(inventario: InventarioV2) -> None:
    """Llama al guardado original y anota su finalizacion cuando el log lo permite."""
    inventario.guardar()  # El metodo y el formato JSON original no se reemplazan.
    try:
        inventario.bitacora.registrar(
            "GUARDADO", f"Inventario guardado en {os.path.abspath(ARCHIVO)}."
        )
    except BitacoraError as error:
        # El inventario YA se guardo: no se informa un fracaso del guardado.
        print(f"Aviso: el inventario se guardo, pero no se registro el evento: {error}")


def main_v2() -> None:
    """Menu adicional que integra la reposicion con las operaciones del original."""
    inventario = InventarioV2()
    try:
        inventario.cargar()  # Se conserva la carga original, con sus limitaciones.
        print("Datos cargados correctamente.")
    except InventarioError as e:
        print(f"Aviso: {e}. Se inicia con inventario vacio.")

    while True:
        mostrar_menu_v2()
        opcion = input("Seleccione una opcion: ").strip()
        try:
            # Las opciones 1 a 4 reutilizan las clases y funciones del companero.
            if opcion == "1":
                codigo = input("Codigo: ")
                nombre = input("Nombre: ")
                precio = leer_decimal("Precio: ")
                cantidad = leer_entero("Cantidad: ")
                inventario.agregar(Producto(codigo, nombre, precio, cantidad))
                print("Producto agregado.")
            elif opcion == "2":
                productos = inventario.listar()
                if not productos:
                    print("El inventario esta vacio.")
                for producto in productos:
                    print(producto)
            elif opcion == "3":
                print(inventario.buscar(input("Codigo a buscar: ").strip()))
            elif opcion == "4":
                codigo = input("Codigo a vender: ").strip()
                unidades = leer_entero("Unidades: ")
                total = inventario.vender(codigo, unidades)
                print(f"Venta realizada. Total: ${total:,.0f}")
            elif opcion == "5":
                guardar_v2(inventario)
                print("Datos guardados. Hasta pronto!")
                break
            elif opcion == "6":
                # Se conserva el texto recibido para registrar intentos incorrectos.
                codigo = input("Codigo del producto a reponer: ")
                unidades = input("Unidades recibidas: ")
                movimiento = inventario.reponer(codigo, unidades)
                print(f"Reposicion realizada: {movimiento['nombre']}.")
                print(f"Stock anterior: {movimiento['stock_anterior']}")
                print(f"Unidades recibidas: {movimiento['unidades']}")
                print(f"Stock nuevo: {movimiento['stock_nuevo']}")
                print("Recuerde usar la opcion 5 para guardar el inventario y salir.")
            elif opcion == "7":
                mostrar_bitacora_v2(inventario.bitacora)
            else:
                print("Opcion no valida.")
        except InventarioError as e:
            print(f"Error: {e}")  # Los errores de reposicion vuelven al mismo menu.
        except KeyboardInterrupt:
            print("\nInterrumpido. Guardando datos...")
            guardar_v2(inventario)
            break
        except Exception as e:
            print(f"Error inesperado: {e}")
        finally:
            # Los contextos 'with' de la bitacora ya cierran los archivos abiertos.
            pass


# ---------- ARRANQUE ADICIONAL - CREADO POR: Cristian Niño ----------
if __name__ == "__main__":
    main_v2()
    # Se finaliza aqui para no abrir un segundo menu cuando termine la V2.
    # Asi se conserva, sin editarlo, el bloque de arranque original que sigue.
    raise SystemExit(0)

# FIN DEL APORTE ADICIONAL - CRISTIAN NINO
# ============================================================


if __name__ == "__main__":  # Solo ejecuta main() si el archivo se corre directamente
    main()