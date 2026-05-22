# =============================================================================
# PASO 5 — PARSER INTEGRADO
# Parser completo de expresiones matemáticas educativas
# =============================================================================
#
# ¿QUÉ HACE ESTE MÓDULO?
#   Integra los tres autómatas en un pipeline de análisis de tres fases:
#
#   FASE 1 — Análisis Léxico (AFD)
#     Tokeniza la expresión: divide el texto en piezas con tipo y valor.
#     Detecta símbolos inválidos y números mal escritos.
#
#   FASE 2 — Análisis Sintáctico (AP + Gramática BNF)
#     Verifica que los tokens estén en el orden correcto según las reglas
#     de la gramática BNF. Detecta errores estructurales.
#
#   FASE 3 — Verificación de Paréntesis (Máquina de Turing)
#     Confirma el balance de paréntesis reescribiendo la cinta.
#     Actúa como segunda verificación independiente del AP.
#
# FLUJO DE ANÁLISIS:
#   expresion → [AFD] → tokens → [AP/BNF] → estructura → [MT] → balance
#       ↓           ↓                ↓                      ↓
#   texto          piezas          orden               equilibrio
#
# ERRORES DETECTADOS Y SUS EXPLICACIONES EDUCATIVAS:
#   - Símbolo fuera del alfabeto   (léxico)
#   - Número decimal incompleto    (léxico)
#   - Operadores consecutivos      (sintáctico)
#   - Paréntesis sin cerrar        (sintáctico / MT)
#   - Paréntesis sin abrir         (sintáctico / MT)
#   - Paréntesis vacíos            (sintáctico)
#   - Inicia con operador binario  (sintáctico)
#   - Termina con operador         (sintáctico)
#   - Dos operandos sin operador   (sintáctico)
# =============================================================================

import sys
import os

_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _raiz not in sys.path:
    sys.path.insert(0, _raiz)

from src.afd_lexico    import AFD_Lexico
from src.ap_sintactico import AP_Sintactico
from src.mt_verificador import MT_Parentesis


# =============================================================================
# CLASE RESULTADO — estructura de datos del análisis
# =============================================================================

class ResultadoAnalisis:
    """
    Contiene el resultado completo del análisis de una expresión matemática.

    Atributos:
        expresion    — la expresión original analizada
        valida       — True si pasó las tres fases sin errores
        tokens       — lista de tokens producidos por el AFD
        fases        — dict con el resultado de cada fase
        errores      — lista de errores enriquecidos con explicación educativa
        sugerencia   — consejo general para corregir la expresión
    """

    def __init__(self, expresion):
        self.expresion  = expresion
        self.valida     = False
        self.tokens     = []
        self.fases      = {
            'lexica':     {'ok': False, 'errores': [], 'detalle': ''},
            'sintactica': {'ok': False, 'errores': [], 'detalle': '', 'pasos': []},
            'mt':         {'ok': False, 'errores': [], 'detalle': '', 'parens': ''},
        }
        self.errores   = []
        self.sugerencia = ''


# =============================================================================
# MENSAJES EDUCATIVOS — contexto explicativo para cada tipo de error
# =============================================================================

# Cada entrada: (fragmento_a_buscar_en_mensaje, explicacion, sugerencia)
_CONTEXTO_ERRORES = [
    (
        "no reconocido",
        "¿Qué pasó? El carácter marcado no forma parte del lenguaje de expresiones "
        "matemáticas. El AFD no tiene ninguna transición definida para ese símbolo.",
        "Usa únicamente: dígitos del 0 al 9, los operadores + - * /, y los paréntesis ( )."
    ),
    (
        "decimal incompleto",
        "¿Qué pasó? Un número decimal debe tener al menos un dígito después del punto. "
        "El AFD llega al estado q2 (punto visto) pero necesita llegar a q3 (dígito decimal) "
        "para aceptar.",
        "Escribe al menos un dígito después del punto. Ejemplo: 3.0 o 3.14, no '3.'"
    ),
    (
        "no puede usarse aquí",
        "¿Qué pasó? El analizador sintáctico estaba aplicando la regla <factor> "
        "(que espera un número, un '(' o un '-' unario) y encontró un operador inesperado.",
        "Verifica que entre dos operadores siempre haya un número o una expresión entre paréntesis."
    ),
    (
        "no puede iniciar",
        "¿Qué pasó? Los operadores * y / son 'binarios': necesitan un valor a su izquierda "
        "y otro a su derecha. Al estar al inicio, no tienen nada a su izquierda.",
        "Mueve el operador entre dos operandos. Si necesitas negación usa el '-' unario: -3 * 4."
    ),
    (
        "incompleta: se esperaba",
        "¿Qué pasó? La expresión terminó en un punto donde la gramática BNF exige continuar. "
        "Posiblemente falta el operando después del último operador.",
        "Asegúrate de que cada operador tenga un número o expresión a su derecha."
    ),
    (
        "sin apertura",
        "¿Qué pasó? El autómata de pila intentó desapilar un '(' para emparejar con ')', "
        "pero la pila solo tenía el marcador de fondo '$'. No había paréntesis abierto.",
        "Revisa que cada ')' tenga su '(' correspondiente antes."
    ),
    (
        "sin cerrar",
        "¿Qué pasó? Al terminar de analizar la expresión, la pila del AP aún tenía "
        "paréntesis apilados sin desapilar, lo que significa que nunca se cerraron.",
        "Agrega ')' al final para cada '(' que hayas abierto."
    ),
    (
        "vacíos",
        "¿Qué pasó? La regla <factor> de la gramática BNF esperaba una expresión dentro "
        "de los paréntesis, pero encontró ')' inmediatamente después de '('.",
        "Escribe algo entre los paréntesis. Ejemplo: (3 + 4) en vez de ()."
    ),
    (
        "¿Falta un operador",
        "¿Qué pasó? Después de reconocer un token completo (número o expresión), "
        "el parser encontró otro operando en lugar de un operador. Hay dos números seguidos.",
        "Coloca un operador (+, -, *, /) entre los dos operandos."
    ),
    (
        "terminó inesperadamente",
        "¿Qué pasó? La gramática esperaba un token más (un número o ')') pero la "
        "expresión se acabó antes de completar la estructura.",
        "Revisa que la expresión no quede cortada a la mitad."
    ),
]


def _enriquecer_error(error_original):
    """
    Toma un error técnico y le agrega explicación educativa y sugerencia.
    Retorna un dict con: posicion, mensaje, explicacion, sugerencia.
    """
    mensaje = error_original.get('mensaje', '')

    for fragmento, explicacion, sugerencia in _CONTEXTO_ERRORES:
        if fragmento.lower() in mensaje.lower():
            return {
                'posicion':   error_original.get('posicion', '?'),
                'mensaje':    mensaje,
                'explicacion': explicacion,
                'sugerencia': sugerencia,
            }

    # Error sin contexto específico → mostrar tal cual
    return {
        'posicion':    error_original.get('posicion', '?'),
        'mensaje':     mensaje,
        'explicacion': '',
        'sugerencia':  '',
    }


# =============================================================================
# PARSER PRINCIPAL
# =============================================================================

class ParserMatematico:
    """
    Parser educativo que analiza una expresión matemática en tres fases.

    Uso básico:
        parser = ParserMatematico()
        resultado = parser.analizar("(3 + 5) * 2")
        parser.mostrar(resultado)
    """

    def analizar(self, expresion):
        """
        Ejecuta el pipeline completo de análisis sobre la expresión.

        Retorna un ResultadoAnalisis con toda la información del análisis.
        """
        resultado = ResultadoAnalisis(expresion)

        # ── FASE 1: Análisis Léxico (AFD) ────────────────────────────────
        afd    = AFD_Lexico()
        tokens, errores_lexicos = afd.tokenizar(expresion)

        resultado.tokens = tokens
        resultado.fases['lexica']['errores'] = errores_lexicos
        resultado.fases['lexica']['ok']      = len(errores_lexicos) == 0

        if tokens:
            seq = '  '.join(t['tipo'] for t in tokens)
            resultado.fases['lexica']['detalle'] = f"Tokens: {seq}"
        else:
            resultado.fases['lexica']['detalle'] = "No se encontraron tokens."

        # Si hay errores léxicos, reportarlos y continuar para detectar más
        for e in errores_lexicos:
            resultado.errores.append(_enriquecer_error(e))

        # ── FASE 2: Análisis Sintáctico (AP + BNF) ───────────────────────
        ap     = AP_Sintactico()
        valido_sint, _, errores_sint, pasos_sint = ap.validar(expresion)

        resultado.fases['sintactica']['ok']     = valido_sint
        resultado.fases['sintactica']['errores'] = errores_sint
        resultado.fases['sintactica']['pasos']  = pasos_sint

        if valido_sint:
            resultado.fases['sintactica']['detalle'] = "Estructura BNF correcta."
        else:
            resultado.fases['sintactica']['detalle'] = (
                f"{len(errores_sint)} error(es) estructural(es) detectado(s)."
            )

        for e in errores_sint:
            resultado.errores.append(_enriquecer_error(e))

        # ── FASE 3: Verificación de Paréntesis (Máquina de Turing) ───────
        mt = MT_Parentesis()
        (acepta_mt, _, mensaje_mt), parens = mt.verificar_expresion(expresion)

        resultado.fases['mt']['ok']     = acepta_mt
        resultado.fases['mt']['parens'] = parens if parens else "(ninguno)"
        resultado.fases['mt']['detalle'] = mensaje_mt

        if not acepta_mt and parens:
            # Solo registrar error de MT si el AP no lo detectó ya
            sint_ya_detecta_parens = any(
                'paréntesis' in e.get('mensaje', '').lower()
                for e in errores_sint
            )
            if not sint_ya_detecta_parens:
                resultado.errores.append(_enriquecer_error({
                    'posicion': '—',
                    'mensaje':  f"MT: {mensaje_mt}",
                }))

        # ── RESULTADO FINAL ───────────────────────────────────────────────
        resultado.valida = (
            resultado.fases['lexica']['ok']     and
            resultado.fases['sintactica']['ok'] and
            resultado.fases['mt']['ok']
        )

        # Eliminar errores duplicados (mismo mensaje y posición)
        vistos, unicos = set(), []
        for e in resultado.errores:
            clave = (e['posicion'], e['mensaje'])
            if clave not in vistos:
                vistos.add(clave)
                unicos.append(e)
        resultado.errores = unicos

        if not resultado.valida and resultado.errores:
            resultado.sugerencia = resultado.errores[0].get('sugerencia', '')

        return resultado

    # ------------------------------------------------------------------
    # VISUALIZACIÓN
    # ------------------------------------------------------------------

    def mostrar(self, resultado, verbose=True):
        """
        Muestra el resultado completo del análisis.

        verbose=True  → muestra explicaciones educativas detalladas
        verbose=False → muestra solo el veredicto y los errores
        """
        ancho = 66
        sep   = "=" * ancho

        print(f"\n{sep}")
        print("  PARSER DE EXPRESIONES MATEMÁTICAS EDUCATIVAS")
        print(f"  Expresión: '{resultado.expresion}'")
        print(sep)

        # Fase 1: Léxico
        f1  = resultado.fases['lexica']
        ico = "✓" if f1['ok'] else "✗"
        print(f"\n  FASE 1 — Análisis Léxico (AFD)         [{ico}]")
        print(f"  {f1['detalle']}")
        if not f1['ok']:
            for e in f1['errores']:
                print(f"  [Pos {e['posicion']:>2}] {e['mensaje']}")

        # Fase 2: Sintáctico
        f2  = resultado.fases['sintactica']
        ico = "✓" if f2['ok'] else "✗"
        print(f"\n  FASE 2 — Análisis Sintáctico (AP + BNF) [{ico}]")
        print(f"  {f2['detalle']}")
        if not f2['ok']:
            for e in f2['errores']:
                print(f"  [Pos {e['posicion']:>2}] {e['mensaje']}")

        # Fase 3: MT
        f3  = resultado.fases['mt']
        ico = "✓" if f3['ok'] else "✗"
        print(f"\n  FASE 3 — Verificación MT (Paréntesis)   [{ico}]")
        print(f"  Paréntesis extraídos: '{f3['parens']}'")
        print(f"  {f3['detalle']}")

        # Resultado final
        print(f"\n  {'-' * (ancho - 2)}")
        if resultado.valida:
            print(f"  RESULTADO: EXPRESIÓN VÁLIDA ✓")
            if verbose:
                print(f"  La expresión cumple con el léxico, la gramática BNF")
                print(f"  y el balance de paréntesis verificado por la MT.")
        else:
            print(f"  RESULTADO: EXPRESIÓN INVÁLIDA ✗")
            print(f"  {len(resultado.errores)} error(es) encontrado(s).")

            if verbose and resultado.errores:
                print(f"\n  DIAGNÓSTICO DETALLADO:")
                print("  " + "-" * (ancho - 2))
                for i, err in enumerate(resultado.errores, 1):
                    print(f"\n  Error {i}  [Pos {err['posicion']}]")
                    print(f"  Mensaje    : {err['mensaje']}")
                    if err.get('explicacion'):
                        print(f"  Explicación: {err['explicacion']}")
                    if err.get('sugerencia'):
                        print(f"  Sugerencia : {err['sugerencia']}")

            if resultado.sugerencia:
                print(f"\n  CONSEJO: {resultado.sugerencia}")

        print(f"{sep}\n")
        return resultado.valida

    def mostrar_resumen(self, expresion, valida):
        """Muestra una línea compacta de resultado (para tablas de prueba)."""
        estado = "VÁLIDA  " if valida else "INVÁLIDA"
        print(f"  {estado} │ {expresion}")


# =============================================================================
# BLOQUE DE PRUEBA
# =============================================================================

if __name__ == '__main__':
    parser = ParserMatematico()

    # ── Tabla resumen: las 20 expresiones de prueba ──────────────────────────
    ancho = 66
    print("\n" + "=" * ancho)
    print("  PARSER INTEGRADO — Tabla de 20 Expresiones de Prueba")
    print("=" * ancho)

    casos = [
        # 10 válidas
        ("3 + 4",                 True),
        ("(3 + 5) * 2",           True),
        ("3.14 * 2.71",           True),
        ("((2 + 3) * 4) - 1",     True),
        ("-3 + 4",                True),
        ("-(3 + 4)",              True),
        ("10 / 2 + 5",            True),
        ("(((3)))",               True),
        ("0.5 + 0.5",             True),
        ("100",                   True),
        # 10 inválidas
        ("3 ++ 4",                False),
        ("(3 + 4",                False),
        ("3 + 4)",                False),
        ("* 3 + 4",               False),
        ("3 + 4 *",               False),
        ("()",                    False),
        ("3 4 + 1",               False),
        ("(3 + (4 * 2)",          False),
        ("/3",                    False),
        ("3 @ 4",                 False),
    ]

    print(f"\n  {'#':<4} {'Expresión':<26} {'Esperado':<10} {'Parser':<10} {'OK'}")
    print("  " + "-" * (ancho - 2))

    total_ok = 0
    for i, (expr, esperado) in enumerate(casos, 1):
        resultado = parser.analizar(expr)
        ok = "✓" if resultado.valida == esperado else "✗"
        if resultado.valida == esperado:
            total_ok += 1
        esp_str = "Válida" if esperado else "Inválida"
        res_str = "Válida" if resultado.valida else "Inválida"
        print(f"  {i:<4} {repr(expr):<26} {esp_str:<10} {res_str:<10} {ok}")

    print("  " + "-" * (ancho - 2))
    print(f"  Resultado: {total_ok}/{len(casos)} casos correctos\n")

    # ── Análisis detallado de 2 expresiones ──────────────────────────────────
    print("\n  ANÁLISIS DETALLADO — expresión válida")
    parser.mostrar(parser.analizar("((2 + 3) * 4) - 1"))

    print("  ANÁLISIS DETALLADO — expresión inválida")
    parser.mostrar(parser.analizar("3 ++ 4"))

    print("  ANÁLISIS DETALLADO — error léxico")
    parser.mostrar(parser.analizar("3 @ 4"))
