"""Pruebas de la ampliacion de Cristian Nino, aisladas de los datos del usuario.
Ejecutar en esta carpeta: python -m unittest -v test_main_v2
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

BASE = Path(__file__).resolve().parent
SOURCE = BASE / 'main_v2_by_cristian_ni\u00f1o.py'
ORIGINAL = BASE / 'main.py'
ORIGINAL_HASH = '5ad0f66ba3427e57b780325b6f4afc8a57c864792f908dd5fb7653ab7a8079fc'
START = b'# ============================================================\n# INICIO DEL APORTE ADICIONAL - CRISTIAN NINO\n'
END = b'# FIN DEL APORTE ADICIONAL - CRISTIAN NINO\n# ============================================================\n\n\n'
AUTHOR = 'Cristian Ni\u00f1o'


class PruebasV2(unittest.TestCase):
    def setUp(self):
        self.prev = Path.cwd()
        self.tmp = tempfile.TemporaryDirectory(prefix='prueba_v2_cristian_')
        self.folder = Path(self.tmp.name)
        os.chdir(self.folder)
        spec = importlib.util.spec_from_file_location('inventario_v2_prueba', SOURCE)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.inv = self.m.InventarioV2()
        self.inv.agregar(self.m.Producto('P001', 'Teclado', 50000, 7))

    def tearDown(self):
        os.chdir(self.prev)
        self.tmp.cleanup()

    def cli(self, entrada):
        # Solo se copia la V2: la prueba comprueba que es autosuficiente.
        local = self.folder / SOURCE.name
        shutil.copyfile(SOURCE, local)
        env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
        return subprocess.run([sys.executable, '-B', str(local)], input=entrada,
                              text=True, encoding='utf-8', capture_output=True,
                              cwd=self.folder, env=env, timeout=10)

    def test_01_original_inmutable(self):
        self.assertEqual(hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(), ORIGINAL_HASH)

    def test_02_solo_se_inserto_un_bloque(self):
        data = SOURCE.read_bytes()
        self.assertEqual(data.count(START), 1)
        self.assertEqual(data.count(END), 1)
        inicio = data.index(START)
        fin = data.index(END) + len(END)
        reconstruido = data[:inicio] + data[fin:]
        self.assertEqual(reconstruido, ORIGINAL.read_bytes())
        self.assertEqual(hashlib.sha256(reconstruido).hexdigest(), ORIGINAL_HASH)

    def test_03_metodos_originales_heredados_sin_sobrescribir(self):
        for nombre in ('agregar', 'buscar', 'vender', 'listar', 'guardar', 'cargar'):
            with self.subTest(metodo=nombre):
                self.assertIs(getattr(self.m.InventarioV2, nombre),
                              getattr(self.m.Inventario, nombre))

    def test_04_operaciones_base(self):
        self.assertEqual(len(self.inv.listar()), 1)
        self.assertEqual(self.inv.vender('P001', 2), 100000)
        self.assertEqual(self.inv.buscar('P001').cantidad, 5)
        with self.assertRaises(self.m.StockInsuficienteError):
            self.inv.vender('P001', 6)
        self.assertEqual(self.inv.buscar('P001').cantidad, 5)

    def test_05_reponer_cinco_sobre_siete_y_log(self):
        resultado = self.inv.reponer('P001', 5)
        self.assertEqual(resultado, {'codigo': 'P001', 'nombre': 'Teclado',
                                    'unidades': 5, 'stock_anterior': 7, 'stock_nuevo': 12})
        self.assertEqual(self.inv.buscar('P001').cantidad, 12)
        registro = self.inv.bitacora.leer_ultimos()[0]
        self.assertEqual(registro['evento'], 'REPOSICION')
        self.assertEqual(registro['autor_aporte'], AUTHOR)
        self.assertIn('stock_anterior=7', registro['detalle'])
        self.assertIn('stock_nuevo=12', registro['detalle'])
        self.assertIsNotNone(datetime.fromisoformat(registro['fecha']).tzinfo)

    def test_06_reponer_stock_cero(self):
        self.inv.buscar('P001').cantidad = 0
        self.assertEqual(self.inv.reponer('P001', 1)['stock_nuevo'], 1)

    def test_07_espacios_y_texto_entero(self):
        self.assertEqual(self.inv.reponer(' P001 ', ' 5 ')['stock_nuevo'], 12)

    def test_08_varias_reposiciones(self):
        for cantidad in (1, 2, 3):
            self.inv.reponer('P001', cantidad)
        self.assertEqual(self.inv.buscar('P001').cantidad, 13)
        self.assertEqual(len(self.inv.bitacora.leer_ultimos()), 3)

    def test_09_unidades_invalidas_no_cambian_stock_y_se_registran(self):
        casos = [0, -1, '0', '-2', '', ' ', 'abc', '3.5', '1,5', 'nan', 'inf',
                 5.0, 2.5, True, False, None, float('nan'), float('inf')]
        for unidades in casos:
            with self.subTest(unidades=repr(unidades)):
                with self.assertRaises(self.m.ReposicionInvalidaError):
                    self.inv.reponer('P001', unidades)
                self.assertEqual(self.inv.buscar('P001').cantidad, 7)
                self.assertEqual(self.inv.bitacora.leer_ultimos()[-1]['evento'],
                                 'ERROR_REPOSICION')
        self.assertEqual(len(self.inv.bitacora.leer_ultimos()), len(casos))

    def test_10_codigos_invalidos_no_cambian_stock(self):
        for codigo in ('', ' ', None, 42, [], {}):
            with self.subTest(codigo=codigo):
                with self.assertRaises(self.m.ReposicionInvalidaError):
                    self.inv.reponer(codigo, 5)
                self.assertEqual(self.inv.buscar('P001').cantidad, 7)
        with self.assertRaises(self.m.ProductoNoEncontradoError):
            self.inv.reponer('NO_EXISTE', 5)
        self.assertEqual(len(self.inv.listar()), 1)

    def test_11_stock_invalido_no_se_repara_silenciosamente(self):
        for estado in (-1, 2.5, True):
            with self.subTest(estado=estado):
                self.inv.buscar('P001').cantidad = estado
                with self.assertRaises(self.m.ReposicionInvalidaError):
                    self.inv.reponer('P001', 5)
                self.assertEqual(self.inv.buscar('P001').cantidad, estado)

    def test_12_fallo_escritura_log_restaura_stock(self):
        self.inv.bitacora.ruta.mkdir()
        with self.assertRaises(self.m.BitacoraError) as captured:
            self.inv.reponer('P001', 5)
        self.assertEqual(self.inv.buscar('P001').cantidad, 7)
        self.assertIsInstance(captured.exception.__cause__, OSError)
        self.assertFalse(Path('inventario.json').exists())

    def test_13_rechazo_y_log_inaccesible_informa_ambos(self):
        self.inv.bitacora.ruta.mkdir()
        with self.assertRaises(self.m.BitacoraError) as captured:
            self.inv.reponer('P001', '-1')
        self.assertIn('entero mayor a 0', str(captured.exception))
        self.assertIn('no se pudo registrar', str(captured.exception))
        self.assertEqual(self.inv.buscar('P001').cantidad, 7)
        self.assertIsInstance(captured.exception.__cause__, self.m.ReposicionInvalidaError)

    def test_14_encadenamiento_de_conversion(self):
        with self.assertRaises(self.m.ReposicionInvalidaError) as captured:
            self.inv.reponer('P001', 'no_es_entero')
        self.assertIsInstance(captured.exception.__cause__, ValueError)

    def test_15_limitaciones_originales_conservadas(self):
        # Se observa el limite anterior; NO se arregla ni se aprueba como requisito.
        self.assertTrue(math.isnan(self.m.Producto('P002', 'Limite', float('nan'), 1).precio))
        self.assertTrue(math.isinf(self.m.Producto('P003', 'Limite', float('inf'), 1).precio))
        Path('inventario.json').write_text('null', encoding='utf-8')
        with self.assertRaises(TypeError):
            self.m.Inventario().cargar()

    def test_16_guardar_y_recargar_despues_de_reponer(self):
        self.inv.reponer('P001', 5)
        self.m.guardar_v2(self.inv)
        recargado = self.m.InventarioV2()
        recargado.cargar()
        self.assertEqual(recargado.buscar('P001').cantidad, 12)
        self.assertEqual(recargado.bitacora.leer_ultimos()[-1]['evento'], 'GUARDADO')

    def test_17_no_hay_autoguardado_del_inventario(self):
        self.inv.reponer('P001', 5)
        self.assertFalse(Path('inventario.json').exists())
        self.assertIn('pendiente de guardar', self.inv.bitacora.leer_ultimos()[0]['detalle'])

    def test_18_historial_append_y_reapertura(self):
        self.inv.reponer('P001', 2)
        self.inv.reponer('P001', 1)
        otra = self.m.BitacoraReposiciones()
        registros = otra.leer_ultimos()
        self.assertEqual(len(registros), 2)
        self.assertIn('stock_nuevo=9', registros[0]['detalle'])
        self.assertIn('stock_nuevo=10', registros[1]['detalle'])

    def test_19_historial_inexistente_y_vacio(self):
        self.assertEqual(self.inv.bitacora.leer_ultimos(), [])
        self.inv.bitacora.ruta.write_text('\n\n', encoding='utf-8')
        self.assertEqual(self.inv.bitacora.leer_ultimos(), [])

    def test_20_consulta_solo_ultimos_veinte(self):
        for n in range(25):
            self.inv.bitacora.registrar('PRUEBA', str(n))
        registros = self.inv.bitacora.leer_ultimos()
        self.assertEqual(len(registros), 20)
        self.assertEqual(registros[0]['detalle'], '5')
        self.assertEqual(registros[-1]['detalle'], '24')
        for limite in (0, -1, True, 2.5):
            with self.assertRaises(self.m.BitacoraError):
                self.inv.bitacora.leer_ultimos(limite)

    def test_21_historial_corrupto_no_se_modifica(self):
        for contenido in (b'{mal\n', b'null\n', b'[42]\n', b'{"fecha":1}\n', b'\xff\n'):
            with self.subTest(contenido=contenido):
                self.inv.bitacora.ruta.write_bytes(contenido)
                with self.assertRaises(self.m.BitacoraError):
                    self.inv.bitacora.leer_ultimos()
                self.assertEqual(self.inv.bitacora.ruta.read_bytes(), contenido)

    def test_22_escribir_en_directorio_y_leer_directorio_controlados(self):
        self.inv.bitacora.ruta.mkdir()
        with self.assertRaises(self.m.BitacoraError):
            self.inv.bitacora.registrar('TEST', 'detalle')
        with self.assertRaises(self.m.BitacoraError):
            self.inv.bitacora.leer_ultimos()

    def test_23_saltos_de_linea_no_falsean_registros(self):
        with self.assertRaises(self.m.ProductoNoEncontradoError):
            self.inv.reponer('NO\nREPOSICION', 5)
        self.assertEqual(len(self.inv.bitacora.ruta.read_text(encoding='utf-8').splitlines()), 1)
        self.assertEqual(self.inv.bitacora.leer_ultimos()[0]['evento'], 'ERROR_REPOSICION')

    def test_24_menu_reutiliza_opciones_y_anade_dos(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.m.mostrar_menu_v2()
        texto = out.getvalue()
        self.assertIn('1. Agregar producto', texto)
        self.assertIn('5. Guardar y salir', texto)
        self.assertIn('6. Reponer existencias', texto)
        self.assertIn('7. Consultar bitacora', texto)
        self.assertIn(AUTHOR, texto)

    def test_25_consola_flujo_completo_sin_dependencia_main(self):
        entrada = '1\nP001\nTeclado\n50000\n10\n4\nP001\n3\n6\nP001\n5\n7\n2\n5\n'
        run = self.cli(entrada)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('Total: $150,000', run.stdout)
        self.assertIn('Stock anterior: 7', run.stdout)
        self.assertIn('Stock nuevo: 12', run.stdout)
        self.assertIn('Stock: 12', run.stdout)
        self.assertEqual(run.stdout.count('Datos cargados correctamente.'), 1)
        self.assertEqual(run.stdout.count('Datos guardados.'), 1)
        self.assertEqual(json.loads(Path('inventario.json').read_text(encoding='utf-8'))[0]['cantidad'], 12)

    def test_26_consola_errores_y_continuidad(self):
        self.inv.guardar()
        entrada = '6\nP001\n0\n6\nP001\n-2\n6\nP001\n2.5\n6\nNO_EXISTE\n5\n6\nP001\n5\n7\n5\n'
        run = self.cli(entrada)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.count('Error:'), 4)
        self.assertIn('Stock nuevo: 12', run.stdout)
        registros = self.inv.bitacora.leer_ultimos()
        self.assertEqual([r['evento'] for r in registros], ['ERROR_REPOSICION'] * 4 + ['REPOSICION', 'GUARDADO'])

    def test_27_consola_reinicio_recupera_stock_e_historial(self):
        self.inv.guardar()
        primera = self.cli('6\nP001\n5\n5\n')
        self.assertEqual(primera.returncode, 0, primera.stderr)
        segunda = self.cli('2\n7\n5\n')
        self.assertEqual(segunda.returncode, 0, segunda.stderr)
        self.assertIn('Stock: 12', segunda.stdout)
        self.assertIn('stock_nuevo=12', segunda.stdout)
        self.assertEqual(len(self.inv.bitacora.leer_ultimos()), 3)

    def test_28_consola_bitacora_no_escribible(self):
        self.inv.guardar()
        self.inv.bitacora.ruta.mkdir()
        run = self.cli('6\nP001\n5\n2\n5\n')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('No se pudo escribir la bitacora', run.stdout)
        self.assertIn('Stock: 7', run.stdout)
        self.assertIn('el inventario se guardo', run.stdout)
        self.assertEqual(json.loads(Path('inventario.json').read_text(encoding='utf-8'))[0]['cantidad'], 7)

    def test_29_consola_historial_corrupto_no_interrumpe_menu(self):
        self.inv.bitacora.ruta.write_text('{incorrecto\n', encoding='utf-8')
        run = self.cli('7\n2\n5\n')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('registro ilegible', run.stdout)
        self.assertIn('El inventario esta vacio.', run.stdout)
        self.assertTrue(self.inv.bitacora.ruta.read_text(encoding='utf-8').startswith('{incorrecto\n'))

    def test_30_fallo_guardado_original_no_se_oculta(self):
        Path('inventario.json').mkdir()
        with self.assertRaises(self.m.InventarioError):
            self.m.guardar_v2(self.inv)
        self.assertFalse(self.inv.bitacora.ruta.exists())

    def test_31_fallo_log_tras_guardar_no_pierde_datos(self):
        self.inv.bitacora.ruta.mkdir()
        texto = io.StringIO()
        with contextlib.redirect_stdout(texto):
            self.m.guardar_v2(self.inv)
        self.assertTrue(Path('inventario.json').exists())
        self.assertIn('el inventario se guardo', texto.getvalue())

    def test_32_objetos_no_afectados(self):
        self.inv.agregar(self.m.Producto('P002', 'Mouse', 25000, 20))
        self.inv.reponer('P001', 5)
        self.assertEqual(self.inv.buscar('P002').cantidad, 20)
        self.assertEqual(self.inv.buscar('P001').precio, 50000)
        self.assertEqual(self.inv.buscar('P001').nombre, 'Teclado')


if __name__ == '__main__':
    unittest.main(verbosity=2)
