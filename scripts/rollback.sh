#!/bin/bash

# ロールバックスクリプト
# investpy Economic Calendar System

set -e  # エラー時に停止

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 設定
APP_NAME="investpy-economic-calendar"
DEPLOY_DIR="/app"
BACKUP_DIR="/app/data/backups"
LOG_DIR="/app/data/logs/deployment"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# ロールバック設定
ROLLBACK_VERSION=${1:-"latest"}  # latest, specific_timestamp
CONFIRM_ROLLBACK=${2:-"false"}   # true, false

# ヘルプ表示
show_help() {
    echo "Usage: $0 [rollback_version] [confirm]"
    echo ""
    echo "Rollback versions:"
    echo "  latest    - Rollback to latest backup (default)"
    echo "  timestamp - Rollback to specific timestamp (YYYYMMDD_HHMMSS)"
    echo ""
    echo "Confirm options:"
    echo "  true      - Confirm rollback without prompting"
    echo "  false     - Prompt for confirmation (default)"
    echo ""
    echo "Examples:"
    echo "  $0 latest"
    echo "  $0 20231201_143000"
    echo "  $0 latest true"
}

# 引数チェック
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# 初期化
init_rollback() {
    log_info "Initializing rollback process..."
    
    # ディレクトリの作成
    mkdir -p "$LOG_DIR"
    
    # ログファイルの設定
    LOG_FILE="$LOG_DIR/rollback_${TIMESTAMP}.log"
    exec 1> >(tee -a "$LOG_FILE")
    exec 2> >(tee -a "$LOG_FILE" >&2)
    
    log_info "Rollback log: $LOG_FILE"
    log_info "Rollback version: $ROLLBACK_VERSION"
    log_info "Confirm rollback: $CONFIRM_ROLLBACK"
    log_info "Timestamp: $TIMESTAMP"
}

# バックアップの確認
check_backups() {
    log_info "Checking available backups..."
    
    # バックアップファイルの一覧
    BACKUP_FILES=($(ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null || true))
    DB_BACKUP_FILES=($(ls -t "$BACKUP_DIR"/db_backup_*.sql 2>/dev/null || true))
    
    if [[ ${#BACKUP_FILES[@]} -eq 0 ]]; then
        log_error "No backup files found in $BACKUP_DIR"
        exit 1
    fi
    
    log_info "Available backup files:"
    for i in "${!BACKUP_FILES[@]}"; do
        backup_file="${BACKUP_FILES[$i]}"
        backup_name=$(basename "$backup_file")
        backup_date=$(echo "$backup_name" | sed 's/backup_\(.*\)\.tar\.gz/\1/')
        log_info "  $((i+1)). $backup_name ($backup_date)"
    done
    
    log_info "Available database backup files:"
    for i in "${!DB_BACKUP_FILES[@]}"; do
        db_backup_file="${DB_BACKUP_FILES[$i]}"
        db_backup_name=$(basename "$db_backup_file")
        db_backup_date=$(echo "$db_backup_name" | sed 's/db_backup_\(.*\)\.sql/\1/')
        log_info "  $((i+1)). $db_backup_name ($db_backup_date)"
    done
}

# ロールバック対象の決定
determine_rollback_target() {
    log_info "Determining rollback target..."
    
    if [[ "$ROLLBACK_VERSION" == "latest" ]]; then
        # 最新のバックアップを選択
        TARGET_BACKUP="${BACKUP_FILES[0]}"
        TARGET_DB_BACKUP="${DB_BACKUP_FILES[0]}"
    else
        # 指定されたタイムスタンプのバックアップを探す
        TARGET_BACKUP="$BACKUP_DIR/backup_${ROLLBACK_VERSION}.tar.gz"
        TARGET_DB_BACKUP="$BACKUP_DIR/db_backup_${ROLLBACK_VERSION}.sql"
        
        if [[ ! -f "$TARGET_BACKUP" ]]; then
            log_error "Backup file not found: $TARGET_BACKUP"
            exit 1
        fi
        
        if [[ ! -f "$TARGET_DB_BACKUP" ]]; then
            log_warning "Database backup file not found: $TARGET_DB_BACKUP"
            TARGET_DB_BACKUP=""
        fi
    fi
    
    log_info "Target backup: $TARGET_BACKUP"
    if [[ -n "$TARGET_DB_BACKUP" ]]; then
        log_info "Target database backup: $TARGET_DB_BACKUP"
    fi
}

# ロールバックの確認
confirm_rollback() {
    if [[ "$CONFIRM_ROLLBACK" == "true" ]]; then
        log_warning "Rollback confirmed automatically"
        return 0
    fi
    
    echo ""
    log_warning "=== ROLLBACK CONFIRMATION ==="
    log_warning "This will rollback the application to:"
    log_warning "  Backup: $TARGET_BACKUP"
    if [[ -n "$TARGET_DB_BACKUP" ]]; then
        log_warning "  Database: $TARGET_DB_BACKUP"
    fi
    log_warning ""
    log_warning "This action cannot be undone!"
    log_warning ""
    
    read -p "Are you sure you want to proceed? (yes/no): " confirm
    
    if [[ "$confirm" != "yes" ]]; then
        log_info "Rollback cancelled by user"
        exit 0
    fi
    
    log_info "Rollback confirmed by user"
}

# 現在の状態のバックアップ
backup_current_state() {
    log_info "Creating backup of current state..."
    
    CURRENT_BACKUP="$BACKUP_DIR/pre_rollback_backup_${TIMESTAMP}.tar.gz"
    
    # 現在の設定ファイルのバックアップ
    tar -czf "$CURRENT_BACKUP" \
        --exclude="*.log" \
        --exclude="*.tmp" \
        --exclude="__pycache__" \
        --exclude="*.pyc" \
        config/ \
        src/ \
        scripts/ \
        requirements/ \
        2>/dev/null || true
    
    log_success "Current state backed up: $CURRENT_BACKUP"
}

# サービスの停止
stop_services() {
    log_info "Stopping services..."
    
    # cronサービスの停止
    if command -v service &> /dev/null; then
        service cron stop || true
    fi
    
    # アプリケーションの停止（必要に応じて）
    # systemctl stop $APP_NAME || true
    
    log_success "Services stopped"
}

# ファイルの復元
restore_files() {
    log_info "Restoring files from backup..."
    
    # バックアップの展開
    tar -xzf "$TARGET_BACKUP" -C "$DEPLOY_DIR"
    
    log_success "Files restored from: $TARGET_BACKUP"
}

# データベースの復元
restore_database() {
    if [[ -z "$TARGET_DB_BACKUP" ]]; then
        log_warning "No database backup specified, skipping database restore"
        return 0
    fi
    
    log_info "Restoring database from backup..."
    
    # データベース接続の確認
    if ! command -v psql &> /dev/null; then
        log_error "psql command not found"
        return 1
    fi
    
    # データベースの復元
    psql "$DATABASE_URL" < "$TARGET_DB_BACKUP"
    
    log_success "Database restored from: $TARGET_DB_BACKUP"
}

# 依存関係の再インストール
reinstall_dependencies() {
    log_info "Reinstalling dependencies..."
    
    # Python依存関係の再インストール
    if [[ -f "requirements/production.txt" ]]; then
        pip install -r requirements/production.txt
    elif [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    fi
    
    # 追加の依存関係
    pip install -r requirements/investpy_calendar.txt
    
    log_success "Dependencies reinstalled"
}

# 設定の復元
restore_config() {
    log_info "Restoring configuration..."
    
    # 本番環境設定の復元
    if [[ -f "config/production_config.json" ]]; then
        cp config/production_config.json config/config.json
    fi
    
    # ログ設定の復元
    if [[ -f "config/logging.yaml" ]]; then
        cp config/logging.yaml config/logging_production.yaml
    fi
    
    log_success "Configuration restored"
}

# crontabの再設定
restore_crontab() {
    log_info "Restoring crontab configuration..."
    
    if [[ -f "scripts/deploy_crontab.py" ]]; then
        python scripts/deploy_crontab.py --schedule-type all
    else
        log_warning "Crontab deployment script not found"
    fi
    
    log_success "Crontab restored"
}

# サービスの再起動
restart_services() {
    log_info "Restarting services..."
    
    # cronサービスの再起動
    if command -v service &> /dev/null; then
        service cron start || true
    fi
    
    # アプリケーションの再起動（必要に応じて）
    # systemctl start $APP_NAME || true
    
    log_success "Services restarted"
}

# ロールバックの検証
verify_rollback() {
    log_info "Verifying rollback..."
    
    # アプリケーションのテスト
    python -c "
import sys
sys.path.insert(0, '/app')
try:
    from src.domain.entities.economic_event import EconomicEvent
    from src.domain.services.investpy import InvestpyService
    from src.application.use_cases.fetch import FetchEconomicCalendarUseCase
    print('Application imports successful after rollback')
except Exception as e:
    print(f'Import error after rollback: {e}')
    sys.exit(1)
"
    
    # サービス監視の実行
    if [[ -f "scripts/monitor_service.py" ]]; then
        python scripts/monitor_service.py
    fi
    
    log_success "Rollback verification completed"
}

# ロールバック完了の通知
notify_rollback_completion() {
    log_info "Sending rollback completion notification..."
    
    # Discord通知（設定されている場合）
    if [[ -n "$DISCORD_WEBHOOK_URL" ]]; then
        MESSAGE="🔄 **Rollback Completed**\n\n"
        MESSAGE+="**Application**: $APP_NAME\n"
        MESSAGE+="**Rollback Version**: $ROLLBACK_VERSION\n"
        MESSAGE+="**Backup File**: $(basename "$TARGET_BACKUP")\n"
        MESSAGE+="**Timestamp**: $TIMESTAMP\n"
        MESSAGE+="**Status**: Success"
        
        curl -H "Content-Type: application/json" \
             -X POST \
             -d "{\"content\":\"$MESSAGE\"}" \
             "$DISCORD_WEBHOOK_URL" || true
    fi
    
    log_success "Rollback completion notification sent"
}

# メイン処理
main() {
    log_info "Starting rollback process..."
    
    init_rollback
    check_backups
    determine_rollback_target
    confirm_rollback
    backup_current_state
    stop_services
    restore_files
    restore_database
    reinstall_dependencies
    restore_config
    restore_crontab
    restart_services
    verify_rollback
    notify_rollback_completion
    
    log_success "Rollback completed successfully!"
    log_info "Rollback log: $LOG_FILE"
    log_info "Previous state backed up: $CURRENT_BACKUP"
}

# スクリプトの実行
main "$@"
