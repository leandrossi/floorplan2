# CURSOR_FILE_BY_FILE_TASKS.md

## 1. Objetivo

Definir tareas operativas por archivo o módulo esperado, usando el formato:

- propósito,
- hacer,
- no hacer,
- criterio de aceptación.

---

## 2. `src/app.py`

### Propósito
Punto de entrada único del wizard.

### Hacer
- inicializar sesión,
- cargar estado del wizard,
- renderizar pantalla actual,
- usar controlador central,
- mantener navegación ordenada.

### No hacer
- no poner lógica de procesamiento pesada,
- no parsear artefactos,
- no ejecutar pipeline directamente,
- no mezclar demasiado render con reglas de negocio.

### Aceptación
- el wizard abre en pantalla `intro`,
- puede cambiar de estado correctamente,
- no contiene lógica dispersa de dominio.

---

## 3. `src/application/wizard_state.py`

### Propósito
Representar el estado vivo del wizard en sesión.

### Hacer
- definir estado de pantalla actual,
- guardar `session_id`,
- guardar paths relevantes,
- guardar selección de nivel,
- registrar si review está aprobada.

### No hacer
- no meter lógica de render,
- no meter acceso directo a archivos,
- no meter lógica del planner.

### Aceptación
- el estado es serializable o fácilmente persistible,
- soporta reruns sin perder continuidad,
- centraliza el estado funcional del flujo.

---

## 4. `src/application/wizard_controller.py`

### Propósito
Orquestar el avance del wizard.

### Hacer
- definir reglas de avance y retroceso,
- validar prerequisitos por pantalla,
- llamar servicios correctos,
- manejar transiciones limpias.

### No hacer
- no construir UI,
- no llamar scripts legacy desde acá,
- no hacer parsing directo de JSON legacy.

### Aceptación
- no se puede saltar de `upload` a `proposal` sin review,
- las reglas de avance están en un solo lugar,
- los errores funcionales se controlan desde este nivel.

---

## 5. `src/domain/enums.py`

### Propósito
Definir enums del dominio.

### Hacer
- enum de pantallas,
- enum de nivel de seguridad,
- enum de estados de procesamiento,
- enum de tipos visuales necesarios.

### No hacer
- no poner strings mágicos dispersos por todo el proyecto.

### Aceptación
- UI y servicios usan enums consistentes.

---

## 6. `src/domain/contracts.py`

### Propósito
Definir contratos estables entre capas.

### Hacer
- `ProcessingResult`
- `ReviewResult`
- `RiskViewModel`
- `ProposalViewModel`
- `KitViewModel`

### No hacer
- no mezclar contratos internos legacy con contratos de UI,
- no dejar campos ambiguos sin propósito.

### Aceptación
- todos los servicios devuelven objetos consistentes y predecibles.

---

## 7. `src/services/workspace_service.py`

### Propósito
Gestionar workspace por sesión.

### Hacer
- crear `session_id`,
- crear carpetas base,
- resolver paths,
- persistir archivos de sesión,
- exponer helpers simples.

### No hacer
- no mezclarlo con pipeline ni review,
- no poner lógica visual.

### Aceptación
- cada sesión tiene carpeta propia,
- los archivos se guardan de forma consistente,
- no hay colisiones entre sesiones.

---

## 8. `src/services/floorplan_processing_service.py`

### Propósito
Encapsular el procesamiento del plano hasta step04.

### Hacer
- recibir archivo,
- guardarlo,
- invocar `pipeline_runner`,
- capturar errores,
- devolver `ProcessingResult`.

### No hacer
- no renderizar progreso visual,
- no exponer detalles de scripts legacy,
- no resolver review aquí.

### Aceptación
- con un archivo válido produce artefactos reutilizables por review,
- ante error devuelve estado claro y controlado.

---

## 9. `src/infrastructure/pipeline_runner.py`

### Propósito
Ejecutar pipeline actual.

### Hacer
- envolver ejecución de scripts existentes,
- devolver status, outputs y errores,
- centralizar rutas y dependencias.

### No hacer
- no cambiar la lógica interna de `final_step01` a `final_step05`,
- no dejar hardcodes visibles hacia la UI.

### Aceptación
- puede correrse desde el servicio sin acoplar la UI al legacy,
- los errores quedan claramente capturados.

---

## 10. `src/services/review_service.py`

### Propósito
Gestionar revisión del plano.

### Hacer
- cargar `review_bundle`,
- aplicar correcciones del usuario,
- validar entrada principal,
- validar cuadro eléctrico,
- guardar `review_approved`.

### No hacer
- no convertir esto en un editor CAD,
- no meter validaciones visuales dentro del servicio.

### Aceptación
- no se puede aprobar review sin marcadores obligatorios,
- deja una salida usable por riesgo y propuesta.

---

## 11. `src/infrastructure/review_bundle_adapter.py`

### Propósito
Traducir artefactos actuales de review a un formato amigable.

### Hacer
- normalizar datos de review,
- exponer preview, leyenda y estructura para la UI,
- preparar patch payloads simples.

### No hacer
- no dejar que la UI manipule directamente el JSON legacy.

### Aceptación
- la pantalla review puede renderizar y guardar cambios sin conocer estructura interna del repo actual.

---

## 12. `src/services/risk_service.py`

### Propósito
Generar la vista fija de riesgo.

### Hacer
- construir overlay de áreas rojas base,
- preparar resumen explicativo,
- devolver `RiskViewModel`.

### No hacer
- no depender del selector de nivel,
- no modificar la propuesta,
- no recalcular riesgo diferente según `min/optimal/max`.

### Aceptación
- el mapa rojo queda fijo entre visitas de la pantalla,
- la salida es usable directamente por la UI.

---

## 13. `src/services/proposal_service.py`

### Propósito
Generar la propuesta de dispositivos según nivel.

### Hacer
- recibir nivel,
- invocar planner vía adapter,
- devolver placements, counts y resumen.

### No hacer
- no mezclar esta lógica con la de riesgo,
- no cambiar el mapa rojo base,
- no exponer `acala_engine` a la UI.

### Aceptación
- al cambiar el nivel cambian dispositivos y kit,
- el diagnóstico visual previo permanece conceptualmente estable.

---

## 14. `src/infrastructure/alarm_engine_adapter.py`

### Propósito
Encapsular el acceso al planner actual.

### Hacer
- mapear inputs desde review aprobada,
- invocar planner,
- transformar salida a objetos de propuesta.

### No hacer
- no tocar reglas internas del planner salvo bug real.

### Aceptación
- la propuesta sale usando la base existente,
- el resto del sistema no depende de detalles internos del engine.

---

## 15. `src/services/kit_service.py`

### Propósito
Construir el kit comercial a partir de la propuesta.

### Hacer
- agrupar por tipo,
- contar cantidades,
- crear copy corto,
- devolver tarjetas renderizables.

### No hacer
- no meter pricing,
- no meter integración comercial compleja,
- no mostrar detalles técnicos profundos.

### Aceptación
- el kit se entiende sin conocimiento técnico,
- cada item tiene razón de uso y cantidad.

---

## 16. `src/ui/screens/*.py`

### Propósito
Renderizar pantallas del wizard.

### Hacer
- usar layout maestro,
- mostrar título, ayuda y CTA,
- renderizar view models,
- mantener copy simple.

### No hacer
- no meter lógica pesada,
- no parsear artefactos,
- no llamar pipeline/planner directamente.

### Aceptación
- cada pantalla cumple un solo objetivo,
- la UI se mantiene limpia y consistente.

---

## 17. `src/ui/components/plan_canvas.py`

### Propósito
Render central del plano y overlays.

### Hacer
- mostrar plano base,
- superponer overlays,
- exponer herramientas mínimas para review,
- permitir zoom y pane básicos.

### No hacer
- no intentar resolver un editor completo,
- no mezclarlo con lógica del wizard.

### Aceptación
- el usuario puede revisar el plano con claridad,
- las interacciones son mínimas pero suficientes.

---

## 18. `src/ui/components/security_level_selector.py`

### Propósito
Seleccionar nivel de seguridad.

### Hacer
- mostrar control segmentado,
- mapear a `min/optimal/max`,
- disparar actualización de propuesta.

### No hacer
- no modificar la pantalla de riesgo,
- no recalcular visualmente áreas rojas.

### Aceptación
- cambiar de nivel refresca propuesta y kit,
- no cambia el diagnóstico base.

---

## 19. `src/ui/components/kit_cards.py`

### Propósito
Mostrar el kit recomendado.

### Hacer
- tarjetas grandes,
- cantidad visible,
- nombre amigable,
- breve explicación.

### No hacer
- no usar formato técnico de catálogo industrial,
- no saturar con texto.

### Aceptación
- el kit se entiende de un vistazo.

---

## 20. `src/ui/theme/*`

### Propósito
Centralizar tokens visuales.

### Hacer
- colores,
- spacing,
- radius,
- tipografía,
- elevaciones.

### No hacer
- no hardcodear estilos en cada pantalla.

### Aceptación
- la experiencia visual es consistente en todo el wizard.
