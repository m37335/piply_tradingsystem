"""
影響度分析システム

経済指標の市場への影響度を分析します。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ImpactLevel(Enum):
    """影響度レベル"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MarketSector(Enum):
    """市場セクター"""
    CURRENCY = "currency"
    STOCK = "stock"
    BOND = "bond"
    COMMODITY = "commodity"
    CRYPTO = "crypto"


@dataclass
class ImpactAnalysis:
    """影響度分析結果"""
    indicator_name: str
    country: str
    impact_level: ImpactLevel
    affected_sectors: List[MarketSector]
    affected_currencies: List[str]
    volatility_impact: float  # 0.0 - 1.0
    confidence_score: float  # 0.0 - 1.0
    analysis_timestamp: datetime
    reasoning: str


@dataclass
class MarketImpact:
    """市場影響"""
    sector: MarketSector
    impact_strength: float  # 0.0 - 1.0
    direction: str  # "positive", "negative", "neutral"
    duration_hours: int
    affected_assets: List[str]


class ImpactAnalyzer:
    """影響度分析システム"""
    
    def __init__(self):
        self.indicator_impacts: Dict[str, Dict[str, Any]] = {}
        self.currency_impacts: Dict[str, Dict[str, Any]] = {}
        self.sector_impacts: Dict[MarketSector, Dict[str, Any]] = {}
        self._init_default_impacts()
    
    def _init_default_impacts(self) -> None:
        """デフォルトの影響度設定を初期化"""
        # 主要経済指標の影響度設定
        self.indicator_impacts = {
            # 雇用関連
            "Non-Farm Payrolls": {
                "impact_level": ImpactLevel.CRITICAL,
                "affected_sectors": [MarketSector.CURRENCY, MarketSector.STOCK, MarketSector.BOND],
                "volatility_impact": 0.9,
                "confidence_score": 0.95,
                "reasoning": "雇用統計は米国経済の最重要指標の一つ"
            },
            "Unemployment Rate": {
                "impact_level": ImpactLevel.HIGH,
                "affected_sectors": [MarketSector.CURRENCY, MarketSector.STOCK],
                "volatility_impact": 0.8,
                "confidence_score": 0.9,
                "reasoning": "失業率は経済の健全性を示す重要指標"
            },
            
            # インフレ関連
            "Consumer Price Index": {
                "impact_level": ImpactLevel.CRITICAL,
                "affected_sectors": [MarketSector.CURRENCY, MarketSector.BOND, MarketSector.STOCK],
                "volatility_impact": 0.85,
                "confidence_score": 0.9,
                "reasoning": "CPIは中央銀行の政策決定に直接影響"
            },
            "Producer Price Index": {
                "impact_level": ImpactLevel.HIGH,
                "affected_sectors": [MarketSector.CURRENCY, MarketSector.BOND],
                "volatility_impact": 0.7,
                "confidence_score": 0.8,
                "reasoning": "PPIは将来のCPIの先行指標"
            },
            
            # GDP関連
            "Gross Domestic Product": {
                "impact_level": ImpactLevel.CRITICAL,
                "affected_sectors": [MarketSector.CURRENCY, MarketSector.STOCK, MarketSector.BOND],
                "volatility_impact": 0.8,
                "confidence_score": 0.85,
                "reasoning": "GDPは経済成長の総合指標"
            },
            
            # 中央銀行関連
            "Federal Funds Rate": {
                "impact_level": ImpactLevel.CRITICAL,
                "affected_sectors": [MarketSector.CURRENCY, MarketSector.BOND, MarketSector.STOCK],
                "volatility_impact": 0.95,
                "confidence_score": 0.98,
                "reasoning": "政策金利は全ての資産クラスに影響"
            },
            "Interest Rate Decision": {
                "impact_level": ImpactLevel.CRITICAL,
                "affected_sectors": [MarketSector.CURRENCY, MarketSector.BOND, MarketSector.STOCK],
                "volatility_impact": 0.9,
                "confidence_score": 0.95,
                "reasoning": "金利決定は市場の最重要イベント"
            },
            
            # 貿易関連
            "Trade Balance": {
                "impact_level": ImpactLevel.MEDIUM,
                "affected_sectors": [MarketSector.CURRENCY],
                "volatility_impact": 0.6,
                "confidence_score": 0.7,
                "reasoning": "貿易収支は通貨に中程度の影響"
            },
            
            # 消費者関連
            "Retail Sales": {
                "impact_level": ImpactLevel.HIGH,
                "affected_sectors": [MarketSector.CURRENCY, MarketSector.STOCK],
                "volatility_impact": 0.7,
                "confidence_score": 0.8,
                "reasoning": "小売売上高は消費動向を示す重要指標"
            },
            "Consumer Confidence": {
                "impact_level": ImpactLevel.MEDIUM,
                "affected_sectors": [MarketSector.STOCK],
                "volatility_impact": 0.5,
                "confidence_score": 0.6,
                "reasoning": "消費者信頼感は株式市場に中程度の影響"
            },
            
            # 製造業関連
            "Industrial Production": {
                "impact_level": ImpactLevel.MEDIUM,
                "affected_sectors": [MarketSector.CURRENCY, MarketSector.STOCK],
                "volatility_impact": 0.6,
                "confidence_score": 0.7,
                "reasoning": "鉱工業生産は製造業の健全性を示す"
            },
            "Manufacturing PMI": {
                "impact_level": ImpactLevel.HIGH,
                "affected_sectors": [MarketSector.CURRENCY, MarketSector.STOCK],
                "volatility_impact": 0.7,
                "confidence_score": 0.8,
                "reasoning": "製造業PMIは景気の先行指標"
            }
        }
        
        # 通貨別の影響度設定
        self.currency_impacts = {
            "USD": {
                "global_impact": 0.9,
                "affected_currencies": ["EUR", "JPY", "GBP", "CHF", "CAD", "AUD"],
                "reasoning": "米ドルは世界の基軸通貨"
            },
            "EUR": {
                "global_impact": 0.8,
                "affected_currencies": ["USD", "GBP", "CHF", "JPY"],
                "reasoning": "ユーロは世界第2の基軸通貨"
            },
            "JPY": {
                "global_impact": 0.7,
                "affected_currencies": ["USD", "EUR", "GBP"],
                "reasoning": "円は主要通貨の一つ"
            },
            "GBP": {
                "global_impact": 0.6,
                "affected_currencies": ["USD", "EUR", "JPY"],
                "reasoning": "ポンドは主要通貨の一つ"
            }
        }
        
        # セクター別の影響度設定
        self.sector_impacts = {
            MarketSector.CURRENCY: {
                "sensitivity": 0.9,
                "reaction_time_minutes": 5,
                "duration_hours": 2
            },
            MarketSector.BOND: {
                "sensitivity": 0.8,
                "reaction_time_minutes": 10,
                "duration_hours": 4
            },
            MarketSector.STOCK: {
                "sensitivity": 0.7,
                "reaction_time_minutes": 15,
                "duration_hours": 6
            },
            MarketSector.COMMODITY: {
                "sensitivity": 0.6,
                "reaction_time_minutes": 30,
                "duration_hours": 8
            },
            MarketSector.CRYPTO: {
                "sensitivity": 0.5,
                "reaction_time_minutes": 60,
                "duration_hours": 12
            }
        }
    
    def analyze_impact(
        self,
        indicator_name: str,
        country: str,
        currency: Optional[str] = None,
        forecast_value: Optional[float] = None,
        previous_value: Optional[float] = None
    ) -> ImpactAnalysis:
        """
        経済指標の影響度を分析
        
        Args:
            indicator_name: 指標名
            country: 国名
            currency: 通貨コード
            forecast_value: 予想値
            previous_value: 前回値
            
        Returns:
            影響度分析結果
        """
        try:
            # 基本の影響度設定を取得
            base_impact = self.indicator_impacts.get(indicator_name, {
                "impact_level": ImpactLevel.MEDIUM,
                "affected_sectors": [MarketSector.CURRENCY],
                "volatility_impact": 0.5,
                "confidence_score": 0.6,
                "reasoning": "一般的な経済指標の影響度"
            })
            
            # 通貨の影響度を調整
            volatility_impact = base_impact["volatility_impact"]
            confidence_score = base_impact["confidence_score"]
            
            if currency and currency in self.currency_impacts:
                currency_impact = self.currency_impacts[currency]
                volatility_impact *= currency_impact["global_impact"]
                confidence_score *= 0.9  # 通貨の影響度で信頼度を調整
            
            # 予想値と前回値の乖離を考慮
            if forecast_value is not None and previous_value is not None:
                deviation = abs(forecast_value - previous_value) / abs(previous_value) if previous_value != 0 else 0
                if deviation > 0.1:  # 10%以上の乖離
                    volatility_impact *= 1.2
                    confidence_score *= 1.1
            
            # 影響度レベルを調整
            impact_level = base_impact["impact_level"]
            if volatility_impact > 0.8:
                impact_level = ImpactLevel.CRITICAL
            elif volatility_impact > 0.6:
                impact_level = ImpactLevel.HIGH
            elif volatility_impact > 0.4:
                impact_level = ImpactLevel.MEDIUM
            else:
                impact_level = ImpactLevel.LOW
            
            # 影響を受ける通貨を決定
            affected_currencies = [currency] if currency else []
            if currency and currency in self.currency_impacts:
                affected_currencies.extend(self.currency_impacts[currency]["affected_currencies"])
            
            return ImpactAnalysis(
                indicator_name=indicator_name,
                country=country,
                impact_level=impact_level,
                affected_sectors=base_impact["affected_sectors"],
                affected_currencies=list(set(affected_currencies)),
                volatility_impact=min(1.0, volatility_impact),
                confidence_score=min(1.0, confidence_score),
                analysis_timestamp=datetime.now(),
                reasoning=base_impact["reasoning"]
            )
        
        except Exception as e:
            logger.error(f"Error analyzing impact: {e}")
            return ImpactAnalysis(
                indicator_name=indicator_name,
                country=country,
                impact_level=ImpactLevel.LOW,
                affected_sectors=[],
                affected_currencies=[],
                volatility_impact=0.0,
                confidence_score=0.0,
                analysis_timestamp=datetime.now(),
                reasoning=f"分析エラー: {str(e)}"
            )
    
    def get_market_impacts(self, analysis: ImpactAnalysis) -> List[MarketImpact]:
        """
        市場セクター別の影響を取得
        
        Args:
            analysis: 影響度分析結果
            
        Returns:
            市場影響のリスト
        """
        market_impacts = []
        
        for sector in analysis.affected_sectors:
            if sector in self.sector_impacts:
                sector_config = self.sector_impacts[sector]
                
                # 影響の強さを計算
                impact_strength = analysis.volatility_impact * sector_config["sensitivity"]
                
                # 影響の方向を決定（簡易実装）
                direction = "neutral"
                if analysis.indicator_name in ["Non-Farm Payrolls", "GDP"]:
                    direction = "positive"  # 一般的に良い指標
                elif analysis.indicator_name in ["Unemployment Rate", "CPI"]:
                    direction = "negative"  # 一般的に悪い指標
                
                # 影響を受ける資産を決定
                affected_assets = []
                if sector == MarketSector.CURRENCY:
                    affected_assets = analysis.affected_currencies
                elif sector == MarketSector.STOCK:
                    affected_assets = [f"{analysis.country}_STOCK_INDEX"]
                elif sector == MarketSector.BOND:
                    affected_assets = [f"{analysis.country}_BOND_YIELD"]
                
                market_impact = MarketImpact(
                    sector=sector,
                    impact_strength=impact_strength,
                    direction=direction,
                    duration_hours=sector_config["duration_hours"],
                    affected_assets=affected_assets
                )
                
                market_impacts.append(market_impact)
        
        return market_impacts
    
    def get_impact_summary(
        self,
        analyses: List[ImpactAnalysis]
    ) -> Dict[str, Any]:
        """
        影響度分析のサマリーを取得
        
        Args:
            analyses: 影響度分析結果のリスト
            
        Returns:
            サマリー情報
        """
        if not analyses:
            return {
                "total_indicators": 0,
                "impact_levels": {},
                "affected_sectors": {},
                "affected_currencies": {},
                "average_volatility": 0.0,
                "average_confidence": 0.0
            }
        
        # 影響度レベル別の集計
        impact_levels = {}
        for analysis in analyses:
            level = analysis.impact_level.value
            impact_levels[level] = impact_levels.get(level, 0) + 1
        
        # 影響を受けるセクター別の集計
        affected_sectors = {}
        for analysis in analyses:
            for sector in analysis.affected_sectors:
                sector_name = sector.value
                affected_sectors[sector_name] = affected_sectors.get(sector_name, 0) + 1
        
        # 影響を受ける通貨別の集計
        affected_currencies = {}
        for analysis in analyses:
            for currency in analysis.affected_currencies:
                affected_currencies[currency] = affected_currencies.get(currency, 0) + 1
        
        # 平均値の計算
        total_volatility = sum(analysis.volatility_impact for analysis in analyses)
        total_confidence = sum(analysis.confidence_score for analysis in analyses)
        
        return {
            "total_indicators": len(analyses),
            "impact_levels": impact_levels,
            "affected_sectors": affected_sectors,
            "affected_currencies": affected_currencies,
            "average_volatility": total_volatility / len(analyses),
            "average_confidence": total_confidence / len(analyses),
            "highest_impact": max(analyses, key=lambda x: x.volatility_impact).indicator_name if analyses else None,
            "lowest_confidence": min(analyses, key=lambda x: x.confidence_score).indicator_name if analyses else None
        }
    
    def add_custom_impact(
        self,
        indicator_name: str,
        impact_config: Dict[str, Any]
    ) -> None:
        """
        カスタム影響度設定を追加
        
        Args:
            indicator_name: 指標名
            impact_config: 影響度設定
        """
        self.indicator_impacts[indicator_name] = impact_config
        logger.info(f"Added custom impact for {indicator_name}")
    
    def update_impact(
        self,
        indicator_name: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        影響度設定を更新
        
        Args:
            indicator_name: 指標名
            updates: 更新内容
            
        Returns:
            更新が成功したかどうか
        """
        if indicator_name not in self.indicator_impacts:
            return False
        
        self.indicator_impacts[indicator_name].update(updates)
        logger.info(f"Updated impact for {indicator_name}")
        return True
    
    def get_impact_config(self, indicator_name: str) -> Optional[Dict[str, Any]]:
        """
        影響度設定を取得
        
        Args:
            indicator_name: 指標名
            
        Returns:
            影響度設定、またはNone
        """
        return self.indicator_impacts.get(indicator_name)
    
    def get_all_impact_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        すべての影響度設定を取得
        
        Returns:
            影響度設定の辞書
        """
        return self.indicator_impacts.copy()
    
    def export_impact_configs(self) -> Dict[str, Any]:
        """
        影響度設定をエクスポート
        
        Returns:
            エクスポートされた設定
        """
        return {
            "export_timestamp": datetime.now().isoformat(),
            "indicator_impacts": self.indicator_impacts,
            "currency_impacts": self.currency_impacts,
            "sector_impacts": {
                sector.value: config for sector, config in self.sector_impacts.items()
            }
        }
    
    def import_impact_configs(self, config_data: Dict[str, Any]) -> int:
        """
        影響度設定をインポート
        
        Args:
            config_data: 設定データ
            
        Returns:
            インポートされた設定数
        """
        imported_count = 0
        
        # 指標影響度設定をインポート
        if "indicator_impacts" in config_data:
            for indicator, config in config_data["indicator_impacts"].items():
                self.indicator_impacts[indicator] = config
                imported_count += 1
        
        # 通貨影響度設定をインポート
        if "currency_impacts" in config_data:
            for currency, config in config_data["currency_impacts"].items():
                self.currency_impacts[currency] = config
                imported_count += 1
        
        # セクター影響度設定をインポート
        if "sector_impacts" in config_data:
            for sector_name, config in config_data["sector_impacts"].items():
                try:
                    sector = MarketSector(sector_name)
                    self.sector_impacts[sector] = config
                    imported_count += 1
                except ValueError:
                    logger.warning(f"Unknown sector: {sector_name}")
        
        logger.info(f"Imported {imported_count} impact configurations")
        return imported_count
