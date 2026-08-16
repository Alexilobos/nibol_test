USE BI_RETAIL_ANALYTICS;
GO

CREATE OR ALTER PROCEDURE dbo.SP_SCORING_CLIENTES
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @fecha_corte DATE;
    DECLARE @fecha_key INT;

    SELECT @fecha_corte = CONVERT(DATE, MAX(fecha_hora))
    FROM dbo.FACT_VENTAS;

    SET @fecha_key = CONVERT(
        INT,
        CONVERT(CHAR(8), @fecha_corte, 112)
    );

    BEGIN TRANSACTION;

    DELETE FROM dbo.FACT_SCORING
    WHERE fecha_key = @fecha_key;

    ;WITH comportamiento AS (
        SELECT
            cliente_key,
            COUNT(*) AS frecuencia_90d,
            SUM(utilidad) AS utilidad_90d,
            AVG(
                CONVERT(DECIMAL(5,2), satisfaccion_cliente)
            ) AS satisfaccion_promedio,
            AVG(score_riesgo_cliente) AS riesgo_mora,
            AVG(probabilidad_fuga) AS probabilidad_fuga
        FROM dbo.FACT_VENTAS
        WHERE fecha_hora >= DATEADD(DAY, -89, @fecha_corte)
        GROUP BY cliente_key
    ),
    calculo AS (
        SELECT
            *,
            CAST(
                40.0 * IIF(
                    frecuencia_90d >= 3,
                    1.0,
                    frecuencia_90d / 3.0
                )
                + 30.0 * IIF(
                    utilidad_90d >= 300,
                    1.0,
                    CASE
                        WHEN utilidad_90d < 0 THEN 0
                        ELSE utilidad_90d / 300.0
                    END
                )
                + 20.0 * (satisfaccion_promedio / 5.0)
                + 10.0 * (1 - riesgo_mora / 100.0)
                AS DECIMAL(6,2)
            ) AS score_cliente
        FROM comportamiento
    )
    INSERT dbo.FACT_SCORING (
        fecha_key,
        cliente_key,
        score_cliente,
        segmento,
        frecuencia_90d,
        utilidad_90d,
        satisfaccion_promedio,
        riesgo_mora,
        probabilidad_fuga
    )
    SELECT
        @fecha_key,
        cliente_key,
        score_cliente,
        CASE
            WHEN score_cliente > 90 THEN N'VIP'
            WHEN score_cliente >= 70 THEN N'Premium'
            WHEN score_cliente >= 50 THEN N'Riesgo medio'
            ELSE N'Riesgo alto'
        END,
        frecuencia_90d,
        utilidad_90d,
        satisfaccion_promedio,
        riesgo_mora,
        probabilidad_fuga
    FROM calculo;

    COMMIT TRANSACTION;
END;
GO