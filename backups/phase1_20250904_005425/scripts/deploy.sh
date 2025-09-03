#!/bin/bash

# 本番環境デプロイメントスクリプト
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

# デプロイメント設定
DEPLOYMENT_TYPE=${1:-"full"}  # full, update, rollback
ENVIRONMENT=${2:-"production"}

# ヘルプ表示
show_help() {
    echo "Usage: $0 [deployment_type] [environment]"
    echo ""
    echo "Deployment types:"
    echo "  full      - Full deployment (default)"
    echo "  update    - Update existing deployment"
    echo "  rollback  - Rollback to previous version"
    echo ""
    echo "Environments:"
    echo "  production - Production environment (default)"
    echo "  staging    - Staging environment"
    echo ""
    echo "Examples:"
    echo "  $0 full production"
    echo "  $0 update staging"
    echo "  $0 rollback production"
}

# 引数チェック
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# 初期化
init_deployment() {
    log_info "Initializing deployment..."
    
    # ディレクトリの作成
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$DEPLOY_DIR/data/logs"
    
    # ログファイルの設定
    LOG_FILE="$LOG_DIR/deploy_${TIMESTAMP}.log"
    exec 1> >(tee -a "$LOG_FILE")
    exec 2> >(tee -a "$LOG_FILE" >&2)
    
    log_info "Deployment log: $LOG_FILE"
    log_info "Deployment type: $DEPLOYMENT_TYPE"
    log_info "Environment: $ENVIRONMENT"
    log_info "Timestamp: $TIMESTAMP"
}

# 環境変数の検証
validate_environment() {
    log_info "Validating environment variables..."
    
    required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "DISCORD_WEBHOOK_URL"
        "OPENAI_API_KEY"
    )
    
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            log_error "  - $var"
        done
        exit 1
    fi
    
    log_success "Environment variables validated"
}

# バックアップの作成
create_backup() {
    log_info "Creating backup..."
    
    BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.tar.gz"
    
    # データベースのバックアップ
    if command -v pg_dump &> /dev/null; then
        log_info "Creating database backup..."
        pg_dump "$DATABASE_URL" > "$BACKUP_DIR/db_backup_${TIMESTAMP}.sql"
    fi
    
    # 設定ファイルのバックアップ
    tar -czf "$BACKUP_FILE" \
        --exclude="*.log" \
        --exclude="*.tmp" \
        --exclude="__pycache__" \
        --exclude="*.pyc" \
        config/ \
        src/ \
        scripts/ \
        requirements/ \
        2>/dev/null || true
    
    log_success "Backup created: $BACKUP_FILE"
}

# 依存関係のインストール
install_dependencies() {
    log_info "Installing dependencies..."
    
    # Python依存関係のインストール
    if [[ -f "requirements/production.txt" ]]; then
        pip install -r requirements/production.txt
    elif [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    else
        log_warning "No requirements file found"
    fi
    
    # 追加の依存関係
    pip install -r requirements/investpy_calendar.txt
    
    log_success "Dependencies installed"
}

# データベースのセットアップ
setup_database() {
    log_info "Setting up database..."
    
    # データベースマイグレーション
    if [[ -f "scripts/setup_database.py" ]]; then
        python scripts/setup_database.py
    fi
    
    # Alembicマイグレーション
    if command -v alembic &> /dev/null; then
        log_info "Running Alembic migrations..."
        alembic upgrade head
    fi
    
    log_success "Database setup completed"
}

# 設定ファイルのデプロイ
deploy_config() {
    log_info "Deploying configuration files..."
    
    # 本番環境設定のコピー
    if [[ -f "config/production_config.json" ]]; then
        cp config/production_config.json config/config.json
    fi
    
    # ログ設定のコピー
    if [[ -f "config/logging.yaml" ]]; then
        cp config/logging.yaml config/logging_production.yaml
    fi
    
    log_success "Configuration deployed"
}

# crontabの設定
setup_crontab() {
    log_info "Setting up crontab..."
    
    if [[ -f "scripts/deploy_crontab.py" ]]; then
        python scripts/deploy_crontab.py --schedule-type all
    else
        log_warning "Crontab deployment script not found"
    fi
    
    log_success "Crontab configured"
}

# アプリケーションの起動テスト
test_application() {
    log_info "Testing application..."
    
    # 基本的なインポートテスト
    python -c "
import sys
sys.path.insert(0, '/app')
try:
    from src.domain.entities.economic_event import EconomicEvent
    from src.domain.services.investpy import InvestpyService
    from src.application.use_cases.fetch import FetchEconomicCalendarUseCase
    print('Application imports successful')
except Exception as e:
    print(f'Import error: {e}')
    sys.exit(1)
"
    
    # ヘルスチェック
    if [[ -f "scripts/health_check.py" ]]; then
        python scripts/health_check.py
    fi
    
    log_success "Application test passed"
}

# サービスの再起動
restart_services() {
    log_info "Restarting services..."
    
    # cronサービスの再起動
    if command -v service &> /dev/null; then
        service cron restart || true
    fi
    
    # アプリケーションの再起動（必要に応じて）
    # systemctl restart $APP_NAME || true
    
    log_success "Services restarted"
}

# デプロイメント後の検証
verify_deployment() {
    log_info "Verifying deployment..."
    
    # サービス監視の実行
    if [[ -f "scripts/monitor_service.py" ]]; then
        python scripts/monitor_service.py
    fi
    
    # ログファイルの確認
    if [[ -d "$LOG_DIR" ]]; then
        log_info "Recent log files:"
        ls -la "$LOG_DIR" | tail -5
    fi
    
    log_success "Deployment verification completed"
}

# ロールバック
rollback() {
    log_warning "Rolling back deployment..."
    
    # 最新のバックアップを探す
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | head -1)
    
    if [[ -z "$LATEST_BACKUP" ]]; then
        log_error "No backup found for rollback"
        exit 1
    fi
    
    log_info "Rolling back to: $LATEST_BACKUP"
    
    # バックアップの復元
    tar -xzf "$LATEST_BACKUP" -C "$DEPLOY_DIR"
    
    # データベースの復元
    LATEST_DB_BACKUP=$(ls -t "$BACKUP_DIR"/db_backup_*.sql 2>/dev/null | head -1)
    if [[ -n "$LATEST_DB_BACKUP" ]]; then
        log_info "Restoring database from: $LATEST_DB_BACKUP"
        psql "$DATABASE_URL" < "$LATEST_DB_BACKUP"
    fi
    
    log_success "Rollback completed"
}

# クリーンアップ
cleanup() {
    log_info "Cleaning up..."
    
    # 古いバックアップの削除（30日以上前）
    find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +30 -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "db_backup_*.sql" -mtime +30 -delete 2>/dev/null || true
    
    # 古いログファイルの削除（7日以上前）
    find "$LOG_DIR" -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    log_success "Cleanup completed"
}

# メイン処理
main() {
    log_info "Starting deployment process..."
    
    case "$DEPLOYMENT_TYPE" in
        "full")
            init_deployment
            validate_environment
            create_backup
            install_dependencies
            setup_database
            deploy_config
            setup_crontab
            test_application
            restart_services
            verify_deployment
            cleanup
            ;;
        "update")
            init_deployment
            validate_environment
            create_backup
            install_dependencies
            deploy_config
            test_application
            restart_services
            verify_deployment
            ;;
        "rollback")
            init_deployment
            rollback
            restart_services
            verify_deployment
            ;;
        *)
            log_error "Invalid deployment type: $DEPLOYMENT_TYPE"
            show_help
            exit 1
            ;;
    esac
    
    log_success "Deployment completed successfully!"
    log_info "Deployment log: $LOG_FILE"
}

# スクリプトの実行
main "$@"
