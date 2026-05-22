# =============================================================================
# PASO 4 — MODELO AVANZADO
# Máquina de Turing (MT) para verificar paréntesis balanceados
# =============================================================================
#
# ¿QUÉ HACE ESTE MÓDULO?
#   Implementa una Máquina de Turing que decide si los paréntesis de una
#   expresión están correctamente balanceados, reescribiendo la cinta.
#
# ¿POR QUÉ UNA MÁQUINA DE TURING Y NO EL AP?
#   El AP ya resuelve este problema. La MT lo resuelve de forma diferente:
#   en lugar de usar una pila, lee y reescribe la cinta. Esto demuestra
#   que la MT es al menos tan poderosa como el AP.
#
# ALGORITMO — "Marcado de Pares desde Adentro hacia Afuera":
#   1. Escanear derecha buscando el primer ')' sin marcar.
#   2. Marcarlo con 'X' y retroceder a la izquierda.
#   3. Buscar el '(' sin marcar más cercano a la izquierda y marcarlo con 'X'.
#   4. Reiniciar el escaneo desde ese punto.
#   5. Repetir hasta que no haya más ')' sin marcar.
#   6. Verificar que no quede ningún '(' sin marcar.
#   7. Resultado: sin '(' sin marcar → ACEPTAR, si queda alguno → RECHAZAR.
#
# ESTADOS DE LA MT:
#   q0        — escanea derecha buscando ')' no marcado
#   q1        — escanea izquierda buscando '(' no marcado para emparejar
#   q_verif   — escanea izquierda verificando que no queden '(' sin marcar
#   q_acepta  — estado de aceptación (paréntesis balanceados)
#   q_rechaza — estado de rechazo   (paréntesis NO balanceados)
#
# ALFABETO DE CINTA:
#   #  — marcador de borde izquierdo (posición 0 de la cinta, nunca se modifica)
#   (  — paréntesis que abre, sin marcar
#   )  — paréntesis que cierra, sin marcar
#   X  — símbolo marcado (par ya emparejado)
#   B  — blanco (celda vacía al final de la cinta)
#
# NOTA SOBRE EL MARCADOR '#':
#   El borde izquierdo de la cinta se marca con '#'. Cuando q1 llega a '#'
#   significa que no encontró '(' → rechazar. Cuando q_verif llega a '#'
#   significa que no quedó ningún '(' sin marcar → aceptar.
#   Esto evita que el cabezal quede atrapado moviéndose infinitamente a la
#   izquierda más allá del inicio de la cinta.
# =============================================================================

import sys
import os

_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _raiz not in sys.path:
    sys.path.insert(0, _raiz)

from src.afd_lexico import AFD_Lexico


class MT_Parentesis:
    """
    Máquina de Turing que decide si una cadena de paréntesis está balanceada.

    Componentes formales:
        Estados          : {q0, q1, q_verif, q_acepta, q_rechaza}
        Alfabeto entrada : {(, )}
        Alfabeto cinta   : {#, (, ), X, B}
        Estado inicial   : q0
        Símbolo blanco   : B
        Borde izquierdo  : #   (evita bucles infinitos al moverse a la izquierda)
        Estados finales  : {q_acepta}
    """

    BLANCO      = 'B'
    MARCADO     = 'X'
    BORDE_IZQ   = '#'

    def __init__(self):
        self.estado_inicial     = 'q0'
        self.estados_aceptacion = {'q_acepta'}
        self.estado_rechazo     = 'q_rechaza'

        # Tabla de transiciones: (estado, símbolo_leído) → (nuevo_estado, símbolo_escrito, dirección)
        # 'R' = mover cabezal a la derecha, 'L' = mover cabezal a la izquierda
        self.transiciones = {

            # q0: escanea derecha buscando el primer ')' sin marcar
            ('q0', '#'):  ('q0',        '#', 'R'),   # saltar borde izquierdo
            ('q0', '('):  ('q0',        '(', 'R'),   # saltar ( → seguir buscando
            ('q0', 'X'):  ('q0',        'X', 'R'),   # saltar marcado → seguir
            ('q0', ')'):  ('q1',        'X', 'L'),   # encontró ) → marcar y retroceder
            ('q0', 'B'):  ('q_verif',   'B', 'L'),   # fin de cinta → ir a verificar

            # q1: escanea izquierda buscando el '(' más cercano para emparejar
            ('q1', 'X'):  ('q1',        'X', 'L'),   # saltar marcados
            ('q1', ')'):  ('q1',        ')', 'L'),   # saltar ) (ya fueron o serán marcados)
            ('q1', '('):  ('q0',        'X', 'R'),   # encontró ( → marcar y reiniciar
            ('q1', '#'):  ('q_rechaza', '#', 'R'),   # llegó al borde sin ( → error: ) sin (

            # q_verif: escanea izquierda verificando que no queden '(' sin marcar
            ('q_verif', 'X'):  ('q_verif',  'X', 'L'),   # marcado → seguir revisando
            ('q_verif', '('):  ('q_rechaza','(', 'R'),   # quedó ( sin marcar → rechazar
            ('q_verif', '#'):  ('q_acepta', '#', 'R'),   # llegó al borde → nada sin marcar → aceptar
        }

    # ------------------------------------------------------------------
    # MÉTODO PRINCIPAL
    # ------------------------------------------------------------------

    def procesar(self, cadena):
        """
        Ejecuta la MT sobre una cadena de '(' y ')'.

        La cinta se inicializa como: # + cadena + B
        El cabezal comienza en la posición 1 (primer símbolo real, después de '#').

        Retorna:
            acepta  (bool)  — True si la cadena está balanceada
            pasos   (list)  — cada paso: {estado, cabeza, lee, escribe, dir, nuevo_estado, cinta}
            mensaje (str)   — descripción del resultado
        """
        # '#' en posición 0 actúa como borde izquierdo fijo
        cinta  = [self.BORDE_IZQ] + list(cadena) + [self.BLANCO]
        cabeza = 1    # empezar después del marcador de borde
        estado = self.estado_inicial
        pasos  = []

        MAX = 10_000

        for _ in range(MAX):
            simbolo = cinta[cabeza] if cabeza < len(cinta) else self.BLANCO

            # Registrar configuración antes de la transición
            paso = {
                'estado': estado,
                'cabeza': cabeza,
                'lee':    simbolo,
                'cinta':  list(cinta),
            }

            # Estados terminales
            if estado in self.estados_aceptacion:
                paso['escribe'] = '—'
                paso['direccion'] = '—'
                paso['nuevo_estado'] = '(fin)'
                pasos.append(paso)
                return True, pasos, "Paréntesis balanceados — ACEPTADA."

            if estado == self.estado_rechazo:
                paso['escribe'] = '—'
                paso['direccion'] = '—'
                paso['nuevo_estado'] = '(fin)'
                pasos.append(paso)
                return False, pasos, "Paréntesis NO balanceados — RECHAZADA."

            # Buscar transición
            clave = (estado, simbolo)
            if clave not in self.transiciones:
                paso['escribe'] = '—'
                paso['direccion'] = '—'
                paso['nuevo_estado'] = 'q_rechaza'
                pasos.append(paso)
                return False, pasos, f"Sin transición para ({estado}, '{simbolo}') — RECHAZADA."

            nuevo_estado, escribe, direccion = self.transiciones[clave]

            paso['escribe']      = escribe
            paso['direccion']    = direccion
            paso['nuevo_estado'] = nuevo_estado
            pasos.append(paso)

            # Aplicar transición
            cinta[cabeza] = escribe
            estado = nuevo_estado

            if direccion == 'R':
                cabeza += 1
                if cabeza >= len(cinta):
                    cinta.append(self.BLANCO)
            else:  # 'L'
                cabeza = max(0, cabeza - 1)

        return False, pasos, "Límite de pasos alcanzado."

    # ------------------------------------------------------------------
    # INTEGRACIÓN CON EL PROYECTO
    # ------------------------------------------------------------------

    def verificar_expresion(self, expresion):
        """
        Extrae los paréntesis de una expresión matemática y ejecuta la MT.
        Retorna ((acepta, pasos, mensaje), cadena_parens).
        """
        afd = AFD_Lexico()
        tokens, _ = afd.tokenizar(expresion)
        parens = ''.join(
            '(' if t['tipo'] == 'LPAREN' else ')'
            for t in tokens if t['tipo'] in ('LPAREN', 'RPAREN')
        )
        return self.procesar(parens), parens

    # ------------------------------------------------------------------
    # VISUALIZACIÓN
    # ------------------------------------------------------------------

    def mostrar_proceso(self, cadena, max_mostrar=30):
        """Muestra la ejecución de la MT paso a paso."""
        acepta, pasos, mensaje = self.procesar(cadena)

        ancho = 72
        print("\n" + "=" * ancho)
        print("  MÁQUINA DE TURING — Verificación de Paréntesis")
        print(f"  Entrada: '{cadena}'   ({len(cadena)} símbolo(s))")
        print("=" * ancho)
        print(f"  {'Paso':<5} {'Estado':<12} {'Lee':<5} {'Escribe':<9} "
              f"{'Dir':<5} {'Nuevo estado':<14} Cinta (>x< = cabezal)")
        print("  " + "-" * (ancho - 2))

        for i, p in enumerate(pasos[:max_mostrar]):
            cinta_vis = self._visualizar_cinta(p['cinta'], p['cabeza'])
            print(f"  {i+1:<5} {p['estado']:<12} {p['lee']:<5} {p['escribe']:<9} "
                  f"{p['direccion']:<5} {p['nuevo_estado']:<14} {cinta_vis}")

        if len(pasos) > max_mostrar:
            print(f"  ... ({len(pasos) - max_mostrar} pasos más omitidos)")

        print("  " + "-" * (ancho - 2))
        resultado = "ACEPTA" if acepta else "RECHAZA"
        print(f"  Resultado       : {resultado} — {mensaje}")
        print(f"  Pasos totales   : {len(pasos)}")
        print("=" * ancho)
        return acepta

    def mostrar_tabla_transiciones(self):
        """Muestra la tabla de transiciones de la MT."""
        ancho = 68
        print("\n" + "=" * ancho)
        print("  TABLA DE TRANSICIONES — Máquina de Turing")
        print("=" * ancho)
        print(f"  {'(Estado, Lee)':<24} → {'Nuevo estado':<16} {'Escribe':<10} Dirección")
        print("  " + "-" * (ancho - 2))

        for (estado, lee), (nuevo, escribe, dir_) in sorted(self.transiciones.items()):
            clave = f"({estado}, '{lee}')"
            print(f"  {clave:<24} → {nuevo:<16} {escribe:<10} {dir_}")

        print("  " + "-" * (ancho - 2))
        print(f"  Estado inicial    : {self.estado_inicial}")
        print(f"  Estado aceptación : {self.estados_aceptacion}")
        print(f"  Estado rechazo    : {self.estado_rechazo}")
        print(f"  Borde izquierdo   : '{self.BORDE_IZQ}'  (posición fija, nunca se sobreescribe)")
        print("=" * ancho)

    def _visualizar_cinta(self, cinta, cabeza):
        """Genera la cinta con el cabezal marcado: símbolo activo entre >< ."""
        partes = []
        for i, s in enumerate(cinta):
            if i == cabeza:
                partes.append(f'>{s}<')   # cabezal activo
            else:
                partes.append(f' {s} ')
        return '[' + ''.join(partes) + ']'


# =============================================================================
# BLOQUE DE PRUEBA
# =============================================================================

if __name__ == '__main__':
    mt = MT_Parentesis()

    mt.mostrar_tabla_transiciones()

    print("\n\n" + "=" * 66)
    print("  CASOS DE PRUEBA — Máquina de Turing")
    print("=" * 66)

    casos = [
        # Válidas
        ("()",         True,  "par simple"),
        ("(())",       True,  "anidado 1 nivel"),
        ("(()())",     True,  "dos grupos internos"),
        ("((()))",     True,  "anidado 2 niveles"),
        ("()()()",     True,  "tres pares seguidos"),
        ("((()()))",   True,  "anidado complejo"),
        ("",           True,  "cadena vacía — trivialmente balanceada"),
        ("(((())))",   True,  "anidado 3 niveles"),
        # Inválidas
        ("(",          False, "solo abre — falta cerrar"),
        (")",          False, "solo cierra — sin abrir"),
        (")()",        False, "cierra antes de abrir"),
        ("(()(",       False, "dos abiertos, uno cerrado"),
        ("())",        False, "un par + cierra extra"),
        ("(()",        False, "abre dos, cierra uno"),
        (")(",         False, "invertido"),
        ("(((", False, "solo abre × 3"),
    ]

    print(f"\n  {'#':<4} {'Cadena':<16} {'Esperado':<12} {'MT':<12} {'OK':<4} Descripción")
    print("  " + "-" * 62)

    total_ok = 0
    for i, (cadena, esperado, desc) in enumerate(casos, 1):
        acepta, _, _ = mt.procesar(cadena)
        ok = "✓" if acepta == esperado else "✗"
        if acepta == esperado:
            total_ok += 1
        print(f"  {i:<4} {repr(cadena):<16} {'Acepta' if esperado else 'Rechaza':<12} "
              f"{'Acepta' if acepta else 'Rechaza':<12} {ok:<4} {desc}")

    print("  " + "-" * 62)
    print(f"  Resultado: {total_ok}/{len(casos)} casos correctos")

    # Demostración detallada: caso válido
    print("\n\n  DEMOSTRACIÓN DETALLADA — '(())' (válida)")
    mt.mostrar_proceso("(())")

    # Demostración detallada: caso inválido
    print("\n\n  DEMOSTRACIÓN DETALLADA — '((' (inválida)")
    mt.mostrar_proceso("((")

    # Integración con expresión matemática
    print("\n\n  INTEGRACIÓN CON EXPRESIONES MATEMÁTICAS")
    mt2 = MT_Parentesis()
    expresiones = [
        "((2 + 3) * 4) - 1",
        "(3 + 4",
        "3 + 4)",
        "3.14 * 2",
    ]
    print(f"\n  {'Expresión':<30} {'Paréntesis':<14} Resultado")
    print("  " + "-" * 56)
    for expr in expresiones:
        (acepta, _, _), parens = mt2.verificar_expresion(expr)
        resultado = "ACEPTA" if acepta else "RECHAZA"
        parens_repr = repr(parens) if parens else "'' (sin paréntesis)"
        print(f"  {repr(expr):<30} {parens_repr:<14} {resultado}")
