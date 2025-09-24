#!/usr/bin/env python3
"""
シグナル抽出スクリプト
- 指定時間内のシグナルのみを抽出
- シグナル詳細を整理して表示
- 統計情報も表示
"""

import re
import sys
from datetime import datetime, timedelta
import pytz

def get_jst_time():
    """JST時刻を取得"""
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst)

def parse_log_timestamp(log_line):
    """ログ行からタイムスタンプを解析"""
    try:
        # ログフォーマット: 2025-09-19 22:32:31,918 - INFO - ...
        timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', log_line)
        if timestamp_match:
            timestamp_str = timestamp_match.group(1)
            # UTC時刻として解析（ログはUTCで記録されている）
            utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            utc_time = pytz.utc.localize(utc_time)
            # JSTに変換
            jst_time = utc_time.astimezone(pytz.timezone('Asia/Tokyo'))
            return jst_time
    except Exception as e:
        pass
    return None

def extract_signal_info(log_lines, start_idx):
    """シグナル情報を抽出"""
    signal_info = {}
    
    for i in range(start_idx, min(start_idx + 50, len(log_lines))):
        line = log_lines[i]
        
        # シンボル
        if 'シンボル:' in line:
            symbol_match = re.search(r'シンボル: (\S+)', line)
            if symbol_match:
                signal_info['symbol'] = symbol_match.group(1)
        
        # タイプ
        if 'タイプ:' in line:
            type_match = re.search(r'タイプ: (\w+)', line)
            if type_match:
                signal_info['type'] = type_match.group(1)
        
        # 信頼度
        if '信頼度:' in line:
            confidence_match = re.search(r'信頼度: ([\d.]+)', line)
            if confidence_match:
                signal_info['confidence'] = float(confidence_match.group(1))
        
        # エントリー価格
        if 'エントリー価格:' in line:
            entry_match = re.search(r'エントリー価格: ([\d.]+)', line)
            if entry_match:
                signal_info['entry_price'] = float(entry_match.group(1))
        
        # ストップロス
        if 'ストップロス:' in line:
            stop_match = re.search(r'ストップロス: ([\d.]+)', line)
            if stop_match:
                signal_info['stop_loss'] = float(stop_match.group(1))
        
        # リスク
        if 'リスク:' in line:
            risk_match = re.search(r'リスク: ([\d.]+)', line)
            if risk_match:
                signal_info['risk'] = float(risk_match.group(1))
        
        # リワード
        if 'リワード:' in line:
            reward_match = re.search(r'リワード: ([\d.]+)', line)
            if reward_match:
                signal_info['reward'] = float(reward_match.group(1))
        
        # リスクリワード比
        if 'リスクリワード比:' in line:
            rr_match = re.search(r'リスクリワード比: ([\d:.]+)', line)
            if rr_match:
                signal_info['risk_reward_ratio'] = rr_match.group(1)
        
        # 生成時刻
        if '生成時刻:' in line:
            time_match = re.search(r'生成時刻: ([\d\s:-]+)', line)
            if time_match:
                signal_info['generation_time'] = time_match.group(1).strip()
        
        # GATE情報
        if 'GATE 1:' in line:
            gate1_match = re.search(r'GATE 1: ([^(]+)', line)
            if gate1_match:
                signal_info['gate1'] = gate1_match.group(1).strip()
        
        if 'GATE 2:' in line:
            gate2_match = re.search(r'GATE 2: ([^(]+)', line)
            if gate2_match:
                signal_info['gate2'] = gate2_match.group(1).strip()
        
        if 'GATE 3:' in line:
            gate3_match = re.search(r'GATE 3: ([^(]+)', line)
            if gate3_match:
                signal_info['gate3'] = gate3_match.group(1).strip()
    
    return signal_info

def extract_recent_signals(hours=3):
    """最近のシグナルを抽出"""
    log_file = "/tmp/analysis_system_fixed.log"
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
    except Exception as e:
        print(f"❌ ログファイル読み込みエラー: {e}")
        return []
    
    # 指定時間前の時刻を計算
    cutoff_time = get_jst_time() - timedelta(hours=hours)
    
    signals = []
    i = 0
    
    while i < len(log_lines):
        line = log_lines[i]
        
        # シグナル生成の開始を検出
        if 'シグナル生成！' in line:
            # この行のタイムスタンプを取得
            timestamp = parse_log_timestamp(line)
            
            if timestamp and timestamp >= cutoff_time:
                # シグナル情報を抽出
                signal_info = extract_signal_info(log_lines, i)
                signal_info['timestamp'] = timestamp
                signals.append(signal_info)
        
        i += 1
    
    return signals

def display_signals(signals):
    """シグナルを表示"""
    if not signals:
        print("📊 指定時間内にシグナルは生成されていません")
        return
    
    print(f"🎯 最近のシグナル一覧 ({len(signals)}件)")
    print("=" * 80)
    
    for i, signal in enumerate(signals, 1):
        print(f"\n📈 シグナル #{i}")
        print(f"   ⏰ 時刻: {signal.get('timestamp', 'N/A').strftime('%Y-%m-%d %H:%M:%S JST')}")
        print(f"   📊 シンボル: {signal.get('symbol', 'N/A')}")
        print(f"   🎯 タイプ: {signal.get('type', 'N/A')}")
        print(f"   📈 信頼度: {signal.get('confidence', 'N/A')}")
        print(f"   💰 エントリー: {signal.get('entry_price', 'N/A')}")
        print(f"   🛑 ストップロス: {signal.get('stop_loss', 'N/A')}")
        print(f"   ⚠️ リスク: {signal.get('risk', 'N/A')}")
        print(f"   🎁 リワード: {signal.get('reward', 'N/A')}")
        print(f"   📊 リスクリワード比: {signal.get('risk_reward_ratio', 'N/A')}")
        print(f"   🚪 GATE 1: {signal.get('gate1', 'N/A')}")
        print(f"   🚪 GATE 2: {signal.get('gate2', 'N/A')}")
        print(f"   🚪 GATE 3: {signal.get('gate3', 'N/A')}")
    
    # 統計情報
    print(f"\n📊 統計情報")
    print("=" * 40)
    
    buy_signals = [s for s in signals if s.get('type') == 'BUY']
    sell_signals = [s for s in signals if s.get('type') == 'SELL']
    
    print(f"   📈 BUYシグナル: {len(buy_signals)}件")
    print(f"   📉 SELLシグナル: {len(sell_signals)}件")
    
    if signals:
        avg_confidence = sum(s.get('confidence', 0) for s in signals) / len(signals)
        print(f"   📊 平均信頼度: {avg_confidence:.2f}")
        
        avg_risk_reward = []
        for s in signals:
            rr = s.get('risk_reward_ratio', '1:0')
            if ':' in rr:
                try:
                    ratio = float(rr.split(':')[1]) / float(rr.split(':')[0])
                    avg_risk_reward.append(ratio)
                except:
                    pass
        
        if avg_risk_reward:
            print(f"   📊 平均リスクリワード比: 1:{sum(avg_risk_reward)/len(avg_risk_reward):.2f}")

if __name__ == "__main__":
    hours = 3  # デフォルト3時間
    
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except ValueError:
            print("❌ 時間は数値で指定してください")
            sys.exit(1)
    
    print(f"🔍 過去{hours}時間のシグナルを抽出中...")
    signals = extract_recent_signals(hours)
    display_signals(signals)
