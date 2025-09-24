"""
FRED (Federal Reserve Economic Data) プロバイダー

FRED APIから経済指標データを取得します。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
import asyncio
import aiohttp

from .base_economic_provider import BaseEconomicProvider, EconomicDataResult

logger = logging.getLogger(__name__)


class FREDProvider(BaseEconomicProvider):
    """FREDプロバイダー"""
    
    def __init__(self, api_key: str):
        """
        FREDプロバイダーを初期化
        
        Args:
            api_key: FRED APIキー
        """
        super().__init__("FRED")
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self) -> None:
        """プロバイダーを初期化"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        logger.info("FRED provider initialized")
    
    async def close(self) -> None:
        """プロバイダーを閉じる"""
        if self.session:
            await self.session.close()
        logger.info("FRED provider closed")
    
    async def get_series_data(
        self,
        series_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        frequency: str = "d",
        units: str = "lin"
    ) -> EconomicDataResult:
        """
        シリーズデータを取得
        
        Args:
            series_id: シリーズID
            start_date: 開始日
            end_date: 終了日
            frequency: 頻度 (d=daily, w=weekly, m=monthly, q=quarterly, a=annual)
            units: 単位 (lin=levels, chg=change, ch1=change from year ago, pch=percent change, pca=percent change from year ago)
            
        Returns:
            経済データ結果
        """
        try:
            if not self.session:
                await self.initialize()
            
            # パラメータを準備
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "frequency": frequency,
                "units": units
            }
            
            if start_date:
                params["observation_start"] = start_date.strftime("%Y-%m-%d")
            if end_date:
                params["observation_end"] = end_date.strftime("%Y-%m-%d")
            
            # APIリクエスト
            url = f"{self.base_url}/series/observations"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_series_data(data, series_id)
                else:
                    error_text = await response.text()
                    logger.error(f"FRED API error: {response.status} - {error_text}")
                    return EconomicDataResult(
                        success=False,
                        error_message=f"API error: {response.status}",
                        data=None
                    )
        
        except Exception as e:
            logger.error(f"Error fetching FRED data: {e}")
            return EconomicDataResult(
                success=False,
                error_message=str(e),
                data=None
            )
    
    def _parse_series_data(self, api_response: Dict[str, Any], series_id: str) -> EconomicDataResult:
        """
        APIレスポンスを解析
        
        Args:
            api_response: APIレスポンス
            series_id: シリーズID
            
        Returns:
            経済データ結果
        """
        try:
            observations = api_response.get("observations", [])
            
            if not observations:
                return EconomicDataResult(
                    success=False,
                    error_message="No data available",
                    data=None
                )
            
            # データを変換
            data_points = []
            for obs in observations:
                date_str = obs.get("date")
                value_str = obs.get("value")
                
                if date_str and value_str != ".":  # "."は欠損値を表す
                    try:
                        date = datetime.strptime(date_str, "%Y-%m-%d")
                        value = float(value_str)
                        
                        data_points.append({
                            "date": date,
                            "value": value,
                            "series_id": series_id
                        })
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse observation: {obs} - {e}")
                        continue
            
            return EconomicDataResult(
                success=True,
                data={
                    "series_id": series_id,
                    "data_points": data_points,
                    "total_points": len(data_points),
                    "source": "FRED"
                },
                metadata={
                    "provider": "FRED",
                    "api_response": api_response
                }
            )
        
        except Exception as e:
            logger.error(f"Error parsing FRED response: {e}")
            return EconomicDataResult(
                success=False,
                error_message=f"Parse error: {e}",
                data=None
            )
    
    async def get_series_info(self, series_id: str) -> EconomicDataResult:
        """
        シリーズ情報を取得
        
        Args:
            series_id: シリーズID
            
        Returns:
            シリーズ情報
        """
        try:
            if not self.session:
                await self.initialize()
            
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json"
            }
            
            url = f"{self.base_url}/series"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_series_info(data, series_id)
                else:
                    error_text = await response.text()
                    logger.error(f"FRED API error: {response.status} - {error_text}")
                    return EconomicDataResult(
                        success=False,
                        error_message=f"API error: {response.status}",
                        data=None
                    )
        
        except Exception as e:
            logger.error(f"Error fetching FRED series info: {e}")
            return EconomicDataResult(
                success=False,
                error_message=str(e),
                data=None
            )
    
    def _parse_series_info(self, api_response: Dict[str, Any], series_id: str) -> EconomicDataResult:
        """
        シリーズ情報を解析
        
        Args:
            api_response: APIレスポンス
            series_id: シリーズID
            
        Returns:
            シリーズ情報
        """
        try:
            series_list = api_response.get("seriess", [])
            
            if not series_list:
                return EconomicDataResult(
                    success=False,
                    error_message="Series not found",
                    data=None
                )
            
            series_info = series_list[0]
            
            return EconomicDataResult(
                success=True,
                data={
                    "series_id": series_id,
                    "title": series_info.get("title", ""),
                    "units": series_info.get("units", ""),
                    "frequency": series_info.get("frequency", ""),
                    "seasonal_adjustment": series_info.get("seasonal_adjustment", ""),
                    "last_updated": series_info.get("last_updated", ""),
                    "notes": series_info.get("notes", ""),
                    "source": "FRED"
                },
                metadata={
                    "provider": "FRED",
                    "api_response": api_response
                }
            )
        
        except Exception as e:
            logger.error(f"Error parsing FRED series info: {e}")
            return EconomicDataResult(
                success=False,
                error_message=f"Parse error: {e}",
                data=None
            )
    
    async def search_series(
        self,
        search_text: str,
        limit: int = 100
    ) -> EconomicDataResult:
        """
        シリーズを検索
        
        Args:
            search_text: 検索テキスト
            limit: 結果の上限
            
        Returns:
            検索結果
        """
        try:
            if not self.session:
                await self.initialize()
            
            params = {
                "search_text": search_text,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": limit,
                "order_by": "popularity",
                "sort_order": "desc"
            }
            
            url = f"{self.base_url}/series/search"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_search_results(data, search_text)
                else:
                    error_text = await response.text()
                    logger.error(f"FRED API error: {response.status} - {error_text}")
                    return EconomicDataResult(
                        success=False,
                        error_message=f"API error: {response.status}",
                        data=None
                    )
        
        except Exception as e:
            logger.error(f"Error searching FRED series: {e}")
            return EconomicDataResult(
                success=False,
                error_message=str(e),
                data=None
            )
    
    def _parse_search_results(self, api_response: Dict[str, Any], search_text: str) -> EconomicDataResult:
        """
        検索結果を解析
        
        Args:
            api_response: APIレスポンス
            search_text: 検索テキスト
            
        Returns:
            検索結果
        """
        try:
            series_list = api_response.get("seriess", [])
            
            search_results = []
            for series in series_list:
                search_results.append({
                    "series_id": series.get("id", ""),
                    "title": series.get("title", ""),
                    "units": series.get("units", ""),
                    "frequency": series.get("frequency", ""),
                    "seasonal_adjustment": series.get("seasonal_adjustment", ""),
                    "popularity": series.get("popularity", 0),
                    "notes": series.get("notes", "")
                })
            
            return EconomicDataResult(
                success=True,
                data={
                    "search_text": search_text,
                    "results": search_results,
                    "total_results": len(search_results),
                    "source": "FRED"
                },
                metadata={
                    "provider": "FRED",
                    "api_response": api_response
                }
            )
        
        except Exception as e:
            logger.error(f"Error parsing FRED search results: {e}")
            return EconomicDataResult(
                success=False,
                error_message=f"Parse error: {e}",
                data=None
            )
    
    async def get_categories(self, category_id: Optional[int] = None) -> EconomicDataResult:
        """
        カテゴリを取得
        
        Args:
            category_id: カテゴリID（Noneの場合はルートカテゴリ）
            
        Returns:
            カテゴリ情報
        """
        try:
            if not self.session:
                await self.initialize()
            
            params = {
                "api_key": self.api_key,
                "file_type": "json"
            }
            
            if category_id:
                params["category_id"] = category_id
            
            url = f"{self.base_url}/categories"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_categories(data, category_id)
                else:
                    error_text = await response.text()
                    logger.error(f"FRED API error: {response.status} - {error_text}")
                    return EconomicDataResult(
                        success=False,
                        error_message=f"API error: {response.status}",
                        data=None
                    )
        
        except Exception as e:
            logger.error(f"Error fetching FRED categories: {e}")
            return EconomicDataResult(
                success=False,
                error_message=str(e),
                data=None
            )
    
    def _parse_categories(self, api_response: Dict[str, Any], category_id: Optional[int]) -> EconomicDataResult:
        """
        カテゴリ情報を解析
        
        Args:
            api_response: APIレスポンス
            category_id: カテゴリID
            
        Returns:
            カテゴリ情報
        """
        try:
            categories = api_response.get("categories", [])
            
            category_list = []
            for category in categories:
                category_list.append({
                    "id": category.get("id", 0),
                    "name": category.get("name", ""),
                    "parent_id": category.get("parent_id", 0),
                    "notes": category.get("notes", "")
                })
            
            return EconomicDataResult(
                success=True,
                data={
                    "category_id": category_id,
                    "categories": category_list,
                    "total_categories": len(category_list),
                    "source": "FRED"
                },
                metadata={
                    "provider": "FRED",
                    "api_response": api_response
                }
            )
        
        except Exception as e:
            logger.error(f"Error parsing FRED categories: {e}")
            return EconomicDataResult(
                success=False,
                error_message=f"Parse error: {e}",
                data=None
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        ヘルスチェック
        
        Returns:
            ヘルス情報
        """
        try:
            # 簡単なAPIリクエストでヘルスチェック
            result = await self.get_series_info("GDP")  # GDPは常に存在するシリーズ
            
            return {
                "status": "healthy" if result.success else "unhealthy",
                "provider": "FRED",
                "api_accessible": result.success,
                "error": result.error_message if not result.success else None
            }
        
        except Exception as e:
            logger.error(f"FRED health check failed: {e}")
            return {
                "status": "unhealthy",
                "provider": "FRED",
                "api_accessible": False,
                "error": str(e)
            }
