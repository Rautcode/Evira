-- Create tables for tracking real-time data

-- Create or update system health status
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[system_health]') AND type in (N'U'))
BEGIN
    CREATE TABLE system_health (
        id INT IDENTITY(1,1) PRIMARY KEY,
        component VARCHAR(50) NOT NULL,
        status BIT NOT NULL DEFAULT 1,
        last_check DATETIME NOT NULL DEFAULT GETDATE(),
        details NTEXT
    );

    -- Insert initial system components
    INSERT INTO system_health (component) VALUES
        ('database'),
        ('wincc'),
        ('email'),
        ('report_engine');
END;

-- Add indexes for report_history if they don't exist
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_report_history_status')
BEGIN
    CREATE INDEX IX_report_history_status ON report_history (status, created_at);
END;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_report_history_template')
BEGIN
    CREATE INDEX IX_report_history_template ON report_history (template_id, created_at);
END;

-- Add indexes for scheduled_tasks if they don't exist
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_scheduled_tasks_status')
BEGIN
    CREATE INDEX IX_scheduled_tasks_status ON scheduled_tasks (status, next_run);
END;

-- Add indexes for activity_log if they don't exist
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_activity_log_type')
BEGIN
    CREATE INDEX IX_activity_log_type ON activity_log (event_type, created_at);
END;
GO

-- Create or update stored procedures for dashboard statistics
CREATE OR ALTER PROCEDURE sp_get_system_health
AS
BEGIN
    SELECT 
        component,
        status,
        last_check,
        details
    FROM system_health
    WHERE last_check >= DATEADD(MINUTE, -5, GETDATE());
END;
GO

CREATE OR ALTER PROCEDURE sp_get_report_stats
    @days_back INT = 7
AS
BEGIN
    SELECT 
        COUNT(*) as total_reports,
        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_reports,
        SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed_reports,
        report_type,
        COUNT(*) as type_count
    FROM report_history
    WHERE created_at >= DATEADD(DAY, -@days_back, GETDATE())
    GROUP BY report_type;
END;
GO

CREATE OR ALTER PROCEDURE sp_get_scheduler_stats
AS
BEGIN
    SELECT 
        COUNT(*) as total_tasks,
        SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_tasks,
        SUM(CASE WHEN next_run <= DATEADD(HOUR, 24, GETDATE()) THEN 1 ELSE 0 END) as upcoming_tasks
    FROM scheduled_tasks;
END;
GO
