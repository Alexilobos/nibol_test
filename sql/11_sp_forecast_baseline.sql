USE BI_RETAIL_ANALYTICS;
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

CREATE OR ALTER PROCEDURE dbo.SP_FORECAST
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    SET DATEFIRST 1;

    DECLARE @fecha_corte DATE;
    DECLARE @inicio_horizonte DATE;
    DECLARE @fin_horizonte DATE;
    DECLARE @inicio_validacion DATE;

    SELECT @fecha_corte = MAX(df.fecha)
    FROM dbo.FACT_VENTAS AS fv
    INNER JOIN dbo.DIM_FECHA AS df
        ON df.fecha_key = fv.fecha_key;

    IF @fecha_corte IS NULL
        THROW 50001, 'No existen ventas para generar forecast.', 1;

    SET @inicio_horizonte = DATEADD(
        MONTH,
        1,
        DATEFROMPARTS(YEAR(@fecha_corte), MONTH(@fecha_corte), 1)
    );

    SET @fin_horizonte = EOMONTH(DATEADD(MONTH, 11, @inicio_horizonte));
    SET @inicio_validacion = DATEADD(
        MONTH,
        -6,
        DATEFROMPARTS(YEAR(@fecha_corte), MONTH(@fecha_corte), 1)
    );

    BEGIN TRY
        BEGIN TRANSACTION;

        ;WITH fechas AS (
            SELECT @inicio_horizonte AS fecha
            UNION ALL
            SELECT DATEADD(DAY, 1, fecha)
            FROM fechas
            WHERE fecha < @fin_horizonte
        )
        INSERT INTO dbo.DIM_FECHA (
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
        SELECT
            CONVERT(INT, CONVERT(CHAR(8), fecha, 112)),
            fecha,
            CONVERT(SMALLINT, YEAR(fecha)),
            CONVERT(TINYINT, DATEPART(QUARTER, fecha)),
            CONVERT(TINYINT, MONTH(fecha)),
            CASE MONTH(fecha)
                WHEN 1 THEN N'Enero'
                WHEN 2 THEN N'Febrero'
                WHEN 3 THEN N'Marzo'
                WHEN 4 THEN N'Abril'
                WHEN 5 THEN N'Mayo'
                WHEN 6 THEN N'Junio'
                WHEN 7 THEN N'Julio'
                WHEN 8 THEN N'Agosto'
                WHEN 9 THEN N'Septiembre'
                WHEN 10 THEN N'Octubre'
                WHEN 11 THEN N'Noviembre'
                WHEN 12 THEN N'Diciembre'
            END,
            CONVERT(TINYINT, DATEPART(ISO_WEEK, fecha)),
            CONVERT(TINYINT, DAY(fecha)),
            CONVERT(BIT, CASE WHEN DATEPART(WEEKDAY, fecha) IN (6, 7) THEN 1 ELSE 0 END)
        FROM fechas
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.DIM_FECHA AS df
            WHERE df.fecha = fechas.fecha
        )
        OPTION (MAXRECURSION 0);

        DECLARE @horizonte TABLE (
            fecha DATE NOT NULL PRIMARY KEY,
            fecha_key INT NOT NULL,
            mes_numero TINYINT NOT NULL
        );

        ;WITH meses AS (
            SELECT @inicio_horizonte AS fecha
            UNION ALL
            SELECT DATEADD(MONTH, 1, fecha)
            FROM meses
            WHERE fecha < DATEADD(MONTH, 11, @inicio_horizonte)
        )
        INSERT INTO @horizonte (fecha, fecha_key, mes_numero)
        SELECT
            fecha,
            CONVERT(INT, CONVERT(CHAR(8), fecha, 112)),
            CONVERT(TINYINT, MONTH(fecha))
        FROM meses
        OPTION (MAXRECURSION 12);

        SELECT
            fv.sucursal_key,
            dp.categoria,
            DATEFROMPARTS(YEAR(df.fecha), MONTH(df.fecha), 1) AS mes,
            SUM(CONVERT(DECIMAL(19, 2), fv.ingreso_neto)) AS ventas_reales
        INTO #ventas_mensuales
        FROM dbo.FACT_VENTAS AS fv
        INNER JOIN dbo.DIM_FECHA AS df
            ON df.fecha_key = fv.fecha_key
        INNER JOIN dbo.DIM_PRODUCTO AS dp
            ON dp.producto_key = fv.producto_key
        WHERE df.fecha <= @fecha_corte
        GROUP BY
            fv.sucursal_key,
            dp.categoria,
            DATEFROMPARTS(YEAR(df.fecha), MONTH(df.fecha), 1);

        SELECT
            sucursal_key,
            categoria,
            CONVERT(TINYINT, MONTH(mes)) AS mes_numero,
            AVG(ventas_reales) AS ventas_promedio
        INTO #estacional_grano
        FROM #ventas_mensuales
        GROUP BY sucursal_key, categoria, MONTH(mes);

        SELECT
            sucursal_key,
            categoria,
            AVG(ventas_reales) AS ventas_promedio
        INTO #promedio_grano
        FROM #ventas_mensuales
        GROUP BY sucursal_key, categoria;

        SELECT
            categoria,
            CONVERT(TINYINT, MONTH(mes)) AS mes_numero,
            AVG(ventas_reales) AS ventas_promedio
        INTO #promedio_categoria_mes
        FROM #ventas_mensuales
        GROUP BY categoria, MONTH(mes);

        SELECT
            CONVERT(TINYINT, MONTH(mes)) AS mes_numero,
            AVG(ventas_reales) AS ventas_promedio
        INTO #promedio_mes
        FROM #ventas_mensuales
        GROUP BY MONTH(mes);

        ;WITH predicciones_validacion AS (
            SELECT
                objetivo.sucursal_key,
                objetivo.categoria,
                objetivo.mes,
                objetivo.ventas_reales,
                AVG(historico.ventas_reales) AS ventas_proyectadas
            FROM #ventas_mensuales AS objetivo
            INNER JOIN #ventas_mensuales AS historico
                ON historico.sucursal_key = objetivo.sucursal_key
                AND historico.categoria = objetivo.categoria
                AND MONTH(historico.mes) = MONTH(objetivo.mes)
                AND historico.mes < objetivo.mes
            WHERE objetivo.mes >= @inicio_validacion
            GROUP BY
                objetivo.sucursal_key,
                objetivo.categoria,
                objetivo.mes,
                objetivo.ventas_reales
        )
        SELECT
            sucursal_key,
            categoria,
            CAST(
                AVG(ABS(ventas_reales - ventas_proyectadas))
                AS DECIMAL(16, 4)
            ) AS mae_validacion
        INTO #mae
        FROM predicciones_validacion
        GROUP BY sucursal_key, categoria;

        DELETE ff
        FROM dbo.FACT_FORECAST AS ff
        INNER JOIN dbo.DIM_FECHA AS df
            ON df.fecha_key = ff.fecha_key
        WHERE ff.modelo = N'BASELINE_ESTACIONAL_SQL'
            AND df.fecha >= @inicio_horizonte
            AND df.fecha <= @fin_horizonte;

        ;WITH grano AS (
            SELECT DISTINCT sucursal_key, categoria
            FROM #ventas_mensuales
        )
        INSERT INTO dbo.FACT_FORECAST (
            fecha_key,
            sucursal_key,
            categoria,
            modelo,
            ventas_proyectadas,
            mae_validacion
        )
        SELECT
            h.fecha_key,
            g.sucursal_key,
            g.categoria,
            N'BASELINE_ESTACIONAL_SQL',
            CAST(
                COALESCE(
                    eg.ventas_promedio,
                    pg.ventas_promedio,
                    pcm.ventas_promedio,
                    pm.ventas_promedio,
                    0
                )
                AS DECIMAL(16, 2)
            ),
            mae.mae_validacion
        FROM @horizonte AS h
        CROSS JOIN grano AS g
        LEFT JOIN #estacional_grano AS eg
            ON eg.sucursal_key = g.sucursal_key
            AND eg.categoria = g.categoria
            AND eg.mes_numero = h.mes_numero
        LEFT JOIN #promedio_grano AS pg
            ON pg.sucursal_key = g.sucursal_key
            AND pg.categoria = g.categoria
        LEFT JOIN #promedio_categoria_mes AS pcm
            ON pcm.categoria = g.categoria
            AND pcm.mes_numero = h.mes_numero
        LEFT JOIN #promedio_mes AS pm
            ON pm.mes_numero = h.mes_numero
        LEFT JOIN #mae AS mae
            ON mae.sucursal_key = g.sucursal_key
            AND mae.categoria = g.categoria;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO