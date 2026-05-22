# =============================================================================
# PASO 7 — PRUEBAS Y SIMULACIÓN
# Suite completa de 30 casos de prueba con tabla de resultados
# =============================================================================
#
# ¿QUÉ HACE ESTE MÓDULO?
#   Ejecuta el parser integrado sobre 30 expresiones de prueba
#   (válidas e inválidas) organizadas por categoría de error,
#   mostrando tablas de resultados, estadísticas y análisis detallados.
#
# CATEGORÍAS DE PRUEBA:
#   A — Expresiones válidas              (13 casos)
#   B — Errores léxicos                 ( 5 casos)
#   C — Errores sintácticos: operadores ( 5 casos)
#   D — Errores sintácticos: paréntesis ( 5 casos)
#   E — Casos borde                     ( 2 casos)
#
# TOTAL: 30 casos de prueba
# =============================================================================

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.parser          import ParserMatematico
from src.afd_lexico      import AFD_Lexico
from src.ap_sintactico   import AP_Parentesis
from src.mt_verificador  import MT_Parentesis


# =============================================================================
# DEFINICIÓN DE CASOS DE PRUEBA
# =============================================================================

CASOS = [
    # ── Categoría A: Expresiones válidas ────────────────────────────────────
    ('A', '3 + 4',               True,  "suma simple de dos enteros"),
    ('A', '(3 + 5) * 2',         True,  "paréntesis con multiplicación"),
    ('A', '3.14 * 2.71',         True,  "producto de dos decimales"),
    ('A', '((2 + 3) * 4) - 1',   True,  "paréntesis anidados de dos niveles"),
    ('A', '-3 + 4',              True,  "menos unario sobre entero"),
    ('A', '-(3 + 4)',            True,  "menos unario sobre expresión"),
    ('A', '10 / 2 + 5',          True,  "división y suma con precedencia"),
    ('A', '(((3)))',             True,  "número con triple anidamiento"),
    ('A', '0.5 + 0.5',           True,  "decimales menores a 1"),
    ('A', '100',                 True,  "número entero solo"),
    ('A', '1 + 2 + 3 + 4',       True,  "cadena de cuatro sumas"),
    ('A', '(1 + 2) * (3 + 4)',   True,  "producto de dos subexpresiones"),
    ('A', '-(-3)',               True,  "doble negación unaria"),

    # ── Categoría B: Errores léxicos ────────────────────────────────────────
    ('B', '3 @ 4',               False, "símbolo '@' fuera del alfabeto"),
    ('B', '3.',                  False, "decimal incompleto — punto sin dígitos"),
    ('B', '5 $ 2',               False, "símbolo '$' fuera del alfabeto"),
    ('B', '2.  + 1',             False, "decimal incompleto seguido de operador"),
    ('B', '3 + 4x',              False, "letra 'x' pegada a un número"),

    # ── Categoría C: Errores sintácticos — operadores ───────────────────────
    ('C', '3 ++ 4',              False, "dos operadores '+' consecutivos"),
    ('C', '3 + * 4',             False, "operadores '+' y '*' consecutivos"),
    ('C', '* 3 + 4',             False, "expresión inicia con operador binario '*'"),
    ('C', '/3',                  False, "expresión inicia con operador binario '/'"),
    ('C', '3 + 4 *',             False, "expresión termina con operador '*'"),

    # ── Categoría D: Errores sintácticos — paréntesis ───────────────────────
    ('D', '(3 + 4',              False, "paréntesis '(' sin cerrar"),
    ('D', '3 + 4)',              False, "paréntesis ')' sin abrir"),
    ('D', '()',                  False, "paréntesis vacíos sin expresión interna"),
    ('D', '(3 + (4 * 2)',        False, "paréntesis interno sin cerrar"),
    ('D', '((3 + 4) * (2 - 1)', False, "paréntesis externo sin cerrar"),

    # ── Categoría E: Casos borde ─────────────────────────────────────────────
    ('E', '',                    False, "expresión vacía"),
    ('E', '+',                   False, "solo un operador binario"),
]


# =============================================================================
# FUNCIONES DE PRESENTACIÓN
# =============================================================================

ANCHO   = 74
SEP     = "=" * ANCHO
SEP_FIN = "-" * ANCHO

NOMBRES_CATEGORIA = {
    'A': "Expresiones válidas",
    'B': "Errores léxicos",
    'C': "Errores — operadores",
    'D': "Errores — paréntesis",
    'E': "Casos borde",
}


def _primer_error(resultado):
    """Extrae el primer mensaje de error (truncado) de un resultado."""
    if resultado.errores:
        msg = resultado.errores[0].get('mensaje', '')
        return msg[:48] + '…' if len(msg) > 48 else msg
    return ''


def ejecutar_suite(parser, mostrar_detalle=False):
    """
    Ejecuta todos los casos de prueba y retorna (resultados, estadísticas).
    """
    resultados   = []
    por_categoria = {cat: {'total': 0, 'ok': 0} for cat in NOMBRES_CATEGORIA}

    for cat, expr, esperado, desc in CASOS:
        t_inicio  = time.perf_counter()
        resultado = parser.analizar(expr)
        t_fin     = time.perf_counter()

        ok        = resultado.valida == esperado
        primer_err = _primer_error(resultado) if not resultado.valida else ''

        resultados.append({
            'cat':        cat,
            'expr':       expr,
            'esperado':   esperado,
            'obtenido':   resultado.valida,
            'ok':         ok,
            'desc':       desc,
            'error_msg':  primer_err,
            'tiempo_ms':  (t_fin - t_inicio) * 1000,
            'resultado':  resultado,
        })

        por_categoria[cat]['total'] += 1
        if ok:
            por_categoria[cat]['ok'] += 1

    return resultados, por_categoria


def imprimir_tabla_completa(resultados):
    """Imprime la tabla de todos los casos con sus resultados."""
    print(f"\n{SEP}")
    print(f"  TABLA DE RESULTADOS — {len(resultados)} Casos de Prueba")
    print(SEP)
    print(f"  {'#':<4} {'Cat':<5} {'Expresión':<28} {'Esper.':<9} "
          f"{'Parser':<9} {'OK':<4} {'Primer error detectado'}")
    print(f"  {SEP_FIN}")

    cat_actual = None
    for i, r in enumerate(resultados, 1):
        # Separador visual por categoría
        if r['cat'] != cat_actual:
            cat_actual = r['cat']
            nombre = NOMBRES_CATEGORIA[cat_actual]
            print(f"\n  ── {nombre} {'─' * (ANCHO - len(nombre) - 7)}")

        esp_str = "Válida  " if r['esperado'] else "Inválida"
        obt_str = "Válida  " if r['obtenido'] else "Inválida"
        ok_str  = "✓" if r['ok'] else "✗"
        expr_r  = repr(r['expr']) if r['expr'] else "''"

        print(f"  {i:<4} [{r['cat']}]  {expr_r:<28} {esp_str:<9} "
              f"{obt_str:<9} {ok_str:<4} {r['error_msg']}")

    print(f"\n  {SEP_FIN}")


def imprimir_estadisticas(resultados, por_categoria):
    """Imprime el resumen estadístico por categoría y global."""
    total_ok    = sum(1 for r in resultados if r['ok'])
    total_casos = len(resultados)
    tiempo_total = sum(r['tiempo_ms'] for r in resultados)

    print(f"\n{SEP}")
    print(f"  ESTADÍSTICAS POR CATEGORÍA")
    print(SEP)
    print(f"  {'Categoría':<30} {'Casos':<8} {'Correctos':<12} {'%'}")
    print(f"  {SEP_FIN}")

    for cat, nombre in NOMBRES_CATEGORIA.items():
        datos = por_categoria[cat]
        pct   = (datos['ok'] / datos['total'] * 100) if datos['total'] else 0
        barra = '█' * int(pct / 10) + '░' * (10 - int(pct / 10))
        print(f"  {nombre:<30} {datos['total']:<8} {datos['ok']:<12} "
              f"{pct:>5.1f}%  {barra}")

    print(f"  {SEP_FIN}")
    pct_global = total_ok / total_casos * 100
    print(f"  {'TOTAL':<30} {total_casos:<8} {total_ok:<12} {pct_global:>5.1f}%")
    print(f"\n  Tiempo total de ejecución : {tiempo_total:.1f} ms")
    print(f"  Tiempo promedio por caso  : {tiempo_total / total_casos:.2f} ms")

    if total_ok == total_casos:
        print(f"\n  TODOS LOS CASOS PASARON CORRECTAMENTE.")
    else:
        fallidos = [r for r in resultados if not r['ok']]
        print(f"\n  {len(fallidos)} caso(s) fallaron:")
        for r in fallidos:
            print(f"    · {repr(r['expr'])} (cat {r['cat']})")

    print(SEP)


def imprimir_analisis_por_categoria(resultados, parser):
    """
    Para cada categoría, muestra el análisis detallado de un caso
    representativo (el primero de cada grupo).
    """
    print(f"\n{SEP}")
    print(f"  ANÁLISIS DETALLADO — Un caso representativo por categoría")
    print(SEP)

    representativos = {}
    for r in resultados:
        if r['cat'] not in representativos:
            representativos[r['cat']] = r

    for cat in sorted(representativos):
        r      = representativos[cat]
        nombre = NOMBRES_CATEGORIA[cat]
        expr   = r['expr'] if r['expr'] else '(vacía)'

        print(f"\n  {'─'*4} Categoría {cat}: {nombre} {'─'*(ANCHO - len(nombre) - 15)}")
        print(f"  Expresión elegida: '{expr}'")
        print(f"  Descripción: {r['desc']}")
        parser.mostrar(r['resultado'], verbose=True)


def imprimir_tabla_transiciones_resumen():
    """Muestra las tablas de transición de todos los autómatas."""
    print(f"\n{SEP}")
    print(f"  TABLAS DE TRANSICIÓN — Resumen de todos los autómatas")
    print(SEP)

    print("\n  ── AFD Léxico (Paso 1)")
    afd = AFD_Lexico()
    afd.mostrar_tabla_transiciones()

    print("\n  ── Máquina de Turing (Paso 4)")
    mt = MT_Parentesis()
    mt.mostrar_tabla_transiciones()


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == '__main__':
    parser = ParserMatematico()

    print(f"\n{SEP}")
    print(f"  SUITE DE PRUEBAS — Parser de Expresiones Matemáticas Educativas")
    print(f"  TCC — Teoría de Autómatas")
    print(SEP)
    print(f"\n  Ejecutando {len(CASOS)} casos de prueba...")

    # Ejecutar todos los casos
    resultados, por_categoria = ejecutar_suite(parser)

    # Imprimir tabla completa
    imprimir_tabla_completa(resultados)

    # Imprimir estadísticas
    imprimir_estadisticas(resultados, por_categoria)

    # Análisis detallado por categoría
    imprimir_analisis_por_categoria(resultados, parser)

    # Tablas de transición
    imprimir_tabla_transiciones_resumen()

    print(f"\n{SEP}")
    print(f"  Fin de la suite de pruebas.")
    print(f"  Archivos del proyecto:")
    print(f"    simulador.py             — Simulador interactivo (ejecutar primero)")
    print(f"    src/afd_lexico.py        — Paso 1: AFD Léxico")
    print(f"    src/afn_equivalencias.py — Paso 2: AFN + conversión + minimización")
    print(f"    src/ap_sintactico.py     — Paso 3: Autómata de Pila + BNF")
    print(f"    src/mt_verificador.py    — Paso 4: Máquina de Turing")
    print(f"    src/parser.py            — Paso 5: Parser integrado")
    print(f"    simulador.py             — Paso 6: Simulador interactivo")
    print(f"    pruebas.py               — Paso 7: Suite de pruebas (este archivo)")
    print(SEP)
