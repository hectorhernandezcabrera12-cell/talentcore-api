## 1. Resumen
El microservicio implementa la lógica de negocio básica correctamente, pero presenta vulnerabilidades críticas de seguridad (BOLA, falta de validación de identidad) y problemas de integridad de datos.
**Veredicto: RECHAZADO**

## 2. Cumplimiento del PRD
| Requisito | Cumple | Evidencia |
| :--- | :---: | :--- |
| Cálculo de saldo por antigüedad | Sí | `calcular_saldo` en `main.py` |
| Creación de empleados con RBAC | Parcial | Solo valida rol, no identidad real |
| Solicitud de vacaciones | Sí | Endpoint `/solicitar` valida saldo |
| Revisión por manager directo | Sí | Endpoint `/revisar` valida `manager_id` |
| Tests de aceptación | Sí | `tests/test_api.py` cubre AC01-03 |

## 3. Seguridad
*   **BOLA (Broken Object Level Authorization):** En `solicitar_vacaciones`, cualquier usuario puede crear solicitudes para cualquier `empleado_id` sin verificar que el `X-User-Id` coincida con el `empleado_id`. Esto permite a un atacante agotar el saldo de otros usuarios.
*   **Autenticación Insegura:** El uso de `X-User-Id` como único mecanismo de autenticación es inaceptable en producción. No hay JWT, OAuth2 ni verificación de firma. Cualquiera puede forjarse como ADMIN.
*   **Validación de Entradas:** Falta validación de rangos en `anios_antiguedad` (puede ser negativo) y `dias_solicitados` (puede ser 0 o negativo). El email no se valida con formato.
*   **Inyección de SQL:** Mitigada por SQLAlchemy ORM, pero se recomienda usar parámetros explícitos en consultas complejas futuras.

## 4. Calidad de código
1.  **Alta:** `crear_empleado` permite crear el primer usuario sin autenticación. Si la base de datos no está vacía, exige header, pero la lógica es frágil. Debe usarse un seed script o endpoint de bootstrap seguro.
2.  **Alta:** Falta validación de `dias_solicitados > 0` en `SolicitudCreate`. Permite solicitudes de 0 o días negativos.
3.  **Media:** `calcular_saldo` realiza una consulta N+1 implícita si se escala. Debe usarse `func.sum` en la consulta SQL en lugar de `sum()` en Python.
4.  **Media:** No se manejan excepciones de base de datos (IntegrityError) en `crear_empleado` si el email ya existe. Devolverá 500 en lugar de 409.
5.  **Baja:** Uso de `Optional[int]` en headers sin default explícito en algunos casos, lo que puede causar errores de tipo si el header está presente pero vacío.

## 5. Mejoras recomendadas
*   Implementar autenticación real (JWT/OAuth2) y extraer el usuario autenticado desde el token, no de headers.
*   Añadir validación Pydantic: `Field(gt=0)` para días y antigüedad, `EmailStr` para emails.
*   Corregir BOLA en `solicitar_vacaciones`: forzar `payload.empleado_id == user_id` autenticado.
*   Usar `func.sum` en SQLAlchemy para calcular saldos eficientemente.
*   Manejar `IntegrityError` para emails duplicados devolviendo 409 Conflict.