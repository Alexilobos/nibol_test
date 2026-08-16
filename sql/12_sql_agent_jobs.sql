USE msdb;
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

IF EXISTS (
    SELECT 1
    FROM dbo.sysjobs
    WHERE name = N'JOB_RETAIL_MICROBATCH'
)
    EXEC dbo.sp_delete_job @job_name = N'JOB_RETAIL_MICROBATCH';

IF EXISTS (
    SELECT 1
    FROM dbo.sysjobs
    WHERE name = N'JOB_RETAIL_FORECAST_MENSUAL'
)
    EXEC dbo.sp_delete_job @job_name = N'JOB_RETAIL_FORECAST_MENSUAL';

IF EXISTS (
    SELECT 1
    FROM dbo.sysschedules
    WHERE name = N'SCHEDULE_RETAIL_MICROBATCH_15M'
)
    EXEC dbo.sp_delete_schedule @schedule_name = N'SCHEDULE_RETAIL_MICROBATCH_15M';

IF EXISTS (
    SELECT 1
    FROM dbo.sysschedules
    WHERE name = N'SCHEDULE_RETAIL_FORECAST_MENSUAL'
)
    EXEC dbo.sp_delete_schedule @schedule_name = N'SCHEDULE_RETAIL_FORECAST_MENSUAL';

IF NOT EXISTS (
    SELECT 1
    FROM dbo.syscategories
    WHERE name = N'Retail Analytics'
        AND category_class = 1
)
    EXEC dbo.sp_add_category
        @class = N'JOB',
        @type = N'LOCAL',
        @name = N'Retail Analytics';
GO

EXEC dbo.sp_add_job
    @job_name = N'JOB_RETAIL_MICROBATCH',
    @enabled = 1,
    @description = N'Carga incremental, scoring de clientes y alertas de negocio.',
    @category_name = N'Retail Analytics',
    @owner_login_name = N'sa';

EXEC dbo.sp_add_jobstep
    @job_name = N'JOB_RETAIL_MICROBATCH',
    @step_name = N'01 - Cargar ventas desde staging',
    @subsystem = N'TSQL',
    @database_name = N'BI_RETAIL_ANALYTICS',
    @command = N'EXEC dbo.SP_CARGA_VENTAS;',
    @on_success_action = 3,
    @on_fail_action = 2,
    @retry_attempts = 3,
    @retry_interval = 5;

EXEC dbo.sp_add_jobstep
    @job_name = N'JOB_RETAIL_MICROBATCH',
    @step_name = N'02 - Cargar inventario desde staging',
    @subsystem = N'TSQL',
    @database_name = N'BI_RETAIL_ANALYTICS',
    @command = N'EXEC dbo.SP_CARGA_INVENTARIO;',
    @on_success_action = 3,
    @on_fail_action = 2,
    @retry_attempts = 3,
    @retry_interval = 5;

EXEC dbo.sp_add_jobstep
    @job_name = N'JOB_RETAIL_MICROBATCH',
    @step_name = N'03 - Calcular scoring de clientes',
    @subsystem = N'TSQL',
    @database_name = N'BI_RETAIL_ANALYTICS',
    @command = N'EXEC dbo.SP_SCORING_CLIENTES;',
    @on_success_action = 3,
    @on_fail_action = 2,
    @retry_attempts = 3,
    @retry_interval = 5;

EXEC dbo.sp_add_jobstep
    @job_name = N'JOB_RETAIL_MICROBATCH',
    @step_name = N'04 - Generar alertas de negocio',
    @subsystem = N'TSQL',
    @database_name = N'BI_RETAIL_ANALYTICS',
    @command = N'EXEC dbo.SP_ALERTAS_NEGOCIO;',
    @on_success_action = 1,
    @on_fail_action = 2,
    @retry_attempts = 3,
    @retry_interval = 5;

EXEC dbo.sp_add_schedule
    @schedule_name = N'SCHEDULE_RETAIL_MICROBATCH_15M',
    @enabled = 1,
    @freq_type = 4,
    @freq_interval = 1,
    @freq_subday_type = 4,
    @freq_subday_interval = 15,
    @active_start_time = 000000;

EXEC dbo.sp_attach_schedule
    @job_name = N'JOB_RETAIL_MICROBATCH',
    @schedule_name = N'SCHEDULE_RETAIL_MICROBATCH_15M';

EXEC dbo.sp_add_jobserver
    @job_name = N'JOB_RETAIL_MICROBATCH',
    @server_name = N'(LOCAL)';
GO

EXEC dbo.sp_add_job
    @job_name = N'JOB_RETAIL_FORECAST_MENSUAL',
    @enabled = 1,
    @description = N'Forecast estacional mensual de ventas.',
    @category_name = N'Retail Analytics',
    @owner_login_name = N'sa';

EXEC dbo.sp_add_jobstep
    @job_name = N'JOB_RETAIL_FORECAST_MENSUAL',
    @step_name = N'01 - Generar forecast mensual',
    @subsystem = N'TSQL',
    @database_name = N'BI_RETAIL_ANALYTICS',
    @command = N'EXEC dbo.SP_FORECAST;',
    @on_success_action = 1,
    @on_fail_action = 2,
    @retry_attempts = 3,
    @retry_interval = 10;

EXEC dbo.sp_add_schedule
    @schedule_name = N'SCHEDULE_RETAIL_FORECAST_MENSUAL',
    @enabled = 1,
    @freq_type = 16,
    @freq_recurrence_factor = 1,
    @freq_interval = 1,
    @active_start_time = 030000;

EXEC dbo.sp_attach_schedule
    @job_name = N'JOB_RETAIL_FORECAST_MENSUAL',
    @schedule_name = N'SCHEDULE_RETAIL_FORECAST_MENSUAL';

EXEC dbo.sp_add_jobserver
    @job_name = N'JOB_RETAIL_FORECAST_MENSUAL',
    @server_name = N'(LOCAL)';
GO