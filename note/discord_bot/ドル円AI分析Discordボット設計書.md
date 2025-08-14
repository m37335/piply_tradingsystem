# ドル円 AI 分析 Discord ボット設計書

## 📋 概要

### プロジェクト名

**USD/JPY AI Analysis Discord Bot**

### 目的

Discord サーバー内でハッシュタグコマンド（`#usdjpy`、`#analyze`等）を使用して、リアルタイムでドル円の AI 分析を実行し、結果を Discord チャンネルに配信するシステム

### 主要機能

- ハッシュタグコマンドによる分析実行
- リアルタイム通貨相関分析
- マルチタイムフレームテクニカル分析
- AI 統合戦略分析
- 分析結果の Discord 配信
- 分析履歴管理
- ユーザー権限管理

## 🏗️ システムアーキテクチャ

### 全体構成図

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Discord Bot   │    │  Analysis API   │    │  Database       │
│                 │    │                 │    │                 │
│ • コマンド受信  │◄──►│ • 通貨相関分析  │◄──►│ • 分析履歴      │
│ • レスポンス    │    │ • テクニカル分析│    │ • ユーザー管理  │
│ • 権限管理      │    │ • AI分析生成    │    │ • 統計情報      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │  External APIs  │              │
         │              │                 │              │
         └──────────────►│ • Yahoo Finance│◄─────────────┘
                        │ • OpenAI API   │
                        │ • Discord API  │
                        └─────────────────┘
```

### レイヤー構成

1. **Presentation Layer**: Discord Bot Interface
2. **Application Layer**: Command Handler, Analysis Orchestrator
3. **Domain Layer**: Analysis Services, Business Logic
4. **Infrastructure Layer**: External APIs, Database, Cache

## 🔧 技術仕様

### 使用技術

- **言語**: Python 3.11+
- **Discord Bot**: discord.py
- **Web Framework**: FastAPI (API 用)
- **データベース**: PostgreSQL + SQLAlchemy
- **キャッシュ**: Redis
- **外部 API**: Yahoo Finance, OpenAI GPT-4
- **コンテナ**: Docker + Docker Compose

### 開発環境

- **OS**: Linux (Ubuntu 20.04+)
- **Python**: 3.11+
- **依存管理**: Poetry
- **テスト**: pytest
- **CI/CD**: GitHub Actions

## 📝 機能仕様

### 1. ハッシュタグコマンド機能

#### 対応コマンド

| コマンド    | 説明           | 権限   | 例          |
| ----------- | -------------- | ------ | ----------- |
| `#usdjpy`   | 基本ドル円分析 | 全員   | `#usdjpy`   |
| `#analyze`  | 詳細分析       | 全員   | `#analyze`  |
| `#forecast` | 予測分析       | 全員   | `#forecast` |
| `#stats`    | 統計情報       | 管理者 | `#stats`    |
| `#help`     | ヘルプ表示     | 全員   | `#help`     |

#### コマンドオプション

```bash
#usdjpy [timeframe] [detail]
#analyze [currency] [timeframe] [options]
#forecast [period] [confidence]
```

#### パラメータ仕様

- **timeframe**: `5m`, `1h`, `4h`, `1d` (デフォルト: `1h`)
- **detail**: `basic`, `full`, `expert` (デフォルト: `basic`)
- **currency**: `USDJPY`, `EURUSD`, `GBPUSD` (デフォルト: `USDJPY`)
- **period**: `1h`, `4h`, `1d`, `1w` (デフォルト: `1d`)
- **confidence**: `low`, `medium`, `high` (デフォルト: `medium`)

### 2. 分析機能

#### 通貨相関分析

- **対象通貨ペア**: USD/JPY, EUR/USD, GBP/USD, EUR/JPY, GBP/JPY
- **分析項目**:
  - 通貨強弱分析
  - 相関性分析
  - 統合予測
  - 信頼度評価

#### テクニカル分析

- **時間軸**: 5 分、1 時間、4 時間、日足
- **指標**:
  - RSI (30, 50, 70 期間)
  - MACD
  - ボリンジャーバンド
  - 移動平均線 (20, 50, 200 期間)

#### AI 統合分析

- **分析内容**:
  - 相関分析結果
  - テクニカル指標統合
  - 売買シナリオ生成
  - リスク管理指針
- **出力形式**: 構造化された戦略レポート

### 3. Discord 配信機能

#### メッセージ形式

```json
{
  "embeds": [
    {
      "title": "🎯 USD/JPY AI Analysis",
      "color": 0x00ff00,
      "fields": [
        {
          "name": "📊 Current Rate",
          "value": "148.384 (+0.19%)",
          "inline": true
        },
        {
          "name": "🎯 Strategy",
          "value": "LONG (90% confidence)",
          "inline": true
        }
      ],
      "description": "AI analysis content...",
      "footer": {
        "text": "Generated at 2025-08-12 12:35 JST"
      }
    }
  ]
}
```

#### 色分けルール

- **緑色 (0x00FF00)**: LONG 戦略
- **赤色 (0xFF0000)**: SHORT 戦略
- **黄色 (0xFFFF00)**: NEUTRAL 戦略
- **青色 (0x0000FF)**: エラー・警告

### 4. 権限管理機能

#### ユーザーレベル

| レベル                 | 権限         | 説明                         |
| ---------------------- | ------------ | ---------------------------- |
| **一般ユーザー**       | 基本分析実行 | 基本的な分析コマンド使用可能 |
| **プレミアムユーザー** | 詳細分析     | 詳細分析、履歴確認可能       |
| **管理者**             | 全機能       | 統計情報、設定変更可能       |
| **システム管理者**     | システム管理 | ボット設定、メンテナンス     |

#### レート制限

- **一般ユーザー**: 1 分間に 1 回
- **プレミアムユーザー**: 1 分間に 3 回
- **管理者**: 1 分間に 10 回

## 🔄 処理フロー

### 1. コマンド受信フロー

```
1. Discordメッセージ受信
   ↓
2. ハッシュタグコマンド検出
   ↓
3. コマンド解析・パラメータ抽出
   ↓
4. ユーザー権限チェック
   ↓
5. レート制限チェック
   ↓
6. 分析実行キュー投入
```

### 2. 分析実行フロー

```
1. 分析リクエスト受信
   ↓
2. キャッシュチェック
   ↓
3. 外部API呼び出し
   ├─ Yahoo Finance (価格データ)
   ├─ 通貨相関分析
   └─ テクニカル指標計算
   ↓
4. AI分析生成 (OpenAI API)
   ↓
5. 結果フォーマット
   ↓
6. Discord配信
   ↓
7. 履歴保存
```

### 3. エラーハンドリングフロー

```
1. エラー発生
   ↓
2. エラータイプ判定
   ├─ API制限エラー
   ├─ ネットワークエラー
   ├─ 権限エラー
   └─ システムエラー
   ↓
3. 適切なエラーメッセージ生成
   ↓
4. ユーザーへの通知
   ↓
5. ログ記録
```

## 🗄️ データベース設計

### テーブル構成

#### 1. users

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    discord_id VARCHAR(20) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    user_level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. analysis_requests

```sql
CREATE TABLE analysis_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    command VARCHAR(50) NOT NULL,
    parameters JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    result_data JSONB
);
```

#### 3. analysis_results

```sql
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES analysis_requests(id),
    currency_pair VARCHAR(10) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    result_data JSONB NOT NULL,
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. user_limits

```sql
CREATE TABLE user_limits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    command_type VARCHAR(50) NOT NULL,
    last_executed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_count INTEGER DEFAULT 1
);
```

## 🔧 実装仕様

### 1. Discord Bot 実装

#### メインファイル構成

```
discord_bot/
├── main.py                 # エントリーポイント
├── bot/
│   ├── __init__.py
│   ├── client.py          # Discord Bot Client
│   ├── commands.py        # コマンドハンドラー
│   ├── permissions.py     # 権限管理
│   └── responses.py       # レスポンス生成
├── services/
│   ├── analysis_service.py # 分析サービス
│   ├── cache_service.py   # キャッシュサービス
│   └── rate_limit.py      # レート制限
└── utils/
    ├── logger.py          # ログ機能
    └── formatter.py       # フォーマット機能
```

#### コマンドハンドラー実装例

```python
class AnalysisCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.analysis_service = AnalysisService()
        self.rate_limiter = RateLimiter()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # ハッシュタグコマンド検出
        if message.content.startswith('#'):
            await self.handle_hashtag_command(message)

    async def handle_hashtag_command(self, message):
        command = self.parse_command(message.content)

        # 権限チェック
        if not await self.check_permissions(message.author, command):
            await message.channel.send("❌ 権限が不足しています")
            return

        # レート制限チェック
        if not await self.rate_limiter.check_limit(message.author.id, command):
            await message.channel.send("⏰ レート制限に達しました")
            return

        # 分析実行
        await self.execute_analysis(message, command)
```

### 2. API 実装

#### FastAPI 実装例

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="USD/JPY Analysis API")

class AnalysisRequest(BaseModel):
    command: str
    parameters: dict
    user_id: str

@app.post("/api/v1/analyze")
async def analyze_currency(request: AnalysisRequest):
    try:
        # 分析実行
        result = await analysis_service.execute(request)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. キャッシュ戦略

#### Redis キャッシュ設計

```python
class CacheService:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0)

    async def get_cached_analysis(self, key: str):
        return await self.redis.get(f"analysis:{key}")

    async def cache_analysis(self, key: str, data: dict, ttl: int = 300):
        await self.redis.setex(f"analysis:{key}", ttl, json.dumps(data))
```

## 🚀 デプロイメント

### Docker 構成

```yaml
# docker-compose.yml
version: "3.8"
services:
  discord-bot:
    build: ./discord_bot
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - postgres
      - redis

  analysis-api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=usdjpy_analysis
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 環境変数

```bash
# .env
DISCORD_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_guild_id
DATABASE_URL=postgresql://user:pass@postgres:5432/usdjpy_analysis
REDIS_URL=redis://redis:6379
OPENAI_API_KEY=your_openai_api_key
YAHOO_FINANCE_API_KEY=your_yahoo_api_key
```

## 📊 監視・ログ

### ログ設計

```python
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('discord_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### メトリクス

- **コマンド実行数**: 時間別、ユーザー別
- **分析成功率**: エラー率、レスポンス時間
- **API 使用量**: 外部 API 呼び出し回数
- **ユーザーアクティビティ**: アクティブユーザー数

## 🔒 セキュリティ

### 認証・認可

- **Discord OAuth2**: ユーザー認証
- **JWT Token**: API 認証
- **Role-based Access Control**: 権限管理

### データ保護

- **暗号化**: 機密データの暗号化
- **アクセス制御**: データベースアクセス制限
- **監査ログ**: 操作履歴の記録

## 📈 パフォーマンス

### 最適化戦略

- **キャッシュ**: Redis による結果キャッシュ
- **非同期処理**: 分析処理の非同期化
- **レート制限**: API 制限の適切な管理
- **負荷分散**: 複数インスタンスでの負荷分散

### 目標性能

- **レスポンス時間**: 5 秒以内
- **同時接続数**: 1000 ユーザー
- **可用性**: 99.9%

## 🧪 テスト戦略

### テスト構成

```python
# tests/
├── unit/
│   ├── test_commands.py
│   ├── test_analysis.py
│   └── test_permissions.py
├── integration/
│   ├── test_discord_api.py
│   └── test_external_apis.py
└── e2e/
    └── test_full_flow.py
```

### テスト実行

```bash
# ユニットテスト
pytest tests/unit/

# 統合テスト
pytest tests/integration/

# E2Eテスト
pytest tests/e2e/
```

## 📅 開発スケジュール

### Phase 1: 基盤開発 (2 週間)

- [ ] Discord Bot 基盤実装
- [ ] データベース設計・実装
- [ ] 基本コマンド実装

### Phase 2: 分析機能実装 (3 週間)

- [ ] 通貨相関分析統合
- [ ] テクニカル分析実装
- [ ] AI 分析生成実装

### Phase 3: UI/UX 改善 (2 週間)

- [ ] Discord 埋め込みメッセージ改善
- [ ] エラーハンドリング強化
- [ ] ユーザビリティ向上

### Phase 4: 運用準備 (1 週間)

- [ ] 監視・ログ実装
- [ ] セキュリティ強化
- [ ] パフォーマンス最適化

## 🎯 成功指標

### 技術指標

- **レスポンス時間**: 5 秒以内
- **エラー率**: 1%以下
- **可用性**: 99.9%

### ビジネス指標

- **アクティブユーザー数**: 月間 1000 人
- **コマンド実行数**: 日間 1000 回
- **ユーザー満足度**: 4.5/5.0

## 🔄 今後の拡張

### 短期拡張 (3 ヶ月)

- 他の通貨ペア対応
- モバイルアプリ連携
- 通知機能強化

### 中期拡張 (6 ヶ月)

- 機械学習モデル統合
- リアルタイムチャート表示
- コミュニティ機能

### 長期拡張 (1 年)

- マルチプラットフォーム対応
- 高度な AI 分析機能
- トレーディング自動化

---

**作成日**: 2025 年 8 月 12 日  
**作成者**: AI Assistant  
**バージョン**: 1.0
