USE BI_RETAIL_ANALYTICS;
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

IF OBJECT_ID(N'dbo.FACT_FORECAST', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FACT_FORECAST (
        forecast_key BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_FACT_FORECAST PRIMARY KEY,
        fecha_key INT NOT NULL
            CONSTRAINT FK_FACT_FORECAST_FECHA
            REFERENCES dbo.DIM_FECHA(fecha_key),
        sucursal_key INT NULL
            CONSTRAINT FK_FACT_FORECAST_SUCURSAL
            REFERENCES dbo.DIM_SUCURSAL(sucursal_key),
        categoria NVARCHAR(80) NOT NULL,
        modelo NVARCHAR(50) NOT NULL,
        ventas_proyectadas DECIMAL(16,2) NOT NULL,
        mae_validacion DECIMAL(16,4) NULL,
        fecha_calculo DATETIME2(0) NOT NULL
            CONSTRAINT DF_FACT_FORECAST_calculo DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_FACT_FORECAST_grano
            UNIQUE (fecha_key, sucursal_key, categoria, modelo)
    );
END;
GO

IF OBJECT_ID(N'dbo.FACT_SCORING', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FACT_SCORING (
        scoring_key BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_FACT_SCORING PRIMARY KEY,
        fecha_key INT NOT NULL
            CONSTRAINT FK_FACT_SCORING_FECHA
            REFERENCES dbo.DIM_FECHA(fecha_key),
        cliente_key INT NOT NULL
            CONSTRAINT FK_FACT_SCORING_CLIENTE
            REFERENCES dbo.DIM_CLIENTE(cliente_key),
        score_cliente DECIMAL(6,2) NOT NULL,
        segmento NVARCHAR(30) NOT NULL,
        frecuencia_90d INT NOT NULL,
        utilidad_90d DECIMAL(14,2) NOT NULL,
        satisfaccion_promedio DECIMAL(5,2) NOT NULL,
        riesgo_mora DECIMAL(5,2) NOT NULL,
        probabilidad_fuga DECIMAL(7,4) NOT NULL,
        fecha_calculo DATETIME2(0) NOT NULL
            CONSTRAINT DF_FACT_SCORING_calculo DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_FACT_SCORING_grano
            UNIQUE (fecha_key, cliente_key),
        CONSTRAINT CK_FACT_SCORING_score
            CHECK (score_cliente BETWEEN 0 AND 100),
        CONSTRAINT CK_FACT_SCORING_fuga
            CHECK (probabilidad_fuga BETWEEN 0 AND 1)
    );
END;
GO

IF OBJECT_ID(N'dbo.ALERTAS_NEGOCIO', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ALERTAS_NEGOCIO (
        alerta_id BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_ALERTAS_NEGOCIO PRIMARY KEY,
        fecha_alerta DATETIME2(0) NOT NULL
            CONSTRAINT DF_ALERTAS_fecha DEFAULT SYSUTCDATETIME(),
        regla NVARCHAR(80) NOT NULL,
        severidad NVARCHAR(20) NOT NULL,
        entidad_tipo NVARCHAR(30) NOT NULL,
        entidad_id NVARCHAR(100) NOT NULL,
        sucursal_key INT NULL
            CONSTRAINT FK_ALERTAS_SUCURSAL
            REFERENCES dbo.DIM_SUCURSAL(sucursal_key),
        mensaje NVARCHAR(500) NOT NULL,
        valor_observado DECIMAL(18,4) NULL,
        umbral DECIMAL(18,4) NULL,
        estado NVARCHAR(20) NOT NULL
            CONSTRAINT DF_ALERTAS_estado DEFAULT N'ABIERTA',
        fecha_alerta_dia AS CONVERT(DATE, fecha_alerta) PERSISTED,
        CONSTRAINT UQ_ALERTAS_ventana
            UNIQUE (
                regla,
                entidad_tipo,
                entidad_id,
                fecha_alerta_dia
            )
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_ALERTAS_estado_fecha'
      AND object_id = OBJECT_ID(N'dbo.ALERTAS_NEGOCIO')
)
BEGIN
    CREATE INDEX IX_ALERTAS_estado_fecha
        ON dbo.ALERTAS_NEGOCIO(estado, fecha_alerta DESC);
END;
GO