"""
LLM分析エンジン

LLMを使用した包括的な市場分析を実行します。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from .market_analyzer import MarketAnalyzer
from .sentiment_analyzer import SentimentAnalyzer
from .pattern_analyzer import PatternAnalyzer
from .risk_analyzer import RiskAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRequest:
    """分析リクエスト"""
    symbol: str
    timeframe: str
    analysis_type: str  # "comprehensive", "sentiment", "pattern", "risk"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class AnalysisResult:
    """分析結果"""
    symbol: str
    timeframe: str
    analysis_type: str
    timestamp: datetime
    success: bool
    results: Dict[str, Any]
    confidence_score: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AnalysisEngine:
    """LLM分析エンジン"""
    
    def __init__(self):
        self.market_analyzer = MarketAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.pattern_analyzer = PatternAnalyzer()
        self.risk_analyzer = RiskAnalyzer()
        self._initialized = False
    
    async def initialize(self) -> None:
        """分析エンジンを初期化"""
        try:
            await self.market_analyzer.initialize()
            await self.sentiment_analyzer.initialize()
            await self.pattern_analyzer.initialize()
            await self.risk_analyzer.initialize()
            
            self._initialized = True
            logger.info("Analysis engine initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize analysis engine: {e}")
            raise
    
    async def close(self) -> None:
        """分析エンジンを閉じる"""
        try:
            await self.market_analyzer.close()
            await self.sentiment_analyzer.close()
            await self.pattern_analyzer.close()
            await self.risk_analyzer.close()
            
            self._initialized = False
            logger.info("Analysis engine closed")
        
        except Exception as e:
            logger.error(f"Error closing analysis engine: {e}")
    
    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """
        分析を実行
        
        Args:
            request: 分析リクエスト
            
        Returns:
            分析結果
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"Starting analysis for {request.symbol} ({request.analysis_type})")
            
            if request.analysis_type == "comprehensive":
                result = await self._comprehensive_analysis(request)
            elif request.analysis_type == "sentiment":
                result = await self._sentiment_analysis(request)
            elif request.analysis_type == "pattern":
                result = await self._pattern_analysis(request)
            elif request.analysis_type == "risk":
                result = await self._risk_analysis(request)
            else:
                raise ValueError(f"Unknown analysis type: {request.analysis_type}")
            
            logger.info(f"Analysis completed for {request.symbol}")
            return result
        
        except Exception as e:
            logger.error(f"Analysis failed for {request.symbol}: {e}")
            return AnalysisResult(
                symbol=request.symbol,
                timeframe=request.timeframe,
                analysis_type=request.analysis_type,
                timestamp=datetime.now(),
                success=False,
                results={},
                confidence_score=0.0,
                error_message=str(e)
            )
    
    async def _comprehensive_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """
        包括的分析を実行
        
        Args:
            request: 分析リクエスト
            
        Returns:
            分析結果
        """
        try:
            # 各分析を並行実行
            market_result = await self.market_analyzer.analyze(request)
            sentiment_result = await self.sentiment_analyzer.analyze(request)
            pattern_result = await self.pattern_analyzer.analyze(request)
            risk_result = await self.risk_analyzer.analyze(request)
            
            # 結果を統合
            combined_results = {
                "market_analysis": market_result.results if market_result.success else {},
                "sentiment_analysis": sentiment_result.results if sentiment_result.success else {},
                "pattern_analysis": pattern_result.results if pattern_result.success else {},
                "risk_analysis": risk_result.results if risk_result.success else {}
            }
            
            # 信頼度スコアを計算
            confidence_scores = [
                market_result.confidence_score,
                sentiment_result.confidence_score,
                pattern_result.confidence_score,
                risk_result.confidence_score
            ]
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            
            # 成功判定
            success = all([
                market_result.success,
                sentiment_result.success,
                pattern_result.success,
                risk_result.success
            ])
            
            return AnalysisResult(
                symbol=request.symbol,
                timeframe=request.timeframe,
                analysis_type=request.analysis_type,
                timestamp=datetime.now(),
                success=success,
                results=combined_results,
                confidence_score=avg_confidence,
                metadata={
                    "individual_results": {
                        "market": market_result.success,
                        "sentiment": sentiment_result.success,
                        "pattern": pattern_result.success,
                        "risk": risk_result.success
                    }
                }
            )
        
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            raise
    
    async def _sentiment_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """
        センチメント分析を実行
        
        Args:
            request: 分析リクエスト
            
        Returns:
            分析結果
        """
        return await self.sentiment_analyzer.analyze(request)
    
    async def _pattern_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """
        パターン分析を実行
        
        Args:
            request: 分析リクエスト
            
        Returns:
            分析結果
        """
        return await self.pattern_analyzer.analyze(request)
    
    async def _risk_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """
        リスク分析を実行
        
        Args:
            request: 分析リクエスト
            
        Returns:
            分析結果
        """
        return await self.risk_analyzer.analyze(request)
    
    async def batch_analyze(self, requests: List[AnalysisRequest]) -> List[AnalysisResult]:
        """
        バッチ分析を実行
        
        Args:
            requests: 分析リクエストのリスト
            
        Returns:
            分析結果のリスト
        """
        if not self._initialized:
            await self.initialize()
        
        results = []
        for request in requests:
            try:
                result = await self.analyze(request)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch analysis failed for {request.symbol}: {e}")
                results.append(AnalysisResult(
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    analysis_type=request.analysis_type,
                    timestamp=datetime.now(),
                    success=False,
                    results={},
                    confidence_score=0.0,
                    error_message=str(e)
                ))
        
        return results
    
    async def get_analysis_history(
        self,
        symbol: str,
        limit: int = 10
    ) -> List[AnalysisResult]:
        """
        分析履歴を取得
        
        Args:
            symbol: シンボル
            limit: 取得件数
            
        Returns:
            分析結果のリスト
        """
        # 実装はデータベースから履歴を取得
        # ここでは簡易実装
        return []
    
    async def health_check(self) -> Dict[str, Any]:
        """
        ヘルスチェック
        
        Returns:
            ヘルス情報
        """
        try:
            health_status = {
                "status": "healthy",
                "initialized": self._initialized,
                "components": {
                    "market_analyzer": await self.market_analyzer.health_check(),
                    "sentiment_analyzer": await self.sentiment_analyzer.health_check(),
                    "pattern_analyzer": await self.pattern_analyzer.health_check(),
                    "risk_analyzer": await self.risk_analyzer.health_check()
                }
            }
            
            # 全体のヘルス状態を判定
            component_statuses = [
                component.get("status", "unknown")
                for component in health_status["components"].values()
            ]
            
            if "unhealthy" in component_statuses:
                health_status["status"] = "degraded"
            elif "unknown" in component_statuses:
                health_status["status"] = "unknown"
            
            return health_status
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_supported_analysis_types(self) -> List[str]:
        """
        サポートされている分析タイプを取得
        
        Returns:
            分析タイプのリスト
        """
        return ["comprehensive", "sentiment", "pattern", "risk"]
    
    def get_analysis_parameters(self, analysis_type: str) -> Dict[str, Any]:
        """
        分析タイプのパラメータを取得
        
        Args:
            analysis_type: 分析タイプ
            
        Returns:
            パラメータの辞書
        """
        parameter_templates = {
            "comprehensive": {
                "include_sentiment": True,
                "include_patterns": True,
                "include_risk": True,
                "depth": "medium"
            },
            "sentiment": {
                "sources": ["news", "social", "market"],
                "timeframe": "24h",
                "confidence_threshold": 0.7
            },
            "pattern": {
                "pattern_types": ["technical", "fundamental", "seasonal"],
                "lookback_period": 30,
                "min_confidence": 0.6
            },
            "risk": {
                "risk_factors": ["volatility", "liquidity", "correlation"],
                "scenario_count": 5,
                "confidence_level": 0.95
            }
        }
        
        return parameter_templates.get(analysis_type, {})
