#!/usr/bin/env python3
"""
リアルタイム監視スクリプト
- 新しいログのみを表示
- シグナル生成時にハイライト
- 自動スクロール
"""

import time
import subprocess
import sys
from datetime import datetime
import pytz

def get_jst_time():
    """JST時刻を取得"""
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).strftime('%H:%M:%S')

def monitor_logs():
    """ログファイルをリアルタイム監視"""
    log_file = "/tmp/analysis_system_fixed.log"
    
    print(f"🔍 リアルタイム監視開始 [{get_jst_time()}]")
    print("=" * 60)
    
    try:
        # tail -f でリアルタイム監視
        process = subprocess.Popen(
            ['tail', '-f', log_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        while True:
            line = process.stdout.readline()
            if line:
                # シグナル生成をハイライト
                if "シグナル生成" in line or "SELL" in line or "BUY" in line:
                    print(f"🎉 {line.strip()}")
                # エラーをハイライト
                elif "ERROR" in line or "エラー" in line:
                    print(f"❌ {line.strip()}")
                # 通常のログ
                else:
                    print(f"📊 {line.strip()}")
            else:
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print(f"\n🛑 監視終了 [{get_jst_time()}]")
        process.terminate()
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    monitor_logs()
