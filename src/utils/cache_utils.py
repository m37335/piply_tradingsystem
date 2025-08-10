"""
Cache Utilities
キャッシュユーティリティ

設計書参照:
- api_optimization_design_2025.md

キャッシュシステム用のユーティリティ関数
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from .logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


def generate_cache_key(
    analysis_type: str,
    currency_pair: str,
    timeframe: Optional[str] = None,
    additional_params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    キャッシュキーを生成

    Args:
        analysis_type: 分析タイプ
        currency_pair: 通貨ペア
        timeframe: 時間軸（オプション）
        additional_params: 追加パラメータ（オプション）

    Returns:
        str: 生成されたキャッシュキー
    """
    try:
        # 基本コンポーネント
        components = {
            "analysis_type": analysis_type,
            "currency_pair": currency_pair,
            "timeframe": timeframe or "",
        }

        # 追加パラメータがあれば追加
        if additional_params:
            components.update(additional_params)

        # JSON文字列に変換してハッシュ化
        json_str = json.dumps(components, sort_keys=True, ensure_ascii=False)
        hash_obj = hashlib.md5(json_str.encode("utf-8"))
        cache_key = f"cache_{hash_obj.hexdigest()}"

        logger.debug(
            f"Generated cache key: {cache_key} for {analysis_type}:{currency_pair}"
        )
        return cache_key

    except Exception as e:
        logger.error(f"Failed to generate cache key: {str(e)}")
        # フォールバック: シンプルなキー生成
        fallback_key = f"cache_{analysis_type}_{currency_pair}_{timeframe or 'default'}"
        return fallback_key


def calculate_ttl(
    base_minutes: int = 60,
    volatility_factor: float = 1.0,
    market_hours_factor: float = 1.0,
) -> int:
    """
    TTL（Time To Live）を計算

    Args:
        base_minutes: 基本TTL（分）
        volatility_factor: ボラティリティ係数（1.0以上で長く、1.0未満で短く）
        market_hours_factor: 市場時間係数（営業時間外は長く）

    Returns:
        int: 計算されたTTL（秒）
    """
    try:
        # 基本TTLを秒に変換
        base_seconds = base_minutes * 60

        # 係数を適用
        adjusted_seconds = int(base_seconds * volatility_factor * market_hours_factor)

        # 最小・最大値を設定
        min_seconds = 60  # 1分
        max_seconds = 24 * 60 * 60  # 24時間

        ttl_seconds = max(min_seconds, min(adjusted_seconds, max_seconds))

        logger.debug(
            f"Calculated TTL: {ttl_seconds}s "
            f"(base: {base_minutes}m, volatility: {volatility_factor}, "
            f"market: {market_hours_factor})"
        )
        return ttl_seconds

    except Exception as e:
        logger.error(f"Failed to calculate TTL: {str(e)}")
        # フォールバック: デフォルト値
        return 60 * 60  # 1時間


def get_cache_statistics(
    cache_data: Dict[str, Any],
    include_timestamps: bool = True,
) -> Dict[str, Any]:
    """
    キャッシュ統計を取得

    Args:
        cache_data: キャッシュデータ
        include_timestamps: タイムスタンプを含めるかどうか

    Returns:
        Dict[str, Any]: キャッシュ統計情報
    """
    try:
        stats = {
            "total_entries": len(cache_data),
            "cache_size_bytes": len(
                json.dumps(cache_data, ensure_ascii=False).encode("utf-8")
            ),
        }

        if include_timestamps:
            stats["generated_at"] = datetime.utcnow().isoformat()

        # エントリータイプ別統計
        entry_types = {}
        for key, value in cache_data.items():
            entry_type = key.split("_")[0] if "_" in key else "unknown"
            entry_types[entry_type] = entry_types.get(entry_type, 0) + 1

        stats["entry_types"] = entry_types

        logger.debug(f"Cache statistics: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Failed to get cache statistics: {str(e)}")
        return {"error": str(e)}


def is_cache_fresh(
    cache_timestamp: datetime,
    max_age_minutes: int = 5,
    current_time: Optional[datetime] = None,
) -> bool:
    """
    キャッシュが新鮮かどうかを判定

    Args:
        cache_timestamp: キャッシュのタイムスタンプ
        max_age_minutes: 最大有効期間（分）
        current_time: 現在時刻（オプション、テスト用）

    Returns:
        bool: キャッシュが新鮮な場合True
    """
    try:
        if current_time is None:
            current_time = datetime.utcnow()

        age = current_time - cache_timestamp
        max_age = timedelta(minutes=max_age_minutes)

        is_fresh = age <= max_age

        logger.debug(
            f"Cache freshness check: {is_fresh} "
            f"(age: {age.total_seconds():.1f}s, max: {max_age.total_seconds():.1f}s)"
        )
        return is_fresh

    except Exception as e:
        logger.error(f"Failed to check cache freshness: {str(e)}")
        return False


def get_cache_key_components(cache_key: str) -> Dict[str, str]:
    """
    キャッシュキーからコンポーネントを抽出

    Args:
        cache_key: キャッシュキー

    Returns:
        Dict[str, str]: キャッシュキーのコンポーネント
    """
    try:
        # キャッシュキーの形式: cache_<hash>
        if not cache_key.startswith("cache_"):
            return {"error": "Invalid cache key format"}

        # ハッシュ部分を取得
        hash_part = cache_key[6:]  # "cache_" を除去

        # 実際の実装では、ハッシュから元のコンポーネントを復元する必要がある
        # 現在は簡易的な実装
        components = {
            "hash": hash_part,
            "key_type": "analysis_cache",
        }

        logger.debug(f"Extracted cache key components: {components}")
        return components

    except Exception as e:
        logger.error(f"Failed to extract cache key components: {str(e)}")
        return {"error": str(e)}


def validate_cache_data(data: Any) -> bool:
    """
    キャッシュデータの妥当性を検証

    Args:
        data: 検証するデータ

    Returns:
        bool: データが妥当な場合True
    """
    try:
        if data is None:
            return False

        # 基本的な型チェック
        if not isinstance(data, (dict, list, str, int, float, bool)):
            return False

        # 辞書の場合、必須フィールドのチェック
        if isinstance(data, dict):
            required_fields = ["timestamp", "data"]
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Cache data missing required field: {field}")
                    return False

        # サイズチェック（1MB制限）
        data_size = len(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        if data_size > 1024 * 1024:  # 1MB
            logger.warning(f"Cache data too large: {data_size} bytes")
            return False

        logger.debug(f"Cache data validation passed: {type(data).__name__}")
        return True

    except Exception as e:
        logger.error(f"Cache data validation failed: {str(e)}")
        return False


def get_cache_expiry_time(
    ttl_seconds: int,
    base_time: Optional[datetime] = None,
) -> datetime:
    """
    キャッシュの有効期限を計算

    Args:
        ttl_seconds: TTL（秒）
        base_time: 基準時刻（オプション）

    Returns:
        datetime: 有効期限
    """
    try:
        if base_time is None:
            base_time = datetime.utcnow()

        expiry_time = base_time + timedelta(seconds=ttl_seconds)

        logger.debug(f"Calculated expiry time: {expiry_time} (TTL: {ttl_seconds}s)")
        return expiry_time

    except Exception as e:
        logger.error(f"Failed to calculate expiry time: {str(e)}")
        # フォールバック: 1時間後
        return datetime.utcnow() + timedelta(hours=1)
