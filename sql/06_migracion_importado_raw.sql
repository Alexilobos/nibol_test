USE BI_RETAIL_ANALYTICS;
GO

IF EXISTS (
    SELECT 1
    FROM sys.columns c
    JOIN sys.types t
        ON c.user_type_id = t.user_type_id
    WHERE c.object_id = OBJECT_ID(N'stg.PRODUCTO_RAW')
      AND c.name = N'importado'
      AND t.name = N'bit'
)
BEGIN
    ALTER TABLE stg.PRODUCTO_RAW
    ALTER COLUMN importado NVARCHAR(5) NULL;
END;
GO