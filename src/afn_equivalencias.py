# =============================================================================
# PASO 2 — EQUIVALENCIAS Y OPTIMIZACIÓN
# AFN → Conversión a AFD (subconjuntos) → Minimización del AFD
# =============================================================================
#
# ¿QUÉ HACE ESTE MÓDULO?
#   Demuestra que un AFN (Autómata Finito No Determinista) y un AFD
#   (Autómata Finito Determinista) son equivalentes: reconocen exactamente
#   el mismo lenguaje.
#
#   Se implementan tres cosas:
#     1. AFN con no-determinismo explícito para reconocer números
#     2. Algoritmo de Construcción de Subconjuntos (AFN → AFD)
#     3. Algoritmo de Minimización por Particiones (AFD → AFD mínimo)
#
# LENGUAJE RECONOCIDO: números enteros y decimales positivos
#   Válidos   : 3   42   0   3.14   100.5   0.5
#   Inválidos : 3.   .5   abc   3..14   (cadena vacía)
#
# ESTADOS DEL AFN (5 estados):
#   s0 — estado inicial
#   s1 — leyendo dígitos (camino entero)                       (aceptación)
#   s2 — leyendo dígitos antes del punto decimal               (no aceptación)
#   s3 — punto decimal leído, esperando primer dígito decimal  (no aceptación)
#   s4 — leyendo dígitos decimales                             (aceptación)
#
# FUENTE DE NO-DETERMINISMO:
#   Desde s0, al leer un dígito, el AFN puede ir a s1 O s2 al mismo tiempo.
#   En un AFD eso no está permitido; aquí sí.
# =============================================================================


# =============================================================================
# PARTE 1 — AUTÓMATA FINITO NO DETERMINISTA (AFN)
# =============================================================================

class AFN_Numeros:
    """
    AFN que reconoce números enteros y decimales con no-determinismo explícito.

    El no-determinismo está en el estado inicial s0: al recibir el primer
    dígito, el autómata va a {s1, s2} simultáneamente (no puede saber aún
    si el número terminará siendo entero o decimal).
    """

    def __init__(self):
        self.estado_inicial      = 's0'
        self.estados_aceptacion  = frozenset({'s1', 's4'})
        self.alfabeto            = ['digito', 'punto']

        # Diferencia clave con el AFD: cada valor es un CONJUNTO de estados,
        # no un solo estado. Eso es el no-determinismo.
        self.transiciones = {
            's0': {
                'digito': frozenset({'s1', 's2'}),  # ← NO-DETERMINISMO
            },
            's1': {
                'digito': frozenset({'s1'}),
            },
            's2': {
                'digito': frozenset({'s2'}),
                'punto':  frozenset({'s3'}),
            },
            's3': {
                'digito': frozenset({'s4'}),
            },
            's4': {
                'digito': frozenset({'s4'}),
            },
        }

    def clasificar(self, caracter):
        """Convierte un carácter en la categoría que usa el AFN."""
        if caracter.isdigit(): return 'digito'
        if caracter == '.':    return 'punto'
        return None

    def mover(self, conjunto_estados, simbolo):
        """
        Calcula todos los estados alcanzables desde un CONJUNTO de estados
        con un símbolo. Este conjunto puede crecer porque el AFN es no
        determinista: varios estados pueden tener transiciones válidas.
        """
        resultado = set()
        for estado in conjunto_estados:
            siguientes = self.transiciones.get(estado, {}).get(simbolo, frozenset())
            resultado.update(siguientes)
        return frozenset(resultado)

    def procesar(self, cadena):
        """
        Simula el AFN sobre una cadena usando rastreo de subconjuntos.
        Retorna True si algún estado final al terminar es de aceptación.
        """
        estados_actuales = frozenset({self.estado_inicial})

        for caracter in cadena:
            simbolo = self.clasificar(caracter)
            if simbolo is None:
                return False
            estados_actuales = self.mover(estados_actuales, simbolo)
            if not estados_actuales:
                return False

        return bool(estados_actuales & self.estados_aceptacion)

    def mostrar_tabla(self):
        """Imprime la tabla de transiciones del AFN."""
        estados = ['s0', 's1', 's2', 's3', 's4']

        ancho = 62
        print("\n" + "=" * ancho)
        print("  TABLA DE TRANSICIONES — AFN (No Determinista)")
        print("=" * ancho)
        print(f"  {'Estado':<14} {'digito':<24} {'punto'}")
        print("  " + "-" * (ancho - 2))

        for est in estados:
            marca = " (*)" if est in self.estados_aceptacion else "    "
            d = self.transiciones.get(est, {}).get('digito', frozenset())
            p = self.transiciones.get(est, {}).get('punto',  frozenset())
            val_d = '{' + ', '.join(sorted(d)) + '}' if d else '∅'
            val_p = '{' + ', '.join(sorted(p)) + '}' if p else '∅'
            print(f"  {est + marca:<14} {val_d:<24} {val_p}")

        print("  " + "-" * (ancho - 2))
        print("  (*) = estado de aceptación")
        print(f"  Estado inicial      : {self.estado_inicial}")
        print(f"  No-determinismo en  : s0 —digito→ {{s1, s2}}")
        print("=" * ancho)


# =============================================================================
# PARTE 2 — ALGORITMO DE CONSTRUCCIÓN DE SUBCONJUNTOS (AFN → AFD)
# =============================================================================

def convertir_afn_a_afd(afn):
    """
    Convierte un AFN en un AFD equivalente usando el algoritmo de subconjuntos.

    Idea central: cada ESTADO del nuevo AFD es un CONJUNTO de estados del AFN.
    El AFD comienza en {estado_inicial_afn} y expande todos los conjuntos
    posibles hasta que no haya ninguno nuevo por descubrir.

    Retorna:
        trans_afd  — tabla de transiciones del AFD
        q0_afd     — estado inicial del AFD (frozenset)
        aceptacion — conjunto de estados de aceptación del AFD
        nombres    — diccionario { frozenset → 'A', 'B', ... }
        pasos      — lista con el detalle de cada paso de la construcción
    """
    q0_afd          = frozenset({afn.estado_inicial})
    pendientes       = [q0_afd]
    visitados        = set()
    orden_descubierto = []   # orden real de descubrimiento para nombrar A, B, C...
    trans_afd        = {}
    aceptacion       = set()
    pasos            = []

    while pendientes:
        conjunto = pendientes.pop(0)

        if conjunto in visitados:
            continue
        visitados.add(conjunto)
        orden_descubierto.append(conjunto)
        trans_afd[conjunto] = {}

        # Este estado del AFD acepta si contiene algún estado de aceptación del AFN
        if conjunto & afn.estados_aceptacion:
            aceptacion.add(conjunto)

        # Calcular transición para cada símbolo del alfabeto
        for simbolo in afn.alfabeto:
            siguiente = afn.mover(conjunto, simbolo)
            trans_afd[conjunto][simbolo] = siguiente

            pasos.append({
                'desde':   conjunto,
                'simbolo': simbolo,
                'hacia':   siguiente,
                'nuevo':   siguiente not in visitados and bool(siguiente)
            })

            if siguiente and siguiente not in visitados:
                pendientes.append(siguiente)

    # Asignar nombres legibles (A, B, C…) en el orden en que fueron descubiertos
    nombres = {conj: chr(ord('A') + i) for i, conj in enumerate(orden_descubierto)}
    nombres[frozenset()] = '∅'

    return trans_afd, q0_afd, aceptacion, nombres, pasos


def mostrar_construccion(afn, trans_afd, q0_afd, aceptacion, nombres, pasos):
    """Muestra el proceso de construcción de subconjuntos paso a paso."""
    ancho = 66

    print("\n" + "=" * ancho)
    print("  CONSTRUCCIÓN DE SUBCONJUNTOS — AFN → AFD")
    print("=" * ancho)
    print(f"  Estado inicial del AFD: {{{afn.estado_inicial}}} → renombrado como '{nombres[q0_afd]}'")
    print()

    # Mostrar cada decisión tomada durante la construcción
    ya_impresos = set()
    paso_num    = 1
    for p in pasos:
        etiqueta    = '{' + ', '.join(sorted(p['desde'])) + '}' if p['desde'] else '∅'
        si          = '{' + ', '.join(sorted(p['hacia'])) + '}' if p['hacia'] else '∅'

        if p['desde'] not in ya_impresos:
            print(f"  Paso {paso_num}: Procesando {etiqueta}  [{nombres.get(p['desde'], '?')}]")
            ya_impresos.add(p['desde'])
            paso_num += 1

        marca_nuevo = "  ← nuevo estado" if p['nuevo'] else ""
        print(f"    Con '{p['simbolo']:8}': {etiqueta} → {si}{marca_nuevo}")

    # Tabla del AFD resultante
    print()
    print(f"  TABLA DEL AFD RESULTANTE")
    print("  " + "-" * (ancho - 2))
    print(f"  {'Estado':<28} {'digito':<16} {'punto'}")
    print("  " + "-" * (ancho - 2))

    for conj, trans in sorted(trans_afd.items(), key=lambda x: nombres.get(x[0], '?')):
        nombre     = nombres.get(conj, '?')
        contenido  = '{' + ', '.join(sorted(conj)) + '}' if conj else '∅'
        marca_ac   = " (*)" if conj in aceptacion else "    "
        etiq       = f"{nombre}{marca_ac} = {contenido}"

        d = trans.get('digito', frozenset())
        p = trans.get('punto',  frozenset())
        print(f"  {etiq:<28} {nombres.get(d, '∅'):<16} {nombres.get(p, '∅')}")

    print("  " + "-" * (ancho - 2))
    print("  (*) = estado de aceptación")
    print("=" * ancho)


# =============================================================================
# PARTE 3 — MINIMIZACIÓN POR PARTICIONES
# =============================================================================

def minimizar_afd(trans_afd, q0_afd, aceptacion, alfabeto):
    """
    Minimiza el AFD usando el Algoritmo de Refinamiento de Particiones.

    Idea: agrupa los estados que son "indistinguibles" entre sí.
    Dos estados son indistinguibles si:
      - Ambos aceptan o ambos no aceptan
      - Para todo símbolo, van al mismo grupo de destino

    Retorna:
        particion_final — conjuntos de estados equivalentes
        historial       — cómo evolucionaron las particiones en cada iteración
    """
    todos    = set(trans_afd.keys()) | {frozenset()}
    F        = frozenset(e for e in todos if e in aceptacion)
    no_F     = frozenset(e for e in todos if e not in aceptacion)

    particion  = set()
    if F:    particion.add(F)
    if no_F: particion.add(no_F)

    historial = [frozenset(particion)]

    while True:
        nueva = set()
        for grupo in particion:
            subgrupos = _dividir(grupo, particion, trans_afd, alfabeto)
            nueva.update(subgrupos)

        if nueva == particion:
            break
        particion = nueva
        historial.append(frozenset(particion))

    return particion, historial


def _dividir(grupo, particion, trans_afd, alfabeto):
    """
    Intenta separar un grupo en subgrupos.
    Dos estados van al mismo subgrupo si para todo símbolo, su
    transición cae en el mismo grupo de la partición actual.
    """
    def grupo_de(estado):
        for g in particion:
            if estado in g:
                return g
        return frozenset()  # estado muerto / no encontrado

    def firma(estado):
        """Identificador único del comportamiento de un estado: a qué grupo va con cada símbolo."""
        return tuple(
            id(grupo_de(trans_afd.get(estado, {}).get(sim, frozenset())))
            for sim in sorted(alfabeto)
        )

    subgrupos = {}
    for estado in grupo:
        f = firma(estado)
        subgrupos.setdefault(f, set()).add(estado)

    return {frozenset(g) for g in subgrupos.values()}


def mostrar_minimizacion(particion_final, historial, nombres, aceptacion):
    """Muestra el proceso de minimización iteración por iteración."""
    ancho = 66

    print("\n" + "=" * ancho)
    print("  MINIMIZACIÓN DEL AFD — Algoritmo de Particiones")
    print("=" * ancho)

    def nombre_grupo(grupo, nombres):
        """Representa un grupo como '{A, B}' usando los nombres del AFD."""
        partes = [nombres.get(est, '∅') for est in grupo]
        return '{' + ', '.join(sorted(partes)) + '}'

    for i, part in enumerate(historial):
        grupos_str = '  |  '.join(nombre_grupo(g, nombres) for g in sorted(part, key=lambda g: sorted(nombres.get(e, '∅') for e in g)))
        etiqueta   = "Inicial" if i == 0 else f"Iteración {i}"
        print(f"  {etiqueta:<14}: {grupos_str}")

    print()

    # Contar estados originales del AFD (todos los estados en la partición inicial)
    estados_originales = sum(len(g) for g in historial[0]) if historial else 0
    estados_minimos    = len(particion_final)

    if estados_originales == estados_minimos:
        print(f"  Resultado: el AFD ya estaba en su forma MÍNIMA ({estados_minimos} estados).")
        print("  No fue posible fusionar ningún par de estados.")
    else:
        fusionados = estados_originales - estados_minimos
        print(f"  Resultado: reducido de {estados_originales} a {estados_minimos} estados.")
        print(f"  Se fusionaron {fusionados} estado(s) equivalente(s).")

    print()
    print("  GRUPOS DEL AFD MÍNIMO:")
    print("  " + "-" * (ancho - 2))
    for grupo in sorted(particion_final, key=lambda g: sorted(nombres.get(e, '∅') for e in g)):
        contenidos = [f"{nombres.get(e,'∅')}={{{', '.join(sorted(e))}}}" if e else "∅" for e in grupo]
        ac         = " (aceptación)" if any(e in aceptacion for e in grupo) else ""
        print(f"  {nombre_grupo(grupo, nombres):<12} → {', '.join(contenidos)}{ac}")
    print("=" * ancho)


# =============================================================================
# BLOQUE DE PRUEBA — ejecutar directamente para ver los tres pasos
# =============================================================================

if __name__ == '__main__':

    # ── Parte 1: AFN ─────────────────────────────────────────────────────────
    afn = AFN_Numeros()
    afn.mostrar_tabla()

    print("\n\n  VERIFICACIÓN DEL AFN CON CADENAS DE PRUEBA")
    casos = [
        ("3",      True,  "entero de 1 dígito"),
        ("42",     True,  "entero de 2 dígitos"),
        ("3.14",   True,  "decimal"),
        ("0.5",    True,  "decimal menor a 1"),
        ("100",    True,  "entero de 3 dígitos"),
        ("3.",     False, "decimal incompleto — falta dígito"),
        (".5",     False, "inicia con punto"),
        ("",       False, "cadena vacía"),
        ("3..14",  False, "doble punto"),
        ("abc",    False, "letras inválidas"),
    ]
    ancho = 58
    print(f"\n  {'Cadena':<12} {'Esperado':<12} {'AFN':<12} {'Descripción'}")
    print("  " + "-" * ancho)
    errores_afn = 0
    for cadena, esperado, desc in casos:
        resultado = afn.procesar(cadena)
        ok        = "✓" if resultado == esperado else "✗"
        if resultado != esperado:
            errores_afn += 1
        print(f"  {repr(cadena):<12} {'Acepta' if esperado else 'Rechaza':<12} "
              f"{'Acepta' if resultado else 'Rechaza':<12} {ok}  {desc}")
    print(f"\n  Resultado: {len(casos) - errores_afn}/{len(casos)} casos correctos")

    # ── Parte 2: Conversión AFN → AFD ────────────────────────────────────────
    trans_afd, q0_afd, aceptacion_afd, nombres, pasos = convertir_afn_a_afd(afn)
    mostrar_construccion(afn, trans_afd, q0_afd, aceptacion_afd, nombres, pasos)

    # ── Parte 3: Minimización ────────────────────────────────────────────────
    particion_final, historial = minimizar_afd(
        trans_afd, q0_afd, aceptacion_afd, afn.alfabeto
    )
    mostrar_minimizacion(particion_final, historial, nombres, aceptacion_afd)
