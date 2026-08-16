# Operación con SQL Server Agent

## Habilitación local

SQL Server Agent se habilita una vez por volumen de Docker:

```bash
docker exec nibol-sqlserver /opt/mssql/bin/mssql-conf set sqlagent.enabled true
docker compose restart sqlserver
```

Verificación:

```sql
SELECT servicename, status_desc
FROM sys.dm_server_services;
```

## Jobs configurados

| Job | Frecuencia | Pasos |
|---|---:|---|
| `JOB_RETAIL_MICROBATCH` | Cada 15 minutos | Carga de ventas e inventario, scoring de clientes y alertas |
| `JOB_RETAIL_FORECAST_MENSUAL` | Día 1 de cada mes, 03:00 | Forecast estacional SQL |

Cada paso tiene hasta tres reintentos. El forecast usa tres reintentos con intervalo de diez minutos.

## Auditoría y monitoreo

- `dbo.SP_CARGA_VENTAS` registra lecturas, inserciones y rechazos en `aud.CARGAS`.
- Los rechazos de calidad se registran en `aud.RECHAZOS`.
- SQL Server Agent conserva resultado, paso y mensaje de ejecución en `msdb.dbo.sysjobhistory`.

Consulta operativa:

```sql
SELECT TOP (20)
    j.name AS job_name,
    h.step_id,
    h.step_name,
    h.run_status,
    h.run_date,
    h.run_time,
    h.message
FROM msdb.dbo.sysjobhistory AS h
INNER JOIN msdb.dbo.sysjobs AS j
    ON j.job_id = h.job_id
ORDER BY h.instance_id DESC;
```

`run_status = 1` representa una ejecución exitosa.

## Alcance de la demostración

En el entorno local, los CSV se cargan a staging mediante el script de carga inicial. El job de microbatch consume y transforma las tablas `stg` de forma idempotente.

En producción, la recepción incremental de archivos o mensajes hacia staging debe ejecutarse antes del job, por ejemplo mediante una integración con ERP, API, SFTP o una herramienta de orquestación. Esta separación evita que la lógica de negocio dependa del formato de llegada de cada fuente.

No se configuró correo SMTP local porque requiere credenciales y un servidor de correo externo. Los errores quedan registrados en `aud.CARGAS` y en el historial del Agent; el correo puede habilitarse posteriormente con Database Mail y un operador de SQL Server Agent.