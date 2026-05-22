# =============================================================================
# PASO 1 — ANÁLISIS LÉXICO
# Autómata Finito Determinista (AFD) para expresiones matemáticas educativas
# =============================================================================
#
# ¿QUÉ HACE ESTE MÓDULO?
#   Toma una expresión matemática como texto (ej: "(3.5 + 2) * 8")
#   y la divide en piezas con significado propio llamadas TOKENS.
#   Es el primer paso antes de verificar si la expresión es válida.
#
# TOKENS QUE RECONOCE:
#   NUM    → número entero o decimal       Ejemplos: 3   42   3.14   0.5
#   OP     → operador aritmético           Ejemplos: +   -    *      /
#   LPAREN → paréntesis que abre           Ejemplo:  (
#   RPAREN → paréntesis que cierra         Ejemplo:  )
#
# EXPRESIÓN REGULAR EQUIVALENTE AL AFD:
#   Número : [0-9]+(\.[0-9]+)?
#   Token  : [0-9]+(\.[0-9]+)? | [+\-*/] | [(] | [)]
#
# ESTADOS DEL AFD:
#   q0 — estado inicial, esperando el comienzo de un token
#   q1 — leyendo dígitos de la parte entera de un número        (aceptación)
#   q2 — se leyó el punto decimal, esperando al menos un dígito (no aceptación)
#   q3 — leyendo dígitos de la parte decimal                    (aceptación)
#   q4 — se leyó un operador +, -, *, /                         (aceptación)
#   q5 — se leyó un paréntesis que abre (                       (aceptación)
#   q6 — se leyó un paréntesis que cierra )                     (aceptación)
# =============================================================================


class AFD_Lexico:
    """
    Autómata Finito Determinista para análisis léxico de expresiones matemáticas.

    Recorre la expresión carácter a carácter, cambia de estado según las
    transiciones definidas, y cuando un token está completo lo registra.
    """

    def __init__(self):
        self.estado_inicial    = 'q0'
        self.estados_aceptacion = {'q1', 'q3', 'q4', 'q5', 'q6'}

        # ------------------------------------------------------------------
        # Tabla de transiciones: {estado: {categoria: estado_siguiente}}
        # Si una categoría NO aparece en un estado, no hay transición válida
        # (el token actual termina o se produce un error).
        # ------------------------------------------------------------------
        self.transiciones = {
            'q0': {
                'digito':   'q1',   # inicio de un número entero
                'operador': 'q4',   # operador  +  -  *  /
                'lparen':   'q5',   # paréntesis que abre  (
                'rparen':   'q6',   # paréntesis que cierra )
            },
            'q1': {                 # leyendo dígitos de la parte entera
                'digito': 'q1',     # continúa el número entero
                'punto':  'q2',     # empieza la parte decimal
            },
            'q2': {                 # acaba de leer el punto decimal
                'digito': 'q3',     # primer dígito decimal → ok
            },
            'q3': {                 # leyendo dígitos de la parte decimal
                'digito': 'q3',     # continúa el número decimal
            },
            'q4': {},               # operador: token de 1 carácter, ya terminó
            'q5': {},               # paréntesis abre: token de 1 carácter
            'q6': {},               # paréntesis cierra: token de 1 carácter
        }

        # Tipo de token que produce cada estado de aceptación
        self.tipo_token = {
            'q1': 'NUM',
            'q3': 'NUM',
            'q4': 'OP',
            'q5': 'LPAREN',
            'q6': 'RPAREN',
        }

    # ------------------------------------------------------------------
    # MÉTODO PRINCIPAL
    # ------------------------------------------------------------------

    def tokenizar(self, expresion):
        """
        Analiza la expresión completa y retorna tokens y errores encontrados.

        Parámetros:
            expresion (str): la expresión matemática a analizar

        Retorna:
            tokens  (list): lista de dicts → {tipo, valor, posicion}
            errores (list): lista de dicts → {posicion, caracter, mensaje}
        """
        tokens  = []
        errores = []

        estado          = self.estado_inicial
        token_actual    = ''    # acumula los caracteres del token en curso
        pos_inicio      = 0    # posición donde comenzó el token actual

        i = 0
        while i < len(expresion):
            caracter  = expresion[i]
            categoria = self.clasificar_simbolo(caracter)

            # ── Espacios: terminan el token actual pero no son tokens ────
            if categoria == 'espacio':
                if token_actual:
                    if estado in self.estados_aceptacion:
                        self._registrar_token(estado, token_actual, pos_inicio, tokens)
                    elif estado == 'q2':
                        errores.append(self._error_decimal(pos_inicio, token_actual))
                    token_actual = ''
                    estado = self.estado_inicial
                i += 1
                continue

            # ── Verificar si existe transición válida ────────────────────
            siguiente = self.transiciones.get(estado, {}).get(categoria)

            if siguiente is not None:
                # Transición válida → avanzar en el AFD
                if not token_actual:
                    pos_inicio = i          # registrar inicio del token
                estado        = siguiente
                token_actual += caracter

                # q4, q5, q6 son de 1 carácter → emitir inmediatamente
                if estado in ('q4', 'q5', 'q6'):
                    self._registrar_token(estado, token_actual, pos_inicio, tokens)
                    token_actual = ''
                    estado = self.estado_inicial

                i += 1

            else:
                # Sin transición válida ───────────────────────────────────
                if estado in self.estados_aceptacion:
                    # El token que veníamos construyendo está completo → emitirlo
                    # NO avanzar i: el carácter actual se reanaliza desde q0
                    self._registrar_token(estado, token_actual, pos_inicio, tokens)
                    token_actual = ''
                    estado = self.estado_inicial

                elif estado == 'q2':
                    # Punto decimal sin dígito después → error
                    errores.append(self._error_decimal(pos_inicio, token_actual))
                    token_actual = ''
                    estado = self.estado_inicial
                    i += 1

                elif estado == self.estado_inicial:
                    # Carácter desconocido desde q0 → error léxico
                    errores.append({
                        'posicion': i + 1,
                        'caracter': caracter,
                        'mensaje': (
                            f"Símbolo '{caracter}' no reconocido en posición {i+1}. "
                            f"El alfabeto válido es: dígitos 0-9, punto '.', "
                            f"operadores +-*/, paréntesis ()."
                        )
                    })
                    i += 1

                else:
                    i += 1

        # ── Fin de la cadena: emitir token pendiente si existe ───────────
        if token_actual:
            if estado in self.estados_aceptacion:
                self._registrar_token(estado, token_actual, pos_inicio, tokens)
            elif estado == 'q2':
                errores.append(self._error_decimal(pos_inicio, token_actual))

        return tokens, errores

    # ------------------------------------------------------------------
    # MÉTODOS AUXILIARES
    # ------------------------------------------------------------------

    def clasificar_simbolo(self, caracter):
        """Traduce un carácter a la categoría que usa el AFD."""
        if caracter.isdigit():      return 'digito'
        if caracter == '.':         return 'punto'
        if caracter in '+-*/':      return 'operador'
        if caracter == '(':         return 'lparen'
        if caracter == ')':         return 'rparen'
        if caracter in ' \t':       return 'espacio'
        return 'desconocido'

    def _registrar_token(self, estado, valor, posicion, lista):
        """Crea un token y lo agrega a la lista."""
        lista.append({
            'tipo':     self.tipo_token[estado],
            'valor':    valor,
            'posicion': posicion + 1    # 1-indexado para mensajes al usuario
        })

    def _error_decimal(self, posicion, fragmento):
        """Genera un dict de error para número decimal incompleto."""
        return {
            'posicion': posicion + 1,
            'caracter': '.',
            'mensaje': (
                f"Número decimal incompleto '{fragmento}' en posición {posicion+1}: "
                f"debe haber al menos un dígito después del punto (ej: 3.14)."
            )
        }

    # ------------------------------------------------------------------
    # MÉTODOS DE VISUALIZACIÓN (útiles para el documento TCC)
    # ------------------------------------------------------------------

    def mostrar_tabla_transiciones(self):
        """Imprime la tabla de transiciones del AFD."""
        categorias = ['digito', 'punto', 'operador', 'lparen', 'rparen']
        estados    = ['q0', 'q1', 'q2', 'q3', 'q4', 'q5', 'q6']

        ancho = 66
        print("\n" + "=" * ancho)
        print("  TABLA DE TRANSICIONES — AFD Léxico")
        print("=" * ancho)

        encabezado = f"  {'Estado':<12}" + "".join(f"{c:<11}" for c in categorias)
        print(encabezado)
        print("-" * ancho)

        for est in estados:
            marca = "(*)" if est in self.estados_aceptacion else "   "
            fila  = f"  {est + ' ' + marca:<12}"
            for cat in categorias:
                siguiente = self.transiciones.get(est, {}).get(cat, '—')
                fila += f"{siguiente:<11}"
            print(fila)

        print("-" * ancho)
        print("  (*) = estado de aceptación")
        print(f"  Estado inicial      : {self.estado_inicial}")
        print(f"  Estados aceptación  : {sorted(self.estados_aceptacion)}")
        print("=" * ancho)

    def mostrar_analisis(self, expresion):
        """
        Muestra el análisis léxico completo de una expresión:
        tokens encontrados y errores detectados.
        """
        tokens, errores = self.tokenizar(expresion)

        ancho = 56
        print("\n" + "=" * ancho)
        print(f"  ANÁLISIS LÉXICO")
        print(f"  Expresión: '{expresion}'")
        print("=" * ancho)

        if tokens:
            print(f"\n  {'#':<5} {'Tipo':<10} {'Valor':<12} {'Posición'}")
            print("  " + "-" * 36)
            for idx, t in enumerate(tokens, 1):
                print(f"  {idx:<5} {t['tipo']:<10} {t['valor']:<12} {t['posicion']}")
        else:
            print("\n  (ningún token reconocido)")

        if errores:
            print(f"\n  ERRORES LÉXICOS ({len(errores)}):")
            print("  " + "-" * 50)
            for e in errores:
                print(f"  [Pos {e['posicion']:>2}] {e['mensaje']}")
        else:
            print(f"\n  Sin errores léxicos. ({len(tokens)} tokens encontrados)")

        print("=" * ancho)
        return tokens, errores


# =============================================================================
# BLOQUE DE PRUEBA — ejecutar este archivo directamente para verificar el AFD
# =============================================================================

if __name__ == '__main__':
    afd = AFD_Lexico()

    # Mostrar la tabla de transiciones del AFD
    afd.mostrar_tabla_transiciones()

    print("\n\n  CASOS DE PRUEBA\n")

    casos = [
        # Expresiones válidas (léxicamente)
        ("(3 + 5) * 2",       "Válida — operación con paréntesis"),
        ("3.14 * 2.71",       "Válida — dos decimales"),
        ("100 / 25 + 3",      "Válida — división y suma"),
        ("((2+3)*4)-1",       "Válida — paréntesis anidados"),
        ("0.5 + 0.5",         "Válida — decimales menores a 1"),

        # Expresiones con errores léxicos
        ("3 @ 4",             "Error — '@' no pertenece al alfabeto"),
        ("2.  + 1",           "Error — punto decimal sin dígitos después"),
        ("3 + 4x",            "Error — letra 'x' inválida"),
        ("5 + #2",            "Error — símbolo '#' inválido"),
    ]

    for expresion, descripcion in casos:
        print(f"  [{descripcion}]")
        afd.mostrar_analisis(expresion)
        print()
