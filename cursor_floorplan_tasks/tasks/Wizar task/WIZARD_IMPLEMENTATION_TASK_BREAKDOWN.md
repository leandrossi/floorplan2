# WIZARD_IMPLEMENTATION_TASK_BREAKDOWN.md

## 1. Objetivo

Dividir el trabajo del MVP en paquetes claros para agentes de codificación, evitando bloqueos, solapamientos y cambios innecesarios sobre la base actual.

## 2. Reglas generales

1. Trabajar sobre el proyecto existente.
2. No rehacer pipeline ni planner.
3. No agregar infraestructura nueva innecesaria.
4. Priorizar encapsulación antes que refactor profundo.
5. Toda pieza nueva debe quedar alineada con el wizard MVP.
6. Toda pantalla debe seguir la guía visual acordada.

## 3. Orden recomendado de ejecución

### Sprint 1 — Estructura base
Objetivo:
armar la base del wizard y el estado de sesión.

Entregables:
- `app.py` con state machine del wizard
- layout maestro
- stepper
- side panel
- footer de navegación
- placeholders de todas las pantallas
- `workspace_service`
- `wizard_state`

Criterios de aceptación:
- se puede navegar entre estados de manera controlada
- existe session id y workspace por sesión
- el flujo no depende todavía del pipeline real

---

### Sprint 2 — Upload y processing
Objetivo:
integrar carga real y procesamiento hasta revisión.

Entregables:
- pantalla upload funcional
- guardado de archivo en workspace
- `floorplan_processing_service`
- `pipeline_runner`
- lectura de artefactos step04
- pantalla processing con feedback visual

Criterios de aceptación:
- un archivo válido dispara el procesamiento
- se guardan artefactos en workspace
- la UI carga una vista procesada inicial

---

### Sprint 3 — Review
Objetivo:
permitir validar y corregir el plano.

Entregables:
- pantalla review
- render del plano interpretado
- herramientas mínimas de corrección
- marcado de entrada principal
- marcado de cuadro eléctrico
- `review_service`
- guardado de `review_approved.json`

Criterios de aceptación:
- no se puede avanzar sin marcadores obligatorios
- la revisión queda persistida en workspace
- la salida aprobada es reutilizable por pasos posteriores

---

### Sprint 4 — Risk y proposal
Objetivo:
separar claramente diagnóstico y propuesta.

Entregables:
- pantalla risk con mapa rojo fijo
- `risk_service`
- pantalla proposal
- `proposal_service`
- `alarm_engine_adapter`
- selector de nivel
- overlay de dispositivos

Criterios de aceptación:
- el riesgo visible no cambia al variar el nivel
- la propuesta sí cambia por nivel
- el planner se invoca usando la base actual

---

### Sprint 5 — Kit y summary
Objetivo:
cerrar el flujo con valor comercial.

Entregables:
- `kit_service`
- pantalla kit
- tarjetas comerciales
- pantalla summary
- CTA final
- mensajes de cierre

Criterios de aceptación:
- el kit refleja la propuesta generada
- el resumen es claro y accionable
- un usuario puede completar el wizard de punta a punta

## 4. Asignación sugerida por agentes

## Agente A — Estructura del wizard
Responsable de:
- `app.py`
- `wizard_state`
- navegación
- stepper
- layout compartido
- footer de acciones

No toca:
- pipeline interno
- planner
- lógica de review

---

## Agente B — Servicios de procesamiento
Responsable de:
- `workspace_service`
- `floorplan_processing_service`
- `pipeline_runner`
- `artifact_store`

No toca:
- UI de revisión
- planner

---

## Agente C — Pantalla de review
Responsable de:
- render del plano interpretado
- toolbar de corrección
- marcado de entrada principal
- marcado de cuadro eléctrico
- `review_service`
- `review_bundle_adapter`

No toca:
- lógica del pipeline
- lógica interna del planner

---

## Agente D — Diagnóstico y propuesta
Responsable de:
- `risk_service`
- `proposal_service`
- `alarm_engine_adapter`
- pantalla risk
- pantalla proposal
- selector de nivel

No toca:
- pipeline previo
- layout base ya acordado

---

## Agente E — Kit y cierre
Responsable de:
- `kit_service`
- `KitCard`
- `SummaryCard`
- pantalla kit
- pantalla summary
- CTAs finales

No toca:
- planner
- review

## 5. Contratos entre equipos

### Contrato A — `ProcessingResult`
Debe exponer al menos:
- `session_id`
- `workspace_path`
- `base_image_path`
- `review_bundle_path`
- `preview_paths`
- `status`

### Contrato B — `ReviewResult`
Debe exponer al menos:
- `approved`
- `review_approved_path`
- `main_entry`
- `electric_board`
- `corrected_preview_path`

### Contrato C — `RiskViewModel`
Debe exponer al menos:
- `base_plan_path`
- `risk_overlay_path`
- `legend`
- `summary_text`

### Contrato D — `ProposalViewModel`
Debe exponer al menos:
- `security_level`
- `devices`
- `overlay_path`
- `counts_by_type`
- `proposal_summary`

### Contrato E — `KitViewModel`
Debe exponer al menos:
- `items`
- `hero_summary`
- `cta_payload`

## 6. Tareas técnicas concretas

## 6.1 Estado y navegación
- crear enum de pantallas
- crear wizard state
- persistir estado en `st.session_state`
- bloquear saltos ilegales de etapa

## 6.2 Workspaces
- generar `session_id`
- crear carpetas base
- guardar input original
- guardar artefactos producidos
- resolver limpieza opcional

## 6.3 Ejecución del pipeline
- encapsular llamado actual
- capturar errores
- mapear outputs a objeto estable
- no dejar rutas hardcodeadas en UI

## 6.4 Revisión
- cargar artefactos visuales
- mapear colores/leyenda
- permitir correcciones mínimas
- validar marcadores obligatorios
- guardar aprobado

## 6.5 Riesgo
- generar una única vista fija de riesgo
- no vincularla al selector de nivel
- exponer texto explicativo listo para UI

## 6.6 Propuesta
- mapear selector a `min | optimal | max`
- generar overlay de dispositivos
- construir contadores simples
- exponer explicación resumida

## 6.7 Kit
- agrupar placements por tipo
- contar cantidades
- enlazar imagen/icono
- construir copy comercial simple

## 7. Riesgos y mitigaciones

### Riesgo 1
Refactor excesivo del proyecto base.

Mitigación:
mantener adaptadores y encapsulación, no reescritura.

### Riesgo 2
La review se vuelve demasiado compleja.

Mitigación:
reducir herramientas del MVP.

### Riesgo 3
Se mezcla riesgo con propuesta.

Mitigación:
pantallas separadas y contratos separados.

### Riesgo 4
Agentes pisan archivos compartidos.

Mitigación:
dividir trabajo por carpetas y contratos.

### Riesgo 5
La UI expone conceptos internos.

Mitigación:
todos los textos visibles salen de copy funcional aprobado.

## 8. Checklist final del MVP

- [ ] Wizard con flujo completo
- [ ] Session workspace funcional
- [ ] Upload real funcionando
- [ ] Processing integrado
- [ ] Review aprobable
- [ ] Entrada principal obligatoria
- [ ] Cuadro eléctrico obligatorio
- [ ] Riesgo fijo visible
- [ ] Propuesta por nivel funcionando
- [ ] Kit generado
- [ ] Resumen final usable

## 9. Criterio de cierre

El MVP se considera cerrado cuando un usuario puede:

1. subir su plano,
2. revisar la interpretación,
3. marcar los datos obligatorios,
4. ver el riesgo,
5. elegir un nivel de protección,
6. obtener una propuesta y un kit,
7. llegar a un cierre claro sin ver complejidades internas.
