#!/usr/bin/env python3

import asyncio
from datetime import datetime
from src.infrastructure.database.repositories.price_data_repository_impl import PriceDataRepositoryImpl
from src.infrastructure.database.database import get_database_session

async def check_aggregated_data():
    session = await get_database_session()
    repo = PriceDataRepositoryImpl(session)
    
    try:
        # 1時間足データを確認
        h1_data = await repo.find_by_timestamp_and_source(
            datetime(2025, 8, 13, 16, 0), 'USD/JPY', '1h_aggregated_data'
        )
        print(f"1h aggregated data: {h1_data}")
        
        # 4時間足データを確認
        h4_data = await repo.find_by_timestamp_and_source(
            datetime(2025, 8, 13, 16, 0), 'USD/JPY', '4h_aggregated_data'
        )
        print(f"4h aggregated data: {h4_data}")
        
        # 日足データを確認
        d1_data = await repo.find_by_timestamp_and_source(
            datetime(2025, 8, 13, 0, 0), 'USD/JPY', '1d_aggregated_data'
        )
        print(f"1d aggregated data: {d1_data}")
        
        # 進行中データを確認
        ongoing_h1 = await repo.find_by_timestamp_and_source(
            datetime(2025, 8, 13, 16, 0), 'USD/JPY', '1h Aggregated (Ongoing)'
        )
        print(f"1h ongoing data: {ongoing_h1}")
        
        ongoing_h4 = await repo.find_by_timestamp_and_source(
            datetime(2025, 8, 13, 16, 0), 'USD/JPY', '4h Aggregated (Ongoing)'
        )
        print(f"4h ongoing data: {ongoing_h4}")
        
        ongoing_d1 = await repo.find_by_timestamp_and_source(
            datetime(2025, 8, 13, 0, 0), 'USD/JPY', '1d Aggregated (Ongoing)'
        )
        print(f"1d ongoing data: {ongoing_d1}")
        
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(check_aggregated_data())
