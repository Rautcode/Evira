-- Initialize database tables for the application

-- Report History table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[report_history]') AND type in (N'U'))
BEGIN
    CREATE TABLE report_history (
        id INT IDENTITY(1,1) PRIMARY KEY,
        report_type VARCHAR(50) NOT NULL,
        template_id VARCHAR(50),
        parameters NTEXT,
        status VARCHAR(20) NOT NULL,
        created_at DATETIME DEFAULT GETDATE(),
        completed_at DATETIME,
        error_message NTEXT,
        file_path VARCHAR(255),
        created_by VARCHAR(100)
    );
END;
GO

-- Scheduled Tasks table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[scheduled_tasks]') AND type in (N'U'))
BEGIN
    CREATE TABLE scheduled_tasks (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        task_type VARCHAR(50) NOT NULL,
        schedule VARCHAR(100) NOT NULL,
        parameters NTEXT,
        status VARCHAR(20) DEFAULT 'active',
        last_run DATETIME,
        next_run DATETIME,
        created_at DATETIME DEFAULT GETDATE(),
        modified_at DATETIME,
        created_by VARCHAR(100)
    );
END;
GO

-- Activity Log table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[activity_log]') AND type in (N'U'))
BEGIN
    CREATE TABLE activity_log (
        id INT IDENTITY(1,1) PRIMARY KEY,
        event_type VARCHAR(50) NOT NULL,
        description NTEXT,
        severity VARCHAR(20) DEFAULT 'info',
        created_at DATETIME DEFAULT GETDATE(),
        user_id VARCHAR(100),
        source VARCHAR(50),
        metadata NTEXT
    );
END;
GO

-- WinCC Tags table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[wincc_tags]') AND type in (N'U'))
BEGIN
    CREATE TABLE wincc_tags (
        id INT IDENTITY(1,1) PRIMARY KEY,
        tag_name VARCHAR(100) NOT NULL UNIQUE,
        tag_type VARCHAR(50),
        value FLOAT,
        quality VARCHAR(20),
        timestamp DATETIME,
        last_update DATETIME DEFAULT GETDATE(),
        description NTEXT,
        machine_id VARCHAR(50),
        active BIT DEFAULT 1
    );
END;
GO

-- Create indexes for better performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_report_history_created_at' AND object_id = OBJECT_ID(N'[dbo].[report_history]'))
BEGIN
    CREATE INDEX idx_report_history_created_at ON report_history(created_at);
END;
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_scheduled_tasks_next_run' AND object_id = OBJECT_ID(N'[dbo].[scheduled_tasks]'))
BEGIN
    CREATE INDEX idx_scheduled_tasks_next_run ON scheduled_tasks(next_run);
END;
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_activity_log_created_at' AND object_id = OBJECT_ID(N'[dbo].[activity_log]'))
BEGIN
    CREATE INDEX idx_activity_log_created_at ON activity_log(created_at);
END;
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_wincc_tags_last_update' AND object_id = OBJECT_ID(N'[dbo].[wincc_tags]'))
BEGIN
    CREATE INDEX idx_wincc_tags_last_update ON wincc_tags(last_update);
END;
GO

-- Machines table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Machines]') AND type in (N'U'))
BEGIN
    CREATE TABLE Machines (
        MachineID VARCHAR(50) PRIMARY KEY,
        MachineName VARCHAR(100) NOT NULL,
        MachineType VARCHAR(50),
        Status VARCHAR(20) DEFAULT 'active',
        LastActive DATETIME DEFAULT GETDATE(),
        Location VARCHAR(100),
        Department VARCHAR(100),
        IsActive BIT DEFAULT 1
    );
END;
GO

-- Reports table (for LEFT JOIN in machines listing query)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Reports]') AND type in (N'U'))
BEGIN
    CREATE TABLE Reports (
        ReportID INT IDENTITY(1,1) PRIMARY KEY,
        MachineID VARCHAR(50) FOREIGN KEY REFERENCES Machines(MachineID),
        ReportType VARCHAR(50),
        CreatedAt DATETIME DEFAULT GETDATE()
    );
END;
GO

-- Logs table (for actual SCADA telemetry data)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[logs]') AND type in (N'U'))
BEGIN
    CREATE TABLE logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        machine_id VARCHAR(50) FOREIGN KEY REFERENCES Machines(MachineID),
        shift VARCHAR(20),
        timestamp DATETIME DEFAULT GETDATE(),
        report_type VARCHAR(50),
        parameter VARCHAR(50),
        value FLOAT,
        unit VARCHAR(20),
        status VARCHAR(20) DEFAULT 'Normal'
    );
END;
GO

-- Create indexes on logs table for faster query performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_logs_machine_shift' AND object_id = OBJECT_ID(N'[dbo].[logs]'))
BEGIN
    CREATE INDEX idx_logs_machine_shift ON logs(machine_id, shift, timestamp);
END;
GO
