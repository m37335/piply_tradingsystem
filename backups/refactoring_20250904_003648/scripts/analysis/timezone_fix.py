#!/usr/bin/env python3
"""
タイムゾーン修正スクリプト
UTCから日本時間（JST）への変更

対象ファイル:
- realtime_monitor.py
- test_alphavantage.py
- test_openai.py
- ai_discord_integration.py
- その他の時刻表示箇所
"""

import os
import re
from datetime import datetime

import pytz


def fix_timezone_in_file(file_path: str):
    """ファイル内のタイムゾーン設定を修正"""
    if not os.path.exists(file_path):
        print(f"⚠️ ファイルが見つかりません: {file_path}")
        return False

    print(f"🔧 修正中: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # datetime.now() -> datetime.now(pytz.timezone('Asia/Tokyo'))
    content = re.sub(
        r"datetime\.now\(\)", 'datetime.now(pytz.timezone("Asia/Tokyo"))', content
    )

    # datetime.now().strftime -> datetime.now(pytz.timezone('Asia/Tokyo')).strftime
    content = re.sub(
        r"datetime\.now\(\)\.strftime",
        'datetime.now(pytz.timezone("Asia/Tokyo")).strftime',
        content,
    )

    # datetime.now().isoformat -> datetime.now(pytz.timezone('Asia/Tokyo')).isoformat
    content = re.sub(
        r"datetime\.now\(\)\.isoformat",
        'datetime.now(pytz.timezone("Asia/Tokyo")).isoformat',
        content,
    )

    # import文にpytzを追加
    if (
        "import pytz" not in content
        and 'datetime.now(pytz.timezone("Asia/Tokyo"))' in content
    ):
        # datetimeのimport文を見つけて、pytzを追加
        if "from datetime import datetime" in content:
            content = content.replace(
                "from datetime import datetime",
                "from datetime import datetime\nimport pytz",
            )
        elif "import datetime" in content:
            content = content.replace("import datetime", "import datetime\nimport pytz")
        else:
            # 他のimport文の後に追加
            import_lines = []
            other_lines = []
            in_imports = True

            for line in content.split("\n"):
                if in_imports and (
                    line.startswith("import ")
                    or line.startswith("from ")
                    or line.startswith("#")
                    or line.strip() == ""
                ):
                    import_lines.append(line)
                else:
                    in_imports = False
                    other_lines.append(line)

            if import_lines:
                import_lines.append("import pytz")
                content = "\n".join(import_lines + other_lines)

    # 内容が変更されている場合のみファイルを更新
    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 修正完了: {file_path}")
        return True
    else:
        print(f"📝 変更なし: {file_path}")
        return False


def main():
    """メイン実行"""
    print("🕘 日本時間（JST）タイムゾーン修正開始...")
    print(f"🌏 現在のシステム時刻: {datetime.now()}")
    print(f"🇯🇵 日本時間: {datetime.now(pytz.timezone('Asia/Tokyo'))}")
    print()

    # 修正対象ファイル
    target_files = [
        "/app/realtime_monitor.py",
        "/app/test_alphavantage.py",
        "/app/test_openai.py",
        "/app/ai_discord_integration.py",
    ]

    modified_files = []

    for file_path in target_files:
        if fix_timezone_in_file(file_path):
            modified_files.append(file_path)

    print()
    print("🎯 修正結果:")
    print(f"✅ 修正されたファイル: {len(modified_files)}")
    for file_path in modified_files:
        print(f"   - {os.path.basename(file_path)}")

    if modified_files:
        print()
        print("🧪 テスト実行...")
        print(
            f"🇯🇵 JST時刻確認: {datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S JST')}"
        )


if __name__ == "__main__":
    main()
