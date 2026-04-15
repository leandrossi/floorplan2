# CURSOR_AGENT_HANDOFF.md

## 1. Objetivo de este documento

Este documento traduce la especificación funcional y visual del wizard a una guía operativa para agentes de codificación trabajando en Cursor.

Su propósito es evitar:
- refactors innecesarios,
- cambios sobre el core actual,
- ambigüedad en la implementación,
- desalineación entre UI, flujo y planner.

## 2. Regla principal del proyecto

Este MVP **no reemplaza** el proyecto actual.

Este MVP debe:
- trabajar sobre el wizard y pipeline existentes,
- encapsular lo actual,
- mejorar experiencia, orden y claridad,
- mantener la lógica estable del planner.

## 3. Decisiones cerradas que no se discuten

### Producto
- El usuario final no sabe de alarmas.
- El usuario no configura sensores manualmente.
- El usuario valida una interpretación automática del plano.
- El wizard debe sentirse como un asesor visual.

### Riesgo y seguridad
- El mapa de riesgo se muestra una sola vez.
- El mapa rojo es diagnóstico base y queda fijo.
- El selector de nivel solo cambia:
  - propuesta de dispositivos,
  - resumen,
  - kit.
- El selector de nivel NO cambia en vivo las áreas rojas visibles.

### Técnica
- Base técnica: Python + Streamlit.
- No crear frontend separado.
- No crear backend API separado.
- No usar base de datos en el MVP.
- No usar colas ni microservicios.
- No refactorizar el planner salvo bug puntual.
- No rehacer `final_step01` a `final_step05`.

## 4. Regla de oro para cualquier agente

Antes de tocar cualquier archivo, el agente debe preguntarse:

1. ¿Esto reutiliza lo ya construido?
2. ¿Esto reduce complejidad o la aumenta?
3. ¿Esto expone al usuario algo técnico que no debería ver?
4. ¿Esto rompe la separación entre diagnóstico y propuesta?

Si la respuesta es problemática, no avanzar por ese camino.

## 5. Orden correcto de implementación

1. Estado y navegación del wizard
2. Workspace por sesión
3. Upload y procesamiento
4. Revisión visual
5. Diagnóstico fijo
6. Propuesta por nivel
7. Kit comercial
8. Resumen final

No implementar primero:
- compra,
- CRM,
- integraciones externas,
- dibujo manual completo,
- rediseño del planner,
- rediseño del pipeline.

## 6. Estructura objetivo

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

## 7. Responsabilidad de carpetas

### `ui/`
Todo lo visible para el usuario:
- pantallas,
- layout,
- componentes,
- tema,
- copy visible.

### `application/`
Control del flujo:
- navegación,
- estado,
- pasos,
- control de avance.

### `domain/`
Modelos estables:
- enums,
- contratos,
- view models,
- validaciones puras.

### `services/`
Casos de uso del wizard:
- procesamiento,
- review,
- riesgo,
- propuesta,
- kit,
- workspace.

### `infrastructure/`
Puente con el proyecto ya existente:
- pipeline runner,
- lectura/escritura de artefactos,
- adaptadores,
- overlays,
- planner adapter.

## 8. Cómo debe pensar Cursor al implementar

### Hacer
- encapsular scripts existentes,
- normalizar outputs a view models,
- simplificar nombres internos,
- diseñar pantallas limpias,
- usar validaciones claras,
- separar bien las etapas del wizard.

### No hacer
- pasar lógica pesada a la UI,
- llamar scripts directamente desde componentes visuales,
- mezclar estados del wizard con render de widgets,
- exponer rutas internas,
- llenar la app de `if/else` dispersos sin controlador central,
- mezclar riesgo fijo con selector de nivel.

## 9. Regla para la UI

La UI debe parecer:
- simple,
- premium,
- tranquila,
- visual.

No debe parecer:
- técnica,
- experimental,
- corporativa pesada,
- editor tipo CAD.

## 10. Regla para las pantallas

Cada pantalla debe tener:
- un objetivo claro,
- una sola acción principal,
- validaciones entendibles,
- progreso visible.

## 11. Regla para servicios

Cada servicio debe tener:
- una única responsabilidad,
- inputs claros,
- outputs predecibles,
- errores controlados.

## 12. Regla para adaptadores

Los adaptadores existen para proteger a la UI del proyecto legacy.

Por lo tanto:
- la UI nunca debería saber de `final_step04_build_matrix_csv.py`,
- la UI nunca debería parsear manualmente `output/final/...`,
- la UI nunca debería hablar directamente con `acala_engine`.

Todo eso debe vivir en `infrastructure/` + `services/`.

## 13. Qué revisar antes de dar por terminado un cambio

Antes de cerrar una tarea, el agente debe verificar:

- que el flujo del wizard no se rompió,
- que el cambio no alteró el mapa de riesgo base,
- que el selector de nivel sigue afectando solo propuesta/kit,
- que el usuario no ve términos internos,
- que el workspace guarda correctamente artefactos,
- que hay criterio de aceptación verificable.

## 14. Definition of done general

El trabajo está bien hecho cuando:
- mejora el wizard sin aumentar complejidad innecesaria,
- reutiliza la base actual,
- mantiene coherencia funcional y visual,
- deja una interfaz clara para usuario no técnico.
