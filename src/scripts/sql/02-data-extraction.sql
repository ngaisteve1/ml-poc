-- =====================================================================
-- ML POC: Data Extraction Queries
-- Purpose: Extract historical archive data for ML model training
-- Use Case: Predict archive volume and storage savings
-- =====================================================================

-- =====================================================================
-- Query 1: Monthly Archive Volume and Trends
-- Description: Aggregates archived files by month to show archive volume trends
-- Used for: Training regression model on archive volume
-- =====================================================================
SELECT 
    YEAR([Created]) AS [Year],
    MONTH([Created]) AS [Month],
    DATEFROMPARTS(YEAR([Created]), MONTH([Created]), 1) AS [MonthStart],
    COUNT(*) AS [FilesArchivedCount],
    SUM([Size]) AS [TotalSizeArchivedBytes],
    CAST(SUM([Size]) AS FLOAT) / 1024 / 1024 / 1024 AS [TotalSizeArchivedGB],
    AVG([Size]) AS [AvgFileSizeBytes],
    MIN([Size]) AS [MinFileSizeBytes],
    MAX([Size]) AS [MaxFileSizeBytes],
    COUNT(DISTINCT [TenantId]) AS [UniqueTenants],
    COUNT(DISTINCT [SiteId]) AS [UniqueSites]
FROM [dbo].[ArchivedFile]
WHERE [Archived] = 1 
    AND [ArchivedAt] IS NOT NULL
GROUP BY 
    YEAR([Created]), 
    MONTH([Created])
ORDER BY [Year] DESC, [Month] DESC;

-- =====================================================================
-- Query 2: File Type Distribution and Archive Patterns
-- Description: Shows file extension trends and their archive frequency
-- Used for: Feature engineering on file types
-- =====================================================================
SELECT 
    CASE 
        WHEN [Filename] LIKE '%.pdf' THEN 'PDF'
        WHEN [Filename] LIKE '%.docx' OR [Filename] LIKE '%.doc' THEN 'Word'
        WHEN [Filename] LIKE '%.xlsx' OR [Filename] LIKE '%.xls' THEN 'Excel'
        WHEN [Filename] LIKE '%.pptx' OR [Filename] LIKE '%.ppt' THEN 'PowerPoint'
        WHEN [Filename] LIKE '%.zip' OR [Filename] LIKE '%.rar' OR [Filename] LIKE '%.7z' THEN 'Archive'
        WHEN [Filename] LIKE '%.jpg' OR [Filename] LIKE '%.jpeg' OR [Filename] LIKE '%.png' OR [Filename] LIKE '%.gif' THEN 'Image'
        WHEN [Filename] LIKE '%.txt' THEN 'Text'
        WHEN [Filename] LIKE '%.csv' THEN 'CSV'
        ELSE 'Other'
    END AS [FileType],
    COUNT(*) AS [FilesCount],
    SUM([Size]) AS [TotalSizeBytes],
    CAST(SUM([Size]) AS FLOAT) / 1024 / 1024 / 1024 AS [TotalSizeGB],
    AVG([Size]) AS [AvgFileSizeBytes],
    CAST(COUNT(*) AS FLOAT) / (SELECT COUNT(*) FROM [dbo].[ArchivedFile] WHERE [Archived] = 1) * 100 AS [PercentOfTotal],
    MIN([Created]) AS [EarliestArchiveDate],
    MAX([Created]) AS [LatestArchiveDate]
FROM [dbo].[ArchivedFile]
WHERE [Archived] = 1 
    AND [ArchivedAt] IS NOT NULL
GROUP BY 
    CASE 
        WHEN [Filename] LIKE '%.pdf' THEN 'PDF'
        WHEN [Filename] LIKE '%.docx' OR [Filename] LIKE '%.doc' THEN 'Word'
        WHEN [Filename] LIKE '%.xlsx' OR [Filename] LIKE '%.xls' THEN 'Excel'
        WHEN [Filename] LIKE '%.pptx' OR [Filename] LIKE '%.ppt' THEN 'PowerPoint'
        WHEN [Filename] LIKE '%.zip' OR [Filename] LIKE '%.rar' OR [Filename] LIKE '%.7z' THEN 'Archive'
        WHEN [Filename] LIKE '%.jpg' OR [Filename] LIKE '%.jpeg' OR [Filename] LIKE '%.png' OR [Filename] LIKE '%.gif' THEN 'Image'
        WHEN [Filename] LIKE '%.txt' THEN 'Text'
        WHEN [Filename] LIKE '%.csv' THEN 'CSV'
        ELSE 'Other'
    END
ORDER BY [FilesCount] DESC;

-- =====================================================================
-- Query 3: Storage Space Saved (Deleted Files)
-- Description: Shows files deleted after archiving = storage saved
-- Used for: Calculate storage savings metric
-- =====================================================================
SELECT 
    YEAR([Deleted]) AS [Year],
    MONTH([Deleted]) AS [Month],
    DATEFROMPARTS(YEAR([Deleted]), MONTH([Deleted]), 1) AS [MonthStart],
    COUNT(*) AS [DeletedFilesCount],
    SUM([Size]) AS [StorageSavedBytes],
    CAST(SUM([Size]) AS FLOAT) / 1024 / 1024 / 1024 AS [StorageSavedGB],
    AVG([Size]) AS [AvgDeletedFileSizeBytes],
    COUNT(DISTINCT [TenantId]) AS [TenantsWithDeletions],
    COUNT(DISTINCT [SiteId]) AS [SitesWithDeletions]
FROM [dbo].[DeletedFile]
WHERE [Deleted] IS NOT NULL
GROUP BY 
    YEAR([Deleted]), 
    MONTH([Deleted])
ORDER BY [Year] DESC, [Month] DESC;

-- =====================================================================
-- Query 4: Archive Job Execution History
-- Description: Shows archive job execution patterns and frequency
-- Used for: Understanding archive scheduling and recurrence
-- =====================================================================
SELECT 
    aj.[Id] AS [JobId],
    aj.[TenantId],
    aj.[JobType],
    aj.[JobMode],
    aj.[Enabled],
    COUNT(af.[Id]) AS [TotalFilesArchived],
    SUM(af.[Size]) AS [TotalVolumeArchived],
    CAST(SUM(af.[Size]) AS FLOAT) / 1024 / 1024 / 1024 AS [TotalVolumeArchivedGB],
    MIN(af.[Created]) AS [FirstArchiveDate],
    MAX(af.[Created]) AS [LastArchiveDate],
    DATEDIFF(DAY, MIN(af.[Created]), MAX(af.[Created])) AS [DaysBetweenFirstAndLast],
    CASE 
        WHEN COUNT(af.[Id]) = 0 THEN NULL
        ELSE CAST(DATEDIFF(DAY, MIN(af.[Created]), MAX(af.[Created])) AS FLOAT) / CAST(COUNT(af.[Id]) - 1 AS FLOAT)
    END AS [AvgDaysBetweenArchives]
FROM [dbo].[ArchiveJob] aj
LEFT JOIN [dbo].[ArchivedFile] af ON af.[SiteId] = aj.[SiteId] 
    AND af.[Archived] = 1
GROUP BY 
    aj.[Id],
    aj.[TenantId],
    aj.[JobType],
    aj.[JobMode],
    aj.[Enabled]
ORDER BY [TotalFilesArchived] DESC;

-- =====================================================================
-- Query 5: Tenant-Level Archive Performance
-- Description: Aggregated metrics by tenant for prediction
-- Used for: Tenant-level forecasting features
-- =====================================================================
SELECT 
    af.[TenantId],
    COUNT(af.[Id]) AS [TotalFilesArchived],
    COUNT(DISTINCT af.[SiteId]) AS [UniqueSitesArchived],
    SUM(af.[Size]) AS [TotalArchiveVolumeBytes],
    CAST(SUM(af.[Size]) AS FLOAT) / 1024 / 1024 / 1024 AS [TotalArchiveVolumeGB],
    AVG(af.[Size]) AS [AvgFileSizeBytes],
    MIN(af.[Created]) AS [FirstArchiveDate],
    MAX(af.[Created]) AS [LastArchiveDate],
    DATEDIFF(DAY, MIN(af.[Created]), MAX(af.[Created])) AS [ArchiveActivitySpanDays],
    df.[DeletedFileCount],
    CAST(df.[DeletedFileSize] AS FLOAT) / 1024 / 1024 / 1024 AS [StorageSavedGB],
    CASE 
        WHEN SUM(af.[Size]) > 0 
        THEN CAST(df.[DeletedFileSize] AS FLOAT) / CAST(SUM(af.[Size]) AS FLOAT) * 100 
        ELSE 0 
    END AS [DeletedPercentage]
FROM [dbo].[ArchivedFile] af
LEFT JOIN (
    SELECT 
        [TenantId],
        COUNT(*) AS [DeletedFileCount],
        SUM([Size]) AS [DeletedFileSize]
    FROM [dbo].[DeletedFile]
    WHERE [Deleted] IS NOT NULL
    GROUP BY [TenantId]
) df ON af.[TenantId] = df.[TenantId]
WHERE af.[Archived] = 1
GROUP BY 
    af.[TenantId],
    df.[DeletedFileCount],
    df.[DeletedFileSize]
ORDER BY [TotalArchiveVolumeBytes] DESC;

-- =====================================================================
-- Query 6: Weekly Archive Trend Data
-- Description: Weekly aggregation for more granular time-series analysis
-- Used for: Time-series forecasting model
-- =====================================================================
SELECT 
    YEAR(af.[Created]) AS [Year],
    MONTH(af.[Created]) AS [Month],
    WEEK = DATEPART(WEEK, af.[Created]),
    DATEFROMPARTS(YEAR(af.[Created]), MONTH(af.[Created]), DAY(af.[Created])) AS [Date],
    DATEPART(WEEKDAY, af.[Created]) AS [DayOfWeek],
    COUNT(af.[Id]) AS [FilesArchivedCount],
    SUM(af.[Size]) AS [VolumeBytesArchived],
    CAST(SUM(af.[Size]) AS FLOAT) / 1024 / 1024 / 1024 AS [VolumeGBArchived],
    COUNT(DISTINCT af.[TenantId]) AS [ActiveTenants],
    COUNT(DISTINCT af.[SiteId]) AS [ActiveSites]
FROM [dbo].[ArchivedFile] af
WHERE af.[Archived] = 1 
    AND af.[ArchivedAt] IS NOT NULL
GROUP BY 
    YEAR(af.[Created]),
    MONTH(af.[Created]),
    DATEPART(WEEK, af.[Created]),
    DATEFROMPARTS(YEAR(af.[Created]), MONTH(af.[Created]), DAY(af.[Created])),
    DATEPART(WEEKDAY, af.[Created])
ORDER BY [Year] DESC, [Month] DESC, [WEEK] DESC;

-- =====================================================================
-- Query 7: Archive State Distribution
-- Description: Shows file states and potential issues
-- Used for: Data quality and state transition analysis
-- =====================================================================
SELECT 
    CASE [State]
        WHEN 0 THEN 'Pending'
        WHEN 1 THEN 'Archiving'
        WHEN 2 THEN 'Archived'
        WHEN 3 THEN 'Failed'
        WHEN 4 THEN 'Restored'
        ELSE 'Unknown'
    END AS [FileState],
    COUNT(*) AS [FileCount],
    SUM([Size]) AS [TotalSizeBytes],
    CAST(SUM([Size]) AS FLOAT) / 1024 / 1024 / 1024 AS [TotalSizeGB],
    CAST(COUNT(*) AS FLOAT) / (SELECT COUNT(*) FROM [dbo].[ArchivedFile]) * 100 AS [PercentOfTotal],
    COUNT([ErrorCode]) AS [FilesWithErrors],
    COUNT(DISTINCT [TenantId]) AS [UniqueTenants]
FROM [dbo].[ArchivedFile]
GROUP BY [State]
ORDER BY [FileCount] DESC;

-- =====================================================================
-- Query 8: Archive Size Distribution (Quantiles)
-- Description: Shows file size distribution patterns
-- Used for: Understanding archive patterns and outliers
-- =====================================================================
SELECT 
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY [Size]) OVER () AS [Q1_FileSizeBytes],
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY [Size]) OVER () AS [Q2_MedianFileSizeBytes],
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY [Size]) OVER () AS [Q3_FileSizeBytes],
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY [Size]) OVER () AS [P95_FileSizeBytes],
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY [Size]) OVER () AS [P99_FileSizeBytes],
    COUNT(*) AS [TotalFiles],
    SUM([Size]) AS [TotalVolumeBytes],
    CAST(SUM([Size]) AS FLOAT) / 1024 / 1024 / 1024 AS [TotalVolumeGB]
FROM [dbo].[ArchivedFile]
WHERE [Archived] = 1
GROUP BY 1;

-- =====================================================================
-- Query 9: Consolidated Training Dataset
-- Description: Combines monthly archive volume with all relevant features
-- Used for: Direct ML model training
-- =====================================================================
SELECT 
    DATEFROMPARTS(YEAR(af.[Created]), MONTH(af.[Created]), 1) AS [MonthStart],
    YEAR(af.[Created]) AS [Year],
    MONTH(af.[Created]) AS [Month],
    -- Volume metrics
    COUNT(af.[Id]) AS [FilesArchivedCount],
    SUM(af.[Size]) AS [VolumeBytesArchived],
    CAST(SUM(af.[Size]) AS FLOAT) / 1024 / 1024 / 1024 AS [VolumeGBArchived],
    AVG(af.[Size]) AS [AvgFileSizeBytes],
    -- Storage saved metrics
    SUM(CASE WHEN df.[Deleted] IS NOT NULL THEN df.[Size] ELSE 0 END) AS [StorageSavedBytes],
    CAST(SUM(CASE WHEN df.[Deleted] IS NOT NULL THEN df.[Size] ELSE 0 END) AS FLOAT) / 1024 / 1024 / 1024 AS [StorageSavedGB],
    -- Engagement metrics
    COUNT(DISTINCT af.[TenantId]) AS [ActiveTenants],
    COUNT(DISTINCT af.[SiteId]) AS [ActiveSites],
    -- File type distribution
    SUM(CASE WHEN af.[Filename] LIKE '%.pdf' THEN 1 ELSE 0 END) AS [PDFCount],
    SUM(CASE WHEN af.[Filename] LIKE '%.docx' OR af.[Filename] LIKE '%.doc' THEN 1 ELSE 0 END) AS [WordCount],
    SUM(CASE WHEN af.[Filename] LIKE '%.xlsx' OR af.[Filename] LIKE '%.xls' THEN 1 ELSE 0 END) AS [ExcelCount],
    -- Error metrics
    SUM(CASE WHEN af.[ErrorCode] <> 0 THEN 1 ELSE 0 END) AS [FilesWithErrors]
FROM [dbo].[ArchivedFile] af
LEFT JOIN [dbo].[DeletedFile] df ON af.[UniqueId] = df.[UniqueId] 
    AND af.[SiteId] = df.[SiteId]
    AND af.[TenantId] = df.[TenantId]
WHERE af.[Archived] = 1
GROUP BY 
    DATEFROMPARTS(YEAR(af.[Created]), MONTH(af.[Created]), 1),
    YEAR(af.[Created]),
    MONTH(af.[Created])
ORDER BY [Year] DESC, [Month] DESC;

-- =====================================================================
-- Query 10: Export for CSV - Simplified Training Dataset
-- Description: Clean, flattened dataset ready for Python/ML
-- Used for: Direct export to CSV for ML training
-- =====================================================================
SELECT 
    FORMAT(DATEFROMPARTS(YEAR(af.[Created]), MONTH(af.[Created]), 1), 'yyyy-MM-01') AS [Period],
    COUNT(af.[Id]) AS [files_archived],
    CAST(SUM(af.[Size]) AS FLOAT) / 1024 / 1024 / 1024 AS [volume_gb],
    CAST(SUM(CASE WHEN df.[Deleted] IS NOT NULL THEN df.[Size] ELSE 0 END) AS FLOAT) / 1024 / 1024 / 1024 AS [storage_saved_gb],
    COUNT(DISTINCT af.[TenantId]) AS [active_tenants],
    COUNT(DISTINCT af.[SiteId]) AS [active_sites],
    AVG(af.[Size]) AS [avg_file_size_bytes],
    SUM(CASE WHEN af.[Filename] LIKE '%.pdf' THEN 1 ELSE 0 END) AS [file_type_pdf],
    SUM(CASE WHEN af.[Filename] LIKE '%.docx' OR af.[Filename] LIKE '%.doc' THEN 1 ELSE 0 END) AS [file_type_word],
    SUM(CASE WHEN af.[Filename] LIKE '%.xlsx' OR af.[Filename] LIKE '%.xls' THEN 1 ELSE 0 END) AS [file_type_excel],
    SUM(CASE WHEN af.[Filename] LIKE '%.jpg' OR af.[Filename] LIKE '%.jpeg' OR af.[Filename] LIKE '%.png' THEN 1 ELSE 0 END) AS [file_type_image],
    SUM(CASE WHEN af.[ErrorCode] <> 0 THEN 1 ELSE 0 END) AS [files_with_errors],
    CAST(SUM(CASE WHEN af.[ErrorCode] <> 0 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(af.[Id]) * 100 AS [error_rate_percent]
FROM [dbo].[ArchivedFile] af
LEFT JOIN [dbo].[DeletedFile] df ON af.[UniqueId] = df.[UniqueId] 
    AND af.[SiteId] = df.[SiteId]
    AND af.[TenantId] = df.[TenantId]
WHERE af.[Archived] = 1 
    AND af.[ArchivedAt] IS NOT NULL
GROUP BY 
    YEAR(af.[Created]),
    MONTH(af.[Created])
ORDER BY [Period];
