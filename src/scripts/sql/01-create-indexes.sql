-- =====================================================================
-- ML POC: Database Indexes for Query Performance Optimization
-- Purpose: Dramatically improve query execution speed
-- Expected Performance Gain: 70-85% faster
-- Estimated Creation Time: 5-15 minutes (depends on table sizes)
-- =====================================================================

-- =====================================================================
-- PRE-EXECUTION CHECKS
-- =====================================================================

-- Check current table sizes before creating indexes
PRINT '=== TABLE SIZE ANALYSIS ===';
SELECT 
    'ArchivedFile' AS [Table],
    COUNT(*) AS [RowCount],
    CAST(SUM(CAST(ac.total_pages AS BIGINT)) * 8 / 1024 AS DECIMAL(18,2)) AS [SizeInMB]
FROM [dbo].[ArchivedFile]
CROSS APPLY (
    SELECT total_pages FROM sys.dm_db_partition_stats 
    WHERE object_id = OBJECT_ID('dbo.ArchivedFile')
) ac

UNION ALL

SELECT 
    'DeletedFile' AS [Table],
    COUNT(*) AS [RowCount],
    CAST(SUM(CAST(ac.total_pages AS BIGINT)) * 8 / 1024 AS DECIMAL(18,2)) AS [SizeInMB]
FROM [dbo].[DeletedFile]
CROSS APPLY (
    SELECT total_pages FROM sys.dm_db_partition_stats 
    WHERE object_id = OBJECT_ID('dbo.DeletedFile')
) ac

UNION ALL

SELECT 
    'ArchiveJob' AS [Table],
    COUNT(*) AS [RowCount],
    CAST(SUM(CAST(ac.total_pages AS BIGINT)) * 8 / 1024 AS DECIMAL(18,2)) AS [SizeInMB]
FROM [dbo].[ArchiveJob]
CROSS APPLY (
    SELECT total_pages FROM sys.dm_db_partition_stats 
    WHERE object_id = OBJECT_ID('dbo.ArchiveJob')
) ac;

-- =====================================================================
-- INDEX 1: ArchivedFile - For Monthly Aggregation (Queries 1, 6, 9, 10)
-- =====================================================================
-- This is the most critical index for ML queries
-- Covers: Year/Month grouping, Archived filter, Size aggregation
-- Expected improvement: 60-80% faster for Queries 1, 6, 9, 10

IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_ArchivedFile_Created_Archived' AND object_id = OBJECT_ID('[dbo].[ArchivedFile]'))
BEGIN
    PRINT 'Dropping existing index: IX_ArchivedFile_Created_Archived';
    DROP INDEX [IX_ArchivedFile_Created_Archived] ON [dbo].[ArchivedFile];
END

PRINT 'Creating index: IX_ArchivedFile_Created_Archived';
CREATE NONCLUSTERED INDEX [IX_ArchivedFile_Created_Archived]
ON [dbo].[ArchivedFile] ([Created], [Archived])
INCLUDE ([Id], [Size], [TenantId], [SiteId], [Filename], [ErrorCode], [UniqueId])
WHERE [Archived] = 1;

-- =====================================================================
-- INDEX 2: ArchivedFile - For UniqueId JOIN (Queries 3, 9, 10)
-- =====================================================================
-- Covers: JOIN with DeletedFile on UniqueId
-- Expected improvement: 50-70% faster for Queries 3, 9, 10

IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_ArchivedFile_UniqueId' AND object_id = OBJECT_ID('[dbo].[ArchivedFile]'))
BEGIN
    PRINT 'Dropping existing index: IX_ArchivedFile_UniqueId';
    DROP INDEX [IX_ArchivedFile_UniqueId] ON [dbo].[ArchivedFile];
END

PRINT 'Creating index: IX_ArchivedFile_UniqueId';
CREATE NONCLUSTERED INDEX [IX_ArchivedFile_UniqueId]
ON [dbo].[ArchivedFile] ([UniqueId], [SiteId], [TenantId])
INCLUDE ([Size], [Created], [Archived], [Filename], [ErrorCode], [ArchivedAt]);

-- =====================================================================
-- INDEX 3: DeletedFile - For Storage Saved Queries (Queries 3, 5)
-- =====================================================================
-- Covers: Deleted date filter for storage savings calculation
-- Expected improvement: 40-60% faster for Queries 3, 5

IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_DeletedFile_Deleted' AND object_id = OBJECT_ID('[dbo].[DeletedFile]'))
BEGIN
    PRINT 'Dropping existing index: IX_DeletedFile_Deleted';
    DROP INDEX [IX_DeletedFile_Deleted] ON [dbo].[DeletedFile];
END

PRINT 'Creating index: IX_DeletedFile_Deleted';
CREATE NONCLUSTERED INDEX [IX_DeletedFile_Deleted]
ON [dbo].[DeletedFile] ([Deleted])
INCLUDE ([Id], [Size], [TenantId], [SiteId], [UniqueId])
WHERE [Deleted] IS NOT NULL;

-- =====================================================================
-- INDEX 4: DeletedFile - For JOIN with ArchivedFile (Queries 3, 9, 10)
-- =====================================================================
-- Covers: Composite key JOIN (UniqueId, SiteId, TenantId)
-- Expected improvement: 50-75% faster for Queries 3, 9, 10

IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_DeletedFile_UniqueId_Composite' AND object_id = OBJECT_ID('[dbo].[DeletedFile]'))
BEGIN
    PRINT 'Dropping existing index: IX_DeletedFile_UniqueId_Composite';
    DROP INDEX [IX_DeletedFile_UniqueId_Composite] ON [dbo].[DeletedFile];
END

PRINT 'Creating index: IX_DeletedFile_UniqueId_Composite';
CREATE NONCLUSTERED INDEX [IX_DeletedFile_UniqueId_Composite]
ON [dbo].[DeletedFile] ([UniqueId], [SiteId], [TenantId])
INCLUDE ([Size], [Deleted], [Id]);

-- =====================================================================
-- INDEX 5: ArchiveJob - For Job Execution History (Query 4)
-- =====================================================================
-- Covers: LEFT JOIN on SiteId
-- Expected improvement: 30-50% faster for Query 4

IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_ArchiveJob_SiteId' AND object_id = OBJECT_ID('[dbo].[ArchiveJob]'))
BEGIN
    PRINT 'Dropping existing index: IX_ArchiveJob_SiteId';
    DROP INDEX [IX_ArchiveJob_SiteId] ON [dbo].[ArchiveJob];
END

PRINT 'Creating index: IX_ArchiveJob_SiteId';
CREATE NONCLUSTERED INDEX [IX_ArchiveJob_SiteId]
ON [dbo].[ArchiveJob] ([SiteId])
INCLUDE ([Id], [TenantId], [JobType], [JobMode], [Enabled]);

-- =====================================================================
-- INDEX 6: ArchivedFile - For TenantId Aggregation (Query 5)
-- =====================================================================
-- Covers: Tenant-level performance metrics
-- Expected improvement: 40-60% faster for Query 5

IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_ArchivedFile_TenantId_Archived' AND object_id = OBJECT_ID('[dbo].[ArchivedFile]'))
BEGIN
    PRINT 'Dropping existing index: IX_ArchivedFile_TenantId_Archived';
    DROP INDEX [IX_ArchivedFile_TenantId_Archived] ON [dbo].[ArchivedFile];
END

PRINT 'Creating index: IX_ArchivedFile_TenantId_Archived';
CREATE NONCLUSTERED INDEX [IX_ArchivedFile_TenantId_Archived]
ON [dbo].[ArchivedFile] ([TenantId], [Archived])
INCLUDE ([Id], [Size], [SiteId], [Created], [Filename], [ErrorCode]);

-- =====================================================================
-- POST-INDEX EXECUTION
-- =====================================================================

-- Update statistics to ensure query optimizer uses indexes
PRINT 'Updating statistics...';
EXEC sp_updatestats;

-- Display index creation results
PRINT '';
PRINT '=== INDEX CREATION COMPLETE ===';
PRINT 'Created 6 nonclustered indexes for optimal performance';
PRINT '';

-- Show created indexes
SELECT 
    OBJECT_NAME(i.object_id) AS [Table],
    i.name AS [IndexName],
    'Nonclustered' AS [Type],
    COUNT(*) AS [Columns]
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
WHERE i.object_id IN (
    OBJECT_ID('[dbo].[ArchivedFile]'),
    OBJECT_ID('[dbo].[DeletedFile]'),
    OBJECT_ID('[dbo].[ArchiveJob]')
)
AND i.name IN (
    'IX_ArchivedFile_Created_Archived',
    'IX_ArchivedFile_UniqueId',
    'IX_DeletedFile_Deleted',
    'IX_DeletedFile_UniqueId_Composite',
    'IX_ArchiveJob_SiteId',
    'IX_ArchivedFile_TenantId_Archived'
)
GROUP BY i.object_id, i.name
ORDER BY OBJECT_NAME(i.object_id), i.name;

-- =====================================================================
-- VERIFICATION QUERIES (Run after indexes created)
-- =====================================================================

PRINT '';
PRINT '=== QUERY EXECUTION TIME TEST ===';
PRINT 'Run these before and after index creation to measure improvement:';
PRINT '';
PRINT 'Test Query 1: Monthly Volume (should be <3 sec with indexes)';
PRINT '-------';

-- This should complete quickly with the new index
SELECT TOP 5
    YEAR([Created]) AS [Year],
    MONTH([Created]) AS [Month],
    COUNT(*) AS [FilesArchivedCount],
    SUM([Size]) AS [TotalSizeArchivedBytes],
    CAST(SUM([Size]) AS FLOAT) / 1024 / 1024 / 1024 AS [TotalSizeArchivedGB]
FROM [dbo].[ArchivedFile]
WHERE [Archived] = 1 AND [ArchivedAt] IS NOT NULL
GROUP BY YEAR([Created]), MONTH([Created])
ORDER BY [Year] DESC, [Month] DESC;

PRINT '';
PRINT 'Test Query 2: Storage Saved (should be <3 sec with indexes)';
PRINT '-------';

SELECT TOP 5
    YEAR([Deleted]) AS [Year],
    MONTH([Deleted]) AS [Month],
    COUNT(*) AS [DeletedFilesCount],
    SUM([Size]) AS [StorageSavedBytes]
FROM [dbo].[DeletedFile]
WHERE [Deleted] IS NOT NULL
GROUP BY YEAR([Deleted]), MONTH([Deleted])
ORDER BY [Year] DESC, [Month] DESC;

PRINT '';
PRINT '=== INDEXES READY FOR ML QUERIES ===';
PRINT 'You can now run all 10 ML extraction queries with optimal performance';
