# WIZARD_AGENT_MASTER_PACKAGE.md

## 1. Propósito del paquete

Este paquete consolida toda la documentación necesaria para que agentes de codificación puedan avanzar sobre el MVP del wizard sin ambigüedades, trabajando sobre la base actual del proyecto y evitando complejidad innecesaria.

El objetivo del producto es construir un **wizard visual, guiado y no técnico** para que un cliente pueda:
1. subir el plano de su vivienda,
2. validar o corregir la interpretación automática,
3. visualizar zonas vulnerables,
4. ver la propuesta de dispositivos,
5. recibir un kit recomendado.

---

## 2. Decisiones cerradas del proyecto

### Producto
- El usuario final no sabe de alarmas.
- El usuario no configura sensores manualmente.
- El usuario corrige una interpretación automática del plano.
- El wizard debe sentirse como un asesor visual.

### Riesgo y seguridad
- El mapa rojo es un diagnóstico base y se muestra una sola vez.
- El mapa rojo queda fijo como concepto visual.
- El selector de nivel solo cambia:
  - propuesta de dispositivos,
  - cantidades,
  - resumen,
  - kit.
- El selector de nivel **no** debe cambiar visualmente el mapa rojo del diagnóstico.

### Técnica
- Se trabaja sobre el proyecto actual.
- Se mantiene Python + Streamlit.
- No se agrega frontend separado.
- No se agrega backend API separado.
- No se agrega base de datos en el MVP.
- No se agregan colas ni microservicios.
- No se refactoriza el planner salvo bug puntual.
- No se rehace el pipeline `final_step01` a `final_step05`.

---

## 3. Solución técnica elegida para el MVP

La solución técnica recomendada es un **monolito modular sobre Streamlit**, apoyado en:
- estado de sesión,
- workspace por sesión,
- servicios para encapsular casos de uso,
- adaptadores para proteger a la UI del código actual,
- reutilización del pipeline y del planner existentes.

### Capas
- **UI Layer**: pantallas, componentes, tema, copy visible.
- **Application Layer**: navegación, estado, reglas de avance.
- **Domain Layer**: enums, contratos, view models, validaciones.
- **Services Layer**: procesamiento, review, riesgo, propuesta, kit, workspace.
- **Infrastructure Layer**: pipeline runner, artifact store, adapters, overlays.

---

## 4. Orden recomendado de lectura para agentes

### Paso 1
Leer: `CURSOR_AGENT_HANDOFF.md`

Objetivo:
entender reglas del proyecto, límites y decisiones que no deben discutirse.

### Paso 2
Leer: `WIZARD_MVP_ARCHITECTURE.md`

Objetivo:
entender la arquitectura objetivo, capas, servicios, adaptadores y flujo técnico general.

### Paso 3
Leer: `WIZARD_UI_SCREEN_BLUEPRINTS.md`

Objetivo:
entender cómo debe verse y sentirse el wizard, pantalla por pantalla.

### Paso 4
Leer: `WIZARD_IMPLEMENTATION_TASK_BREAKDOWN.md`

Objetivo:
entender el orden de implementación por sprints y distribución por agentes.

### Paso 5
Leer: `CURSOR_FILE_BY_FILE_TASKS.md`

Objetivo:
ejecutar tareas concretas por archivo o módulo, con criterios de aceptación claros.

### Paso 6
Leer: `MVP_ACCEPTANCE_TESTS.md`

Objetivo:
validar funcionalmente que el MVP está bien resuelto.

---

## 5. Orden recomendado de implementación

1. Estado y navegación del wizard
2. Workspace por sesión
3. Upload y procesamiento
4. Revisión visual
5. Diagnóstico fijo
6. Propuesta por nivel
7. Kit comercial
8. Resumen final

---

## 6. Estructura objetivo del proyecto

```text
src/
  app.py

  ui/
    screens/
    components/
    theme/

  application/
  domain/
  services/
  infrastructure/
```

---

## 7. Paquetes de trabajo sugeridos

### Agente A — Estructura del wizard
- app
- navegación
- estado
- layout
- stepper
- footer

### Agente B — Procesamiento
- workspace
- upload
- processing service
- pipeline runner
- artifact store

### Agente C — Review
- pantalla review
- canvas de revisión
- validación de entrada principal
- validación de cuadro eléctrico
- review service
- review bundle adapter

### Agente D — Riesgo y propuesta
- risk service
- proposal service
- alarm engine adapter
- pantalla risk
- pantalla proposal
- selector de nivel

### Agente E — Kit y cierre
- kit service
- cards
- summary
- CTA final

---

## 8. Reglas que no deben romperse

1. No exponer términos internos al usuario.
2. No llamar scripts legacy desde componentes UI.
3. No mezclar riesgo fijo con selector de nivel.
4. No transformar la revisión en un editor CAD complejo.
5. No rehacer el planner ni el pipeline.
6. No agregar infraestructura que aumente complejidad sin valor directo para el MVP.

---

## 9. Criterio general de calidad

El trabajo está bien hecho cuando:
- mejora el wizard sin aumentar complejidad innecesaria,
- reutiliza el proyecto actual,
- mantiene separación clara entre diagnóstico y propuesta,
- ofrece una UI clara para usuario no técnico,
- deja contratos y servicios estables para seguir iterando.

---

## 10. Contenido del paquete

### Arquitectura
- `WIZARD_MVP_ARCHITECTURE.md`

### UI y pantallas
- `WIZARD_UI_SCREEN_BLUEPRINTS.md`

### Plan de implementación
- `WIZARD_IMPLEMENTATION_TASK_BREAKDOWN.md`

### Guía para Cursor
- `CURSOR_AGENT_HANDOFF.md`

### Tareas por archivo
- `CURSOR_FILE_BY_FILE_TASKS.md`

### Pruebas de aceptación
- `MVP_ACCEPTANCE_TESTS.md`

---

## 11. Uso recomendado del paquete

### Si trabaja una sola persona
Seguir el orden de lectura recomendado y luego implementar por sprints.

### Si trabajan varios agentes
1. compartir este documento maestro,
2. repartir trabajo por paquete,
3. respetar contratos entre capas,
4. validar con `MVP_ACCEPTANCE_TESTS.md` antes de cerrar cada entrega.

---

## 12. Entregable final esperado

Un MVP en el que un usuario pueda:
1. subir un plano,
2. revisar la interpretación,
3. marcar datos obligatorios,
4. ver un diagnóstico fijo de riesgo,
5. elegir nivel de protección,
6. obtener una propuesta y un kit,
7. cerrar el flujo sin ver complejidades internas.

---
Generado automáticamente para consolidar el paquete maestro del wizard.
