USE BI_RETAIL_ANALYTICS;
GO

CREATE OR ALTER PROCEDURE dbo.SP_CARGA_VENTAS
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    SET DATEFIRST 1;

    DECLARE @auditoria_id BIGINT;
    DECLARE @filas_leidas INT;
    DECLARE @filas_insertadas INT = 0;

    SELECT @filas_leidas = COUNT(*)
    FROM stg.VENTAS_RAW;

    INSERT aud.CARGAS (
        proceso,
        estado,
        filas_leidas
    )
    VALUES (
        N'SP_CARGA_VENTAS',
        N'EN_PROCESO',
        @filas_leidas
    );

    SET @auditoria_id = SCOPE_IDENTITY();

    BEGIN TRY
        BEGIN TRANSACTION;

        INSERT dbo.DIM_FECHA (
            fecha_key,
            fecha,
            anio,
            trimestre,
            mes,
            nombre_mes,
            semana,
            dia,
            es_fin_semana
        )
        SELECT DISTINCT
            CONVERT(INT, CONVERT(CHAR(8), f.fecha_dia, 112)),
            f.fecha_dia,
            YEAR(f.fecha_dia),
            DATEPART(QUARTER, f.fecha_dia),
            MONTH(f.fecha_dia),
            DATENAME(MONTH, f.fecha_dia),
            DATEPART(ISO_WEEK, f.fecha_dia),
            DAY(f.fecha_dia),
            IIF(DATEPART(WEEKDAY, f.fecha_dia) IN (6, 7), 1, 0)
        FROM stg.FECHA_RAW f
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.DIM_FECHA d
            WHERE d.fecha = f.fecha_dia
        );

        INSERT dbo.DIM_SUCURSAL (
            id_sucursal_origen,
            sucursal,
            region,
            ciudad,
            factor_demanda
        )
        SELECT
            s.id_sucursal,
            s.sucursal,
            s.region,
            s.ciudad,
            s.factor_demanda_sucursal
        FROM stg.SUCURSAL_RAW s
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.DIM_SUCURSAL d
            WHERE d.id_sucursal_origen = s.id_sucursal
        );

        INSERT dbo.DIM_CLIENTE (
            id_cliente_origen,
            cliente,
            score_riesgo_base,
            lealtad_latente,
            preferencia_digital,
            ingreso_relativo
        )
        SELECT
            c.id_cliente,
            c.cliente,
            c.score_riesgo_cliente_base,
            c.lealtad_latente,
            c.preferencia_digital,
            c.ingreso_relativo
        FROM stg.CLIENTE_RAW c
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.DIM_CLIENTE d
            WHERE d.id_cliente_origen = c.id_cliente
        );

        INSERT dbo.DIM_PRODUCTO (
            id_producto_origen,
            producto,
            categoria,
            costo_base,
            margen_objetivo,
            importado,
            popularidad
        )
        SELECT
            p.id_producto,
            p.producto,
            p.categoria,
            p.costo_base,
            p.margen_objetivo,
            CASE LOWER(LTRIM(RTRIM(p.importado)))
                WHEN N'true' THEN CAST(1 AS BIT)
                WHEN N'1' THEN CAST(1 AS BIT)
                ELSE CAST(0 AS BIT)
            END,
            p.popularidad
        FROM stg.PRODUCTO_RAW p
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.DIM_PRODUCTO d
            WHERE d.id_producto_origen = p.id_producto
        );

        INSERT dbo.FACT_VENTAS (
            id_venta_origen,
            fecha_key,
            sucursal_key,
            cliente_key,
            producto_key,
            fecha_hora,
            vendedor,
            costo,
            precio,
            cantidad,
            descuento,
            ingreso_neto,
            utilidad,
            metodo_pago,
            tiempo_entrega,
            satisfaccion_cliente,
            indice_macroeconomico,
            clima,
            dolar_paralelo,
            nivel_trafico,
            score_riesgo_cliente,
            probabilidad_fuga,
            fuga_real_90d,
            indice_inflacion,
            es_outlier_simulado,
            compras_previas_cliente
        )
        SELECT
            s.id_venta,
            CONVERT(
                INT,
                CONVERT(CHAR(8), CONVERT(DATE, s.fecha), 112)
            ),
            ds.sucursal_key,
            dc.cliente_key,
            dp.producto_key,
            s.fecha,
            s.vendedor,
            s.costo,
            s.precio,
            s.cantidad,
            s.descuento,
            s.ingreso_neto,
            s.utilidad,
            s.metodo_pago,
            s.tiempo_entrega,
            s.satisfaccion_cliente,
            s.indice_macroeconomico,
            s.clima,
            s.dolar_paralelo,
            s.nivel_trafico,
            s.score_riesgo_cliente,
            s.probabilidad_fuga,
            s.fuga_real_90d,
            s.indice_inflacion,
            s.es_outlier_simulado,
            s.compras_previas_cliente
        FROM stg.VENTAS_RAW s
        JOIN dbo.DIM_SUCURSAL ds
            ON ds.id_sucursal_origen = s.id_sucursal
        JOIN dbo.DIM_CLIENTE dc
            ON dc.id_cliente_origen = s.id_cliente
        JOIN dbo.DIM_PRODUCTO dp
            ON dp.id_producto_origen = s.id_producto
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.FACT_VENTAS f
            WHERE f.id_venta_origen = s.id_venta
        );

        SET @filas_insertadas = @@ROWCOUNT;

        COMMIT TRANSACTION;

        UPDATE aud.CARGAS
        SET
            fin = SYSUTCDATETIME(),
            estado = N'EXITOSO',
            filas_insertadas = @filas_insertadas
        WHERE auditoria_id = @auditoria_id;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        UPDATE aud.CARGAS
        SET
            fin = SYSUTCDATETIME(),
            estado = N'ERROR',
            mensaje_error = ERROR_MESSAGE()
        WHERE auditoria_id = @auditoria_id;

        THROW;
    END CATCH;
END;
GO