# Contexto Técnico Completo — TCC Teoría de Autómatas

**Parser de Expresiones Matemáticas Educativas**  
Este documento recoge todo el razonamiento, decisiones de diseño e implementación del proyecto, paso a paso. Está pensado para quien vaya a documentarlo formalmente o necesite entender el fondo de cada decisión.

---

## 1. Problemática y motivación

El proyecto surge de una necesidad real: estudiantes de programación en Montería, Córdoba, cometen errores frecuentes al escribir expresiones matemáticas en entornos de programación. Los errores más comunes son:

- Paréntesis que abren pero nunca se cierran: `(3 + 4`
- Operadores mal ubicados: `3 ++ 4`, `* 3`, `3 + 4 *`
- Símbolos que no pertenecen al lenguaje: `3 @ 4`, `5 $ 2`
- Decimales incompletos: `3.` sin dígitos después del punto

Los mensajes de error de los compiladores suelen ser crípticos. Este proyecto construye un parser educativo que no solo detecta el error sino que explica qué regla formal fue violada y cómo corregirlo.

**Por qué es relevante para teoría de autómatas:** Una expresión matemática es un lenguaje formal. Analizarla implica exactamente los cuatro modelos estudiados en el curso: AFD (léxico), AP+BNF (sintáctico), y MT (verificación). El proyecto demuestra que la teoría de autómatas no es abstracta — es la base de cualquier compilador o intérprete real.

---

## 2. Arquitectura general: el pipeline

El parser funciona como una cadena de tres fases en secuencia:

```
Expresión de texto
       ↓
[FASE 1] AFD Léxico       → tokeniza la cadena
       ↓
[FASE 2] AP + BNF         → valida la estructura gramatical
       ↓
[FASE 3] Máquina de Turing → verifica el balance de paréntesis
       ↓
Resultado: válida/inválida + diagnóstico educativo
```

Si una fase detecta un error, el análisis continúa para recoger todos los errores posibles, pero el resultado final es inválido. Los errores se deduplican antes de mostrarlos (ver Paso 5).

---

## 3. Paso 1 — AFD Léxico (`src/afd_lexico.py`)

### Qué hace

Es el primer autómata de la cadena. Lee la expresión carácter a carácter y la divide en **tokens** — las unidades mínimas con significado: números (`NUM`), operadores (`OP`), paréntesis que abren (`LPAREN`) y paréntesis que cierran (`RPAREN`).

### Estados y qué representan

| Estado | Significado | ¿Acepta? |
|--------|-------------|----------|
| q0 | Inicial, esperando el primer carácter de un nuevo token | No |
| q1 | Leyendo un número entero (dígitos) | Sí → NUM |
| q2 | Leyó un punto decimal, esperando dígitos | No |
| q3 | Leyendo la parte decimal de un número | Sí → NUM |
| q4 | Leyó un operador (+, -, *, /) | Sí → OP |
| q5 | Leyó un paréntesis que abre | Sí → LPAREN |
| q6 | Leyó un paréntesis que cierra | Sí → RPAREN |

**Por qué q2 no acepta:** Si la cadena termina justo en `3.`, eso no es un número válido. El punto requiere al menos un dígito después. Si el AFD llegara a q2 y no encontrara dígito, emite error "decimal incompleto".

### Algoritmo de máxima mordida

El AFD consume tantos caracteres como pueda antes de emitir un token. Cuando desde un estado aceptor no existe transición para el carácter actual, emite el token acumulado y reinicia desde q0 con ese mismo carácter. Esto permite reconocer `3.14` como un solo token NUM en lugar de emitir `3` y luego fallar con `.`.

### Tabla de transiciones (δ)

```
δ(q0, dígito)   = q1
δ(q0, punto)    = error  (punto sin dígito antes)
δ(q0, operador) = q4
δ(q0, '(')      = q5
δ(q0, ')')      = q6
δ(q1, dígito)   = q1
δ(q1, punto)    = q2
δ(q2, dígito)   = q3
δ(q3, dígito)   = q3
```

Cualquier carácter no cubierto desde q0 genera un error léxico. Los espacios se ignoran (se saltan antes de consultar la tabla).

### Alfabeto válido

`{0,1,2,3,4,5,6,7,8,9, ., +, -, *, /, (, )}`

Todo carácter fuera de este conjunto produce el error: *"Símbolo 'X' no reconocido. El alfabeto válido es: dígitos 0-9, punto '.', operadores +-*/, paréntesis ()."*

---

## 4. Paso 2 — AFN y equivalencia con AFD (`src/afn_equivalencias.py`)

### Por qué se incluye un AFN

El AFD del Paso 1 es determinista por diseño. Este módulo demuestra el concepto de **no-determinismo** construyendo un AFN que también reconoce números, y luego muestra que es equivalente a un AFD mediante la construcción de subconjuntos.

### El no-determinismo del AFN

El punto clave está en la transición desde el estado inicial `s0` al leer un dígito:

```
δ(s0, dígito) = {s1, s2}
```

El AFN puede ir simultáneamente a dos estados: `s1` (donde está reconociendo un entero) y `s2` (donde anticipa que podría venir un decimal). Esto es no-determinismo puro — un AFD nunca puede estar en dos estados a la vez.

### Estados del AFN

| Estado | Significado | ¿Acepta? |
|--------|-------------|----------|
| s0 | Inicial | No |
| s1 | Leyendo entero | Sí |
| s2 | Leyendo entero, anticipa decimal | Sí |
| s3 | Leyó punto, esperando dígitos decimales | No |
| s4 | Leyendo parte decimal | Sí |

### Construcción de subconjuntos (AFN → AFD)

El algoritmo parte del estado inicial `{s0}` y calcula, para cada posible entrada, a qué conjunto de estados del AFN llegaría simultáneamente. Cada conjunto se convierte en un estado del AFD:

| Estado AFD | Conjunto de estados AFN | ¿Acepta? |
|------------|------------------------|----------|
| A | {s0} | No |
| B | {s1, s2} | Sí |
| C | {s3} | No |
| D | {s4} | Sí |
| ∅ | {} | No |

Los estados se nombran en orden de descubrimiento (A, B, C, D...) no por tamaño del conjunto, lo que da un orden intuitivo al seguir el algoritmo.

### Minimización por particiones

El algoritmo parte de dos grupos: estados aceptores `{B, D}` y no aceptores `{A, C, ∅}`. Itera refinando los grupos: dos estados van al mismo grupo si para todo símbolo del alfabeto llevan al mismo grupo destino.

**Resultado:** el AFD obtenido ya es mínimo. Ningún par de estados puede fusionarse porque todos tienen comportamientos distintos frente a al menos un símbolo. Esto es un resultado válido — la minimización no siempre reduce; a veces confirma que el AFD ya era óptimo.

---

## 5. Paso 3 — Autómata de Pila y gramática BNF (`src/ap_sintactico.py`)

### Por qué se necesita un AP y no basta con el AFD

El AFD solo puede reconocer lenguajes regulares. Los paréntesis anidados no son un lenguaje regular — requieren "contar" cuántos `(` hay abiertos, y esa memoria no cabe en un AFD finito. El AP agrega una **pila** como memoria auxiliar, lo que lo hace más poderoso.

### Gramática BNF formal

```
<expresion> ::= <termino>
              | <expresion> '+' <termino>
              | <expresion> '-' <termino>

<termino>   ::= <factor>
              | <termino>  '*' <factor>
              | <termino>  '/' <factor>

<factor>    ::= NUM
              | '(' <expresion> ')'
              | '-' <factor>

NUM = [0-9]+ ( '.' [0-9]+ )?
```

**Precedencia codificada en la gramática:**
- `<expresion>` maneja `+` y `-` (menor precedencia)
- `<termino>` maneja `*` y `/` (mayor precedencia)
- `<factor>` maneja el menos unario y los paréntesis (mayor precedencia de todas)

La jerarquía de reglas garantiza que `3 + 4 * 2` se evalúe como `3 + (4*2) = 11` y no como `(3+4) * 2 = 14`.

### AP_Parentesis — autómata de pila explícito

Este componente implementa un AP formal con estados, pila y tabla de transiciones. Solo mira los tokens de tipo `LPAREN` y `RPAREN`:

| (Estado, Token, Tope de pila) | Acción |
|-------------------------------|--------|
| (q0, LPAREN, cualquiera) | PUSH A — apila símbolo A |
| (q1, RPAREN, A) | POP — desapila A |
| (q1, RPAREN, $) | ERROR — cierra sin haber abierto |
| (q1, fin, $) | ACEPTA — pila vacía |
| (q1, fin, A) | ERROR — quedó un ( sin cerrar |

El símbolo `$` es el fondo de pila (siempre está). El símbolo `A` representa un paréntesis abierto.

### AP_Sintactico — parser de descenso recursivo

Implementa las reglas BNF como funciones que se llaman entre sí recursivamente:

- `_expresion()` → llama a `_termino()`, luego busca `+` o `-` y vuelve a llamar
- `_termino()` → llama a `_factor()`, luego busca `*` o `/` y vuelve a llamar
- `_factor()` → consume `NUM`, o `(` + `_expresion()` + `)`, o `-` + `_factor()`

Este estilo es equivalente a un AP — la pila de llamadas del lenguaje actúa como la pila del autómata. Cuando la recursión llega al fondo y puede consumir todos los tokens, la expresión es válida.

### Errores que detecta

- Dos operadores consecutivos: `3 ++ 4` → en `_factor()` se esperaba NUM o `(` pero llegó `+`
- Operador al inicio: `* 3` → igual, `_factor()` recibe `*`
- Operador al final: `3 + 4 *` → `_factor()` llega a fin de cadena sin token
- Paréntesis sin cerrar: `(3 + 4` → `_factor()` espera `)` pero llega fin de cadena
- Paréntesis vacíos: `()` → `_factor()` espera NUM o `(` pero llega `)`

---

## 6. Paso 4 — Máquina de Turing (`src/mt_verificador.py`)

### Por qué una MT si el AP ya verifica los paréntesis

El AP ya resuelve el problema. La MT lo resuelve de forma completamente diferente — en lugar de usar una pila, **reescribe la cinta**. Esto tiene dos propósitos teóricos:

1. Demostrar que la MT puede simular lo que hace el AP (es al menos tan poderosa)
2. Mostrar el modelo más general de la jerarquía de Chomsky

### Alfabeto de cinta

| Símbolo | Significado |
|---------|-------------|
| `#` | Marcador de borde izquierdo (nunca se modifica) |
| `(` | Paréntesis que abre, sin emparejar |
| `)` | Paréntesis que cierra, sin emparejar |
| `X` | Par ya emparejado (marcado) |
| `B` | Blanco (celda vacía al final) |

### Por qué existe el marcador `#`

Sin él, cuando el cabezal está en la posición 0 e intenta moverse a la izquierda, `max(0, cabeza-1)` lo mantiene en 0 indefinidamente. El estado `q1` seguiría leyendo el mismo símbolo en bucle hasta el límite de 10.000 pasos. El `#` actúa como "pared": cuando `q1` llega a `#` sabe que no encontró `(` → rechaza. Cuando `q_verif` llega a `#` sabe que no quedó ningún `(` sin marcar → acepta.

### Algoritmo: marcado de pares de adentro hacia afuera

```
Cinta inicial: # ( ( ) ) B

Paso 1: q0 escanea derecha → encuentra primer ')' en posición 4
        Marca X → cinta: # ( ( X ) B ... espera, la posición 3 es )
        
En realidad para "(())" la cinta es: # ( ( ) ) B

q0: avanza hasta encontrar ')' (posición 3)
    Escribe X → # ( ( X ) B
    Cambia a q1, mueve izquierda

q1: retrocede buscando '(' más cercano (posición 2)
    Escribe X → # ( X X ) B
    Cambia a q0, mueve derecha

q0: avanza, salta X, encuentra ')' (posición 4)
    Escribe X → # ( X X X B
    ... espera, posición 4 es )
    Escribe X → # X X X X B (después de marcar el ( en posición 1)

q0: llega a B → cambia a q_verif, mueve izquierda

q_verif: escanea izquierda, solo encuentra X y # → ACEPTA
```

### Estados

| Estado | Función |
|--------|---------|
| q0 | Escanea derecha buscando `)` sin marcar |
| q1 | Escanea izquierda buscando `(` sin marcar |
| q_verif | Escanea izquierda verificando que no quede `(` |
| q_acepta | Estado final de aceptación |
| q_rechaza | Estado final de rechazo |

### Tabla de transiciones completa

```
(q0, #)        → (q0, #, R)         saltar borde
(q0, ()        → (q0, (, R)         saltar ( sin marcar, seguir buscando )
(q0, X)        → (q0, X, R)         saltar marcado
(q0, ))        → (q1, X, L)         encontró ) → marcar, retroceder
(q0, B)        → (q_verif, B, L)    fin de cinta → verificar

(q1, X)        → (q1, X, L)         saltar marcados
(q1, ))        → (q1, ), L)         saltar ) sin marcar
(q1, ()        → (q0, X, R)         encontró ( → marcar, reiniciar
(q1, #)        → (q_rechaza, #, R)  ) sin ( correspondiente → rechazar

(q_verif, X)   → (q_verif, X, L)    marcado → seguir revisando
(q_verif, ()   → (q_rechaza, (, R)  quedó ( sin marcar → rechazar
(q_verif, #)   → (q_acepta, #, R)   llegó al borde sin ( → aceptar
```

### Integración con expresiones matemáticas

El método `verificar_expresion()` primero tokeniza la expresión con el AFD y extrae solo los tokens `LPAREN` y `RPAREN`, construyendo una cadena pura de paréntesis (ej. `"(()"` de `"(3 + (4 * 2)"`). Luego corre la MT sobre esa cadena. Esto desacopla la MT del léxico — la MT solo ve paréntesis, nunca números ni operadores.

---

## 7. Paso 5 — Parser integrado (`src/parser.py`)

### Clase ResultadoAnalisis

Almacena el resultado completo de un análisis:

```python
resultado.expresion   # la expresión original
resultado.valida      # bool
resultado.tokens      # lista de tokens del AFD
resultado.fases       # dict con estado de cada fase: {'lexico': bool, 'sintactico': bool, 'turing': bool}
resultado.errores     # lista de dicts {posicion, mensaje, explicacion, sugerencia}
resultado.sugerencia  # sugerencia general (el primer error con sugerencia)
```

### El pipeline en `analizar()`

```python
def analizar(self, expresion):
    # Fase 1: AFD
    afd = AFD_Lexico()
    tokens, errores_lexico = afd.tokenizar(expresion)

    # Fase 2: AP + BNF
    ap = AP_Sintactico(tokens)
    errores_sintacticos = ap.validar()

    # Fase 3: MT
    mt = MT_Parentesis()
    (acepta_mt, _, mensaje_mt), _ = mt.verificar_expresion(expresion)

    # Consolidar y deduplicar errores
    ...
```

### Deduplicación de errores

Sin deduplicación, el símbolo `@` en `3 @ 4` genera el mismo error tres veces: una cuando el AFD lo detecta directamente, y dos más cuando el AP corre internamente su propio AFD. La deduplicación usa un conjunto de tuplas `(posicion, mensaje)` para filtrar duplicados antes de armar la lista final:

```python
vistos = set()
unicos = []
for e in todos_los_errores:
    clave = (e['posicion'], e['mensaje'])
    if clave not in vistos:
        vistos.add(clave)
        unicos.append(e)
```

### Enriquecimiento educativo

El diccionario `_CONTEXTO_ERRORES` mapea fragmentos de mensajes técnicos a explicaciones en lenguaje estudiante. Por ejemplo:

- `"no reconocido"` → *"El carácter marcado no forma parte del lenguaje. El AFD no tiene ninguna transición definida para ese símbolo."*
- `"dos operadores"` → *"El analizador sintáctico estaba aplicando la regla `<factor>` y encontró un operador inesperado."*
- `"sin cerrar"` → *"Cada '(' debe tener exactamente un ')' correspondiente. El AP llegó al final de la pila sin encontrarlo."*

El método `_enriquecer_error()` recorre `_CONTEXTO_ERRORES` y agrega los campos `explicacion` y `sugerencia` al dict de error si algún fragmento coincide con el mensaje técnico.

---

## 8. Paso 6 — Simulador interactivo (`simulador.py`)

### Menú de opciones

| Opción | Función | Módulo que usa |
|--------|---------|----------------|
| 1 | Analizar expresión completa | `parser.py` |
| 2 | Tabla de transiciones del AFD | `afd_lexico.py` |
| 3 | AFN + conversión + minimización | `afn_equivalencias.py` |
| 4 | Simulación del AP paso a paso | `ap_sintactico.py` |
| 5 | Simulación de la MT paso a paso | `mt_verificador.py` |
| 6 | 20 pruebas automáticas | `parser.py` (inline) |
| 7 | Gramática BNF con ejemplos | (texto estático) |
| 8 | Guía de errores comunes | (texto estático) |

### Flujo de la opción 1 (la más completa)

1. Pide una expresión al usuario
2. Corre `parser.analizar()` y muestra las tres fases con ✓ o ✗
3. Si hay errores: muestra diagnóstico detallado con Explicación y Sugerencia
4. Si es válida: ofrece ver la simulación del AP, la MT, o ambas

### Opción 5 — Detección automática del tipo de entrada

La opción 5 acepta tanto cadenas puras de paréntesis (`(())`) como expresiones matemáticas completas (`(3 + 4) * 2`). Detecta el tipo así:

```python
solo_parens = all(c in '()' for c in entrada)
```

Si es expresión completa, extrae los paréntesis con `verificar_expresion()` antes de correr la MT.

---

## 9. Paso 7 — Suite de pruebas (`pruebas.py`)

### Categorías de prueba

| Cat | Tipo | Casos | Criterio |
|-----|------|-------|---------|
| A | Expresiones válidas | 13 | `resultado.valida == True` |
| B | Errores léxicos | 5 | AFD rechaza, `resultado.valida == False` |
| C | Errores de operadores | 5 | AP rechaza, `resultado.valida == False` |
| D | Errores de paréntesis | 5 | AP o MT rechazan, `resultado.valida == False` |
| E | Casos borde | 2 | Expresión vacía, solo operador |

### Casos destacados por categoría

**Categoría A (válidos):**
- `-(-3)` — doble negación unaria (prueba recursividad de `_factor()`)
- `(((3)))` — triple anidamiento (prueba que la pila y la MT manejan profundidad arbitraria)
- `1 + 2 + 3 + 4` — asociatividad izquierda en cadena

**Categoría B (errores léxicos):**
- `3.` — punto al final sin dígitos (q2 no acepta)
- `2.  + 1` — decimal incompleto seguido de espacio y operador
- `3 + 4x` — letra pegada a número (x no tiene transición desde q1)

**Categoría C (errores de operadores):**
- `* 3 + 4` — operador binario al inicio (no hay `_factor()` que empiece con `*`)
- `/3` — igual pero con división

**Categoría D (errores de paréntesis):**
- `(3 + (4 * 2)` — paréntesis interno cerrado, externo no
- `((3 + 4) * (2 - 1)` — dos grupos internos, uno externo sin cerrar

**Categoría E (casos borde):**
- `''` — expresión vacía: el AFD produce cero tokens, el AP falla en el primer intento de consumir
- `'+'` — solo un operador binario: `_expresion()` llama `_termino()` que llama `_factor()` que recibe `+` → error

### Resultado esperado: 30/30 — 100%

---

## 10. Decisiones de diseño relevantes

### Por qué Python puro (sin librerías externas)

El requisito del TCC era demostrar los autómatas desde cero. Usar `ply`, `lark` o cualquier parser generator habría ocultado la teoría. Cada transición, cada estado y cada paso del algoritmo está explícito en el código.

### Por qué las transiciones están en diccionarios

El tutor usaba diccionarios `{(estado, símbolo): nuevo_estado}` en sus ejemplos. Se mantuvo ese estilo para que el código sea directamente comparable con la notación formal de la tabla de transiciones δ. Cada entrada del diccionario corresponde a una fila de la tabla.

### Por qué el AP formal y el parser recursivo coexisten

El `AP_Parentesis` (con pila, estados y tabla) es la demostración formal del autómata de pila teórico. El `AP_Sintactico` (descenso recursivo) es su implementación práctica equivalente. Mostrar ambos permite conectar la teoría con la práctica: el stack de llamadas de Python es la pila del AP.

### Por qué la MT corre aunque el AP ya verificó los paréntesis

La MT es independiente del AP. Cuando ambos rechazan la misma expresión, es una confirmación cruzada. Cuando el AP acepta (porque la expresión es válida), la MT también acepta — esto demuestra que los dos modelos son equivalentes para este problema, aunque el mecanismo interno sea completamente diferente.

### Por qué se deduplicaron los errores

Sin deduplicación, `3 @ 4` producía el mismo error tres veces: una del AFD directo en `parser.py` y dos del AFD interno que `AP_Sintactico` usa para tokenizar. Mostrar el mismo error repetido confunde al estudiante y hace parecer que hay múltiples problemas donde solo hay uno.

---

## 11. Estructura final de archivos

```
TCC-Teorias-Automatas/
│
├── simulador.py               ← Paso 6: entrada principal, menú interactivo
├── pruebas.py                 ← Paso 7: suite de 30 casos de prueba
├── README.md                  ← Documentación visual del repositorio
├── CONTEXTO_TECNICO.md        ← Este archivo
├── .gitignore                 ← Excluye __pycache__ y .pyc
│
└── src/
    ├── __init__.py            ← Marca src/ como paquete Python (necesario para imports)
    ├── afd_lexico.py          ← Paso 1: AFD léxico, tokenizador
    ├── afn_equivalencias.py   ← Paso 2: AFN + construcción subconjuntos + minimización
    ├── ap_sintactico.py       ← Paso 3: AP formal + parser BNF recursivo
    ├── mt_verificador.py      ← Paso 4: Máquina de Turing
    └── parser.py              ← Paso 5: pipeline integrado, enriquecimiento de errores
```

---

## 12. Cómo ejecutar cada componente de forma aislada

Cada módulo en `src/` tiene su propio bloque `if __name__ == '__main__':` con casos de prueba. Se pueden correr individualmente para ver solo ese autómata:

```bash
# Solo el AFD léxico (Paso 1)
python3 src/afd_lexico.py

# Solo el AFN y equivalencias (Paso 2)
python3 src/afn_equivalencias.py

# Solo el AP (Paso 3)
python3 src/ap_sintactico.py

# Solo la MT (Paso 4)
python3 src/mt_verificador.py

# Simulador interactivo completo (Pasos 1-6)
python3 simulador.py

# Suite de 30 pruebas automáticas (Paso 7)
python3 pruebas.py
```

---

## 13. Conexión con la jerarquía de Chomsky

El proyecto recorre la jerarquía de Chomsky de menor a mayor poder expresivo, todos aplicados al mismo problema:

| Nivel | Modelo | Lenguaje reconocido | Uso en el proyecto |
|-------|--------|--------------------|--------------------|
| Tipo 3 | AFD / AFN | Regular | Tokens: números, operadores, paréntesis |
| Tipo 2 | AP + BNF | Libre de contexto | Estructura gramatical de la expresión |
| Tipo 0 | MT | Recursivamente enumerable | Verificación de paréntesis balanceados |

**Observación importante:** los paréntesis balanceados en realidad son un lenguaje libre de contexto (Tipo 2), no Tipo 0. La MT puede reconocerlos porque es más poderosa, no porque sean exclusivos de ese nivel. Esto ilustra que los niveles superiores siempre pueden hacer lo que hacen los inferiores.
