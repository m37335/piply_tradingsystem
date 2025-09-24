#!/usr/bin/env python3
"""
ログ管理スクリプト
- ログファイルのクリア
- ログローテーション
- ログサイズ監視
"""

import os
import shutil
from datetime import datetime
import pytz

def get_jst_time():
    """JST時刻を取得"""
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')

def clear_log(log_file="/tmp/analysis_system_fixed.log"):
    """ログファイルをクリア"""
    try:
        with open(log_file, 'w') as f:
            f.write("")
        print(f"✅ ログファイルクリア完了 [{get_jst_time()}]")
        return True
    except Exception as e:
        print(f"❌ ログクリアエラー: {e}")
        return False

def rotate_log(log_file="/tmp/analysis_system_fixed.log", max_size_mb=10):
    """ログローテーション"""
    try:
        if not os.path.exists(log_file):
            return True
            
        size_mb = os.path.getsize(log_file) / (1024 * 1024)
        
        if size_mb > max_size_mb:
            # バックアップ作成
            backup_file = f"{log_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.move(log_file, backup_file)
            
            # 新しいログファイル作成
            with open(log_file, 'w') as f:
                f.write("")
                
            print(f"🔄 ログローテーション完了 [{get_jst_time()}]")
            print(f"   バックアップ: {backup_file}")
            print(f"   元サイズ: {size_mb:.2f}MB")
            return True
        else:
            print(f"📊 ログサイズ: {size_mb:.2f}MB (上限: {max_size_mb}MB)")
            return False
            
    except Exception as e:
        print(f"❌ ログローテーションエラー: {e}")
        return False

def get_log_stats(log_file="/tmp/analysis_system_fixed.log"):
    """ログ統計情報を取得"""
    try:
        if not os.path.exists(log_file):
            print("📊 ログファイルが存在しません")
            return
            
        size_mb = os.path.getsize(log_file) / (1024 * 1024)
        
        # 行数カウント
        with open(log_file, 'r') as f:
            lines = f.readlines()
            line_count = len(lines)
            
        print(f"📊 ログ統計 [{get_jst_time()}]")
        print(f"   ファイル: {log_file}")
        print(f"   サイズ: {size_mb:.2f}MB")
        print(f"   行数: {line_count:,}行")
        
        # 最近のシグナル数をカウント
        signal_count = sum(1 for line in lines if "シグナル生成" in line)
        print(f"   シグナル数: {signal_count}個")
        
    except Exception as e:
        print(f"❌ ログ統計エラー: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "clear":
            clear_log()
        elif command == "rotate":
            rotate_log()
        elif command == "stats":
            get_log_stats()
        else:
            print("使用方法: python log_manager.py [clear|rotate|stats]")
    else:
        print("使用方法: python log_manager.py [clear|rotate|stats]")
