-- PostgreSQL Schema for Exchange Analytics
-- Converted from SQLite schema

-- Analysis Cache Table
CREATE TABLE analysis_cache (
    id SERIAL PRIMARY KEY,
    analysis_type VARCHAR(50) NOT NULL,
    currency_pair VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10),
    analysis_data JSONB NOT NULL,
    cache_key VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);

-- Data Fetch History Table
CREATE TABLE data_fetch_history (
    id SERIAL PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL,
    fetch_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    data_source VARCHAR(50) NOT NULL,
    fetch_type VARCHAR(20) NOT NULL,
    success BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    http_status_code INTEGER,
    data_count INTEGER,
    error_code VARCHAR(50),
    error_message TEXT,
    error_details JSONB,
    data_summary JSONB,
    cache_used BOOLEAN NOT NULL,
    cache_level VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT idx_data_fetch_history_unique UNIQUE (currency_pair, fetch_timestamp, data_source)
);

-- Pattern Detections Table
CREATE TABLE pattern_detections (
    id SERIAL PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_name VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(5, 2) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    detection_data JSONB,
    indicator_data JSONB,
    notification_sent BOOLEAN NOT NULL DEFAULT FALSE,
    notification_sent_at TIMESTAMP WITH TIME ZONE,
    notification_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT idx_pattern_detections_unique UNIQUE (currency_pair, timestamp, pattern_type)
);

-- Price Data Table
CREATE TABLE price_data (
    id SERIAL PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    data_timestamp TIMESTAMP WITH TIME ZONE,
    fetched_at TIMESTAMP WITH TIME ZONE,
    open_price DECIMAL(10, 5) NOT NULL,
    high_price DECIMAL(10, 5) NOT NULL,
    low_price DECIMAL(10, 5) NOT NULL,
    close_price DECIMAL(10, 5) NOT NULL,
    volume BIGINT,
    data_source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT idx_price_data_currency_timestamp_source UNIQUE (currency_pair, timestamp, data_source)
);

-- System Config Table
CREATE TABLE system_config (
    id BIGSERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_category VARCHAR(50) NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    config_type VARCHAR(20) NOT NULL,
    default_value JSONB,
    validation_rules JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);

-- Technical Indicators Table
CREATE TABLE technical_indicators (
    id SERIAL PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    indicator_type VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    value DECIMAL(15, 8) NOT NULL,
    additional_data JSONB,
    parameters JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT idx_tech_indicators_unique UNIQUE (currency_pair, timestamp, indicator_type, timeframe)
);

-- Create Indexes for Analysis Cache
CREATE INDEX idx_analysis_cache_expires ON analysis_cache (expires_at);
CREATE INDEX idx_analysis_cache_analysis_type ON analysis_cache (analysis_type);
CREATE INDEX idx_analysis_cache_currency_pair ON analysis_cache (currency_pair);
CREATE INDEX idx_analysis_cache_type_pair ON analysis_cache (analysis_type, currency_pair);
CREATE INDEX idx_analysis_cache_timeframe ON analysis_cache (timeframe);

-- Create Indexes for Data Fetch History
CREATE INDEX idx_data_fetch_history_composite ON data_fetch_history (currency_pair, success, fetch_timestamp);
CREATE INDEX idx_data_fetch_history_type ON data_fetch_history (fetch_type);
CREATE INDEX idx_data_fetch_history_source ON data_fetch_history (data_source);
CREATE INDEX idx_data_fetch_history_success ON data_fetch_history (success);
CREATE INDEX idx_data_fetch_history_error ON data_fetch_history (error_code);
CREATE INDEX idx_data_fetch_history_timestamp ON data_fetch_history (fetch_timestamp);

-- Create Indexes for Pattern Detections
CREATE INDEX idx_pattern_detections_notification ON pattern_detections (notification_sent);
CREATE INDEX idx_pattern_detections_composite ON pattern_detections (currency_pair, pattern_type, timestamp);
CREATE INDEX idx_pattern_detections_confidence ON pattern_detections (confidence_score);
CREATE INDEX idx_pattern_detections_type ON pattern_detections (pattern_type);
CREATE INDEX idx_pattern_detections_timestamp ON pattern_detections (timestamp);

-- Create Indexes for Price Data
CREATE INDEX idx_price_data_currency ON price_data (currency_pair);
CREATE INDEX idx_price_data_timestamp ON price_data (timestamp);
CREATE INDEX idx_price_data_currency_timestamp_composite ON price_data (currency_pair, timestamp);

-- Create Indexes for System Config
CREATE INDEX idx_system_config_category ON system_config (config_category);
CREATE INDEX idx_system_config_active ON system_config (is_active);
CREATE INDEX idx_system_config_composite ON system_config (config_category, is_active);
CREATE INDEX idx_system_config_type ON system_config (config_type);

-- Create Indexes for Technical Indicators
CREATE INDEX idx_tech_indicators_timeframe ON technical_indicators (timeframe);
CREATE INDEX idx_tech_indicators_type ON technical_indicators (indicator_type);
CREATE INDEX idx_tech_indicators_timestamp ON technical_indicators (timestamp);
CREATE INDEX idx_tech_indicators_composite ON technical_indicators (currency_pair, indicator_type, timestamp);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_analysis_cache_updated_at BEFORE UPDATE ON analysis_cache FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_data_fetch_history_updated_at BEFORE UPDATE ON data_fetch_history FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pattern_detections_updated_at BEFORE UPDATE ON pattern_detections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_price_data_updated_at BEFORE UPDATE ON price_data FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_technical_indicators_updated_at BEFORE UPDATE ON technical_indicators FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for JSONB columns (PostgreSQL specific optimizations)
CREATE INDEX idx_analysis_cache_analysis_data_gin ON analysis_cache USING GIN (analysis_data);
CREATE INDEX idx_data_fetch_history_error_details_gin ON data_fetch_history USING GIN (error_details);
CREATE INDEX idx_data_fetch_history_data_summary_gin ON data_fetch_history USING GIN (data_summary);
CREATE INDEX idx_pattern_detections_detection_data_gin ON pattern_detections USING GIN (detection_data);
CREATE INDEX idx_pattern_detections_indicator_data_gin ON pattern_detections USING GIN (indicator_data);
CREATE INDEX idx_system_config_config_value_gin ON system_config USING GIN (config_value);
CREATE INDEX idx_technical_indicators_additional_data_gin ON technical_indicators USING GIN (additional_data);
CREATE INDEX idx_technical_indicators_parameters_gin ON technical_indicators USING GIN (parameters);

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
