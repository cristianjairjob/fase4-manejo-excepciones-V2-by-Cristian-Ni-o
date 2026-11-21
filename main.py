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


if __name__ == "__main__":  # Solo ejecuta main() si el archivo se corre directamente
    main()