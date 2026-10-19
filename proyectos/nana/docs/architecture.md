# Arquitectura de la demo pública

Flask/Jinja → CSV sintético fijo → core.py/pandas → resultados por sesión → CSV/SQLite.
Datos de entrada incluidos en demo/, nunca reales. No hay conexiones externas,
autenticación empresarial, volumen persistente ni base de datos de usuarios.

Gunicorn usa un worker y dos hilos, una réplica. La clave se comparte por entorno,
las carpetas viven fuera de static y las descargas requieren sesión y vigencia.
La lógica de limpieza queda separada de la presentación. El despliegue es Docker
como usuario no root. Si se evoluciona a datos propios se requiere revisión nueva:
autenticación/autorización, validación de negocio, almacenamiento compartido,
retención, concurrencia y control de abuso adecuado.
