# Guía de ejecución

## 1. Requisitos

- Python 3 y `venv`
- Docker Engine y Docker Compose
- Git
- Power BI Desktop para Windows (usado mediante una máquina virtual)

> No se versiona el archivo `.env` porque contiene una contraseña local.

## 2. Preparar el entorno Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configurar y levantar SQL Server

Crear el archivo local de variables a partir del ejemplo:

```bash
cp .env.example .env
```

Editar `.env` y definir una contraseña local segura para SQL Server.

```bash
docker compose up -d
docker compose ps
```

Para detener el entorno sin borrar la base persistente:

```bash
docker compose down
```

## 4. Generar y validar los datos sintéticos

```bash
source .venv/bin/activate

python src/generar_datos.py
python src/generar_inventario.py

python -m unittest discover -s tests -v
python tests/validar_dataset_final.py
python tests/validar_inventario.py
```

Resultados esperados:

- 5.000 ventas y 30 columnas en `FACT_VENTAS`.
- 100 outliers simulados.
- 6.000 snapshots de inventario.
- 480 registros de stock crítico.
- Todas las pruebas automatizadas exitosas.

## 5. Crear y cargar el Data Warehouse

Los archivos CSV generados en `data/raw/` se montan en el contenedor como `/var/opt/mssql/import`.

Ejecutar los scripts SQL en este orden:

```bash
docker exec -i nibol-sqlserver /bin/sh -c \
  'SQLCMDPASSWORD="$MSSQL_SA_PASSWORD" /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -C' \
  < sql/01_database.sql
```

Repetir el mismo comando para los siguientes scripts, cambiando solo el nombre del archivo:

```text
sql/02_dimensions.sql
sql/03_staging_dimensiones_auditoria.sql
sql/04_hechos_y_staging_ventas.sql
sql/06_migracion_importado_raw.sql
sql/05_carga_staging_csv.sql
sql/07_sp_carga_ventas.sql
sql/08_analitica_y_alertas.sql
sql/09_sp_scoring_clientes.sql
sql/10_sp_alertas_negocio.sql
sql/11_sp_forecast_baseline.sql
sql/13_sp_carga_inventario.sql
```

Luego ejecutar las cargas y procesos analíticos:

```bash
docker exec nibol-sqlserver /bin/sh -c \
  'SQLCMDPASSWORD="$MSSQL_SA_PASSWORD" /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -C -d BI_RETAIL_ANALYTICS -Q "EXEC dbo.SP_CARGA_VENTAS; EXEC dbo.SP_CARGA_INVENTARIO; EXEC dbo.SP_SCORING_CLIENTES; EXEC dbo.SP_ALERTAS_NEGOCIO; EXEC dbo.SP_FORECAST;"'
```

Verificación mínima:

```bash
docker exec nibol-sqlserver /bin/sh -c \
  'SQLCMDPASSWORD="$MSSQL_SA_PASSWORD" /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -C -d BI_RETAIL_ANALYTICS -Q "SELECT COUNT(*) AS fact_ventas FROM dbo.FACT_VENTAS; SELECT COUNT(*) AS fact_inventario FROM dbo.FACT_INVENTARIO; SELECT regla, COUNT(*) AS alertas FROM dbo.ALERTAS_NEGOCIO GROUP BY regla;"'
```

## 6. Automatización con SQL Server Agent

Para habilitar SQL Server Agent localmente:

```bash
docker exec nibol-sqlserver /opt/mssql/bin/mssql-conf set sqlagent.enabled true
docker compose restart sqlserver
```

Después de que el contenedor esté operativo, crear los jobs:

```bash
docker exec -i nibol-sqlserver /bin/sh -c \
  'SQLCMDPASSWORD="$MSSQL_SA_PASSWORD" /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -C' \
  < sql/12_sql_agent_jobs.sql
```

El proyecto implementa un microbatch cada 15 minutos y un forecast mensual. La configuración de notificaciones por correo requiere credenciales SMTP del entorno productivo, por lo que no se incluye en el repositorio.

## 7. Forecast avanzado en Python

```bash
source .venv/bin/activate
python src/modelar_forecast.py
```

El proceso compara un baseline estacional con Holt-Winters aditivo usando validación temporal de seis meses y selecciona el modelo con menor MAE por serie región-categoría.

## 8. Dashboard Power BI

Abrir:

```text
powerbi/nibol_retail_analytics.pbix
```

El dashboard utiliza DirectQuery contra `BI_RETAIL_ANALYTICS`.

En una máquina virtual, la dirección del host puede variar. En este entorno se utilizó:

```text
192.168.122.1,1433
```

Autenticación: SQL Server, usuario `sa` y la contraseña definida localmente en `.env`.

El modelo usa relaciones uno a muchos, activas y con filtro en una sola dirección desde las dimensiones hacia las tablas de hechos.

## 9. Versiones relevantes

- `v0.1-data-simulation`: generación y validación de datos.
- `v0.2-sql-warehouse`: Data Warehouse, procedimientos, alertas y automatización.
- `v0.3-powerbi-dashboard`: dashboard, modelo semántico y medidas DAX.