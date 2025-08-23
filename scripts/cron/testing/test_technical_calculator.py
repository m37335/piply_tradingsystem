#!/usr/bin/env python3
"""
制限付きテクニカル指標計算テストスクリプト

このスクリプトは、計算対象件数を制限してテクニカル指標計算をテストします。
本番実行前に動作確認を行うために使用します。

使用方法:
    python scripts/cron/test_technical_calculator.py --limit 100
    python scripts/cron/test_technical_calculator.py --limit 500
    python scripts/cron/test_technical_calculator.py --full      # 制限なし（本番実行）
    python scripts/cron/test_technical_calculator.py --diff-only # 差分検知のみ実行
"""

import argparse
import asyncio
import sys
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append("/app")


async def test_technical_calculation(limit: int = None, diff_only: bool = False):
    """
    制限付きテクニカル指標計算テスト

    Args:
        limit: 各時間足の取得件数制限（Noneの場合は全件取得）
        diff_only: 差分検知のみ実行するかどうか
    """
    try:
        from scripts.cron.enhanced_unified_technical_calculator import (
            EnhancedUnifiedTechnicalCalculator,
        )

        print("🧪 制限付きテクニカル指標計算テスト開始")
        print("=" * 60)

        if diff_only:
            print("🔍 差分検知モード: 未計算データのみを対象")
        elif limit:
            print(f"🔒 テストモード: 各時間足{limit}件まで")
        else:
            print("🚀 本番モード: 全件計算")

        print(f"⏰ 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 計算器を初期化
        calculator = EnhancedUnifiedTechnicalCalculator("USD/JPY")
        await calculator.initialize()

        try:
            if diff_only:
                # 差分検知付き計算を実行
                print("🔍 差分検知付きテクニカル指標計算を実行中...")
                result = await calculator.calculate_with_diff_detection(limit=limit)
                
                # 差分検知結果の表示
                print("\n" + "=" * 60)
                print("📊 差分検知結果サマリー")
                print("=" * 60)
                
                status = result.get("status", "unknown")
                print(f"📈 実行ステータス: {status}")
                
                if status == "success":
                    execution_time = result.get("execution_time", 0)
                    total_processed = result.get("total_processed", 0)
                    differences = result.get("differences", {})
                    
                    print(f"⏱️ 実行時間: {execution_time:.2f}秒")
                    print(f"📊 処理件数: {total_processed:,}件")
                    
                    if differences:
                        print("🔍 差分検知結果:")
                        for timeframe, count in differences.items():
                            if count > 0:
                                print(f"   📈 {timeframe}: {count:,}件の未計算データ")
                    
                    # 計算状況の表示
                    calculation_status = await calculator.get_calculation_status()
                    if calculation_status:
                        overall_progress = calculation_status.get("overall_progress", 0)
                        print(f"📊 全体進捗: {overall_progress:.1f}%")
                    
                    print(f"⏰ 終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print("=" * 60)
                    
                    if total_processed > 0:
                        print(
                            "✅ 差分検知テスト成功: 未計算データの処理が正常に完了しました"
                        )
                        return True
                    else:
                        print(
                            "ℹ️ 差分検知完了: 処理対象の未計算データがありませんでした"
                        )
                        return True
                else:
                    error_msg = result.get("error", "不明なエラー")
                    print(f"❌ 差分検知テスト失敗: {error_msg}")
                    return False
            else:
                # 従来の全件計算を実行
                results = await calculator.calculate_all_indicators(limit=limit)

                # 結果の表示
                print("\n" + "=" * 60)
                print("📊 テスト結果サマリー")
                print("=" * 60)

                total_calculated = sum(results.values())
                print(f"📈 総計算件数: {total_calculated:,}件")

                for timeframe, count in results.items():
                    print(f"   📊 {timeframe}: {count:,}件")

                # 成功率の計算
                expected_indicators = 6  # RSI, MACD, BB, MA, STOCH, ATR
                expected_timeframes = 4  # M5, H1, H4, D1
                expected_total = expected_indicators * expected_timeframes

                if limit:
                    # 制限付きの場合、期待値は制限に依存
                    print(f"🔒 制限付き実行のため、期待値は制限{limit}件に依存")
                else:
                    print(
                        f"📊 期待値: {expected_total}指標 × {expected_timeframes}時間足 = {expected_total * expected_timeframes}件"
                    )

                print(f"⏰ 終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 60)

                if total_calculated > 0:
                    print("✅ テスト成功: テクニカル指標計算が正常に完了しました")
                    return True
                else:
                    print("❌ テスト失敗: 計算件数が0件でした")
                    return False

        finally:
            # クリーンアップ
            await calculator.cleanup()

    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback

        print(f"詳細エラー: {traceback.format_exc()}")
        return False


async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="制限付きテクニカル指標計算テスト")
    parser.add_argument(
        "--limit", type=int, help="各時間足の取得件数制限（例: 100, 500）"
    )
    parser.add_argument(
        "--full", action="store_true", help="制限なしで全件計算（本番実行）"
    )
    parser.add_argument(
        "--diff-only", action="store_true", help="差分検知のみ実行（未計算データのみ）"
    )

    args = parser.parse_args()

    if args.diff_only:
        print("🔍 差分検知モード: 未計算データのみを対象に計算を実行します")
        success = await test_technical_calculation(limit=None, diff_only=True)
    elif args.full:
        print("🚀 本番モード: 制限なしで全件計算を実行します")
        success = await test_technical_calculation(limit=None)
    elif args.limit:
        print(f"🧪 テストモード: 各時間足{args.limit}件まで計算を実行します")
        success = await test_technical_calculation(limit=args.limit)
    else:
        print("🧪 デフォルトテストモード: 各時間足100件まで計算を実行します")
        success = await test_technical_calculation(limit=100)

    if success:
        print("\n🎉 テストが正常に完了しました！")
        sys.exit(0)
    else:
        print("\n💥 テストが失敗しました。")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
