# WIZARD_UI_SCREEN_BLUEPRINTS.md

## 1. Dirección visual general

### Posicionamiento visual
La interfaz debe sentirse como:
- un **asesor visual premium**,
- una experiencia **calma, clara y moderna**,
- una herramienta para personas sin conocimiento técnico.

### Sensación buscada
- tranquilidad,
- confianza,
- simplicidad,
- guía paso a paso,
- mucha claridad visual.

### Sensación a evitar
- dashboard técnico,
- software corporativo pesado,
- herramienta de ingeniería,
- editor complejo tipo CAD.

## 2. Principios visuales

1. El plano es el protagonista.
2. La ayuda va en un panel lateral.
3. Hay una acción principal por pantalla.
4. El progreso es visible en todo momento.
5. El rojo se reserva para riesgo y alertas.
6. El lenguaje visual debe ser residencial, no industrial.

## 3. Layout maestro

```text
┌──────────────────────────────────────────────────────────────┐
│ Header liviano + stepper                                    │
├──────────────────────────────────────────────────────────────┤
│ Canvas principal                         Panel lateral       │
│ 70% - 75%                                25% - 30%          │
│                                                             │
│ plano / visual central                    título etapa      │
│ overlays                                  ayuda             │
│ zoom / herramientas                       checklist         │
│                                           validaciones      │
│                                           CTA               │
├──────────────────────────────────────────────────────────────┤
│ Footer con navegación                                         │
└──────────────────────────────────────────────────────────────┘
```

## 4. Guía visual del sistema

### Colores
- fondo general claro
- superficies blancas
- acento azul profundo / índigo suave
- verde suave para éxito
- ámbar suave para advertencia
- rojo translúcido solo para riesgo

### Tipografía
- títulos grandes y limpios
- texto corto
- poco bloque de lectura
- mucha jerarquía visual

### Bordes y superficies
- radio generoso
- cards grandes
- sombras suaves
- mucho aire

### Iconografía
- lineal y moderna
- consistente en todo el flujo
- evitar íconos técnicos complejos

## 5. Pantallas

## Pantalla 1. Intro

### Objetivo
Explicar el proceso con muy poca fricción.

### Estructura
- header simple
- título principal
- video corto o animación del proceso
- 3 beneficios resumidos
- CTA principal: `Comenzar`

### Contenido sugerido
Título:
`Protegé tu casa en pocos pasos`

Subtítulo:
`Subí tu plano, revisá lo que interpretamos y te mostramos la protección recomendada.`

Beneficios:
- No necesitás conocimientos técnicos
- Vas a ver tu plano de forma visual
- Recibís una propuesta personalizada

### Regla
No convertir esta pantalla en una landing comercial.

---

## Pantalla 2. Upload

### Objetivo
Hacer que subir el plano sea trivial.

### Estructura
- título de etapa
- dropzone grande
- formatos admitidos
- ejemplos visuales de plano correcto
- CTA para continuar luego de carga válida

### Componentes
- `UploadDropzone`
- `ExampleCard`
- `HelpHint`

### Mensajes
- `Podés subir una imagen o PDF`
- `Si algo no se interpreta bien, después lo vas a poder corregir`

### Regla
El usuario no debe sentirse evaluado; debe sentirse acompañado.

---

## Pantalla 3. Processing

### Objetivo
Mostrar que el sistema está entendiendo la casa.

### Estructura
- plano real del usuario en el centro
- overlay animado de escaneo
- estados de procesamiento
- barra de progreso por etapas

### Estados visuales sugeridos
- Detectando paredes
- Detectando puertas y ventanas
- Preparando revisión
- Generando vista inicial

### Componentes
- `ProcessingCanvas`
- `ProgressPhases`
- `StatusChipRow`

### Regla
No usar solo spinner.
Tiene que existir una sensación de trabajo real sobre el plano.

---

## Pantalla 4. Review

### Objetivo
Permitir corrección simple de la interpretación automática.

### Estructura
Canvas central:
- plano interpretado
- overlays suaves de muro, puerta, ventana, libre
- zoom y pane mínimos
- toolbar simple

Panel lateral:
- título
- explicación breve
- checklist
- CTA de confirmación

### Herramientas del MVP
- marcar muro
- marcar puerta
- marcar ventana
- marcar espacio libre
- marcar entrada principal
- marcar cuadro eléctrico

### Herramientas excluidas
- dibujo libre complejo
- edición geométrica avanzada
- edición CAD

### Checklist lateral
- Paredes correctas
- Puertas correctas
- Ventanas correctas
- Entrada principal marcada
- Cuadro eléctrico marcado

### Regla crítica
El usuario corrige, no redibuja.

---

## Pantalla 5. Risk

### Objetivo
Mostrar vulnerabilidad del plano de forma clara.

### Estructura
Canvas central:
- plano validado
- overlay rojo translúcido
- posible leyenda de riesgo

Panel lateral:
- título
- explicación humana del diagnóstico
- texto breve sobre accesos y puntos a cubrir
- CTA `Ver solución`

### Contenido importante
Este mapa de riesgo es **fijo**.
No cambia al modificar mínimo / óptimo / máximo.

### Regla crítica
Esta pantalla muestra el problema.
No mezclar con selector de nivel.

---

## Pantalla 6. Proposal

### Objetivo
Mostrar la solución sobre el plano.

### Estructura
Canvas central:
- plano validado
- iconos de dispositivos
- pequeños labels o tooltips opcionales

Panel lateral:
- selector de nivel
- resumen de cantidades
- explicación breve
- CTA `Ver kit`

### Selector
Usar control segmentado:
- Básico
- Recomendado
- Máximo

Mapeo interno:
- Básico -> `min`
- Recomendado -> `optimal`
- Máximo -> `max`

### Regla crítica
Al cambiar el nivel:
- cambia la propuesta de dispositivos,
- cambia el kit,
- no cambian las áreas rojas visibles del paso anterior.

---

## Pantalla 7. Kit

### Objetivo
Traducir propuesta técnica a propuesta comercial entendible.

### Estructura
- título
- subtítulo breve
- grilla de tarjetas
- CTA principal

### Tarjetas
Cada tarjeta debe mostrar:
- imagen o ícono del componente
- nombre amigable
- cantidad
- una línea de propósito

### Ejemplos de copy
- `Sensor magnético — protege accesos exteriores`
- `Sensor de movimiento — cubre áreas de circulación`
- `Teclado — permite activar y desactivar la alarma`

### Regla
No mostrar especificaciones técnicas profundas en MVP.

---

## Pantalla 8. Summary

### Objetivo
Cerrar el flujo y dejar una acción clara.

### Estructura
- miniatura del plano final
- resumen ejecutivo
- resumen del kit
- CTA final

### CTAs posibles
- Solicitar este kit
- Descargar resumen
- Hablar con un asesor

### Regla
Debe sentirse como cierre comercial claro, no como fin de un procesamiento técnico.

## 6. Componentes base a construir

### Navegación
- `WizardStepper`
- `ActionFooter`
- `BackButton`
- `PrimaryCTA`

### Layout
- `ScreenLayout`
- `CanvasPanel`
- `SidePanel`

### Feedback
- `StatusBanner`
- `InlineValidation`
- `ProgressPhases`
- `HelpHint`

### Plano
- `PlanCanvas`
- `Legend`
- `OverlayToggle`
- `ToolSelector`

### Comercial
- `KitCard`
- `SummaryCard`
- `SecurityLevelSelector`

## 7. Reglas visuales que no deben romperse

1. No usar rojo como color general del producto.
2. No llenar el canvas con texto.
3. No usar una sidebar izquierda pesada.
4. No hacer pantallas densas en información.
5. No exponer nombres técnicos internos.
6. No convertir revisión en una experiencia tipo AutoCAD.

## 8. Tono de copy

### Debe sonar
- claro,
- tranquilo,
- profesional,
- guiado.

### No debe sonar
- robótico,
- excesivamente técnico,
- alarmista,
- burocrático.

### Ejemplos
- `Estamos analizando la distribución de tu casa`
- `Revisá lo que interpretamos y corregí solo si hace falta`
- `Estas son las áreas que necesitan protección`
- `Este es el kit recomendado para tu plano`

## 9. Definition of done visual

La UI está bien resuelta cuando:
- el usuario entiende el siguiente paso sin pensar demasiado,
- el plano siempre es el elemento principal,
- el progreso está claro,
- la revisión es simple,
- el diagnóstico genera confianza,
- la propuesta se siente lógica,
- el kit se entiende sin conocimientos técnicos.
