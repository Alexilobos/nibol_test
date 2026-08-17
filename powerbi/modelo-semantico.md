# Modelo semántico de Power BI

## Fuente y modo de conexión

El reporte `nibol_retail_analytics.pbix` se conecta a `BI_RETAIL_ANALYTICS` en SQL Server mediante DirectQuery.

El warehouse se actualiza mediante SQL Server Agent cada 15 minutos. DirectQuery permite que las consultas del reporte lean el estado actual del warehouse. Power BI Desktop no ejecuta refresco programado por sí mismo; en producción se publicaría en Power BI Service y se configuraría un gateway.

## Esquema estrella

Dimensiones:

- `DIM_FECHA`
- `DIM_SUCURSAL`
- `DIM_PRODUCTO`
- `DIM_CLIENTE`

Hechos:

- `FACT_VENTAS`
- `FACT_INVENTARIO`
- `FACT_SCORING`
- `FACT_FORECAST`
- `ALERTAS_NEGOCIO`

Las relaciones son uno a varios, activas y con dirección de filtro única desde dimensiones hacia hechos. Este diseño evita ambigüedad, doble conteo y propagación de filtros difícil de explicar.

No se usa dirección bidireccional, relaciones entre hechos ni muchos a muchos. En particular, `FACT_FORECAST[categoria]` no se relaciona por texto con `DIM_PRODUCTO[categoria]`, porque esa relación podría no ser única. La categoría de pronóstico se filtra dentro de su propio hecho.

`DIM_FECHA[fecha]` está marcada como tabla de fechas para habilitar inteligencia de tiempo.

## Páginas del reporte

1. **Resumen ejecutivo**: ventas netas, utilidad, margen, clientes activos, tendencia, ventas por región y Top 5 productos.
2. **Riesgo y operación**: stock crítico, clientes de riesgo alto, alertas abiertas, sucursales prioritarias y detalle de alertas.
3. **Pronóstico 2026**: ventas proyectadas, MAE promedio, evolución mensual y proyección por categoría y región.

## Criterios de diseño

Las medidas DAX se prefieren sobre columnas calculadas: se recalculan con el contexto de filtro y son adecuadas para DirectQuery. El modelo usa una página por decisión de negocio para que el usuario pueda pasar de monitoreo ejecutivo a acción operativa sin saturar una sola pantalla.