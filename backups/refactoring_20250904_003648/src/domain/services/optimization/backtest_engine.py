"""
バックテストエンジン

プロトレーダー向け為替アラートシステム用のバックテストエンジン
設計書参照: /app/note/2025-01-15_実装計画_Phase3_パフォーマンス最適化.yaml
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)
from src.infrastructure.database.models.signal_performance_model import (
    SignalPerformanceModel,
)


class BacktestEngine:
    """
    バックテストエンジン

    責任:
    - 過去データでのシグナル生成
    - 仮想的な取引実行シミュレーション
    - バックテスト結果の詳細分析
    - パラメータ最適化

    特徴:
    - リアルタイムシミュレーション
    - 詳細結果分析
    - パラメータ最適化
    - 履歴管理
    """

    def __init__(self, db_session: AsyncSession):
        """
        初期化

        Args:
            db_session: データベースセッション
        """
        self.db_session = db_session
        self.currency_pair = "USD/JPY"
        self.initial_balance = 10000.0  # 初期資金
        self.commission_rate = 0.0001  # 手数料率（0.01%）

    async def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "H1",
        strategy_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        バックテストを実行

        Args:
            start_date: 開始日
            end_date: 終了日
            timeframe: タイムフレーム
            strategy_params: 戦略パラメータ

        Returns:
            Dict[str, Any]: バックテスト結果
        """
        try:
            # 過去データを取得
            historical_data = await self._get_historical_data(
                start_date, end_date, timeframe
            )

            if not historical_data:
                return {"error": "過去データが不足しています"}

            # バックテスト実行
            backtest_results = self._execute_backtest(
                historical_data, strategy_params or {}
            )

            # 結果分析
            analysis = self._analyze_backtest_results(backtest_results)

            # パフォーマンス統計
            performance_stats = self._calculate_performance_statistics(
                backtest_results
            )

            return {
                "backtest_info": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "timeframe": timeframe,
                    "initial_balance": self.initial_balance,
                    "strategy_params": strategy_params,
                },
                "trades": backtest_results["trades"],
                "equity_curve": backtest_results["equity_curve"],
                "performance_statistics": performance_stats,
                "analysis": analysis,
                "execution_timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error running backtest: {e}")
            return {"error": str(e)}

    async def _get_historical_data(
        self, start_date: datetime, end_date: datetime, timeframe: str
    ) -> List[Dict[str, Any]]:
        """
        過去データを取得

        Args:
            start_date: 開始日
            end_date: 終了日
            timeframe: タイムフレーム

        Returns:
            List[Dict[str, Any]]: 過去データ
        """
        query = select(TechnicalIndicatorModel).where(
            TechnicalIndicatorModel.currency_pair == self.currency_pair,
            TechnicalIndicatorModel.timeframe == timeframe,
            TechnicalIndicatorModel.timestamp >= start_date,
            TechnicalIndicatorModel.timestamp <= end_date,
        ).order_by(TechnicalIndicatorModel.timestamp)

        result = await self.db_session.execute(query)
        indicators = result.scalars().all()

        # データを辞書形式に変換
        historical_data = []
        for indicator in indicators:
            data = {
                "timestamp": indicator.timestamp,
                "open": indicator.open,
                "high": indicator.high,
                "low": indicator.low,
                "close": indicator.close,
                "volume": indicator.volume,
                "RSI": indicator.RSI,
                "SMA_20": indicator.SMA_20,
                "MACD_histogram": indicator.MACD_histogram,
                "ATR": indicator.ATR,
                "BB_upper": indicator.BB_upper,
                "BB_lower": indicator.BB_lower,
                "BB_middle": indicator.BB_middle,
                "ADX": indicator.ADX,
            }
            historical_data.append(data)

        return historical_data

    def _execute_backtest(
        self, historical_data: List[Dict[str, Any]], strategy_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        バックテストを実行

        Args:
            historical_data: 過去データ
            strategy_params: 戦略パラメータ

        Returns:
            Dict[str, Any]: バックテスト結果
        """
        # デフォルトパラメータ
        default_params = {
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "volume_multiplier": 1.5,
            "risk_reward_ratio": 2.0,
            "max_position_size": 0.1,  # 10%
        }

        # パラメータをマージ
        params = {**default_params, **strategy_params}

        # バックテスト状態
        current_balance = self.initial_balance
        equity_curve = []
        trades = []
        open_position = None

        for i, data in enumerate(historical_data):
            current_price = data["close"]
            current_time = data["timestamp"]

            # エクイティカーブを更新
            equity_curve.append({
                "timestamp": current_time,
                "balance": current_balance,
                "open_position_value": open_position["value"] if open_position else 0,
                "total_equity": current_balance + (open_position["value"] if open_position else 0),
            })

            # オープンポジションのチェック
            if open_position:
                # 決済条件チェック
                exit_signal = self._check_exit_conditions(
                    open_position, data, params
                )

                if exit_signal:
                    # ポジション決済
                    exit_price = self._calculate_exit_price(
                        open_position, data, exit_signal
                    )
                    
                    # 損益計算
                    pnl = self._calculate_pnl(
                        open_position["type"], open_position["entry_price"], exit_price
                    )
                    
                    # 手数料計算
                    commission = (
                        open_position["position_size"] * exit_price * self.commission_rate
                    )
                    
                    net_pnl = pnl - commission
                    current_balance += net_pnl

                    # 取引記録
                    trade = {
                        "entry_time": open_position["entry_time"],
                        "exit_time": current_time,
                        "type": open_position["type"],
                        "entry_price": open_position["entry_price"],
                        "exit_price": exit_price,
                        "position_size": open_position["position_size"],
                        "pnl": pnl,
                        "commission": commission,
                        "net_pnl": net_pnl,
                        "exit_reason": exit_signal,
                        "duration_minutes": int(
                            (current_time - open_position["entry_time"]).total_seconds() / 60
                        ),
                    }
                    trades.append(trade)
                    open_position = None

            # 新規エントリーシグナルチェック
            if not open_position and i > 20:  # 初期データをスキップ
                entry_signal = self._check_entry_conditions(data, params)

                if entry_signal:
                    # ポジションサイズ計算
                    position_size = self._calculate_position_size(
                        current_balance, current_price, params
                    )

                    # オープンポジション作成
                    open_position = {
                        "type": entry_signal["type"],
                        "entry_price": current_price,
                        "entry_time": current_time,
                        "position_size": position_size,
                        "value": position_size * current_price,
                        "stop_loss": entry_signal["stop_loss"],
                        "take_profit": entry_signal["take_profit"],
                    }

        # 最後のポジションを決済
        if open_position and historical_data:
            last_data = historical_data[-1]
            exit_price = last_data["close"]
            
            pnl = self._calculate_pnl(
                open_position["type"], open_position["entry_price"], exit_price
            )
            commission = (
                open_position["position_size"] * exit_price * self.commission_rate
            )
            net_pnl = pnl - commission
            current_balance += net_pnl

            trade = {
                "entry_time": open_position["entry_time"],
                "exit_time": last_data["timestamp"],
                "type": open_position["type"],
                "entry_price": open_position["entry_price"],
                "exit_price": exit_price,
                "position_size": open_position["position_size"],
                "pnl": pnl,
                "commission": commission,
                "net_pnl": net_pnl,
                "exit_reason": "end_of_period",
                "duration_minutes": int(
                    (last_data["timestamp"] - open_position["entry_time"]).total_seconds() / 60
                ),
            }
            trades.append(trade)

        return {
            "trades": trades,
            "equity_curve": equity_curve,
            "final_balance": current_balance,
            "total_return": ((current_balance - self.initial_balance) / self.initial_balance) * 100,
        }

    def _check_entry_conditions(
        self, data: Dict[str, Any], params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        エントリー条件をチェック

        Args:
            data: 市場データ
            params: 戦略パラメータ

        Returns:
            Optional[Dict[str, Any]]: エントリーシグナル
        """
        rsi = data.get("RSI")
        sma_20 = data.get("SMA_20")
        macd_hist = data.get("MACD_histogram")
        volume = data.get("volume")
        current_price = data["close"]

        if not all([rsi, sma_20, macd_hist, volume]):
            return None

        # 買いシグナル
        if (
            rsi < params["rsi_oversold"]
            and current_price > sma_20
            and macd_hist > 0
        ):
            stop_loss = sma_20 * 0.995
            take_profit = current_price * (1 + params["risk_reward_ratio"] * 0.01)
            
            return {
                "type": "BUY",
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": 70,
            }

        # 売りシグナル
        elif (
            rsi > params["rsi_overbought"]
            and current_price < sma_20
            and macd_hist < 0
        ):
            stop_loss = sma_20 * 1.005
            take_profit = current_price * (1 - params["risk_reward_ratio"] * 0.01)
            
            return {
                "type": "SELL",
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": 70,
            }

        return None

    def _check_exit_conditions(
        self, position: Dict[str, Any], data: Dict[str, Any], params: Dict[str, Any]
    ) -> Optional[str]:
        """
        決済条件をチェック

        Args:
            position: オープンポジション
            data: 市場データ
            params: 戦略パラメータ

        Returns:
            Optional[str]: 決済理由
        """
        current_price = data["close"]
        position_type = position["type"]

        # ストップロス
        if position_type == "BUY" and current_price <= position["stop_loss"]:
            return "stop_loss"
        elif position_type == "SELL" and current_price >= position["stop_loss"]:
            return "stop_loss"

        # 利益確定
        if position_type == "BUY" and current_price >= position["take_profit"]:
            return "take_profit"
        elif position_type == "SELL" and current_price <= position["take_profit"]:
            return "take_profit"

        return None

    def _calculate_exit_price(
        self, position: Dict[str, Any], data: Dict[str, Any], exit_reason: str
    ) -> float:
        """
        決済価格を計算

        Args:
            position: オープンポジション
            data: 市場データ
            exit_reason: 決済理由

        Returns:
            float: 決済価格
        """
        if exit_reason == "stop_loss":
            return position["stop_loss"]
        elif exit_reason == "take_profit":
            return position["take_profit"]
        else:
            return data["close"]

    def _calculate_position_size(
        self, balance: float, price: float, params: Dict[str, Any]
    ) -> float:
        """
        ポジションサイズを計算

        Args:
            balance: 現在の残高
            price: 現在価格
            params: 戦略パラメータ

        Returns:
            float: ポジションサイズ
        """
        max_size = balance * params["max_position_size"]
        return max_size / price

    def _calculate_pnl(self, position_type: str, entry_price: float, exit_price: float) -> float:
        """
        損益を計算

        Args:
            position_type: ポジションタイプ
            entry_price: エントリー価格
            exit_price: 決済価格

        Returns:
            float: 損益
        """
        if position_type == "BUY":
            return exit_price - entry_price
        elif position_type == "SELL":
            return entry_price - exit_price
        else:
            return 0.0

    def _analyze_backtest_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        バックテスト結果を分析

        Args:
            results: バックテスト結果

        Returns:
            Dict[str, Any]: 分析結果
        """
        trades = results["trades"]
        equity_curve = results["equity_curve"]

        if not trades:
            return {"error": "取引がありません"}

        # 基本統計
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t["net_pnl"] > 0])
        losing_trades = len([t for t in trades if t["net_pnl"] < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

        # 損益統計
        total_pnl = sum(t["net_pnl"] for t in trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        max_profit = max(t["net_pnl"] for t in trades) if trades else 0
        max_loss = min(t["net_pnl"] for t in trades) if trades else 0

        # ドローダウン計算
        max_drawdown = self._calculate_max_drawdown(equity_curve)

        # シャープレシオ計算
        returns = self._calculate_returns(equity_curve)
        sharpe_ratio = self._calculate_sharpe_ratio(returns)

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
        }

    def _calculate_performance_statistics(
        self, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        パフォーマンス統計を計算

        Args:
            results: バックテスト結果

        Returns:
            Dict[str, Any]: パフォーマンス統計
        """
        trades = results["trades"]
        final_balance = results["final_balance"]
        total_return = results["total_return"]

        if not trades:
            return {}

        # 月次リターン
        monthly_returns = self._calculate_monthly_returns(trades)

        # ボラティリティ
        returns = self._calculate_returns(results["equity_curve"])
        volatility = np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0

        # 最大連続損失
        max_consecutive_losses = self._calculate_max_consecutive_losses(trades)

        # プロフィットファクター
        total_profit = sum(t["net_pnl"] for t in trades if t["net_pnl"] > 0)
        total_loss = abs(sum(t["net_pnl"] for t in trades if t["net_pnl"] < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        return {
            "total_return": total_return,
            "final_balance": final_balance,
            "volatility": volatility,
            "monthly_returns": monthly_returns,
            "max_consecutive_losses": max_consecutive_losses,
            "profit_factor": profit_factor,
        }

    def _calculate_max_drawdown(self, equity_curve: List[Dict[str, Any]]) -> float:
        """
        最大ドローダウンを計算

        Args:
            equity_curve: エクイティカーブ

        Returns:
            float: 最大ドローダウン
        """
        if not equity_curve:
            return 0.0

        peak = equity_curve[0]["total_equity"]
        max_drawdown = 0.0

        for point in equity_curve:
            equity = point["total_equity"]
            if equity > peak:
                peak = equity
            else:
                drawdown = (peak - equity) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def _calculate_returns(self, equity_curve: List[Dict[str, Any]]) -> List[float]:
        """
        リターンを計算

        Args:
            equity_curve: エクイティカーブ

        Returns:
            List[float]: リターンリスト
        """
        returns = []
        for i in range(1, len(equity_curve)):
            prev_equity = equity_curve[i-1]["total_equity"]
            curr_equity = equity_curve[i]["total_equity"]
            if prev_equity > 0:
                ret = (curr_equity - prev_equity) / prev_equity
                returns.append(ret)
        return returns

    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """
        シャープレシオを計算

        Args:
            returns: リターンリスト

        Returns:
            float: シャープレシオ
        """
        if len(returns) < 2:
            return 0.0

        avg_return = np.mean(returns)
        std_return = np.std(returns)
        risk_free_rate = 0.02 / 252  # 年2%を日次に変換

        if std_return > 0:
            return (avg_return - risk_free_rate) / std_return * np.sqrt(252)
        else:
            return 0.0

    def _calculate_monthly_returns(self, trades: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        月次リターンを計算

        Args:
            trades: 取引リスト

        Returns:
            Dict[str, float]: 月次リターン
        """
        monthly_pnl = {}
        
        for trade in trades:
            month_key = trade["exit_time"].strftime("%Y-%m")
            if month_key not in monthly_pnl:
                monthly_pnl[month_key] = 0.0
            monthly_pnl[month_key] += trade["net_pnl"]

        return monthly_pnl

    def _calculate_max_consecutive_losses(self, trades: List[Dict[str, Any]]) -> int:
        """
        最大連続損失を計算

        Args:
            trades: 取引リスト

        Returns:
            int: 最大連続損失数
        """
        max_consecutive = 0
        current_consecutive = 0

        for trade in trades:
            if trade["net_pnl"] < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    async def optimize_parameters(
        self,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "H1",
        param_ranges: Optional[Dict[str, List[Any]]] = None,
    ) -> Dict[str, Any]:
        """
        パラメータ最適化を実行

        Args:
            start_date: 開始日
            end_date: 終了日
            timeframe: タイムフレーム
            param_ranges: パラメータ範囲

        Returns:
            Dict[str, Any]: 最適化結果
        """
        # デフォルトパラメータ範囲
        default_ranges = {
            "rsi_oversold": [20, 25, 30, 35],
            "rsi_overbought": [65, 70, 75, 80],
            "volume_multiplier": [1.0, 1.5, 2.0],
            "risk_reward_ratio": [1.5, 2.0, 2.5, 3.0],
            "max_position_size": [0.05, 0.1, 0.15],
        }

        ranges = param_ranges or default_ranges
        best_result = None
        best_sharpe = -999
        optimization_results = []

        # グリッドサーチ
        for rsi_oversold in ranges["rsi_oversold"]:
            for rsi_overbought in ranges["rsi_overbought"]:
                for volume_multiplier in ranges["volume_multiplier"]:
                    for risk_reward_ratio in ranges["risk_reward_ratio"]:
                        for max_position_size in ranges["max_position_size"]:
                            params = {
                                "rsi_oversold": rsi_oversold,
                                "rsi_overbought": rsi_overbought,
                                "volume_multiplier": volume_multiplier,
                                "risk_reward_ratio": risk_reward_ratio,
                                "max_position_size": max_position_size,
                            }

                            # バックテスト実行
                            result = await self.run_backtest(
                                start_date, end_date, timeframe, params
                            )

                            if "error" not in result:
                                analysis = result.get("analysis", {})
                                sharpe_ratio = analysis.get("sharpe_ratio", 0)

                                optimization_results.append({
                                    "params": params,
                                    "sharpe_ratio": sharpe_ratio,
                                    "total_return": result.get("total_return", 0),
                                    "max_drawdown": analysis.get("max_drawdown", 0),
                                })

                                if sharpe_ratio > best_sharpe:
                                    best_sharpe = sharpe_ratio
                                    best_result = {
                                        "params": params,
                                        "result": result,
                                    }

        return {
            "best_parameters": best_result["params"] if best_result else {},
            "best_sharpe_ratio": best_sharpe,
            "optimization_results": optimization_results,
            "total_combinations": len(optimization_results),
        }
