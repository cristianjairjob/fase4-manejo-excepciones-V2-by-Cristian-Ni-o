"""Regresion de las funciones base conservadas dentro de la V2.
Uso: python -m unittest -v test_regresion_base
Todas las escrituras se realizan en carpetas temporales.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SOURCE = (Path(__file__).resolve().parent / "main_v2_by_cristian_ni\u00f1o.py").resolve()
OUT = Path(__file__).resolve().parent
SOURCE_BYTES = SOURCE.read_bytes()
HASH_BEFORE = hashlib.sha256(SOURCE_BYTES).hexdigest()
EVIDENCE: dict[str, str] = {}


@contextlib.contextmanager
def original_aislado():
    """Importa una copia exacta sin activar el menu; usa un directorio temporal."""
    previous = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="revision_inventario_") as folder:
        location = Path(folder)
        copied = location / "main.py"
        shutil.copyfile(SOURCE, copied)
        assert copied.read_bytes() == SOURCE_BYTES
        os.chdir(location)
        try:
            spec = importlib.util.spec_from_file_location("inventario_original", copied)
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            yield module, location
        finally:
            os.chdir(previous)


def correr_menu(folder: Path, entrada: str) -> subprocess.CompletedProcess:
    """Ejecuta el programa original como proceso real con entradas preparadas."""
    environment = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [sys.executable, "-B", str(folder / "main.py")],
        input=entrada, text=True, encoding="utf-8", capture_output=True,
        timeout=10, cwd=folder, env=environment,
    )


class PruebasOriginal(unittest.TestCase):
    def setUp(self):
        self.context = original_aislado()
        self.m, self.folder = self.context.__enter__()

    def tearDown(self):
        self.context.__exit__(None, None, None)

    def producto(self):
        return self.m.Producto("P001", "Teclado", 50000, 10)

    def test_01_sintaxis(self):
        compile(SOURCE_BYTES, str(SOURCE), "exec")

    def test_02_crear_producto_y_quitar_espacios(self):
        p = self.m.Producto(" P001 ", " Teclado ", 50000, 10)
        self.assertEqual((p.codigo, p.nombre, p.precio, p.cantidad), ("P001", "Teclado", 50000, 10))

    def test_03_codigo_vacio(self):
        with self.assertRaises(self.m.ProductoInvalidoError):
            self.m.Producto("  ", "Teclado", 50000, 10)

    def test_04_nombre_vacio(self):
        with self.assertRaises(self.m.ProductoInvalidoError):
            self.m.Producto("P001", "  ", 50000, 10)

    def test_05_precio_cero(self):
        with self.assertRaises(self.m.ProductoInvalidoError):
            self.m.Producto("P001", "Teclado", 0, 10)

    def test_06_precio_negativo(self):
        with self.assertRaises(self.m.ProductoInvalidoError):
            self.m.Producto("P001", "Teclado", -1, 10)

    def test_07_precio_texto(self):
        with self.assertRaises(self.m.ProductoInvalidoError):
            self.m.Producto("P001", "Teclado", "abc", 10)

    def test_08_cantidad_negativa(self):
        with self.assertRaises(self.m.ProductoInvalidoError):
            self.m.Producto("P001", "Teclado", 50000, -1)

    def test_09_cantidad_decimal(self):
        with self.assertRaises(self.m.ProductoInvalidoError):
            self.m.Producto("P001", "Teclado", 50000, 1.5)

    def test_10_stock_cero_permitido(self):
        self.assertEqual(self.m.Producto("P001", "Teclado", 50000, 0).cantidad, 0)

    def test_11_venta_valida(self):
        p = self.producto()
        p.vender(3)
        self.assertEqual(p.cantidad, 7)

    def test_12_venta_agota_existencias(self):
        p = self.producto()
        p.vender(10)
        self.assertEqual(p.cantidad, 0)

    def test_13_venta_cero(self):
        p = self.producto()
        with self.assertRaises(self.m.ProductoInvalidoError):
            p.vender(0)
        self.assertEqual(p.cantidad, 10)

    def test_14_venta_negativa(self):
        p = self.producto()
        with self.assertRaises(self.m.ProductoInvalidoError):
            p.vender(-1)
        self.assertEqual(p.cantidad, 10)

    def test_15_venta_fraccionaria(self):
        p = self.producto()
        with self.assertRaises(self.m.ProductoInvalidoError):
            p.vender(1.5)
        self.assertEqual(p.cantidad, 10)

    def test_16_venta_sin_stock_no_descuenta(self):
        p = self.producto()
        with self.assertRaises(self.m.StockInsuficienteError):
            p.vender(11)
        self.assertEqual(p.cantidad, 10)

    def test_17_codigo_duplicado_no_reemplaza(self):
        inv = self.m.Inventario()
        p = self.producto()
        inv.agregar(p)
        with self.assertRaises(self.m.ProductoInvalidoError):
            inv.agregar(self.m.Producto("P001", "Otro", 1, 1))
        self.assertIs(inv.buscar("P001"), p)
        self.assertEqual(len(inv.listar()), 1)

    def test_18_buscar_existente(self):
        inv = self.m.Inventario()
        p = self.producto()
        inv.agregar(p)
        self.assertIs(inv.buscar("P001"), p)

    def test_19_buscar_inexistente(self):
        with self.assertRaises(self.m.ProductoNoEncontradoError):
            self.m.Inventario().buscar("NO_EXISTE")

    def test_20_listar(self):
        inv = self.m.Inventario()
        self.assertEqual(inv.listar(), [])
        p = self.producto()
        inv.agregar(p)
        self.assertEqual(inv.listar(), [p])

    def test_21_total_venta(self):
        inv = self.m.Inventario()
        inv.agregar(self.producto())
        self.assertEqual(inv.vender("P001", 3), 150000)
        self.assertEqual(inv.buscar("P001").cantidad, 7)

    def test_22_cargar_archivo_inexistente(self):
        inv = self.m.Inventario()
        inv.cargar()
        self.assertEqual(inv.listar(), [])

    def test_23_guardar_y_recargar(self):
        inv = self.m.Inventario()
        inv.agregar(self.producto())
        inv.vender("P001", 3)
        inv.guardar()
        saved = json.loads((self.folder / "inventario.json").read_text(encoding="utf-8"))
        self.assertEqual(saved[0]["cantidad"], 7)
        other = self.m.Inventario()
        other.cargar()
        self.assertEqual(other.buscar("P001").a_diccionario(), inv.buscar("P001").a_diccionario())

    def test_24_json_danado(self):
        (self.folder / "inventario.json").write_text("{mal formado", encoding="utf-8")
        with self.assertRaises(self.m.InventarioError):
            self.m.Inventario().cargar()

    def test_25_json_campo_ausente(self):
        (self.folder / "inventario.json").write_text('[{"codigo":"P001"}]', encoding="utf-8")
        with self.assertRaises(self.m.InventarioError):
            self.m.Inventario().cargar()

    def test_26_error_lectura_sistema_archivos(self):
        (self.folder / "inventario.json").mkdir()
        with self.assertRaises(self.m.InventarioError):
            self.m.Inventario().cargar()

    def test_27_error_escritura_sistema_archivos(self):
        (self.folder / "inventario.json").mkdir()
        with self.assertRaises(self.m.InventarioError):
            self.m.Inventario().guardar()

    def test_28_leer_entero_reintenta(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["abc", "2.5", "4"]), contextlib.redirect_stdout(output):
            self.assertEqual(self.m.leer_entero("Cantidad: "), 4)
        self.assertEqual(output.getvalue().count("Error:"), 2)

    def test_29_leer_decimal_reintenta(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["abc", "25.5"]), contextlib.redirect_stdout(output):
            self.assertEqual(self.m.leer_decimal("Precio: "), 25.5)
        self.assertIn("Error:", output.getvalue())

    def test_30_menu_completo_y_reinicio(self):
        data = "1\nP001\nTeclado\n50000\n10\n2\n3\nP001\n4\nP001\n3\n2\n5\n"
        run = correr_menu(self.folder, data)
        EVIDENCE["menu_operacion_valida.txt"] = run.stdout + run.stderr
        self.assertEqual(run.returncode, 0)
        self.assertIn("Total: $150,000", run.stdout)
        self.assertIn("Stock: 7", run.stdout)
        second = correr_menu(self.folder, "2\n5\n")
        EVIDENCE["menu_recarga.txt"] = second.stdout + second.stderr
        self.assertEqual(second.returncode, 0)
        self.assertIn("Stock: 7", second.stdout)

    def test_31_menu_continua_tras_errores(self):
        data = (
            "9\n3\nNO_EXISTE\n"
            "1\nP001\nTeclado\n50000\n10\n"
            "1\nP001\nOtro\n1\n1\n"
            "4\nP001\n11\n"
            "4\nP001\n-1\n"
            "4\nP001\n2\n2\n5\n"
        )
        run = correr_menu(self.folder, data)
        EVIDENCE["menu_errores_controlados.txt"] = run.stdout + run.stderr
        self.assertEqual(run.returncode, 0)
        self.assertIn("No existe el producto", run.stdout)
        self.assertIn("Ya existe un producto", run.stdout)
        self.assertIn("Stock insuficiente", run.stdout)
        self.assertIn("Total: $100,000", run.stdout)
        self.assertIn("Stock: 8", run.stdout)

    def test_32_menu_recupera_json_sintacticamente_danado(self):
        (self.folder / "inventario.json").write_text("{mal formado", encoding="utf-8")
        run = correr_menu(self.folder, "2\n5\n")
        EVIDENCE["menu_json_danado.txt"] = run.stdout + run.stderr
        self.assertEqual(run.returncode, 0)
        self.assertIn("Aviso:", run.stdout)
        self.assertIn("Datos guardados", run.stdout)



if __name__ == "__main__":
    unittest.main(verbosity=2)
