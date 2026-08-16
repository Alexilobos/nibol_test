USE BI_RETAIL_ANALYTICS;
GO

IF OBJECT_ID(N'stg.VENTAS_RAW', N'U') IS NULL
BEGIN
    CREATE TABLE stg.VENTAS_RAW (
        id_venta BIGINT NOT NULL,
        fecha DATETIME2(0) NOT NULL,
        id_sucursal INT NOT NULL,
        sucursal NVARCHAR(100) NOT NULL,
        region NVARCHAR(50) NOT NULL,
        vendedor NVARCHAR(100) NOT NULL,
        id_cliente INT NOT NULL,
        cliente NVARCHAR(100) NOT NULL,
        id_producto INT NOT NULL,
        categoria NVARCHAR(80) NOT NULL,
        producto NVARCHAR(100) NOT NULL,
        costo DECIMAL(12,2) NOT NULL,
        precio DECIMAL(12,2) NOT NULL,
        cantidad INT NOT NULL,
        descuento DECIMAL(7,4) NOT NULL,
        ingreso_neto DECIMAL(14,2) NOT NULL,
        utilidad DECIMAL(14,2) NOT NULL,
        metodo_pago NVARCHAR(30) NOT NULL,
        tiempo_entrega INT NOT NULL,
        satisfaccion_cliente TINYINT NOT NULL,
        indice_macroeconomico DECIMAL(10,4) NOT NULL,
        clima NVARCHAR(30) NOT NULL,
        dolar_paralelo DECIMAL(12,4) NOT NULL,
        nivel_trafico DECIMAL(12,2) NOT NULL,
        score_riesgo_cliente DECIMAL(5,2) NOT NULL,
        probabilidad_fuga DECIMAL(7,4) NOT NULL,
        fuga_real_90d BIT NOT NULL,
        indice_inflacion DECIMAL(10,4) NOT NULL,
        es_outlier_simulado BIT NOT NULL,
        compras_previas_cliente INT NOT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.FACT_VENTAS', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FACT_VENTAS (
        venta_key BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_FACT_VENTAS PRIMARY KEY,
        id_venta_origen BIGINT NOT NULL
            CONSTRAINT UQ_FACT_VENTAS_origen UNIQUE,
        fecha_key INT NOT NULL
            CONSTRAINT FK_FACT_VENTAS_FECHA
            REFERENCES dbo.DIM_FECHA(fecha_key),
        sucursal_key INT NOT NULL
            CONSTRAINT FK_FACT_VENTAS_SUCURSAL
            REFERENCES dbo.DIM_SUCURSAL(sucursal_key),
        cliente_key INT NOT NULL
            CONSTRAINT FK_FACT_VENTAS_CLIENTE
            REFERENCES dbo.DIM_CLIENTE(cliente_key),
        producto_key INT NOT NULL
            CONSTRAINT FK_FACT_VENTAS_PRODUCTO
            REFERENCES dbo.DIM_PRODUCTO(producto_key),
        fecha_hora DATETIME2(0) NOT NULL,
        vendedor NVARCHAR(100) NOT NULL,
        costo DECIMAL(12,2) NOT NULL,
        precio DECIMAL(12,2) NOT NULL,
        cantidad INT NOT NULL,
        descuento DECIMAL(7,4) NOT NULL,
        ingreso_neto DECIMAL(14,2) NOT NULL,
        utilidad DECIMAL(14,2) NOT NULL,
        metodo_pago NVARCHAR(30) NOT NULL,
        tiempo_entrega INT NOT NULL,
        satisfaccion_cliente TINYINT NOT NULL,
        indice_macroeconomico DECIMAL(10,4) NOT NULL,
        clima NVARCHAR(30) NOT NULL,
        dolar_paralelo DECIMAL(12,4) NOT NULL,
        nivel_trafico DECIMAL(12,2) NOT NULL,
        score_riesgo_cliente DECIMAL(5,2) NOT NULL,
        probabilidad_fuga DECIMAL(7,4) NOT NULL,
        fuga_real_90d BIT NOT NULL,
        indice_inflacion DECIMAL(10,4) NOT NULL,
        es_outlier_simulado BIT NOT NULL,
        compras_previas_cliente INT NOT NULL,
        CONSTRAINT CK_FACT_VENTAS_cantidad
            CHECK (cantidad > 0),
        CONSTRAINT CK_FACT_VENTAS_descuento
            CHECK (descuento BETWEEN 0 AND 0.60),
        CONSTRAINT CK_FACT_VENTAS_satisfaccion
            CHECK (satisfaccion_cliente BETWEEN 1 AND 5),
        CONSTRAINT CK_FACT_VENTAS_fuga
            CHECK (probabilidad_fuga BETWEEN 0 AND 1)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_FACT_VENTAS_fecha_sucursal'
      AND object_id = OBJECT_ID(N'dbo.FACT_VENTAS')
)
BEGIN
    CREATE INDEX IX_FACT_VENTAS_fecha_sucursal
        ON dbo.FACT_VENTAS(fecha_key, sucursal_key);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_FACT_VENTAS_cliente_fecha'
      AND object_id = OBJECT_ID(N'dbo.FACT_VENTAS')
)
BEGIN
    CREATE INDEX IX_FACT_VENTAS_cliente_fecha
        ON dbo.FACT_VENTAS(cliente_key, fecha_hora);
END;
GO

IF OBJECT_ID(N'stg.INVENTARIO_RAW', N'U') IS NULL
BEGIN
    CREATE TABLE stg.INVENTARIO_RAW (
        fecha_corte DATETIME2(0) NOT NULL,
        id_sucursal INT NOT NULL,
        id_producto INT NOT NULL,
        stock_actual INT NOT NULL,
        punto_reorden INT NOT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.FACT_INVENTARIO', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FACT_INVENTARIO (
        inventario_key BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_FACT_INVENTARIO PRIMARY KEY,
        fecha_key INT NOT NULL
            CONSTRAINT FK_FACT_INVENTARIO_FECHA
            REFERENCES dbo.DIM_FECHA(fecha_key),
        sucursal_key INT NOT NULL
            CONSTRAINT FK_FACT_INVENTARIO_SUCURSAL
            REFERENCES dbo.DIM_SUCURSAL(sucursal_key),
        producto_key INT NOT NULL
            CONSTRAINT FK_FACT_INVENTARIO_PRODUCTO
            REFERENCES dbo.DIM_PRODUCTO(producto_key),
        fecha_corte DATETIME2(0) NOT NULL,
        stock_actual INT NOT NULL,
        punto_reorden INT NOT NULL,
        CONSTRAINT UQ_FACT_INVENTARIO_grano
            UNIQUE (fecha_corte, sucursal_key, producto_key),
        CONSTRAINT CK_FACT_INVENTARIO_stock
            CHECK (stock_actual >= 0),
        CONSTRAINT CK_FACT_INVENTARIO_reorden
            CHECK (punto_reorden >= 0)
    );
END;
GO