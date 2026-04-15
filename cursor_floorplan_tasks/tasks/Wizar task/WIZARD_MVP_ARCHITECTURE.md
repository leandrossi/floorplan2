# WIZARD_MVP_ARCHITECTURE.md

## 1. Objetivo

Construir un wizard visual y guiado para que un cliente sin conocimientos técnicos pueda:

1. subir el plano de su vivienda,
2. validar o corregir la interpretación automática,
3. visualizar las zonas vulnerables,
4. ver la propuesta de dispositivos,
5. recibir un kit recomendado.

## 2. Decisiones cerradas del MVP

### 2.1 Decisiones funcionales
- El usuario **no configura sensores manualmente**.
- El usuario **corrige una interpretación automática** del plano.
- Las **áreas rojas se muestran una sola vez como diagnóstico base**.
- El selector de nivel (`min`, `optimal`, `max`) **solo cambia la propuesta de dispositivos y el kit**.
- El wizard debe sentirse como un **asesor visual**, no como una herramienta de ingeniería.

### 2.2 Decisiones técnicas
- Se trabaja **sobre el proyecto actual**.
- No se rehace el pipeline `final_step01` a `final_step05`.
- No se modifica el core de `vendor/acala_engine` salvo bug concreto.
- Se mantiene **Python + Streamlit** como base del MVP.
- No se agrega backend separado, base de datos, colas, microservicios ni frontend independiente.
- Se encapsula la lógica existente en **servicios y adaptadores** para bajar acoplamiento.

## 3. Principio rector

El MVP debe priorizar:

- **baja complejidad técnica**,
- **máximo reaprovechamiento del código actual**,
- **ordenamiento por capas**,
- **flujo guiado con estado controlado**.

## 4. Componentes existentes que deben reutilizarse

### Pipeline
- `final_step01_parse_and_rasterize.py`
- `final_step02_classify_space.py`
- `final_step03_assign_rooms.py`
- `final_step04_build_matrix_csv.py`
- `final_step05_plan_alarm.py`

### Planner
- `vendor/acala_engine/`

### Artefactos
- `review_bundle.json`
- `review_approved.json`
- outputs bajo `output/final/...`

### Wizard actual
- `wizard_app.py`
- `ui_components.py`

## 5. Componentes que NO deben tocarse en esta fase

No tocar salvo error puntual:
- reglas internas del `acala_engine`,
- mapeo lógico de `security_level`,
- contratos base del pipeline ya aprobados,
- convenciones internas de matrices y artefactos del pipeline.

## 6. Arquitectura recomendada

### 6.1 Tipo de solución
Monolito modular sobre Streamlit.

### 6.2 Capas

#### UI Layer
Responsable de:
- pantallas,
- navegación,
- stepper,
- side panel,
- mensajes,
- validaciones visibles,
- render del plano.

#### Application Layer
Responsable de:
- orquestación del wizard,
- avance de etapas,
- estado de sesión,
- llamadas a servicios,
- control de errores funcionales.

#### Domain Layer
Responsable de:
- modelos,
- enums,
- contratos,
- validadores,
- view models para la UI.

#### Infrastructure Layer
Responsable de:
- ejecutar pipeline existente,
- leer y escribir artefactos,
- adaptar review bundle,
- llamar planner,
- gestionar workspace de sesión.

## 7. Estructura propuesta del proyecto

```text
src/
  app.py

  ui/
    screens/
      intro.py
      upload.py
      processing.py
      review.py
      risk.py
      proposal.py
      kit.py
      summary.py
    components/
      stepper.py
      side_panel.py
      plan_canvas.py
      legend.py
      status_banner.py
      kit_cards.py
      action_footer.py
    theme/
      tokens.py
      styles.py

  application/
    wizard_controller.py
    wizard_state.py
    navigation.py

  domain/
    models.py
    enums.py
    contracts.py
    validators.py
    view_models.py

  services/
    floorplan_processing_service.py
    review_service.py
    risk_service.py
    proposal_service.py
    kit_service.py
    workspace_service.py

  infrastructure/
    pipeline_runner.py
    artifact_store.py
    review_bundle_adapter.py
    alarm_engine_adapter.py
    image_overlay_adapter.py
```

## 8. Estado del wizard

Usar un state machine simple en sesión:

- `intro`
- `upload`
- `processing`
- `review`
- `risk`
- `proposal`
- `kit`
- `summary`

### Regla
No usar navegación libre entre pantallas en el MVP.
El avance debe estar gobernado por validaciones.

## 9. Workspace por sesión

### Objetivo
Aislar procesamiento y artefactos por usuario/sesión.

### Estructura sugerida

```text
workspaces/
  session_<uuid>/
    input/
    processing/
    review/
    proposal/
    exports/
```

### Guardar en workspace
- archivo subido,
- outputs del pipeline,
- `review_bundle.json`,
- `review_approved.json`,
- propuesta generada,
- imágenes auxiliares,
- resumen exportable.

## 10. Servicios del MVP

### 10.1 `floorplan_processing_service`
Responsable de:
- recibir el archivo subido,
- guardarlo en workspace,
- ejecutar pipeline existente hasta step04,
- devolver un `ProcessingResult`.

### 10.2 `review_service`
Responsable de:
- cargar `review_bundle.json`,
- aplicar correcciones,
- marcar entrada principal,
- marcar cuadro eléctrico,
- guardar `review_approved.json`,
- validar consistencia para avanzar.

### 10.3 `risk_service`
Responsable de:
- construir la vista de diagnóstico base,
- generar overlay de áreas rojas,
- exponer explicaciones simples para la UI.

### 10.4 `proposal_service`
Responsable de:
- ejecutar propuesta de instalación según nivel,
- recibir `min | optimal | max`,
- devolver `ProposalViewModel`,
- no recalcular ni redibujar un mapa rojo “variable”.

### 10.5 `kit_service`
Responsable de:
- agrupar dispositivos,
- contar cantidades,
- generar tarjetas comerciales,
- construir resumen del kit.

### 10.6 `workspace_service`
Responsable de:
- crear sesión,
- resolver paths,
- limpiar temporales,
- persistir outputs del wizard.

## 11. Adaptadores necesarios

### `pipeline_runner`
Envuelve la ejecución del pipeline actual.
Debe devolver resultados útiles a la aplicación sin que la UI conozca scripts ni rutas internas.

### `review_bundle_adapter`
Transforma artefactos de revisión actuales a un modelo usable por la UI.

### `alarm_engine_adapter`
Envuelve la llamada al planner y traduce la salida a un modelo de propuesta usable por pantalla.

### `artifact_store`
Centraliza lectura/escritura de JSON, imágenes, matrices y previews.

### `image_overlay_adapter`
Construye overlays visuales para:
- plano interpretado,
- áreas rojas,
- dispositivos.

## 12. Flujo técnico completo

1. Usuario entra al wizard.
2. Se crea o recupera `session_id`.
3. Usuario sube archivo.
4. `floorplan_processing_service` guarda archivo y corre pipeline hasta step04.
5. Se carga `review_bundle`.
6. Usuario corrige/valida plano.
7. `review_service` guarda `review_approved`.
8. `risk_service` genera diagnóstico visual fijo.
9. Usuario elige nivel en pantalla de propuesta.
10. `proposal_service` ejecuta planner con el nivel.
11. `kit_service` arma kit comercial.
12. Se muestra resumen final.

## 13. Contratos funcionales entre capas

### Processing -> Review
Debe entregar:
- imagen/plano base,
- interpretación visible,
- leyenda de tipos,
- datos de edición necesarios.

### Review -> Risk
Debe entregar:
- plano corregido,
- entrada principal,
- cuadro eléctrico,
- validación aprobada.

### Risk -> Proposal
Debe entregar:
- plano corregido,
- marcador de riesgo base,
- nivel seleccionado.

### Proposal -> Kit
Debe entregar:
- placements por tipo,
- cantidades,
- metadata mínima para copy y tarjetas.

## 14. Validaciones mínimas

### Upload
- formato válido,
- archivo legible,
- tamaño aceptable.

### Review
No avanzar sin:
- confirmación del plano,
- entrada principal,
- cuadro eléctrico.

### Proposal
No avanzar si:
- no existe propuesta válida,
- el planner devuelve error inconsistente.

## 15. Manejo de errores

### Errores esperables
- plano ilegible,
- procesamiento incompleto,
- marcadores faltantes,
- propuesta no generable,
- artefactos faltantes en workspace.

### Regla UX
Todo error debe mostrar:
- qué pasó,
- qué puede hacer el usuario,
- cómo seguir.

## 16. Orden de implementación

### Ola 1
- state machine,
- shell del wizard,
- estructura de pantallas,
- workspace de sesión.

### Ola 2
- procesamiento y carga de artefactos,
- pantalla de upload,
- pantalla de processing.

### Ola 3
- revisión visual,
- marcado de entrada principal,
- marcado de cuadro eléctrico,
- guardado aprobado.

### Ola 4
- diagnóstico de riesgo fijo,
- propuesta por nivel,
- integración con planner.

### Ola 5
- kit,
- resumen,
- CTA final,
- pulido de validaciones y mensajes.

## 17. Lo que queda fuera del MVP

- dibujo total desde cero,
- editor CAD avanzado,
- frontend separado en React,
- backend API independiente,
- base de datos,
- cola de jobs,
- compra online,
- CRM,
- colaboración multiusuario.

## 18. Definition of done del MVP

El MVP está listo cuando:
- un usuario puede completar el wizard de punta a punta,
- el plano se procesa usando la base actual,
- puede revisar y corregir lo necesario,
- ve un diagnóstico fijo de riesgo,
- puede generar propuesta por nivel,
- recibe un kit claro y entendible,
- todo ocurre sin exponer términos técnicos internos.
