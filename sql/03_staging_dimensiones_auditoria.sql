USE BI_RETAIL_ANALYTICS;
GO

IF OBJECT_ID(N'stg.SUCURSAL_RAW', N'U') IS NULL
BEGIN
    CREATE TABLE stg.SUCURSAL_RAW (
        id_sucursal INT NOT NULL,
        sucursal NVARCHAR(100) NOT NULL,
        region NVARCHAR(50) NOT NULL,
        ciudad NVARCHAR(100) NOT NULL,
        factor_demanda_sucursal DECIMAL(9,4) NULL
    );
END;
GO

IF OBJECT_ID(N'stg.CLIENTE_RAW', N'U') IS NULL
BEGIN
    CREATE TABLE stg.CLIENTE_RAW (
        id_cliente INT NOT NULL,
        cliente NVARCHAR(100) NOT NULL,
        score_riesgo_cliente_base DECIMAL(5,2) NULL,
        lealtad_latente DECIMAL(8,4) NULL,
        preferencia_digital DECIMAL(8,4) NULL,
        ingreso_relativo DECIMAL(10,4) NULL
    );
END;
GO

IF OBJECT_ID(N'stg.PRODUCTO_RAW', N'U') IS NULL
BEGIN
    CREATE TABLE stg.PRODUCTO_RAW (
        id_producto INT NOT NULL,
        producto NVARCHAR(100) NOT NULL,
        categoria NVARCHAR(80) NOT NULL,
        costo_base DECIMAL(12,2) NULL,
        margen_objetivo DECIMAL(7,4) NULL,
        importado BIT NULL,
        popularidad DECIMAL(10,4) NULL
    );
END;
GO

IF OBJECT_ID(N'stg.FECHA_RAW', N'U') IS NULL
BEGIN
    CREATE TABLE stg.FECHA_RAW (
        fecha_dia DATE NOT NULL,
        indice_inflacion DECIMAL(10,4) NOT NULL,
        dolar_paralelo DECIMAL(12,4) NOT NULL,
        indice_macroeconomico DECIMAL(10,4) NOT NULL,
        demanda_calendario DECIMAL(10,6) NOT NULL
    );
END;
GO

IF OBJECT_ID(N'aud.CARGAS', N'U') IS NULL
BEGIN
    CREATE TABLE aud.CARGAS (
        auditoria_id BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_AUD_CARGAS PRIMARY KEY,
        carga_id UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT DF_AUD_CARGAS_id DEFAULT NEWID(),
        proceso NVARCHAR(100) NOT NULL,
        inicio DATETIME2(0) NOT NULL
            CONSTRAINT DF_AUD_CARGAS_inicio DEFAULT SYSUTCDATETIME(),
        fin DATETIME2(0) NULL,
        estado NVARCHAR(20) NOT NULL,
        filas_leidas INT NOT NULL
            CONSTRAINT DF_AUD_CARGAS_leidas DEFAULT 0,
        filas_insertadas INT NOT NULL
            CONSTRAINT DF_AUD_CARGAS_insertadas DEFAULT 0,
        filas_rechazadas INT NOT NULL
            CONSTRAINT DF_AUD_CARGAS_rechazadas DEFAULT 0,
        mensaje_error NVARCHAR(2000) NULL
    );
END;
GO

IF OBJECT_ID(N'aud.RECHAZOS', N'U') IS NULL
BEGIN
    CREATE TABLE aud.RECHAZOS (
        rechazo_id BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_AUD_RECHAZOS PRIMARY KEY,
        auditoria_id BIGINT NOT NULL
            CONSTRAINT FK_AUD_RECHAZOS_CARGAS
            REFERENCES aud.CARGAS(auditoria_id),
        tabla_origen NVARCHAR(100) NOT NULL,
        clave_origen NVARCHAR(200) NULL,
        motivo NVARCHAR(1000) NOT NULL,
        fecha_registro DATETIME2(0) NOT NULL
            CONSTRAINT DF_AUD_RECHAZOS_fecha DEFAULT SYSUTCDATETIME()
    );
END;
GO