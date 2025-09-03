#!/usr/bin/env python3
"""
Simple Initial Data Load Script
簡易初回データ取得スクリプト
"""

import asyncio
import os
import sys
from datetime import datetime

sys.path.append("/app")

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient


async def main():
    """メイン関数"""
    print("=== 簡易初回データ取得開始 ===")

    # 環境変数設定（SQLiteを強制使用）
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/test_app.db"

    try:
        # セッション初期化
        session = await get_async_session()
        print("✅ データベースセッション接続完了")

        # Yahoo Financeクライアント初期化
        yahoo = YahooFinanceClient()
        print("✅ Yahoo Financeクライアント初期化完了")

        # 履歴データ取得
        print("📊 7日分の5分足データを取得中...")
        df = await yahoo.get_historical_data("USD/JPY", "7d", "5m")

        if df is None or df.empty:
            print("❌ データが取得できませんでした")
            return

        print(f"✅ 取得データ: {len(df)}件")

        # リポジトリ初期化
        repo = PriceDataRepositoryImpl(session)

        # データ保存
        saved_count = 0
        for timestamp, row in df.iterrows():
            try:
                # タイムスタンプ処理
                if hasattr(timestamp, "to_pydatetime"):
                    dt = timestamp.to_pydatetime()
                else:
                    dt = datetime.now()

                # 価格データモデル作成
                price_data = PriceDataModel(
                    currency_pair="USD/JPY",
                    timestamp=dt,
                    open_price=float(row["Open"]),
                    high_price=float(row["High"]),
                    low_price=float(row["Low"]),
                    close_price=float(row["Close"]),
                    volume=int(row["Volume"]) if row["Volume"] > 0 else 1000000,
                    data_source="Yahoo Finance",
                )

                # 保存
                await repo.save(price_data)
                saved_count += 1

                # 100件ごとにコミット
                if saved_count % 100 == 0:
                    await session.commit()
                    print(f"💾 保存済み: {saved_count}件")

            except Exception as e:
                print(f"⚠️ 保存エラー (timestamp: {timestamp}): {e}")
                continue

        # 最後にコミット
        await session.commit()

        print(f"✅ 完了: {saved_count}件保存")

        # セッション終了
        await session.close()

    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
