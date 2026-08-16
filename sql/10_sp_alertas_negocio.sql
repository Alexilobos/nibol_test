USE BI_RETAIL_ANALYTICS;
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

CREATE OR ALTER PROCEDURE dbo.SP_ALERTAS_NEGOCIO
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @fecha_corte DATE;
    DECLARE @fecha_alerta DATETIME2(0);
    DECLARE @fecha_key INT;
    DECLARE @sucursal_key INT;
    DECLARE @sucursal NVARCHAR(100);
    DECLARE @ventas_actuales DECIMAL(18,2);
    DECLARE @ventas_previas DECIMAL(18,2);

    SELECT @fecha_corte = CONVERT(DATE, MAX(fecha_hora))
    FROM dbo.FACT_VENTAS;

    SET @fecha_alerta = DATEADD(
        HOUR,
        12,
        CONVERT(DATETIME2(0), @fecha_corte)
    );

    SET @fecha_key = CONVERT(
        INT,
        CONVERT(CHAR(8), @fecha_corte, 112)
    );

    DECLARE cursor_sucursales CURSOR LOCAL FAST_FORWARD FOR
        SELECT sucursal_key, sucursal
        FROM dbo.DIM_SUCURSAL;

    OPEN cursor_sucursales;

    FETCH NEXT FROM cursor_sucursales
    INTO @sucursal_key, @sucursal;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        SELECT @ventas_actuales = COALESCE(
            SUM(ingreso_neto),
            0
        )
        FROM dbo.FACT_VENTAS
        WHERE sucursal_key = @sucursal_key
          AND fecha_hora >= DATEADD(DAY, -6, @fecha_corte)
          AND fecha_hora < DATEADD(DAY, 1, @fecha_corte);

        SELECT @ventas_previas = COALESCE(
            SUM(ingreso_neto),
            0
        )
        FROM dbo.FACT_VENTAS
        WHERE sucursal_key = @sucursal_key
          AND fecha_hora >= DATEADD(DAY, -13, @fecha_corte)
          AND fecha_hora < DATEADD(DAY, -6, @fecha_corte);

        IF @ventas_previas > 0
           AND @ventas_actuales < @ventas_previas * 0.80
        BEGIN
            INSERT dbo.ALERTAS_NEGOCIO (
                fecha_alerta,
                regla,
                severidad,
                entidad_tipo,
                entidad_id,
                sucursal_key,
                mensaje,
                valor_observado,
                umbral
            )
            SELECT
                @fecha_alerta,
                N'CAIDA_VENTAS_20',
                N'ALTA',
                N'SUCURSAL',
                CONVERT(NVARCHAR(100), @sucursal_key),
                @sucursal_key,
                CONCAT(
                    N'Caída de ventas superior a 20% en ',
                    @sucursal
                ),
                @ventas_actuales,
                @ventas_previas * 0.80
            WHERE NOT EXISTS (
                SELECT 1
                FROM dbo.ALERTAS_NEGOCIO a
                WHERE a.regla = N'CAIDA_VENTAS_20'
                  AND a.entidad_tipo = N'SUCURSAL'
                  AND a.entidad_id = CONVERT(
                      NVARCHAR(100),
                      @sucursal_key
                  )
                  AND a.fecha_alerta_dia = @fecha_corte
            );
        END;

        FETCH NEXT FROM cursor_sucursales
        INTO @sucursal_key, @sucursal;
    END;

    CLOSE cursor_sucursales;
    DEALLOCATE cursor_sucursales;

    INSERT dbo.ALERTAS_NEGOCIO (
        fecha_alerta,
        regla,
        severidad,
        entidad_tipo,
        entidad_id,
        sucursal_key,
        mensaje,
        valor_observado,
        umbral
    )
    SELECT
        @fecha_alerta,
        N'UTILIDAD_NEGATIVA',
        N'MEDIA',
        N'VENTA',
        CONVERT(NVARCHAR(100), f.id_venta_origen),
        f.sucursal_key,
        CONCAT(
            N'Utilidad negativa en venta ',
            f.id_venta_origen
        ),
        f.utilidad,
        0
    FROM dbo.FACT_VENTAS f
    WHERE f.fecha_hora >= DATEADD(DAY, -6, @fecha_corte)
      AND f.fecha_hora < DATEADD(DAY, 1, @fecha_corte)
      AND f.utilidad < 0
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.ALERTAS_NEGOCIO a
          WHERE a.regla = N'UTILIDAD_NEGATIVA'
            AND a.entidad_tipo = N'VENTA'
            AND a.entidad_id = CONVERT(
                NVARCHAR(100),
                f.id_venta_origen
            )
            AND a.fecha_alerta_dia = @fecha_corte
      );

    INSERT dbo.ALERTAS_NEGOCIO (
        fecha_alerta,
        regla,
        severidad,
        entidad_tipo,
        entidad_id,
        mensaje,
        valor_observado,
        umbral
    )
    SELECT
        @fecha_alerta,
        N'FUGA_PROBABLE_70',
        N'ALTA',
        N'CLIENTE',
        CONVERT(NVARCHAR(100), s.cliente_key),
        N'Probabilidad de fuga superior a 70%',
        s.probabilidad_fuga,
        0.70
    FROM dbo.FACT_SCORING s
    WHERE s.fecha_key = @fecha_key
      AND s.probabilidad_fuga > 0.70
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.ALERTAS_NEGOCIO a
          WHERE a.regla = N'FUGA_PROBABLE_70'
            AND a.entidad_tipo = N'CLIENTE'
            AND a.entidad_id = CONVERT(
                NVARCHAR(100),
                s.cliente_key
            )
            AND a.fecha_alerta_dia = @fecha_corte
      );

    INSERT dbo.ALERTAS_NEGOCIO (
        fecha_alerta,
        regla,
        severidad,
        entidad_tipo,
        entidad_id,
        sucursal_key,
        mensaje,
        valor_observado,
        umbral
    )
    SELECT
        @fecha_alerta,
        N'STOCK_CRITICO',
        N'ALTA',
        N'INVENTARIO',
        CONCAT(
            i.sucursal_key,
            N'-',
            i.producto_key
        ),
        i.sucursal_key,
        N'Stock actual por debajo del punto de reorden',
        i.stock_actual,
        i.punto_reorden
    FROM dbo.FACT_INVENTARIO i
    WHERE CONVERT(DATE, i.fecha_corte) = @fecha_corte
      AND i.stock_actual <= i.punto_reorden
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.ALERTAS_NEGOCIO a
          WHERE a.regla = N'STOCK_CRITICO'
            AND a.entidad_tipo = N'INVENTARIO'
            AND a.entidad_id = CONCAT(
                i.sucursal_key,
                N'-',
                i.producto_key
            )
            AND a.fecha_alerta_dia = @fecha_corte
      );
END;
GO