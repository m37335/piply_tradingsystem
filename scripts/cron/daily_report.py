#!/usr/bin/env python3
"""
Daily Report Script for Cron
日次レポート送信スクリプト
"""

import asyncio
import os
import sys

sys.path.append("/app")


async def main():
    try:
        from data_scheduler import DataScheduler

        scheduler = DataScheduler()
        await scheduler._send_daily_report()
        print("Daily report sent successfully")
    except Exception as e:
        print(f"Daily report error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
