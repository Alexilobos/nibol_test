USE BI_RETAIL_ANALYTICS;
GO

IF OBJECT_ID(N'dbo.DIM_FECHA', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DIM_FECHA (
        fecha_key INT NOT NULL
            CONSTRAINT PK_DIM_FECHA PRIMARY KEY,
        fecha DATE NOT NULL
            CONSTRAINT UQ_DIM_FECHA_fecha UNIQUE,
        anio SMALLINT NOT NULL,
        trimestre TINYINT NOT NULL,
        mes TINYINT NOT NULL,
        nombre_mes NVARCHAR(20) NOT NULL,
        semana TINYINT NOT NULL,
        dia TINYINT NOT NULL,
        es_fin_semana BIT NOT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.DIM_SUCURSAL', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DIM_SUCURSAL (
        sucursal_key INT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_DIM_SUCURSAL PRIMARY KEY,
        id_sucursal_origen INT NOT NULL
            CONSTRAINT UQ_DIM_SUCURSAL_origen UNIQUE,
        sucursal NVARCHAR(100) NOT NULL,
        region NVARCHAR(50) NOT NULL,
        ciudad NVARCHAR(100) NOT NULL,
        factor_demanda DECIMAL(9,4) NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.DIM_CLIENTE', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DIM_CLIENTE (
        cliente_key INT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_DIM_CLIENTE PRIMARY KEY,
        id_cliente_origen INT NOT NULL
            CONSTRAINT UQ_DIM_CLIENTE_origen UNIQUE,
        cliente NVARCHAR(100) NOT NULL,
        score_riesgo_base DECIMAL(5,2) NULL,
        lealtad_latente DECIMAL(8,4) NULL,
        preferencia_digital DECIMAL(8,4) NULL,
        ingreso_relativo DECIMAL(10,4) NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.DIM_PRODUCTO', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DIM_PRODUCTO (
        producto_key INT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_DIM_PRODUCTO PRIMARY KEY,
        id_producto_origen INT NOT NULL
            CONSTRAINT UQ_DIM_PRODUCTO_origen UNIQUE,
        producto NVARCHAR(100) NOT NULL,
        categoria NVARCHAR(80) NOT NULL,
        costo_base DECIMAL(12,2) NULL,
        margen_objetivo DECIMAL(7,4) NULL,
        importado BIT NULL,
        popularidad DECIMAL(10,4) NULL
    );
END;
GO