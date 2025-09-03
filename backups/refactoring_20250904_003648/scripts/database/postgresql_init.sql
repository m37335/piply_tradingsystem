-- PostgreSQL Initialization Script
-- Exchange Analytics Database Setup

-- Create user and grant permissions
-- CREATE USER exchange_user WITH PASSWORD 'exchange_password';
-- GRANT ALL PRIVILEGES ON DATABASE exchange_analytics TO exchange_user;

-- Connect to the database
\c exchange_analytics_production_db;

-- Grant permissions to exchange_analytics_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO exchange_analytics_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO exchange_analytics_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO exchange_analytics_user;

-- Grant future permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO exchange_analytics_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO exchange_analytics_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO exchange_analytics_user;

-- Create some initial system configurations
INSERT INTO system_config (
    config_key, 
    config_category, 
    config_value, 
    description, 
    is_active, 
    config_type, 
    created_at, 
    updated_at
) VALUES 
(
    'database.migration.version',
    'system',
    '"1.0.0"',
    'Current database migration version',
    true,
    'string',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    'database.type',
    'system',
    '"postgresql"',
    'Database type being used',
    true,
    'string',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    'system.timezone',
    'system',
    '"Asia/Tokyo"',
    'System timezone',
    true,
    'string',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    'logging.level',
    'system',
    '"INFO"',
    'Logging level',
    true,
    'string',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Create indexes for better performance
-- These are already in the schema file, but adding some additional ones

-- Partitioning setup for price_data (optional for large datasets)
-- CREATE TABLE price_data_partitioned (
--     LIKE price_data INCLUDING ALL
-- ) PARTITION BY RANGE (timestamp);

-- Create a function to get current database info
CREATE OR REPLACE FUNCTION get_database_info()
RETURNS TABLE (
    database_name TEXT,
    current_user TEXT,
    current_timestamp TIMESTAMP,
    version TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        current_database()::TEXT,
        current_user::TEXT,
        CURRENT_TIMESTAMP,
        'PostgreSQL 15'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION get_database_info() TO exchange_analytics_user;

-- Create a function to get table statistics
CREATE OR REPLACE FUNCTION get_table_stats()
RETURNS TABLE (
    table_name TEXT,
    row_count BIGINT,
    table_size TEXT,
    index_size TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname||'.'||tablename::TEXT,
        n_tup_ins + n_tup_upd + n_tup_del::BIGINT,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))::TEXT,
        pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename))::TEXT
    FROM pg_stat_user_tables
    ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION get_table_stats() TO exchange_analytics_user;

-- Create a view for system health monitoring
CREATE VIEW system_health AS
SELECT 
    'database' as component,
    current_database() as name,
    'PostgreSQL' as type,
    version() as version,
    CURRENT_TIMESTAMP as last_check
UNION ALL
SELECT 
    'connection' as component,
    'active_connections' as name,
    count(*)::TEXT as type,
    'connections' as version,
    CURRENT_TIMESTAMP as last_check
FROM pg_stat_activity
WHERE state = 'active';

-- Grant select permission on view
GRANT SELECT ON system_health TO exchange_analytics_user;

-- Create a function to clean up old data (for maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_data(
    days_to_keep INTEGER DEFAULT 30
)
RETURNS TABLE (
    table_name TEXT,
    deleted_count BIGINT
) AS $$
DECLARE
    cutoff_date TIMESTAMP;
BEGIN
    cutoff_date := CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep;
    
    -- Clean up old analysis cache
    DELETE FROM analysis_cache WHERE expires_at < cutoff_date;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    table_name := 'analysis_cache';
    RETURN NEXT;
    
    -- Clean up old data fetch history
    DELETE FROM data_fetch_history WHERE fetch_timestamp < cutoff_date;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    table_name := 'data_fetch_history';
    RETURN NEXT;
    
    -- Clean up old pattern detections
    DELETE FROM pattern_detections WHERE timestamp < cutoff_date;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    table_name := 'pattern_detections';
    RETURN NEXT;
    
    -- Note: price_data and technical_indicators are not cleaned up by default
    -- as they contain historical data that might be needed for analysis
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION cleanup_old_data(INTEGER) TO exchange_analytics_user;

-- Create a function to get database size information
CREATE OR REPLACE FUNCTION get_database_size()
RETURNS TABLE (
    database_name TEXT,
    size TEXT,
    size_bytes BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        current_database()::TEXT,
        pg_size_pretty(pg_database_size(current_database()))::TEXT,
        pg_database_size(current_database());
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION get_database_size() TO exchange_analytics_user;

-- Log the completion
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL initialization completed successfully';
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'User: %', current_user;
    RAISE NOTICE 'Timestamp: %', CURRENT_TIMESTAMP;
END $$;
