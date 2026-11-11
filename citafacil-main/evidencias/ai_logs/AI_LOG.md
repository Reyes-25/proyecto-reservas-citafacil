# AI Development Log - Proyecto Reservas Citafacil

## Equipo
- **Dev:** Amir Reyes
- **Reviewer:** Julio Gudiño
- **QA:** Héctor Ortega

## Registro de Actividades

| Fecha | Actividad | Herramienta IA | Qué se solicitó | Resultado | Decisión Humana |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 27/10/2026 | Análisis de Arquitectura | Copilot Chat | Analizar estructura de `citafacil` y encontrar el punto de entrada para el calendario | Explicó la estructura (backend/frontend/tests), la BD (SQLAlchemy + SQLite) y señaló `public.py` y `availability.py` como puntos clave. | **Aceptada.** El análisis fue preciso y nos ahorró horas de lectura manual. |
| 27/10/2026 | Análisis de Reserva Rápida | Copilot Chat | Analizar flujo de reserva y proponer solución | Propuso dos opciones: `localStorage` (solo frontend) o perfil en servidor (requiere modelo `Customer` y lógica de privacidad). | **Decisión Humana:** Elegimos `localStorage` con un checkbox de consentimiento. Rechazamos la opción del servidor por ser demasiado compleja para este Sprint. |
| 27/10/2026 | Implementación Reserva Rápida | Copilot Chat | Implementar `localStorage` en `index.html` con checkbox de consentimiento | Agregó precarga, checkbox y guardado condicional. No tocó el backend. | **Aceptada.** La implementación cumple el Issue y respeta el alcance. |
| 27/10/2026 | Análisis de Gráficos | Copilot Chat | Analizar datos para gráficos de demanda | Identificó que `Appointment` tiene fechas y estados; propuso endpoint `/api/admin/forecast`, consulta agregada en `crud.py` y gráfico con Canvas nativo. Advirtió que el precio histórico no se guarda. | **Aceptada parcialmente.** Usaremos Canvas nativo y endpoint. Rechazamos la predicción compleja; haremos gráfico de histórico. |
| 27/10/2026 | Implementación Gráficos (Backend) | Copilot Chat | Crear `get_appointment_history` y `GET /api/admin/forecast` | Generó la consulta agregada y el endpoint. Validó con SQLite en memoria que los conteos diarios/semanales/mensuales funcionan. | **Aceptada.** El código es correcto y la IA se auto-validó con pruebas. |
| 27/10/2026 | Corrección de configuración frontend | Copilot Chat | Corregir URL de API y manejo de token en admin.html | Cambió DEFAULT_API a localhost y reemplazó el token hardcodeado por la variable TOKEN del login. | **Aceptada.** El panel funciona contra el backend local y el token ya no está expuesto en el código. |
