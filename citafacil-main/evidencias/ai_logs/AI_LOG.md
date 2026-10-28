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