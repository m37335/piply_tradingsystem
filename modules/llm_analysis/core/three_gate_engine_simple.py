# 簡素化されたThreeGateEngineのリスク管理部分

def _calculate_stop_loss_simple(self, data: Dict[str, Any], gate1: GateResult, gate2: GateResult, entry_price: float) -> float:
    """ストップロスの計算（ATRベース、簡素化版）"""
    atr = data.get('ATR_14', 0.01)
    
    # ATRが0の場合はデフォルト値を使用
    if atr <= 0:
        atr = 0.01
    
    # シグナルタイプに基づくストップロス計算
    signal_type = self._determine_signal_type(gate1, gate2, None)
    
    if signal_type == 'BUY':
        # 買いの場合：エントリー価格より下にストップロス
        return entry_price - (atr * 1.5)
    elif signal_type == 'SELL':
        # 売りの場合：エントリー価格より上にストップロス
        return entry_price + (atr * 1.5)
    else:
        # NEUTRALの場合はデフォルトで買い方向
        return entry_price - (atr * 1.5)

def _calculate_take_profit_simple(self, data: Dict[str, Any], gate1: GateResult, gate2: GateResult, entry_price: float) -> List[float]:
    """テイクプロフィットの計算（ATRベース、簡素化版）"""
    atr = data.get('ATR_14', 0.01)
    
    # ATRが0の場合はデフォルト値を使用
    if atr <= 0:
        atr = 0.01
    
    # シグナルタイプに基づくテイクプロフィット計算
    signal_type = self._determine_signal_type(gate1, gate2, None)
    
    if signal_type == 'BUY':
        # 買いの場合：エントリー価格より上にテイクプロフィット
        return [
            entry_price + (atr * 2.0),  # 1st target
            entry_price + (atr * 3.0),  # 2nd target
            entry_price + (atr * 4.0)   # 3rd target
        ]
    elif signal_type == 'SELL':
        # 売りの場合：エントリー価格より下にテイクプロフィット
        return [
            entry_price - (atr * 2.0),  # 1st target
            entry_price - (atr * 3.0),  # 2nd target
            entry_price - (atr * 4.0)   # 3rd target
        ]
    else:
        # NEUTRALの場合はデフォルトで買い方向
        return [
            entry_price + (atr * 2.0),  # 1st target
            entry_price + (atr * 3.0),  # 2nd target
            entry_price + (atr * 4.0)   # 3rd target
        ]
