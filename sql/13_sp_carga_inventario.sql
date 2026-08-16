USE BI_RETAIL_ANALYTICS;
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

CREATE OR ALTER PROCEDURE dbo.SP_CARGA_INVENTARIO
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @auditoria_id BIGINT;
    DECLARE @filas_leidas INT;
    DECLARE @filas_insertadas INT = 0;
    DECLARE @filas_rechazadas INT = 0;

    SELECT @filas_leidas = COUNT(*)
    FROM stg.INVENTARIO_RAW;

    INSERT INTO aud.CARGAS (
        proceso,
        estado,
        filas_leidas,
        filas_insertadas,
        filas_rechazadas,
        inicio
    )
    VALUES (
        N'SP_CARGA_INVENTARIO',
        N'EN_PROCESO',
        @filas_leidas,
        0,
        0,
        SYSUTCDATETIME()
    );

    SET @auditoria_id = SCOPE_IDENTITY();

    BEGIN TRY
        BEGIN TRANSACTION;

        SELECT @filas_rechazadas = COUNT(*)
        FROM stg.INVENTARIO_RAW AS ir
        LEFT JOIN dbo.DIM_FECHA AS df
            ON df.fecha = CONVERT(DATE, ir.fecha_corte)
        LEFT JOIN dbo.DIM_SUCURSAL AS ds
            ON ds.id_sucursal_origen = ir.id_sucursal
        LEFT JOIN dbo.DIM_PRODUCTO AS dp
            ON dp.id_producto_origen = ir.id_producto
        WHERE df.fecha_key IS NULL
            OR ds.sucursal_key IS NULL
            OR dp.producto_key IS NULL
            OR ir.stock_actual < 0
            OR ir.punto_reorden <= 0;

        INSERT INTO dbo.FACT_INVENTARIO (
            fecha_key,
            sucursal_key,
            producto_key,
            fecha_corte,
            stock_actual,
            punto_reorden
        )
        SELECT
            df.fecha_key,
            ds.sucursal_key,
            dp.producto_key,
            ir.fecha_corte,
            ir.stock_actual,
            ir.punto_reorden
        FROM stg.INVENTARIO_RAW AS ir
        INNER JOIN dbo.DIM_FECHA AS df
            ON df.fecha = CONVERT(DATE, ir.fecha_corte)
        INNER JOIN dbo.DIM_SUCURSAL AS ds
            ON ds.id_sucursal_origen = ir.id_sucursal
        INNER JOIN dbo.DIM_PRODUCTO AS dp
            ON dp.id_producto_origen = ir.id_producto
        WHERE ir.stock_actual >= 0
            AND ir.punto_reorden > 0
            AND NOT EXISTS (
                SELECT 1
                FROM dbo.FACT_INVENTARIO AS fi
                WHERE fi.fecha_corte = ir.fecha_corte
                    AND fi.sucursal_key = ds.sucursal_key
                    AND fi.producto_key = dp.producto_key
            );

        SET @filas_insertadas = @@ROWCOUNT;

        UPDATE aud.CARGAS
        SET
            estado = N'EXITOSO',
            filas_insertadas = @filas_insertadas,
            filas_rechazadas = @filas_rechazadas,
            fin = SYSUTCDATETIME()
        WHERE auditoria_id = @auditoria_id;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        UPDATE aud.CARGAS
        SET
            estado = N'ERROR',
            fin = SYSUTCDATETIME()
        WHERE auditoria_id = @auditoria_id;

        THROW;
    END CATCH;
END;
GO