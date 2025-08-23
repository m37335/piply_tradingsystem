-- Notification History Table
-- 通知履歴テーブル

CREATE TABLE IF NOT EXISTS notification_history (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(50) NOT NULL,
    currency_pair VARCHAR(10),
    message_content TEXT,
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);

-- Indexes for Notification History
CREATE INDEX IF NOT EXISTS idx_notification_history_sent_at ON notification_history (sent_at);
CREATE INDEX IF NOT EXISTS idx_notification_history_type ON notification_history (notification_type);
CREATE INDEX IF NOT EXISTS idx_notification_history_currency_pair ON notification_history (currency_pair);
CREATE INDEX IF NOT EXISTS idx_notification_history_success ON notification_history (success);
CREATE INDEX IF NOT EXISTS idx_notification_history_type_sent ON notification_history (notification_type, sent_at);

-- Comments
COMMENT ON TABLE notification_history IS '通知履歴テーブル';
COMMENT ON COLUMN notification_history.notification_type IS '通知タイプ（discord, email, etc.）';
COMMENT ON COLUMN notification_history.currency_pair IS '通貨ペア';
COMMENT ON COLUMN notification_history.message_content IS '送信メッセージ内容';
COMMENT ON COLUMN notification_history.sent_at IS '送信時刻';
COMMENT ON COLUMN notification_history.success IS '送信成功フラグ';
COMMENT ON COLUMN notification_history.error_message IS 'エラーメッセージ';
COMMENT ON COLUMN notification_history.metadata IS '追加メタデータ（JSON形式）';
