# Plan de Cierre del Sprint — Proyecto Reservas Citafacil

> Documento de planificación para resolver conflictos, completar las historias de usuario
> y cerrar el desarrollo del sprint.
>
> Seguimiento de avance: ver `PROGRESO_SPRINT.md`.

---

## 1. Diagnóstico inicial

| Elemento | Estado |
|---|---|
| `feature/reserva-rapida` (PR #7) | Limpio, listo para merge; no cumple al 100% Issue #1 (falta correo) |
| `feature/calendario-dinamico` (PR #6) | 1 conflicto en `evidencias/ai_logs/AI_LOG.md`; solo backend, falta calendario visual (Issue #2) |
| `feature/graficos-demanda` (PR #8) | Fusionado, pero Issue #3 sigue abierto y falta filtro por servicio |
| Issues #4 y #5 | Sin empezar |
| Causa del conflicto | Ambas ramas agregan filas al final de la misma tabla `AI_LOG.md` (sin salto de línea final). El código backend no conflictúa |

### Inventario de ramas y PRs

- Ramas remotas: `main`, `feature/graficos-demanda`, `feature/calendario-dinamico`, `feature/reserva-rapida`.
- PRs: #8 (fusionado), #6 (abierto, con conflicto), #7 (abierto, limpio).
- Issues abiertos: #1, #2, #3, #4, #5.

---

## 2. Fase 0 — Preparación

- [ ] Actualizar `main` (`git pull`).
- [ ] Crear entorno Linux (el `venv` existente es de Windows).
- [ ] Instalar dependencias del backend.
- [ ] Ejecutar tests de línea base.
- [ ] Autenticar `gh` para gestionar PRs.

```bash
git switch main && git pull
python3 -m venv .venv
.venv/bin/pip install -r citafacil-main/backend/requirements.txt
cd citafacil-main/backend && ../../.venv/bin/python -m pytest -q
gh auth login
```

---

## 3. Fase 1 — Resolver el conflicto y destrabar PRs

**Estrategia:** integrar primero el PR #7 (limpio) y luego sincronizar el #6 una sola vez.
Así el `AI_LOG.md` se resuelve una única vez.

### Paso 1 — Merge PR #7
- Revisar el diff (`index.html`, +12 líneas), aprobar y fusionar.
- Decidir antes el tema del correo (ver Fase 3).

### Paso 2 — Sincronizar PR #6 con main

```bash
git fetch origin
git switch -c feature/calendario-dinamico origin/feature/calendario-dinamico
git merge origin/main
# conflicto esperado: citafacil-main/evidencias/ai_logs/AI_LOG.md
```

**Resolución del `AI_LOG.md`:** conservar la unión de filas en orden cronológico:

1. Análisis de Arquitectura.
2. Análisis de Reserva Rápida.
3. Implementación Reserva Rápida.
4. Análisis de Gráficos.
5. Implementación Gráficos (Backend).
6. Corrección de configuración frontend.
7. Plan de Implementación (Calendario).
8. Implementación Backend (Calendario).
9. Prueba Backend (Calendario).

Además, agregar salto de línea al final del archivo para evitar futuros conflictos.

```bash
git add citafacil-main/evidencias/ai_logs/AI_LOG.md
git commit -m "merge: sincronizar calendario con main y resolver AI_LOG"
git push origin feature/calendario-dinamico
```

**Verificación:** `git merge-tree --write-tree origin/main origin/feature/calendario-dinamico`
sin conflictos + `pytest` en verde. No usar `push --force`.

---

## 4. Fase 2 — Completar Issue #2 antes de fusionar PR #6

El PR #6 solo entrega `GET /api/calendar`; falta lo visual:

- [ ] En `frontend/index.html`: al seleccionar servicio (y al cargar), llamar
      `/api/calendar?service_id=...&start_date=...&end_date=...` para el mes visible.
- [ ] Renderizar grilla mensual con estados `available` / `occupied` / `closed`;
      deshabilitar días no disponibles.
- [ ] Reconsultar automáticamente al cambiar de servicio y al navegar de mes.
- [ ] Limitar el rango en backend (máximo sugerido: 62 días).
- [ ] Tests nuevos en `tests/test_booking.py`: 200, 404 servicio inexistente,
      422 rango invertido, día cerrado y día ocupado.
- [ ] Capturas en `evidencias/capturas/` + filas en `AI_LOG.md`.
- [ ] Cerrar PR #6 con `Closes #2`.

---

## 5. Fase 3 — Completar/cerrar Issues #1 y #3

### Issue #1 (reserva rápida)

- El criterio pide "nombre, correo y teléfono", pero formulario y modelo solo tienen
  nombre/teléfono.
- Opción A: agregar email opcional a `models.Appointment`, `schemas`, formulario y
  localStorage. Considerar que SQLite no tiene migraciones.
- Opción B: documentar la desviación en `AI_LOG.md`/README y validar con el docente.
- [ ] Verificar que la segunda reserva quede precargada y se complete en <3 clics.
- [ ] Cerrar Issue #1.

### Issue #3 (gráficos)

- [ ] Agregar `service_id` opcional a `/api/admin/forecast` y a
      `crud.get_appointment_history`.
- [ ] Añadir selector de servicio en `admin.html` y enviarlo como parámetro.
- [ ] Test del filtro.
- [ ] Cerrar Issue #3 (ya está el merge; falta el criterio).

---

## 6. Fase 4 — Issues #4 y #5

### #4 Correo de confirmación (<1 min)

- [ ] Agregar `customer_email` al modelo/schema/formulario (con consentimiento).
- [ ] Configurar proveedor (SMTP/SendGrid) por variables de entorno.
- [ ] Enviar tras confirmar (síncrono o background task) e incluir fecha, hora,
      servicio y profesional.
- [ ] Test con proveedor mockeado.

### #5 Panel de métricas

- [ ] Endpoint `/api/admin/metrics` (total citas día/semana, ingresos estimados,
      rango de fechas).
- [ ] Tarjetas + filtros en `admin.html`.
- [ ] Considerar guardar `price_at_booking` en `Appointment`, porque el precio
      histórico hoy no se conserva.

---

## 7. Organización del trabajo

| Orden | Trabajo | Responsable sugerido |
|---|---|---|
| 1 | Merge PR #7 + sincronizar/resolver PR #6 | Dev + Reviewer |
| 2 | Calendario visual + tests + evidencias (#2) | Dev / QA |
| 3 | Cerrar #1 (decisión email) y #3 (filtro) | Dev + Reviewer |
| 4 | #4 correo | Dev / QA |
| 5 | #5 métricas | Dev / QA |
| 6 | QA final + README + cierre de issues | QA |

### Reglas de flujo

- Una rama corta por issue (`feature/issue-N-descripcion`), PR por issue con `Closes #N`.
- Mantener ramas actualizadas con `main` antes de pedir review.
- Nada de commits directos a `main`; merge vía PR con al menos 1 revisión.
- Tablero GitHub Projects: `Backlog → En desarrollo → En review → QA → Hecho`.

### Definition of Done

- Código implementado.
- Tests verdes.
- Evidencia (captura) en `evidencias/capturas/`.
- Fila en `AI_LOG.md`.
- Checkbox del README actualizado.
- Issue cerrado.
- PR fusionado.

---

## 8. Estimación

- Fase 1: 1 día.
- Fase 2 (#2): 2–3 días.
- Fase 3 (#1 y #3): 1–2 días.
- Fase 4 (#4 y #5): 3–4 días cada una, con QA en paralelo.
