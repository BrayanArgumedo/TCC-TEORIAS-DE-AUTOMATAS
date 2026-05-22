# =============================================================================
# PASO 3 — ANÁLISIS SINTÁCTICO
# Autómata de Pila (AP) + Validador de Gramática BNF
# =============================================================================
#
# ¿QUÉ HACE ESTE MÓDULO?
#   Recibe los tokens del AFD Léxico y verifica que estén organizados
#   correctamente según las reglas de la gramática BNF.
#   Para ello usa un Autómata de Pila (AP): un AFD con una pila extra.
#
# ¿POR QUÉ NECESITAMOS UNA PILA?
#   Los paréntesis pueden anidarse sin límite: ((3+4)*2).
#   Un AFD no puede contar niveles de anidamiento porque no tiene memoria.
#   La pila actúa como esa memoria: apila cuando ve '(' y desapila con ')'.
#
# GRAMÁTICA BNF DEL LENGUAJE:
#   <expresion> ::= <termino>
#                 | <expresion> '+' <termino>
#                 | <expresion> '-' <termino>
#   <termino>   ::= <factor>
#                 | <termino> '*' <factor>
#                 | <termino> '/' <factor>
#   <factor>    ::= NUM
#                 | '(' <expresion> ')'
#                 | '-' <factor>
#
# COMPONENTES:
#   1. AP_Parentesis  — AP formal que verifica solo paréntesis balanceados
#   2. AP_Sintactico  — validador completo de la gramática BNF
#      (implementado como parser de descenso recursivo, equivalente a un AP)
#
# ESTADOS DEL AP_Parentesis:
#   q0 — estado inicial (antes de empezar a leer)
#   q1 — procesando tokens, apilando y desapilando paréntesis
#   q2 — estado de aceptación (pila vacía al terminar)
#
# ALFABETO DE PILA DEL AP_Parentesis:
#   $  — marcador de fondo, indica que la pila está vacía
#   A  — representa un paréntesis '(' pendiente de cerrar
# =============================================================================

import sys
import os

_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _raiz not in sys.path:
    sys.path.insert(0, _raiz)

from src.afd_lexico import AFD_Lexico


# =============================================================================
# PARTE 1 — AP FORMAL PARA PARÉNTESIS BALANCEADOS
# =============================================================================

class AP_Parentesis:
    """
    Autómata de Pila que verifica exclusivamente si los paréntesis
    de una lista de tokens están correctamente balanceados.

    Componentes formales:
        Estados          : {q0, q1, q2}
        Alfabeto entrada : {LPAREN, RPAREN, NUM, OP}
        Alfabeto pila    : {$, A}
        Estado inicial   : q0
        Símbolo de fondo : $
        Estado aceptación: {q2}

    Lógica de la pila:
        Al ver LPAREN → apilar 'A' (un paréntesis abierto pendiente)
        Al ver RPAREN → desapilar 'A' (cerrar el último abierto)
        Al finalizar  → aceptar solo si la pila quedó con únicamente '$'
    """

    FONDO = '$'
    PAREN = 'A'

    def __init__(self):
        self.estado_inicial    = 'q0'
        self.estado_proceso    = 'q1'
        self.estado_aceptacion = 'q2'

        # Tabla de transiciones: (estado, tipo_token, tope_pila) → (nuevo_estado, acción)
        self.transiciones = {
            ('q1', 'LPAREN', '$'): ('q1', 'PUSH'),    # ( con fondo  → apilar A
            ('q1', 'LPAREN', 'A'): ('q1', 'PUSH'),    # ( con A      → apilar A
            ('q1', 'RPAREN', 'A'): ('q1', 'POP'),     # ) con A      → desapilar
            ('q1', 'RPAREN', '$'): ('q1', 'ERROR'),   # ) sin nada   → error
            ('q1', 'NUM',    '$'): ('q1', 'SKIP'),    # número       → pila intacta
            ('q1', 'NUM',    'A'): ('q1', 'SKIP'),
            ('q1', 'OP',     '$'): ('q1', 'SKIP'),    # operador     → pila intacta
            ('q1', 'OP',     'A'): ('q1', 'SKIP'),
        }

    def procesar(self, tokens):
        """
        Procesa la lista de tokens y verifica el balance de paréntesis.

        Retorna:
            valido  (bool) — True si los paréntesis están balanceados
            pasos   (list) — estado de la pila en cada token
            mensaje (str)  — descripción del resultado
        """
        pila   = [self.FONDO]
        estado = self.estado_proceso
        pasos  = []

        for token in tokens:
            tipo  = token['tipo']
            tope  = pila[-1]
            clave = (estado, tipo, tope)
            accion = self.transiciones.get(clave, (estado, 'SKIP'))[1]

            paso = {
                'token':       token,
                'accion':      accion,
                'pila_antes':  list(pila),
            }

            if accion == 'PUSH':
                pila.append(self.PAREN)
                paso['descripcion'] = f"'(' pos {token['posicion']} → APILAR"
            elif accion == 'POP':
                pila.pop()
                paso['descripcion'] = f"')' pos {token['posicion']} → DESAPILAR"
            elif accion == 'ERROR':
                paso['descripcion'] = f"')' pos {token['posicion']} → ERROR: pila vacía"
                paso['pila_despues'] = list(pila)
                pasos.append(paso)
                return (False, pasos,
                        f"Paréntesis ')' en posición {token['posicion']} "
                        f"sin apertura '(' correspondiente.")
            else:
                paso['descripcion'] = f"{tipo} pos {token['posicion']} → sin cambio"

            paso['pila_despues'] = list(pila)
            pasos.append(paso)

        # Al terminar: la pila debe contener solo el marcador de fondo
        if len(pila) > 1:
            faltantes = len(pila) - 1
            return (False, pasos,
                    f"Faltan {faltantes} paréntesis de cierre ')'.")

        return True, pasos, "Paréntesis correctamente balanceados."

    def mostrar_proceso(self, tokens):
        """Muestra el estado de la pila en cada paso."""
        valido, pasos, mensaje = self.procesar(tokens)

        ancho = 72
        print("\n" + "=" * ancho)
        print("  AUTÓMATA DE PILA — Verificación de Paréntesis")
        print("=" * ancho)
        print(f"  {'Token':<10} {'Tipo':<10} {'Acción':<12} "
              f"{'Pila antes':<20} {'Pila después'}")
        print("  " + "-" * (ancho - 2))

        for p in pasos:
            t   = p['token']
            ant = str(p['pila_antes'])
            des = str(p['pila_despues'])
            print(f"  {repr(t['valor']):<10} {t['tipo']:<10} {p['accion']:<12} "
                  f"{ant:<20} {des}")

        print("  " + "-" * (ancho - 2))
        print(f"  Resultado: {'BALANCEADOS' if valido else 'NO BALANCEADOS'} — {mensaje}")
        print("=" * ancho)
        return valido, mensaje


# =============================================================================
# PARTE 2 — VALIDADOR BNF COMPLETO
# =============================================================================

class _ErrorSintactico(Exception):
    """Excepción interna para señalar errores de sintaxis con posición."""
    def __init__(self, posicion, mensaje):
        super().__init__(mensaje)
        self.posicion = posicion


class AP_Sintactico:
    """
    Validador sintáctico completo basado en la gramática BNF.

    Implementado como parser de descenso recursivo, que es equivalente
    computacionalmente a un Autómata de Pila que aplica las reglas de la
    gramática como producciones en la pila.

    Cada método representa una regla de la gramática BNF:
        _expresion() → regla <expresion>
        _termino()   → regla <termino>
        _factor()    → regla <factor>

    Errores que detecta:
        - Expresión vacía
        - Paréntesis sin cerrar o sin abrir
        - Paréntesis vacíos ()
        - Operadores consecutivos: 3 ++ 4
        - Operador binario al inicio: * 3
        - Expresión termina con operador: 3 +
        - Dos operandos seguidos sin operador: 3 4
    """

    def __init__(self):
        self.tokens  = []
        self.pos     = 0
        self.errores = []
        self.pasos   = []

    # ------------------------------------------------------------------
    # INTERFAZ PRINCIPAL
    # ------------------------------------------------------------------

    def validar(self, expresion):
        """
        Valida la expresión completa: primero aplica léxico y luego sintáctico.

        Retorna:
            valido  (bool)
            tokens  (list)
            errores (list)
            pasos   (list)
        """
        afd = AFD_Lexico()
        tokens, errores_lexicos = afd.tokenizar(expresion)

        self.tokens  = tokens
        self.pos     = 0
        self.errores = list(errores_lexicos)
        self.pasos   = []

        if not tokens:
            self.errores.append({
                'posicion': 1,
                'mensaje':  "La expresión está vacía o no contiene tokens válidos."
            })
            return False, tokens, self.errores, self.pasos

        try:
            self._expresion()

            # Si quedaron tokens sin consumir, hay un problema estructural
            if self.pos < len(self.tokens):
                t = self.tokens[self.pos]
                if t['tipo'] == 'RPAREN':
                    raise _ErrorSintactico(
                        t['posicion'],
                        f"Paréntesis ')' en posición {t['posicion']} "
                        f"sin apertura '(' correspondiente."
                    )
                raise _ErrorSintactico(
                    t['posicion'],
                    f"Token inesperado '{t['valor']}' en posición {t['posicion']}. "
                    f"¿Falta un operador entre dos operandos?"
                )

        except _ErrorSintactico as e:
            self.errores.append({'posicion': e.posicion, 'mensaje': str(e)})

        valido = len(self.errores) == 0
        return valido, tokens, self.errores, self.pasos

    # ------------------------------------------------------------------
    # REGLAS DE LA GRAMÁTICA BNF (descenso recursivo)
    # ------------------------------------------------------------------

    def _expresion(self):
        """
        Regla BNF:
            <expresion> ::= <termino> (('+' | '-') <termino>)*
        """
        self._log("Aplicando regla <expresion> → buscar <termino>")
        self._termino()

        while self._tipo_actual() == 'OP' and self._valor_actual() in ('+', '-'):
            op = self._consumir('OP')
            self._log(f"<expresion>: operador '{op}' consumido → buscar siguiente <termino>")
            self._termino()

    def _termino(self):
        """
        Regla BNF:
            <termino> ::= <factor> (('*' | '/') <factor>)*
        """
        self._log("Aplicando regla <termino> → buscar <factor>")
        self._factor()

        while self._tipo_actual() == 'OP' and self._valor_actual() in ('*', '/'):
            op = self._consumir('OP')
            self._log(f"<termino>: operador '{op}' consumido → buscar siguiente <factor>")
            self._factor()

    def _factor(self):
        """
        Regla BNF:
            <factor> ::= NUM | '(' <expresion> ')' | '-' <factor>
        """
        # Caso 1: número
        if self._tipo_actual() == 'NUM':
            num = self._consumir('NUM')
            self._log(f"<factor>: número '{num}' consumido")
            return

        # Caso 2: expresión entre paréntesis
        if self._tipo_actual() == 'LPAREN':
            self._consumir('LPAREN')
            self._log("<factor>: '(' consumido → buscar <expresion> interna")

            if self._tipo_actual() == 'RPAREN':
                t = self.tokens[self.pos]
                raise _ErrorSintactico(
                    t['posicion'],
                    f"Paréntesis vacíos en posición {t['posicion']}: "
                    f"'()' no contiene ninguna expresión válida."
                )

            self._expresion()

            if self._tipo_actual() != 'RPAREN':
                pos = self.tokens[self.pos - 1]['posicion'] if self.pos > 0 else 1
                falta = self._valor_actual() or 'fin de expresión'
                raise _ErrorSintactico(
                    pos,
                    f"Se esperaba ')' para cerrar paréntesis, "
                    f"pero se encontró '{falta}' cerca de posición {pos}."
                )

            self._consumir('RPAREN')
            self._log("<factor>: ')' consumido → paréntesis cerrado")
            return

        # Caso 3: menos unario
        if self._tipo_actual() == 'OP' and self._valor_actual() == '-':
            self._consumir('OP')
            self._log("<factor>: menos unario '-' consumido → buscar <factor>")
            self._factor()
            return

        # Ningún caso válido: producir error descriptivo
        if self.pos >= len(self.tokens):
            ultima = self.tokens[-1]['posicion'] if self.tokens else 1
            raise _ErrorSintactico(
                ultima,
                "Expresión incompleta: se esperaba un número o '(' al final."
            )

        t = self.tokens[self.pos]

        if t['tipo'] == 'RPAREN':
            raise _ErrorSintactico(
                t['posicion'],
                f"Paréntesis ')' en posición {t['posicion']} sin apertura correspondiente."
            )

        if t['tipo'] == 'OP':
            raise _ErrorSintactico(
                t['posicion'],
                f"Operador '{t['valor']}' en posición {t['posicion']} no puede "
                f"usarse aquí. Se esperaba un número o '('. "
                f"¿Hay dos operadores seguidos?"
            )

        raise _ErrorSintactico(
            t['posicion'],
            f"Token inesperado '{t['valor']}' en posición {t['posicion']}."
        )

    # ------------------------------------------------------------------
    # MÉTODOS AUXILIARES
    # ------------------------------------------------------------------

    def _tipo_actual(self):
        """Tipo del token en la posición actual (None si se acabaron)."""
        return self.tokens[self.pos]['tipo'] if self.pos < len(self.tokens) else None

    def _valor_actual(self):
        """Valor del token en la posición actual (None si se acabaron)."""
        return self.tokens[self.pos]['valor'] if self.pos < len(self.tokens) else None

    def _consumir(self, tipo_esperado):
        """Consume el token actual si coincide con el tipo esperado."""
        if self.pos >= len(self.tokens):
            ultima = self.tokens[-1]['posicion'] if self.tokens else 1
            raise _ErrorSintactico(
                ultima,
                f"Se esperaba '{tipo_esperado}' pero la expresión terminó inesperadamente."
            )
        token = self.tokens[self.pos]
        if token['tipo'] != tipo_esperado:
            raise _ErrorSintactico(
                token['posicion'],
                f"Se esperaba {tipo_esperado} pero se encontró "
                f"'{token['valor']}' en posición {token['posicion']}."
            )
        self.pos += 1
        return token['valor']

    def _log(self, descripcion):
        """Registra un paso del análisis."""
        actual = self.tokens[self.pos] if self.pos < len(self.tokens) else None
        self.pasos.append({'descripcion': descripcion, 'token': actual})

    # ------------------------------------------------------------------
    # VISUALIZACIÓN
    # ------------------------------------------------------------------

    def mostrar_resultado(self, expresion, valido, tokens, errores, pasos):
        """Muestra el resultado completo del análisis sintáctico."""
        ancho = 66
        print("\n" + "=" * ancho)
        print("  ANÁLISIS SINTÁCTICO (AP + Gramática BNF)")
        print(f"  Expresión: '{expresion}'")
        print("=" * ancho)

        if tokens:
            secuencia = '  '.join(t['tipo'] for t in tokens)
            print(f"\n  Secuencia de tokens : {secuencia}")

        print(f"\n  Pasos del analizador sintáctico:")
        print("  " + "-" * (ancho - 2))
        for p in pasos:
            tok = f"(token actual: '{p['token']['valor']}')" if p['token'] else "(fin)"
            print(f"  {p['descripcion']}")
            print(f"    {tok}")

        if errores:
            print(f"\n  ERRORES DETECTADOS ({len(errores)}):")
            print("  " + "-" * (ancho - 2))
            for e in errores:
                print(f"  [Pos {e['posicion']:>2}] {e['mensaje']}")
        else:
            print(f"\n  Sin errores. Expresión VÁLIDA según la gramática BNF.")

        print(f"\n  Resultado: {'VÁLIDA' if valido else 'INVÁLIDA'}")
        print("=" * ancho)
        return valido


# =============================================================================
# BLOQUE DE PRUEBA
# =============================================================================

if __name__ == '__main__':

    ap_paren    = AP_Parentesis()
    ap_sintax   = AP_Sintactico()
    afd         = AFD_Lexico()

    print("\n" + "=" * 66)
    print("  PASO 3 — PRUEBAS DEL AUTÓMATA DE PILA")
    print("=" * 66)

    casos = [
        # Válidas
        ("3 + 4",             True,  "suma simple"),
        ("(3 + 5) * 2",       True,  "paréntesis y multiplicación"),
        ("3.14 * 2.71",       True,  "dos números decimales"),
        ("((2 + 3) * 4) - 1", True,  "paréntesis anidados"),
        ("-3 + 4",            True,  "menos unario"),
        ("-(3 + 4)",          True,  "menos unario con paréntesis"),
        ("10 / 2 + 5",        True,  "división y suma"),
        ("(((3)))",           True,  "triple anidamiento"),
        ("0.5 + 0.5",         True,  "decimales menores a 1"),
        ("100",               True,  "número solo"),
        # Inválidas
        ("3 ++ 4",            False, "operadores consecutivos"),
        ("(3 + 4",            False, "paréntesis sin cerrar"),
        ("3 + 4)",            False, "paréntesis sin abrir"),
        ("* 3 + 4",           False, "inicia con operador binario"),
        ("3 + 4 *",           False, "termina con operador"),
        ("()",                False, "paréntesis vacíos"),
        ("3 4 + 1",           False, "dos operandos seguidos"),
        ("(3 + (4 * 2)",      False, "paréntesis interno sin cerrar"),
        ("/3",                False, "inicia con división"),
        ("3 + * 4",           False, "operadores consecutivos distintos"),
    ]

    # Tabla resumen
    ancho = 66
    print(f"\n  {'#':<4} {'Expresión':<25} {'Esperado':<10} {'AP':<10} {'OK'}")
    print("  " + "-" * (ancho - 2))

    errores_totales = 0
    for i, (expr, esperado, desc) in enumerate(casos, 1):
        valido, tokens, errores, pasos = ap_sintax.validar(expr)
        ok = "✓" if valido == esperado else "✗"
        if valido != esperado:
            errores_totales += 1
        esperado_str = "Válida" if esperado else "Inválida"
        resultado_str = "Válida" if valido else "Inválida"
        print(f"  {i:<4} {repr(expr):<25} {esperado_str:<10} {resultado_str:<10} {ok}  {desc}")

    print("  " + "-" * (ancho - 2))
    print(f"  Resultado: {len(casos) - errores_totales}/{len(casos)} casos correctos")

    # Demostración detallada del AP de paréntesis con un caso
    print("\n\n  DEMOSTRACIÓN DETALLADA — AP de Paréntesis")
    expr_demo = "((2 + 3) * 4) - 1"
    tokens_demo, _ = afd.tokenizar(expr_demo)
    ap_paren.mostrar_proceso(tokens_demo)

    # Demostración detallada del validador BNF con un error
    print("\n\n  DEMOSTRACIÓN DETALLADA — Validador BNF con error")
    expr_error = "3 ++ 4"
    v, tok, err, pas = ap_sintax.validar(expr_error)
    ap_sintax.mostrar_resultado(expr_error, v, tok, err, pas)
