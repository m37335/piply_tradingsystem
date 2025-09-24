"""
初期スキーママイグレーション

データベースの初期スキーマを作成します。
"""

from .migration_manager import BaseMigration
from ..core.database.connection_manager import ConnectionManager
from ..models.price_data import CREATE_PRICE_DATA_TABLE, CREATE_PRICE_DATA_VIEWS
from ..models.data_collection_log import CREATE_DATA_COLLECTION_LOG_TABLE, CREATE_DATA_COLLECTION_LOG_VIEWS
from ..models.data_quality_metrics import CREATE_DATA_QUALITY_METRICS_TABLE, CREATE_DATA_QUALITY_METRICS_VIEWS
from ..models.llm_analysis_results import CREATE_LLM_ANALYSIS_RESULTS_TABLE, CREATE_LLM_ANALYSIS_RESULTS_VIEWS
from ..models.llm_analysis_input_data import CREATE_LLM_ANALYSIS_INPUT_DATA_TABLE, CREATE_LLM_ANALYSIS_INPUT_DATA_VIEWS
from ..models.llm_analysis_quality import CREATE_LLM_ANALYSIS_QUALITY_TABLE, CREATE_LLM_ANALYSIS_QUALITY_VIEWS


class Migration001InitialSchema(BaseMigration):
    """初期スキーママイグレーション"""
    
    def get_migration_id(self) -> str:
        return "001_initial_schema"
    
    def get_description(self) -> str:
        return "Create initial database schema with all tables and views"
    
    async def up(self, connection_manager: ConnectionManager) -> None:
        """マイグレーションを実行"""
        
        # 拡張機能を有効化
        await connection_manager.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
        await connection_manager.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements;")
        await connection_manager.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        
        # テーブルを作成
        await connection_manager.execute(CREATE_PRICE_DATA_TABLE)
        await connection_manager.execute(CREATE_DATA_COLLECTION_LOG_TABLE)
        await connection_manager.execute(CREATE_DATA_QUALITY_METRICS_TABLE)
        await connection_manager.execute(CREATE_LLM_ANALYSIS_RESULTS_TABLE)
        await connection_manager.execute(CREATE_LLM_ANALYSIS_INPUT_DATA_TABLE)
        await connection_manager.execute(CREATE_LLM_ANALYSIS_QUALITY_TABLE)
        
        # ビューを作成
        await connection_manager.execute(CREATE_PRICE_DATA_VIEWS)
        await connection_manager.execute(CREATE_DATA_COLLECTION_LOG_VIEWS)
        await connection_manager.execute(CREATE_DATA_QUALITY_METRICS_VIEWS)
        await connection_manager.execute(CREATE_LLM_ANALYSIS_RESULTS_VIEWS)
        await connection_manager.execute(CREATE_LLM_ANALYSIS_INPUT_DATA_VIEWS)
        await connection_manager.execute(CREATE_LLM_ANALYSIS_QUALITY_VIEWS)
        
        # TimescaleDBのハイパーテーブルを作成
        try:
            await connection_manager.execute("SELECT create_hypertable('price_data', 'timestamp');")
        except Exception:
            pass  # 既にハイパーテーブルの場合は無視
        
        try:
            await connection_manager.execute("SELECT create_hypertable('data_collection_log', 'created_at');")
        except Exception:
            pass
        
        try:
            await connection_manager.execute("SELECT create_hypertable('llm_analysis_results', 'created_at');")
        except Exception:
            pass
        
        # 圧縮ポリシーを作成
        try:
            await connection_manager.execute("SELECT add_compression_policy('price_data', INTERVAL '7 days');")
        except Exception:
            pass
        
        try:
            await connection_manager.execute("SELECT add_compression_policy('data_collection_log', INTERVAL '7 days');")
        except Exception:
            pass
        
        try:
            await connection_manager.execute("SELECT add_compression_policy('llm_analysis_results', INTERVAL '7 days');")
        except Exception:
            pass
        
        # 保持ポリシーを作成
        try:
            await connection_manager.execute("SELECT add_retention_policy('price_data', INTERVAL '2 years');")
        except Exception:
            pass
        
        try:
            await connection_manager.execute("SELECT add_retention_policy('data_collection_log', INTERVAL '1 year');")
        except Exception:
            pass
        
        try:
            await connection_manager.execute("SELECT add_retention_policy('llm_analysis_results', INTERVAL '1 year');")
        except Exception:
            pass
    
    async def down(self, connection_manager: ConnectionManager) -> None:
        """マイグレーションをロールバック"""
        
        # ビューを削除
        views_to_drop = [
            "latest_price_data", "daily_price_summary", "timeframe_availability",
            "collection_success_rate", "collection_error_stats", "recent_collection_activity",
            "quality_metrics_summary", "quality_alerts",
            "latest_llm_analysis", "llm_analysis_summary", "llm_analysis_cost_analysis",
            "llm_analysis_confidence_analysis", "llm_analysis_input_summary",
            "llm_analysis_input_data_type_stats", "llm_analysis_input_details",
            "llm_analysis_quality_summary", "llm_analysis_quality_trend",
            "llm_analysis_quality_alerts", "llm_analysis_quality_by_type"
        ]
        
        for view_name in views_to_drop:
            try:
                await connection_manager.execute(f"DROP VIEW IF EXISTS {view_name};")
            except Exception:
                pass
        
        # テーブルを削除
        tables_to_drop = [
            "llm_analysis_quality",
            "llm_analysis_input_data", 
            "llm_analysis_results",
            "data_quality_metrics",
            "data_collection_log",
            "price_data"
        ]
        
        for table_name in tables_to_drop:
            try:
                await connection_manager.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
            except Exception:
                pass
