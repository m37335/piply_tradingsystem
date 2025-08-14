"""
データベースクエリ最適化システム

責任:
- クエリ実行計画の分析
- インデックス最適化
- クエリキャッシュ
- パフォーマンス改善提案
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result

from ....utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


@dataclass
class QueryMetrics:
    """クエリメトリクス"""
    query_hash: str
    query_text: str
    execution_time_ms: float
    row_count: int
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None


@dataclass
class IndexRecommendation:
    """インデックス推奨事項"""
    table_name: str
    column_name: str
    index_type: str
    reason: str
    estimated_improvement: float
    priority: str


class QueryOptimizer:
    """クエリ最適化システム"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.query_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.cache_ttl = 300  # 5分
        self.slow_query_threshold_ms = 100  # 100ms以上を遅いクエリとする
        
    async def analyze_query_performance(self, query_text: str, params: Dict = None) -> Dict[str, Any]:
        """クエリパフォーマンスを分析"""
        try:
            start_time = time.time()
            
            # クエリ実行
            result = await self.session.execute(text(query_text), params or {})
            rows = result.fetchall()
            
            execution_time_ms = (time.time() - start_time) * 1000
            row_count = len(rows)
            
            # クエリハッシュを生成
            query_hash = self._generate_query_hash(query_text, params)
            
            metrics = QueryMetrics(
                query_hash=query_hash,
                query_text=query_text,
                execution_time_ms=execution_time_ms,
                row_count=row_count,
                timestamp=datetime.now(),
                success=True
            )
            
            # パフォーマンス分析
            analysis = await self._analyze_query_metrics(metrics)
            
            return {
                "metrics": metrics,
                "analysis": analysis,
                "result_count": row_count,
                "is_slow": execution_time_ms > self.slow_query_threshold_ms
            }
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            metrics = QueryMetrics(
                query_hash=self._generate_query_hash(query_text, params),
                query_text=query_text,
                execution_time_ms=execution_time_ms,
                row_count=0,
                timestamp=datetime.now(),
                success=False,
                error_message=str(e)
            )
            
            logger.error(f"クエリ実行エラー: {e}")
            return {
                "metrics": metrics,
                "analysis": {"error": str(e)},
                "result_count": 0,
                "is_slow": False
            }
    
    async def _analyze_query_metrics(self, metrics: QueryMetrics) -> Dict[str, Any]:
        """クエリメトリクスを分析"""
        analysis = {
            "performance_grade": "A",
            "recommendations": [],
            "issues": []
        }
        
        # 実行時間による評価
        if metrics.execution_time_ms > 1000:
            analysis["performance_grade"] = "D"
            analysis["issues"].append("実行時間が非常に長い (>1秒)")
        elif metrics.execution_time_ms > 500:
            analysis["performance_grade"] = "C"
            analysis["issues"].append("実行時間が長い (>500ms)")
        elif metrics.execution_time_ms > 100:
            analysis["performance_grade"] = "B"
            analysis["issues"].append("実行時間がやや長い (>100ms)")
        
        # 結果行数による評価
        if metrics.row_count > 10000:
            analysis["issues"].append("大量のデータを取得 (>10,000行)")
            analysis["recommendations"].append("LIMIT句の追加を検討")
        elif metrics.row_count > 1000:
            analysis["issues"].append("多くのデータを取得 (>1,000行)")
        
        # クエリ構造の分析
        query_lower = metrics.query_text.lower()
        if "select *" in query_lower:
            analysis["recommendations"].append("SELECT *の代わりに必要な列のみ指定")
        
        if "order by" in query_lower and "limit" not in query_lower:
            analysis["recommendations"].append("ORDER BY句にLIMIT句の追加を検討")
        
        if "like '%" in query_lower:
            analysis["recommendations"].append("前方一致検索の使用を検討 (LIKE 'pattern%')")
        
        return analysis
    
    async def get_index_recommendations(self) -> List[IndexRecommendation]:
        """インデックス推奨事項を取得"""
        recommendations = []
        
        try:
            # テーブル構造を分析
            inspector = inspect(self.session.get_bind())
            tables = inspector.get_table_names()
            
            for table_name in tables:
                # 主キーとインデックスを確認
                pk_columns = inspector.get_pk_constraint(table_name)['constrained_columns']
                indexes = inspector.get_indexes(table_name)
                existing_index_columns = set()
                
                for index in indexes:
                    existing_index_columns.update(index['column_names'])
                
                # カラム情報を取得
                columns = inspector.get_columns(table_name)
                
                for column in columns:
                    column_name = column['name']
                    
                    # 主キーはスキップ
                    if column_name in pk_columns:
                        continue
                    
                    # 既にインデックスがある場合はスキップ
                    if column_name in existing_index_columns:
                        continue
                    
                    # インデックス推奨の判定
                    data_type = str(column['type']).lower()
                    
                    if 'timestamp' in data_type or 'datetime' in data_type:
                        recommendations.append(IndexRecommendation(
                            table_name=table_name,
                            column_name=column_name,
                            index_type="BTREE",
                            reason="日時カラムは範囲検索でよく使用される",
                            estimated_improvement=0.8,
                            priority="high"
                        ))
                    
                    elif 'varchar' in data_type or 'text' in data_type:
                        recommendations.append(IndexRecommendation(
                            table_name=table_name,
                            column_name=column_name,
                            index_type="BTREE",
                            reason="文字列カラムは検索条件でよく使用される",
                            estimated_improvement=0.6,
                            priority="medium"
                        ))
                    
                    elif 'int' in data_type or 'float' in data_type:
                        recommendations.append(IndexRecommendation(
                            table_name=table_name,
                            column_name=column_name,
                            index_type="BTREE",
                            reason="数値カラムは比較検索でよく使用される",
                            estimated_improvement=0.7,
                            priority="medium"
                        ))
        
        except Exception as e:
            logger.error(f"インデックス推奨事項取得エラー: {e}")
        
        return recommendations
    
    async def create_recommended_indexes(self) -> Dict[str, Any]:
        """推奨インデックスを作成"""
        recommendations = await self.get_index_recommendations()
        results = {
            "created": 0,
            "failed": 0,
            "errors": []
        }
        
        for rec in recommendations:
            try:
                index_name = f"idx_{rec.table_name}_{rec.column_name}"
                create_sql = f"""
                CREATE INDEX IF NOT EXISTS {index_name} 
                ON {rec.table_name} ({rec.column_name})
                """
                
                await self.session.execute(text(create_sql))
                await self.session.commit()
                
                results["created"] += 1
                logger.info(f"インデックス作成成功: {index_name}")
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{rec.table_name}.{rec.column_name}: {str(e)}")
                logger.error(f"インデックス作成失敗: {rec.table_name}.{rec.column_name} - {e}")
        
        return results
    
    async def analyze_table_statistics(self) -> Dict[str, Any]:
        """テーブル統計情報を分析"""
        try:
            inspector = inspect(self.session.get_bind())
            tables = inspector.get_table_names()
            
            statistics = {}
            
            for table_name in tables:
                # 行数を取得
                count_result = await self.session.execute(
                    text(f"SELECT COUNT(*) as count FROM {table_name}")
                )
                row_count = count_result.scalar()
                
                # テーブルサイズを取得
                size_result = await self.session.execute(text("""
                    SELECT page_count * page_size as size_bytes
                    FROM pragma_page_count(), pragma_page_size()
                    WHERE name = :table_name
                """), {"table_name": table_name})
                size_bytes = size_result.scalar() or 0
                
                # インデックス数を取得
                indexes = inspector.get_indexes(table_name)
                
                statistics[table_name] = {
                    "row_count": row_count,
                    "size_mb": size_bytes / (1024 * 1024),
                    "index_count": len(indexes),
                    "indexes": [idx['name'] for idx in indexes]
                }
            
            return statistics
            
        except Exception as e:
            logger.error(f"テーブル統計情報取得エラー: {e}")
            return {}
    
    def _generate_query_hash(self, query_text: str, params: Dict = None) -> str:
        """クエリハッシュを生成"""
        query_data = {
            "query": query_text,
            "params": params or {}
        }
        return hashlib.md5(json.dumps(query_data, sort_keys=True).encode()).hexdigest()
    
    async def cache_query_result(self, query_hash: str, result: Any) -> None:
        """クエリ結果をキャッシュ"""
        self.query_cache[query_hash] = (result, datetime.now())
    
    def get_cached_result(self, query_hash: str) -> Optional[Any]:
        """キャッシュされた結果を取得"""
        if query_hash in self.query_cache:
            result, timestamp = self.query_cache[query_hash]
            
            # TTLチェック
            if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                return result
            else:
                # 期限切れのキャッシュを削除
                del self.query_cache[query_hash]
        
        return None
    
    async def optimize_common_queries(self) -> Dict[str, Any]:
        """一般的なクエリの最適化"""
        optimizations = {
            "price_data_queries": [],
            "technical_indicator_queries": [],
            "pattern_detection_queries": []
        }
        
        # 価格データクエリの最適化
        price_queries = [
            "SELECT * FROM price_data WHERE currency_pair = :pair ORDER BY timestamp DESC LIMIT 100",
            "SELECT * FROM price_data WHERE timestamp >= :start_date AND timestamp <= :end_date",
            "SELECT AVG(close_price) FROM price_data WHERE currency_pair = :pair AND timestamp >= :start_date"
        ]
        
        for query in price_queries:
            analysis = await self.analyze_query_performance(query, {"pair": "USD/JPY"})
            optimizations["price_data_queries"].append(analysis)
        
        # テクニカル指標クエリの最適化
        indicator_queries = [
            "SELECT * FROM technical_indicators WHERE indicator_type = :type AND timeframe = :timeframe ORDER BY timestamp DESC LIMIT 50",
            "SELECT * FROM technical_indicators WHERE currency_pair = :pair AND timestamp >= :start_date"
        ]
        
        for query in indicator_queries:
            analysis = await self.analyze_query_performance(
                query, 
                {"type": "RSI", "timeframe": "M5", "pair": "USD/JPY"}
            )
            optimizations["technical_indicator_queries"].append(analysis)
        
        return optimizations
    
    async def generate_optimization_report(self) -> Dict[str, Any]:
        """最適化レポートを生成"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "table_statistics": await self.analyze_table_statistics(),
            "index_recommendations": await self.get_index_recommendations(),
            "query_optimizations": await self.optimize_common_queries(),
            "cache_statistics": {
                "cached_queries": len(self.query_cache),
                "cache_hit_rate": 0.0  # 実装が必要
            }
        }
        
        return report
