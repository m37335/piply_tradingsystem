-- プロトレーダー向け為替アラートシステム - テーブル作成
-- 作成日: 2025-01-15
-- バージョン: 1.0.0

-- 1. アラート設定テーブル（alert_settings）
CREATE TABLE alert_settings (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,           -- 'entry_signal', 'exit_signal', 'risk_alert'
    indicator_type VARCHAR(20),                -- 'RSI', 'MACD', 'BB', 'MA'
    timeframe VARCHAR(10),                     -- 'M5', 'M15', 'H1', 'H4', 'D1'
    threshold_value DECIMAL(15, 8),            -- 閾値
    condition_type VARCHAR(20),                -- 'above', 'below', 'cross', 'divergence'
    risk_reward_min DECIMAL(5, 2),             -- 最小リスク/リワード比
    confidence_min INTEGER,                    -- 最小信頼度（0-100）
    is_active BOOLEAN DEFAULT TRUE,
    notification_channels JSONB,               -- ['discord', 'email', 'slack']
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT idx_alert_settings_unique UNIQUE (alert_type, indicator_type, timeframe)
);

-- 2. エントリーシグナルテーブル（entry_signals）
CREATE TABLE entry_signals (
    id SERIAL PRIMARY KEY,
    signal_type VARCHAR(10) NOT NULL,          -- 'BUY', 'SELL'
    currency_pair VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    
    -- 価格情報
    entry_price DECIMAL(10, 5) NOT NULL,
    stop_loss DECIMAL(10, 5) NOT NULL,
    take_profit DECIMAL(10, 5) NOT NULL,
    
    -- リスク管理
    risk_reward_ratio DECIMAL(5, 2) NOT NULL,
    risk_amount DECIMAL(10, 2),                -- リスク額（USD）
    position_size DECIMAL(10, 2),              -- 推奨ポジションサイズ
    
    -- 分析情報
    confidence_score INTEGER NOT NULL,         -- 0-100
    indicators_used JSONB NOT NULL,            -- 使用した指標
    market_conditions JSONB,                   -- 市場状況
    trend_strength DECIMAL(5, 2),              -- トレンド強度
    
    -- 管理情報
    is_executed BOOLEAN DEFAULT FALSE,
    executed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT idx_entry_signals_unique UNIQUE (currency_pair, timestamp, signal_type, timeframe)
);

-- 3. リスクアラートテーブル（risk_alerts）
CREATE TABLE risk_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,           -- 'volatility_spike', 'correlation_change', 'liquidity_warning'
    currency_pair VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    
    -- アラート情報
    severity VARCHAR(10) NOT NULL,             -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    message TEXT NOT NULL,
    recommended_action TEXT,
    
    -- データ
    market_data JSONB NOT NULL,                -- 市場データ
    threshold_value DECIMAL(15, 8),            -- 閾値
    current_value DECIMAL(15, 8),              -- 現在値
    
    -- 管理情報
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. シグナルパフォーマンステーブル（signal_performance）
CREATE TABLE signal_performance (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER REFERENCES entry_signals(id),
    currency_pair VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    
    -- 取引情報
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_time TIMESTAMP WITH TIME ZONE,
    entry_price DECIMAL(10, 5) NOT NULL,
    exit_price DECIMAL(10, 5),
    
    -- 結果
    pnl DECIMAL(10, 5),                        -- 損益
    pnl_percentage DECIMAL(5, 2),              -- 損益率（%）
    exit_reason VARCHAR(50),                   -- 'take_profit', 'stop_loss', 'manual', 'trend_change'
    
    -- 統計
    duration_minutes INTEGER,                  -- 保有時間（分）
    max_profit DECIMAL(10, 5),                 -- 最大利益
    max_loss DECIMAL(10, 5),                   -- 最大損失
    drawdown DECIMAL(5, 2),                    -- 最大ドローダウン（%）
    
    -- 管理情報
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成

-- アラート設定テーブル
CREATE INDEX idx_alert_settings_active ON alert_settings (is_active);
CREATE INDEX idx_alert_settings_type ON alert_settings (alert_type, indicator_type);
CREATE INDEX idx_alert_settings_timeframe ON alert_settings (timeframe);

-- エントリーシグナルテーブル
CREATE INDEX idx_entry_signals_timestamp ON entry_signals (timestamp DESC);
CREATE INDEX idx_entry_signals_currency_timeframe ON entry_signals (currency_pair, timeframe);
CREATE INDEX idx_entry_signals_executed ON entry_signals (is_executed, timestamp);
CREATE INDEX idx_entry_signals_confidence ON entry_signals (confidence_score DESC);

-- リスクアラートテーブル
CREATE INDEX idx_risk_alerts_severity ON risk_alerts (severity, timestamp DESC);
CREATE INDEX idx_risk_alerts_currency ON risk_alerts (currency_pair, timestamp DESC);
CREATE INDEX idx_risk_alerts_acknowledged ON risk_alerts (is_acknowledged, timestamp);

-- シグナルパフォーマンステーブル
CREATE INDEX idx_signal_performance_pnl ON signal_performance (pnl_percentage DESC);
CREATE INDEX idx_signal_performance_duration ON signal_performance (duration_minutes);
CREATE INDEX idx_signal_performance_exit_reason ON signal_performance (exit_reason);

-- JSONBインデックス（PostgreSQL最適化）
CREATE INDEX idx_alert_settings_channels_gin ON alert_settings USING GIN (notification_channels);
CREATE INDEX idx_entry_signals_indicators_gin ON entry_signals USING GIN (indicators_used);
CREATE INDEX idx_entry_signals_conditions_gin ON entry_signals USING GIN (market_conditions);
CREATE INDEX idx_risk_alerts_market_data_gin ON risk_alerts USING GIN (market_data);

-- 更新タイムスタンプトリガー関数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- トリガー作成
CREATE TRIGGER update_alert_settings_updated_at 
    BEFORE UPDATE ON alert_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entry_signals_updated_at 
    BEFORE UPDATE ON entry_signals 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signal_performance_updated_at 
    BEFORE UPDATE ON signal_performance 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 初期データ投入（テスト用）
INSERT INTO alert_settings (
    alert_type, 
    indicator_type, 
    timeframe, 
    threshold_value, 
    condition_type, 
    risk_reward_min, 
    confidence_min, 
    notification_channels
) VALUES 
    ('entry_signal', 'RSI', 'M5', 30.0, 'below', 2.0, 70, '["discord"]'),
    ('entry_signal', 'RSI', 'M5', 70.0, 'above', 2.0, 70, '["discord"]'),
    ('entry_signal', 'BB', 'M5', 0.0, 'cross', 2.5, 75, '["discord"]'),
    ('risk_alert', 'ATR', 'M5', 2.0, 'above', 0.0, 50, '["discord", "email"]');

-- 権限設定（必要に応じて調整）
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
