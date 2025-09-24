#!/usr/bin/env python3
"""
三層ゲート式フィルタリングシステム監視ツール

新システムの動作状況を監視し、詳細な統計情報を表示します。
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class ThreeGateMonitor:
    """三層ゲート式フィルタリングシステム監視ツール"""
    
    def __init__(self):
        self.connection_manager = None
        self.is_running = False
        
    async def initialize(self):
        """監視ツールの初期化"""
        try:
            logger.info("🔧 三層ゲート監視ツール初期化開始")
            
            # データベース接続の初期化
            db_config = DatabaseConfig()
            self.connection_manager = DatabaseConnectionManager(
                connection_string=db_config.connection_string,
                min_connections=2,
                max_connections=5
            )
            await self.connection_manager.initialize()
            
            logger.info("✅ 三層ゲート監視ツール初期化完了")
            
        except Exception as e:
            logger.error(f"❌ 監視ツール初期化エラー: {e}")
            raise
    
    async def start_monitoring(self):
        """監視の開始"""
        if self.is_running:
            logger.warning("⚠️ 監視は既に実行中です")
            return
        
        try:
            logger.info("👁️ 三層ゲート監視開始")
            self.is_running = True
            
            while self.is_running:
                await self._display_status()
                await asyncio.sleep(30)  # 30秒間隔で更新
                
        except KeyboardInterrupt:
            logger.info("🛑 監視を停止します")
        except Exception as e:
            logger.error(f"❌ 監視エラー: {e}")
        finally:
            self.is_running = False
    
    async def _display_status(self):
        """ステータスの表示"""
        try:
            # 画面をクリア
            print("\033[2J\033[H", end="")
            
            # ヘッダー
            print("=" * 80)
            print("🚪 三層ゲート式フィルタリングシステム監視")
            print("=" * 80)
            print(f"⏰ 更新時刻: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print()
            
            # イベント処理状況
            await self._display_event_status()
            print()
            
            # シグナル生成状況
            await self._display_signal_status()
            print()
            
            # ゲート通過率
            await self._display_gate_statistics()
            print()
            
            # 最近のシグナル
            await self._display_recent_signals()
            print()
            
            # フッター
            print("=" * 80)
            print("💡 Ctrl+C で終了")
            print("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ ステータス表示エラー: {e}")
    
    async def _display_event_status(self):
        """イベント処理状況の表示"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # 未処理イベント数
                unprocessed = await conn.fetchval("""
                    SELECT COUNT(*) FROM events 
                    WHERE event_type = 'data_collection_completed' AND processed = FALSE
                """)
                
                # 処理済みイベント数（過去1時間）
                processed_1h = await conn.fetchval("""
                    SELECT COUNT(*) FROM events 
                    WHERE event_type = 'data_collection_completed' 
                    AND processed = TRUE 
                    AND processed_at >= NOW() - INTERVAL '1 hour'
                """)
                
                # 最新のイベント処理時刻
                last_processed = await conn.fetchval("""
                    SELECT MAX(processed_at) FROM events 
                    WHERE event_type = 'data_collection_completed' AND processed = TRUE
                """)
                
                print("📊 イベント処理状況:")
                print(f"   🔄 未処理イベント: {unprocessed}")
                print(f"   ✅ 過去1時間処理済み: {processed_1h}")
                print(f"   ⏰ 最新処理時刻: {last_processed or 'なし'}")
                
        except Exception as e:
            print(f"❌ イベント状況取得エラー: {e}")
    
    async def _display_signal_status(self):
        """シグナル生成状況の表示"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # 過去1時間のシグナル数
                signals_1h = await conn.fetchval("""
                    SELECT COUNT(*) FROM three_gate_signals 
                    WHERE created_at >= NOW() - INTERVAL '1 hour'
                """)
                
                # 過去24時間のシグナル数
                signals_24h = await conn.fetchval("""
                    SELECT COUNT(*) FROM three_gate_signals 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                
                # 最新のシグナル
                latest_signal = await conn.fetchrow("""
                    SELECT symbol, signal_type, overall_confidence, created_at
                    FROM three_gate_signals 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                
                print("🎯 シグナル生成状況:")
                print(f"   📈 過去1時間: {signals_1h}")
                print(f"   📊 過去24時間: {signals_24h}")
                
                if latest_signal:
                    print(f"   🆕 最新シグナル: {latest_signal['symbol']} {latest_signal['signal_type']} "
                          f"(信頼度: {latest_signal['overall_confidence']:.2f}) "
                          f"at {latest_signal['created_at']}")
                else:
                    print("   🆕 最新シグナル: なし")
                
        except Exception as e:
            print(f"❌ シグナル状況取得エラー: {e}")
    
    async def _display_gate_statistics(self):
        """ゲート通過率の表示"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # 各ゲートのパターン別統計
                gate_stats = await conn.fetch("""
                    SELECT 
                        gate1_pattern,
                        gate2_pattern,
                        gate3_pattern,
                        COUNT(*) as count,
                        AVG(overall_confidence) as avg_confidence
                    FROM three_gate_signals 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY gate1_pattern, gate2_pattern, gate3_pattern
                    ORDER BY count DESC
                    LIMIT 5
                """)
                
                print("🚪 ゲート通過パターン統計 (過去24時間):")
                for stat in gate_stats:
                    print(f"   📊 {stat['gate1_pattern']} → {stat['gate2_pattern']} → {stat['gate3_pattern']}")
                    print(f"      💯 回数: {stat['count']}, 平均信頼度: {stat['avg_confidence']:.2f}")
                
        except Exception as e:
            print(f"❌ ゲート統計取得エラー: {e}")
    
    async def _display_recent_signals(self):
        """最近のシグナルの表示"""
        try:
            async with self.connection_manager.get_connection() as conn:
                recent_signals = await conn.fetch("""
                    SELECT 
                        symbol, signal_type, overall_confidence, 
                        entry_price, stop_loss, created_at
                    FROM three_gate_signals 
                    ORDER BY created_at DESC 
                    LIMIT 3
                """)
                
                print("🆕 最近のシグナル:")
                for signal in recent_signals:
                    print(f"   🎯 {signal['symbol']} {signal['signal_type']} "
                          f"(信頼度: {signal['overall_confidence']:.2f})")
                    print(f"      💰 エントリー: {signal['entry_price']}, "
                          f"ストップ: {signal['stop_loss']}")
                    print(f"      ⏰ {signal['created_at']}")
                    print()
                
        except Exception as e:
            print(f"❌ 最近のシグナル取得エラー: {e}")
    
    async def close(self):
        """監視ツールの終了"""
        try:
            logger.info("🔧 三層ゲート監視ツール終了")
            
            if self.connection_manager:
                await self.connection_manager.close()
            
            logger.info("✅ 三層ゲート監視ツール終了完了")
            
        except Exception as e:
            logger.error(f"❌ 監視ツール終了エラー: {e}")


# シグナルハンドラー
def signal_handler(signum, frame):
    """シグナルハンドラー"""
    logger.info(f"🛑 シグナル {signum} を受信しました。監視を停止します...")
    if 'monitor' in globals():
        monitor.is_running = False


async def main():
    """メイン関数"""
    global monitor
    
    # シグナルハンドラーの設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    monitor = ThreeGateMonitor()
    
    try:
        # 監視ツールの初期化と開始
        await monitor.initialize()
        await monitor.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("🛑 ユーザーによる中断")
    except Exception as e:
        logger.error(f"❌ 監視ツールエラー: {e}")
        sys.exit(1)
    finally:
        await monitor.close()


if __name__ == "__main__":
    # 監視ツールの実行
    asyncio.run(main())
