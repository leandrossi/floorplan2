# MVP_ACCEPTANCE_TESTS.md

## 1. Objetivo

Definir las pruebas funcionales mínimas que deben pasar antes de considerar usable el MVP del wizard.

---

## 2. Caso 1 — Inicio del flujo

### Escenario
Un usuario entra por primera vez al wizard.

### Resultado esperado
- ve pantalla de introducción,
- entiende que el flujo tiene pasos,
- existe un CTA claro para comenzar.

### Falla si
- cae en una pantalla técnica,
- no se entiende el próximo paso,
- hay elementos del pipeline visibles.

---

## 3. Caso 2 — Upload válido

### Escenario
El usuario sube un archivo válido.

### Resultado esperado
- el archivo se acepta,
- se guarda en workspace,
- el wizard pasa a procesamiento,
- no se rompe la sesión.

### Falla si
- el archivo se pierde,
- no se guarda correctamente,
- el flujo vuelve al inicio sin explicación.

---

## 4. Caso 3 — Processing

### Escenario
Se ejecuta el procesamiento.

### Resultado esperado
- la pantalla muestra estado visual útil,
- el usuario entiende que se está analizando su plano,
- al finalizar queda disponible una vista inicial.

### Falla si
- solo hay spinner sin contexto,
- no hay feedback,
- termina sin salida de revisión.

---

## 5. Caso 4 — Review sin marcadores

### Escenario
El usuario intenta avanzar sin marcar entrada principal o cuadro eléctrico.

### Resultado esperado
- el wizard bloquea el avance,
- muestra mensaje claro,
- indica qué falta completar.

### Falla si
- permite avanzar igual,
- muestra error técnico incomprensible.

---

## 6. Caso 5 — Review aprobada

### Escenario
El usuario revisa y confirma el plano correctamente.

### Resultado esperado
- se guarda `review_approved`,
- la sesión conserva estado aprobado,
- el flujo puede pasar a riesgo.

### Falla si
- se pierde la aprobación al recargar,
- no queda persistido el resultado.

---

## 7. Caso 6 — Riesgo fijo

### Escenario
El usuario entra a la pantalla de riesgo y luego cambia de nivel en propuesta.

### Resultado esperado
- el mapa de riesgo se mantiene conceptualmente fijo,
- el usuario no ve cambiar áreas rojas por mover el nivel.

### Falla si
- el selector de nivel recalcula o redibuja el rojo visible como diagnóstico cambiante.

---

## 8. Caso 7 — Propuesta por nivel

### Escenario
El usuario cambia entre Básico, Recomendado y Máximo.

### Resultado esperado
- cambian los dispositivos propuestos,
- cambian cantidades y resumen,
- el flujo sigue estable.

### Falla si
- el nivel no impacta la propuesta,
- el cambio rompe la pantalla,
- se mezcla con la lógica de riesgo base.

---

## 9. Caso 8 — Kit generado

### Escenario
Se genera el kit desde la propuesta.

### Resultado esperado
- aparecen tarjetas claras,
- cada item tiene cantidad,
- el usuario entiende para qué sirve cada componente.

### Falla si
- el kit se ve como una lista técnica poco clara,
- no hay relación entre propuesta y kit.

---

## 10. Caso 9 — Resumen final

### Escenario
El usuario completa todo el wizard.

### Resultado esperado
- ve un resumen final claro,
- existe una acción final comprensible,
- la experiencia cierra de manera lógica.

### Falla si
- el cierre parece técnico o inconcluso,
- no hay CTA claro,
- el usuario no entiende qué logró.

---

## 11. Caso 10 — Error de procesamiento

### Escenario
El archivo no puede procesarse correctamente.

### Resultado esperado
- se informa el problema en lenguaje humano,
- se ofrece volver a intentar o revisar,
- no se rompe el flujo completo.

### Falla si
- aparece traceback,
- se exponen rutas internas,
- el usuario queda bloqueado sin salida.

---

## 12. Caso 11 — Aislamiento por sesión

### Escenario
Dos usuarios o dos sesiones distintas usan el wizard.

### Resultado esperado
- cada una tiene workspace propio,
- no se cruzan archivos ni resultados,
- el estado es independiente.

### Falla si
- una sesión pisa artefactos de otra,
- aparecen previews equivocadas.

---

## 13. Caso 12 — Coherencia visual

### Escenario
Se recorre el wizard completo.

### Resultado esperado
- el plano es siempre protagonista,
- existe progreso visible,
- la UI mantiene consistencia de estilo,
- no aparecen pantallas improvisadas.

### Falla si
- cada pantalla parece de un producto distinto,
- se usan estilos y tonos inconsistentes.

---

## 14. Checklist final de aceptación

- [ ] Inicio claro
- [ ] Upload estable
- [ ] Processing con feedback útil
- [ ] Review con validaciones obligatorias
- [ ] Riesgo fijo separado de propuesta
- [ ] Propuesta dependiente del nivel
- [ ] Kit entendible
- [ ] Resumen final claro
- [ ] Manejo de errores humano
- [ ] Workspaces aislados
- [ ] Coherencia visual general
