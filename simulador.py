# =============================================================================
# SIMULADOR INTERACTIVO
# Parser de Expresiones Matemáticas Educativas
# =============================================================================
#
# Punto de entrada principal del proyecto.
# Integra todos los módulos en una interfaz de línea de comandos
# para que estudiantes puedan analizar expresiones matemáticas y
# entender por qué son válidas o inválidas.
#
# Uso:
#   python3 simulador.py
#
# Módulos utilizados:
#   src/afd_lexico.py       — Análisis léxico (AFD)
#   src/afn_equivalencias.py — AFN + conversión + minimización
#   src/ap_sintactico.py    — Análisis sintáctico (AP + BNF)
#   src/mt_verificador.py   — Verificación de paréntesis (MT)
#   src/parser.py           — Parser integrado (pipeline completo)
# =============================================================================

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.afd_lexico       import AFD_Lexico
from src.afn_equivalencias import AFN_Numeros, convertir_afn_a_afd, minimizar_afd, mostrar_construccion, mostrar_minimizacion
from src.ap_sintactico    import AP_Parentesis, AP_Sintactico
from src.mt_verificador   import MT_Parentesis
from src.parser           import ParserMatematico


# =============================================================================
# CONSTANTES DE PRESENTACIÓN
# =============================================================================

ANCHO    = 66
SEP      = "=" * ANCHO
SEP_FINO = "-" * ANCHO
TITULO   = "PARSER DE EXPRESIONES MATEMÁTICAS EDUCATIVAS"
VERSION  = "Basado en AFD · AP · Gramática BNF · Máquina de Turing"


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def limpiar():
    """Limpia la pantalla según el sistema operativo."""
    os.system('cls' if os.name == 'nt' else 'clear')

def pausar():
    """Pausa la ejecución hasta que el usuario presione Enter."""
    input("\n  Presiona Enter para continuar...")

def encabezado():
    """Imprime el encabezado del simulador."""
    print(f"\n{SEP}")
    print(f"  {TITULO}")
    print(f"  {VERSION}")
    print(SEP)

def subencabezado(titulo):
    """Imprime un subencabezado de sección."""
    print(f"\n{SEP}")
    print(f"  {titulo}")
    print(SEP)


# =============================================================================
# OPCIONES DEL MENÚ
# =============================================================================

def menu_principal():
    """Muestra el menú principal y retorna la opción elegida."""
    encabezado()
    print("""
  ¿Qué deseas hacer?

  [1]  Analizar una expresión matemática
  [2]  Ver tabla de transiciones del AFD (Análisis Léxico)
  [3]  Ver AFN, conversión AFN→AFD y minimización
  [4]  Ver simulación del Autómata de Pila (paréntesis)
  [5]  Ver simulación de la Máquina de Turing
  [6]  Ejecutar las 20 pruebas del sistema
  [7]  Ver la gramática BNF del lenguaje
  [8]  Ayuda — ¿Cómo funciona este simulador?
  [0]  Salir
""")
    return input("  Elige una opción: ").strip()


# =============================================================================
# OPCIÓN 1 — ANALIZAR EXPRESIÓN
# =============================================================================

def analizar_expresion():
    subencabezado("OPCIÓN 1 — Análisis de Expresión Matemática")

    print("""
  Escribe una expresión matemática para analizarla.
  Ejemplos válidos   : (3 + 5) * 2   |   3.14 * 2.71   |   -(4 + 1)
  Ejemplos inválidos : 3 ++ 4         |   (3 + 4        |   * 3
""")

    expresion = input("  Expresión: ").strip()
    if not expresion:
        print("\n  No escribiste ninguna expresión.")
        pausar()
        return

    parser   = ParserMatematico()
    resultado = parser.analizar(expresion)

    # Mostrar resultado completo
    parser.mostrar(resultado)

    if not resultado.valida:
        pausar()
        return

    # Si es válida, ofrecer opciones de detalle
    print("\n  La expresión es válida. ¿Quieres ver detalles adicionales?")
    print("  [a] Simulación del Autómata de Pila")
    print("  [b] Simulación de la Máquina de Turing")
    print("  [c] Ambos")
    print("  [n] No, volver al menú")

    opcion = input("\n  Elige: ").strip().lower()

    if opcion in ('a', 'c'):
        subencabezado("DETALLE — Autómata de Pila")
        afd    = AFD_Lexico()
        tokens, _ = afd.tokenizar(expresion)
        ap_p   = AP_Parentesis()
        ap_p.mostrar_proceso(tokens)

    if opcion in ('b', 'c'):
        subencabezado("DETALLE — Máquina de Turing")
        mt     = MT_Parentesis()
        (_, _, _), parens = mt.verificar_expresion(expresion)
        if parens:
            mt.mostrar_proceso(parens)
        else:
            print("\n  La expresión no contiene paréntesis.")
            print("  La MT acepta trivialmente (no hay nada que verificar).")

    pausar()


# =============================================================================
# OPCIÓN 2 — TABLA AFD
# =============================================================================

def ver_tabla_afd():
    subencabezado("OPCIÓN 2 — Tabla de Transiciones del AFD Léxico")
    print("""
  El AFD (Autómata Finito Determinista) es la primera etapa del parser.
  Recorre la expresión carácter a carácter y clasifica cada pieza en
  un tipo de token: NUM, OP, LPAREN o RPAREN.

  La tabla muestra para cada estado y símbolo, a qué estado se va.
  Los estados marcados (*) son de aceptación: el token está completo.
""")
    afd = AFD_Lexico()
    afd.mostrar_tabla_transiciones()
    pausar()


# =============================================================================
# OPCIÓN 3 — AFN + CONVERSIÓN + MINIMIZACIÓN
# =============================================================================

def ver_afn_equivalencias():
    subencabezado("OPCIÓN 3 — AFN, Conversión AFN→AFD y Minimización")
    print("""
  Esta sección demuestra la equivalencia entre autómatas:
    · El AFN tiene no-determinismo: desde un estado puede ir a varios a la vez.
    · La Construcción de Subconjuntos convierte el AFN en un AFD equivalente.
    · La Minimización reduce el AFD al menor número de estados posible.
""")
    afn = AFN_Numeros()
    afn.mostrar_tabla()

    trans_afd, q0_afd, aceptacion, nombres, pasos = convertir_afn_a_afd(afn)
    mostrar_construccion(afn, trans_afd, q0_afd, aceptacion, nombres, pasos)

    particion_final, historial = minimizar_afd(
        trans_afd, q0_afd, aceptacion, afn.alfabeto
    )
    mostrar_minimizacion(particion_final, historial, nombres, aceptacion)
    pausar()


# =============================================================================
# OPCIÓN 4 — SIMULACIÓN AP
# =============================================================================

def ver_simulacion_ap():
    subencabezado("OPCIÓN 4 — Simulación del Autómata de Pila")
    print("""
  El AP (Autómata de Pila) verifica que los paréntesis estén balanceados.
  Usa una pila como memoria adicional:
    · Al ver '(' → apila un símbolo A
    · Al ver ')' → desapila un símbolo A
    · Al terminar → acepta solo si la pila queda vacía (solo el fondo '$')

  Escribe una expresión para ver la pila en cada paso.
""")

    expresion = input("  Expresión (Enter para usar el ejemplo): ").strip()
    if not expresion:
        expresion = "((2 + 3) * 4) - 1"
        print(f"  Usando: '{expresion}'")

    afd    = AFD_Lexico()
    tokens, _ = afd.tokenizar(expresion)

    if not tokens:
        print("\n  No se encontraron tokens en la expresión.")
        pausar()
        return

    ap = AP_Parentesis()
    ap.mostrar_proceso(tokens)
    pausar()


# =============================================================================
# OPCIÓN 5 — SIMULACIÓN MT
# =============================================================================

def ver_simulacion_mt():
    subencabezado("OPCIÓN 5 — Simulación de la Máquina de Turing")
    print("""
  La MT verifica paréntesis marcando pares en la cinta:
    · Escanea derecha buscando ')' → lo marca con X
    · Retrocede buscando el '(' más cercano → lo marca con X
    · Repite hasta que no queden paréntesis sin marcar
    · Si al verificar no queda ningún '(' sin marcar → ACEPTA

  La cinta muestra: >x< = posición actual del cabezal

  Escribe una cadena de paréntesis (o una expresión completa).
""")

    entrada = input("  Entrada (Enter para usar el ejemplo): ").strip()
    if not entrada:
        entrada = "(())"
        print(f"  Usando: '{entrada}'")

    mt = MT_Parentesis()

    # Detectar si es una expresión completa o solo paréntesis
    solo_parens = all(c in '()' for c in entrada)

    if solo_parens:
        mt.mostrar_proceso(entrada)
    else:
        print(f"\n  Extrayendo paréntesis de la expresión...")
        (acepta, pasos, mensaje), parens = mt.verificar_expresion(entrada)
        print(f"  Paréntesis extraídos: '{parens}'")
        if parens:
            mt.mostrar_proceso(parens)
        else:
            print(f"  La expresión no contiene paréntesis — MT acepta trivialmente.")

    pausar()


# =============================================================================
# OPCIÓN 6 — PRUEBAS DEL SISTEMA
# =============================================================================

def ejecutar_pruebas():
    subencabezado("OPCIÓN 6 — Suite de 20 Pruebas del Sistema")
    print("""
  Se ejecutan 20 expresiones de prueba (10 válidas y 10 inválidas)
  para verificar que el parser funciona correctamente en todos los casos.
""")

    parser = ParserMatematico()

    casos = [
        ("3 + 4",               True,  "suma simple"),
        ("(3 + 5) * 2",         True,  "paréntesis y multiplicación"),
        ("3.14 * 2.71",         True,  "decimales"),
        ("((2 + 3) * 4) - 1",   True,  "paréntesis anidados"),
        ("-3 + 4",              True,  "menos unario"),
        ("-(3 + 4)",            True,  "menos unario con paréntesis"),
        ("10 / 2 + 5",          True,  "división y suma"),
        ("(((3)))",             True,  "triple anidamiento"),
        ("0.5 + 0.5",           True,  "decimales menores a 1"),
        ("100",                 True,  "número solo"),
        ("3 ++ 4",              False, "operadores consecutivos"),
        ("(3 + 4",              False, "paréntesis sin cerrar"),
        ("3 + 4)",              False, "paréntesis sin abrir"),
        ("* 3 + 4",             False, "inicia con operador binario"),
        ("3 + 4 *",             False, "termina con operador"),
        ("()",                  False, "paréntesis vacíos"),
        ("3 4 + 1",             False, "dos operandos sin operador"),
        ("(3 + (4 * 2)",        False, "paréntesis interno sin cerrar"),
        ("/3",                  False, "inicia con división"),
        ("3 @ 4",               False, "símbolo inválido"),
    ]

    print(f"  {'#':<4} {'Expresión':<26} {'Esperado':<10} {'Parser':<10} {'OK':<4} Descripción")
    print("  " + SEP_FINO)

    total_ok = 0
    for i, (expr, esperado, desc) in enumerate(casos, 1):
        resultado = parser.analizar(expr)
        ok        = "✓" if resultado.valida == esperado else "✗"
        if resultado.valida == esperado:
            total_ok += 1
        esp_str = "Válida  " if esperado else "Inválida"
        res_str = "Válida  " if resultado.valida else "Inválida"
        print(f"  {i:<4} {repr(expr):<26} {esp_str:<10} {res_str:<10} {ok:<4} {desc}")

    print("  " + SEP_FINO)
    porcentaje = (total_ok / len(casos)) * 100
    print(f"  Resultado: {total_ok}/{len(casos)} correctos ({porcentaje:.0f}%)")

    if total_ok == len(casos):
        print(f"\n  Todos los casos pasaron correctamente.")
    else:
        print(f"\n  {len(casos) - total_ok} caso(s) fallaron. Revisa los módulos.")

    pausar()


# =============================================================================
# OPCIÓN 7 — GRAMÁTICA BNF
# =============================================================================

def ver_gramatica_bnf():
    subencabezado("OPCIÓN 7 — Gramática BNF del Lenguaje")
    print("""
  La gramática BNF (Backus-Naur Form) define las reglas que determinan
  si una expresión matemática está correctamente escrita.

  Cada regla dice: "esto puede ser reemplazado por aquello".
  Las reglas más generales usan las más específicas, formando una jerarquía
  que también define la PRECEDENCIA de operadores (los de mayor precedencia
  están en las reglas más internas).

  ──────────────────────────────────────────────────────────
  GRAMÁTICA BNF — Expresiones Matemáticas Educativas
  ──────────────────────────────────────────────────────────

  <expresion> ::= <termino>
                | <expresion> '+' <termino>
                | <expresion> '-' <termino>

  <termino>   ::= <factor>
                | <termino>  '*' <factor>
                | <termino>  '/' <factor>

  <factor>    ::= NUM
                | '(' <expresion> ')'
                | '-' <factor>

  Donde NUM es: [0-9]+ ( '.' [0-9]+ )?
  Ejemplos de NUM: 3   42   0.5   3.14   100

  ──────────────────────────────────────────────────────────
  PRECEDENCIA DE OPERADORES (de menor a mayor):
    + y -  →  menor precedencia  (regla <expresion>)
    * y /  →  mayor precedencia  (regla <termino>)
    - unario → mayor aún         (regla <factor>)
  ──────────────────────────────────────────────────────────

  EJEMPLOS DE DERIVACIÓN:

    3 + 4 * 2
      = <expresion>
      = <expresion> '+' <termino>
      = <termino>   '+' <termino> '*' <factor>
      = <factor>    '+' <factor>  '*' NUM(2)
      = NUM(3)      '+'  NUM(4)   '*' NUM(2)
      Resultado: 3 + (4*2) = 11   (no 14, por precedencia)
""")
    pausar()


# =============================================================================
# OPCIÓN 8 — AYUDA
# =============================================================================

def ver_ayuda():
    subencabezado("OPCIÓN 8 — Ayuda")
    print("""
  ¿QUÉ ES ESTE SIMULADOR?
  ────────────────────────
  Es una herramienta educativa que analiza expresiones matemáticas
  usando los mismos principios que usan los compiladores de programación.

  ¿QUÉ ES UNA EXPRESIÓN VÁLIDA?
  ──────────────────────────────
  Una expresión válida puede contener:
    · Números enteros:   3   42   100
    · Números decimales: 3.14   0.5
    · Operadores:        +   -   *   /
    · Paréntesis:        (   )
    · Menos unario:      -3   -(3+4)

  Ejemplos válidos:
    3 + 4             → suma simple
    (3 + 5) * 2       → paréntesis cambian el orden
    3.14 * 2.71       → decimales
    -(3 + 4)          → negación de una expresión
    ((2 + 3) * 4) - 1 → paréntesis anidados

  ¿CÓMO LEER EL RESULTADO?
  ──────────────────────────
  El análisis tiene tres fases:

  FASE 1 [AFD] — ¿Están bien escritas las piezas?
    Si hay [✓]: los tokens son válidos (números, operadores, paréntesis)
    Si hay [✗]: hay algún símbolo que no pertenece al lenguaje

  FASE 2 [AP + BNF] — ¿Está bien organizada la estructura?
    Si hay [✓]: la expresión sigue la gramática BNF correctamente
    Si hay [✗]: hay un error de orden (operadores mal ubicados, etc.)

  FASE 3 [MT] — ¿Los paréntesis están balanceados?
    Si hay [✓]: cada '(' tiene su ')' correspondiente
    Si hay [✗]: hay paréntesis sin emparejar

  ERRORES COMUNES Y CÓMO CORREGIRLOS:
  ─────────────────────────────────────
    3 ++ 4     → Dos operadores seguidos. Escribe: 3 + 4
    (3 + 4     → Falta cerrar. Escribe: (3 + 4)
    3 + 4)     → Falta abrir. Escribe: (3 + 4)
    * 3        → Operador al inicio. Escribe: 3 * (algo)
    3 + 4 *    → Operador al final. Escribe: 3 + 4 * 2
    ()         → Paréntesis vacíos. Escribe: (3 + 4)
    3 @ 4      → '@' no existe. Usa solo: + - * /
""")
    pausar()


# =============================================================================
# BUCLE PRINCIPAL DEL SIMULADOR
# =============================================================================

def main():
    opciones = {
        '1': analizar_expresion,
        '2': ver_tabla_afd,
        '3': ver_afn_equivalencias,
        '4': ver_simulacion_ap,
        '5': ver_simulacion_mt,
        '6': ejecutar_pruebas,
        '7': ver_gramatica_bnf,
        '8': ver_ayuda,
    }

    while True:
        limpiar()
        opcion = menu_principal()

        if opcion == '0':
            limpiar()
            print(f"\n{SEP}")
            print(f"  Gracias por usar el simulador.")
            print(f"  TCC — Teoría de Autómatas")
            print(f"{SEP}\n")
            break

        if opcion in opciones:
            limpiar()
            opciones[opcion]()
        else:
            print("\n  Opción no válida. Elige entre 0 y 8.")
            pausar()


if __name__ == '__main__':
    main()
