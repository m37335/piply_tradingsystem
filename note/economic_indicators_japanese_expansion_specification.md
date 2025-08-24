# 経済指標日本語化・詳細情報拡張システム 開発仕様書 (並行開発版)

## 1. プロジェクト概要

### 1.1 プロジェクト名

**経済指標日本語化・詳細情報拡張システム (並行開発版)**

### 1.2 目的

- 既存 investpy 経済カレンダーシステムを維持しながら、制約準拠の新システムを並行構築
- 経済指標の日本語翻訳・説明機能の提供
- 投資家向けの経済指標詳細情報の自動配信
- 分析・解説機能の実装
- 段階的・安全な移行によるリスク最小化

### 1.3 背景

現在の investpy 経済カレンダーシステムでは、英語の経済指標名のみが表示されており、以下の課題がある：

- 日本語話者にとって指標の意味が理解しにくい
- 各指標の市場への影響が不明確
- 投資判断に必要な詳細情報が不足
- 分析・解説機能が不十分
- **既存スクリプトが巨大化** (economic_indicators_discord.py: 51,166 行)

### 1.4 開発戦略

#### 1.4.1 並行開発アプローチ

**基本方針**

- **既存システム**: そのまま維持・稼働継続
- **新システム**: 制約準拠で新規構築 (全ファイル 400 行以内)
- **移行**: 段階的・安全な移行

**メリット**

1. **リスク最小化**: 既存システムへの影響なし
2. **品質保証**: 新システムは制約準拠で高品質
3. **段階的移行**: 安全な移行が可能
4. **並行稼働**: 移行期間中のサービス継続

#### 1.4.2 制約準拠アーキテクチャ

**ファイルサイズ制約**

- 全ファイル: 400 行以内
- エンティティ: 200 行以内
- サービス: 250 行以内
- リポジトリ: 300 行以内
- 統合スクリプト: 300 行以内

**品質制約**

- テストカバレッジ: 95%以上
- Linter エラー: 0 件
- 単一責任原則 (SRP) 準拠
- 依存性注入 (DI) 実装

### 1.5 期待効果

- **ユーザビリティ向上**: 日本語表示による理解促進
- **投資判断支援**: 詳細情報による意思決定支援
- **分析効果**: 経済指標の理解促進
- **コスト削減**: 手動準備による運用コスト最小化
- **保守性向上**: 制約準拠による高品質コード
- **リスク最小化**: 並行開発による安全な移行

## 2. システム要件

### 2.1 機能要件

#### 2.1.1 基本機能

- [ ] 経済指標の日本語翻訳表示
- [ ] 指標の詳細説明表示
- [ ] 市場への影響分析表示
- [ ] 投資判断支援情報表示
- [ ] 関連指標の表示

#### 2.1.2 拡張機能

- [ ] 分析・解説機能の実装
- [ ] 分析レポート管理
- [ ] 質問応答システム
- [ ] 経済指標比較機能
- [ ] パーソナライズされた解説

#### 2.1.3 管理機能

- [ ] マスターデータ管理
- [ ] 翻訳キャッシュ管理
- [ ] 統計・分析機能
- [ ] 品質管理機能
- [ ] システム設定管理

### 2.2 非機能要件

#### 2.2.1 パフォーマンス

- 翻訳処理時間: 1 秒以内
- データベース応答時間: 100ms 以内
- 同時アクセス数: 100 ユーザー以上
- **新システム応答時間**: 既存システム同等以上

#### 2.2.2 可用性

- システム稼働率: 99.5%以上
- 障害復旧時間: 30 分以内
- データバックアップ: 日次
- **並行稼働期間**: 5 週間 (段階的移行)

#### 2.2.3 セキュリティ

- データ暗号化: 転送時・保存時
- アクセス制御: ロールベース
- 監査ログ: 全操作記録

#### 2.2.4 コスト

- 月額運用コスト: ¥5,000 以下
- 初期開発コスト: ¥0（既存システム活用）
- API 利用料: 最小限に抑制

#### 2.2.5 制約準拠

- **ファイルサイズ**: 全ファイル 400 行以内
- **テストカバレッジ**: 95%以上
- **コード品質**: Linter エラー 0 件
- **アーキテクチャ**: DDD 準拠

## 3. システム設計

### 3.1 アーキテクチャ

#### 3.1.1 既存システム (維持)

```
scripts/cron/
├── economic_indicators_discord.py (51,166行) - 既存・稼働継続
├── weekly_economic_indicators_discord.py (24,336行) - 既存・稼働継続
└── economic_calendar_cache_manager.py (14,575行) - 既存・稼働継続
```

#### 3.1.2 新システム (制約準拠)

```
src/
├── domain/                    # ドメイン層 (制約準拠)
│   ├── entities/             # エンティティ (~200行/ファイル)
│   ├── repositories/         # リポジトリ (~300行/ファイル)
│   └── services/             # ドメインサービス (~250行/ファイル)
├── application/              # アプリケーション層
│   ├── use_cases/           # ユースケース (~200行/ファイル)
│   └── services/            # アプリケーションサービス (~250行/ファイル)
├── infrastructure/           # インフラストラクチャ層
│   ├── database/            # データベース (~300行/ファイル)
│   ├── external/            # 外部API (~200行/ファイル)
│   └── config/              # 設定 (~150行/ファイル)
└── utils/                   # ユーティリティ (~150行/ファイル)
```

#### 3.1.3 新統合スクリプト (制約準拠)

```
scripts/cron/
├── enhanced_economic_indicators_discord.py (~300行)
├── enhanced_weekly_economic_indicators_discord.py (~300行)
└── enhanced_economic_calendar_cache_manager.py (~300行)
```

### 3.2 移行戦略

#### 3.2.1 段階的移行アプローチ

**Step 1: 並行稼働開始**

```
既存システム: economic_indicators_discord.py (稼働継続)
新システム: enhanced_economic_indicators_discord.py (稼働開始)
```

**Step 2: 段階的移行**

```
Week 1: 10% のトラフィックを新システムに移行
Week 2: 30% のトラフィックを新システムに移行
Week 3: 50% のトラフィックを新システムに移行
Week 4: 80% のトラフィックを新システムに移行
Week 5: 100% のトラフィックを新システムに移行
```

**Step 3: 完全移行**

```
既存システム: 停止・アーカイブ
新システム: 完全稼働
```

#### 3.2.2 移行監視・制御

**監視項目**

- **機能比較**: 既存 vs 新システムの出力比較
- **パフォーマンス**: 応答時間・処理時間の比較
- **エラー率**: エラー発生率の監視
- **ユーザー満足度**: 配信品質の評価

**ロールバック戦略**

- **即座ロールバック**: 重大な問題発生時
- **段階的ロールバック**: 軽微な問題発生時
- **部分ロールバック**: 特定機能のみロールバック

## 4. 実装計画 (並行開発版)

### 4.1 Phase 1: 新システム基盤構築 (Week 1-3)

#### 4.1.1 Week 1: データベース基盤構築

- [ ] 新規データベーステーブル 3 個の設計・作成
- [ ] エンティティ・モデル・リポジトリ実装 (制約準拠)
- [ ] マイグレーションスクリプト 3 個の作成
- [ ] 単体テストスイートの実装

#### 4.1.2 Week 2: 基本サービス実装

- [ ] 翻訳サービス実装 (制約準拠)
- [ ] 情報取得サービス実装 (制約準拠)
- [ ] キャッシュ機能実装 (制約準拠)
- [ ] 外部 API クライアント実装

#### 4.1.3 Week 3: マスターデータ準備

- [ ] 主要経済指標 50 件の情報収集
- [ ] YAML ファイルでの構造化
- [ ] データベースへの登録
- [ ] データ品質チェック

### 4.2 Phase 2: 新機能実装 (Week 4-6)

#### 4.2.1 Week 4: 翻訳・詳細情報機能

- [ ] 翻訳サービス完成 (制約準拠)
- [ ] 詳細情報機能実装 (制約準拠)
- [ ] 市場影響分析機能実装
- [ ] 投資判断支援機能実装

#### 4.2.2 Week 5: AI 分析機能

- [ ] AI 分析サービス実装 (制約準拠)
- [ ] 比較分析機能実装
- [ ] レポート生成機能実装
- [ ] 分析品質管理機能実装

#### 4.2.3 Week 6: Discord 統合機能

- [ ] 拡張 Discord サービス実装 (制約準拠)
- [ ] 日本語メッセージ作成機能
- [ ] 詳細情報フォーマット機能
- [ ] 既存システム統合機能

### 4.3 Phase 3: 統合・テスト (Week 7-8)

#### 4.3.1 Week 7: 新統合スクリプト作成

- [ ] enhanced_economic_indicators_discord.py 作成 (~300 行)
- [ ] enhanced_weekly_economic_indicators_discord.py 作成 (~300 行)
- [ ] enhanced_economic_calendar_cache_manager.py 作成 (~300 行)
- [ ] 統合テストスイート実装

#### 4.3.2 Week 8: 品質チェック・最適化

- [ ] パフォーマンステスト実施
- [ ] 品質チェックレポート作成
- [ ] 制約準拠確認 (全ファイル 400 行以内)
- [ ] テストカバレッジ 95%以上達成

### 4.4 Phase 4: 段階的移行 (Week 9-10)

#### 4.4.1 Week 9: 並行稼働開始

- [ ] 並行稼働システム構築
- [ ] 段階的移行開始 (10% → 30% → 50%)
- [ ] 動作検証・監視
- [ ] 問題対応・調整

#### 4.4.2 Week 10: 完全移行

- [ ] 段階的移行完了 (80% → 100%)
- [ ] 既存システム停止
- [ ] 移行完了レポート作成
- [ ] 新システム完全稼働

## 5. 技術仕様

### 5.1 使用技術

#### 5.1.1 既存システム (維持)

- **言語**: Python 3.11
- **データベース**: PostgreSQL (既存)
- **経済データ**: investpy システム (既存)
- **配信**: Discord Webhook (既存)

#### 5.1.2 新システム (制約準拠)

- **言語**: Python 3.11
- **アーキテクチャ**: ドメイン駆動設計 (DDD)
- **データベース**: PostgreSQL (既存統合)
- **キャッシュ**: Redis (新規追加)
- **ORM**: SQLAlchemy 2.0
- **依存性注入**: 手動実装

#### 5.1.3 外部 API

- **翻訳**: Google Translate API（無料枠活用）
- **AI**: OpenAI GPT-4（最小限使用）
- **経済データ**: 既存 investpy システム

#### 5.1.4 開発ツール

- **テスト**: pytest, pytest-asyncio, pytest-cov
- **Linting**: flake8, black, isort
- **型チェック**: mypy
- **ドキュメント**: Sphinx
- **制約チェック**: カスタムスクリプト (400 行制限)

### 5.2 パフォーマンス要件

#### 5.2.1 レスポンス時間

- 翻訳処理: 1 秒以内
- 情報取得: 500ms 以内
- キャッシュヒット: 100ms 以内
- データベースクエリ: 200ms 以内

#### 5.2.2 スループット

- 同時翻訳処理: 10 リクエスト/秒
- 情報取得: 50 リクエスト/秒
- キャッシュ処理: 100 リクエスト/秒

#### 5.2.3 リソース使用量

- CPU 使用率: 平均 30%以下
- メモリ使用量: 2GB 以下
- ディスク使用量: 1GB 以下

### 5.3 セキュリティ要件

#### 5.3.1 データ保護

- 個人情報の暗号化
- 転送時の TLS 暗号化
- アクセスログの記録
- 定期的なセキュリティ監査

#### 5.3.2 認証・認可

- API 認証（将来的）
- ロールベースアクセス制御
- セッション管理
- パスワードポリシー

## 6. データ仕様

### 6.1 経済指標マスターデータ

#### 6.1.1 基本情報構造

```yaml
indicators:
  "Consumer Price Index (CPI)":
    japanese_name: "消費者物価指数"
    category: "インフレ"
    subcategory: "消費者物価"
    frequency: "月次"
    importance: "高"
    country: "united states"

    description: |
      消費者が購入する商品・サービスの価格変動を測定する指標。
      インフレーションの重要な指標として、中央銀行の金融政策に大きな影響を与える。

    calculation_method: |
      消費者が購入する代表的な商品・サービスの価格を調査し、
      基準年を100として指数化したもの。

    unit: "指数"
    base_year: 1982

    currency_impact: |
      CPI上昇 → インフレ懸念 → 利上げ期待 → 通貨高
      CPI下落 → デフレ懸念 → 利下げ期待 → 通貨安

    stock_impact: |
      CPI上昇 → 利上げ懸念 → 企業コスト増 → 株安
      CPI下落 → 景気後退懸念 → 企業収益悪化 → 株安

    bond_impact: |
      CPI上昇 → 利上げ期待 → 債券価格下落
      CPI下落 → 利下げ期待 → 債券価格上昇

    good_value_tips: "適度なインフレ（2-3%）は経済成長に好影響"
    bad_value_tips: "高インフレ（5%以上）は経済に悪影響"
    surprise_impact: "予想との乖離が大きいほど市場への影響も大きい"

    threshold_values:
      low: 1.0
      moderate: 2.5
      high: 5.0
      critical: 10.0

    related_indicators:
      - "Producer Price Index (PPI)"
      - "GDP Deflator"
      - "Core CPI"
      - "Personal Consumption Expenditures (PCE)"

    examples:
      - title: "2023年米国CPI"
        value: "3.1%"
        impact: "利上げ期待でドル高"
        date: "2023-12"

      - title: "2022年日本CPI"
        value: "4.0%"
        impact: "30年ぶりの高水準"
        date: "2022-12"
```

### 6.2 翻訳ルール

#### 6.2.1 翻訳優先順位

1. **マスターデータ**: 事前準備済み翻訳
2. **キャッシュ**: 過去翻訳履歴
3. **API 翻訳**: Google Translate API
4. **フォールバック**: 英語表示

#### 6.2.2 翻訳品質管理

- 専門用語の統一
- 文脈に応じた翻訳調整
- ユーザーフィードバック反映
- 定期的な翻訳見直し

### 6.3 分析コンテンツ

#### 6.3.1 レベル別説明

```yaml
learning_content:
  "Consumer Price Index (CPI)":
    beginner:
      title: "CPIって何？"
      content: "物価の上がり下がりを測る温度計のようなものです"
      tips: "数字が大きいほど物価が上がっている"

    intermediate:
      title: "CPIの詳細解説"
      content: "消費者が買うものの価格変化を指数化した指標"
      tips: "コアCPIと合わせて見ることでより正確な判断が可能"

    expert:
      title: "CPIの投資戦略"
      content: "CPIの変化は金融政策に直結し、全資産クラスに影響"
      tips: "予想値との乖離が市場のボラティリティを生む"
```

## 7. 実装詳細

### 7.1 翻訳サービス実装

#### 7.1.1 TranslationService

```python
class TranslationService:
    def __init__(
        self,
        master_repo: IndicatorMasterRepository,
        cache_repo: TranslationCacheRepository,
        google_client: GoogleTranslateClient
    ):
        self.master_repo = master_repo
        self.cache_repo = cache_repo
        self.google_client = google_client

    async def translate_indicator(self, indicator_name: str) -> str:
        """経済指標名を日本語に翻訳"""
        # 1. マスターデータ確認
        master_data = await self.master_repo.find_by_english_name(indicator_name)
        if master_data:
            return master_data.japanese_name

        # 2. キャッシュ確認
        cached = await self.cache_repo.find_translation(indicator_name, "en-ja")
        if cached:
            return cached.translated_text

        # 3. API翻訳
        translated = await self.google_client.translate(indicator_name, "en", "ja")

        # 4. キャッシュ保存
        await self.cache_repo.save_translation(
            indicator_name, translated, "en-ja"
        )

        return translated
```

#### 7.1.2 IndicatorInfoService

```python
class IndicatorInfoService:
    def __init__(self, master_repo: IndicatorMasterRepository):
        self.master_repo = master_repo

    async def get_indicator_info(self, indicator_name: str) -> Dict[str, Any]:
        """経済指標の詳細情報を取得"""
        indicator = await self.master_repo.find_by_english_name(indicator_name)
        if not indicator:
            return None

        return {
            "japanese_name": indicator.japanese_name,
            "category": indicator.category,
            "description": indicator.description,
            "market_impact": {
                "currency": indicator.currency_impact,
                "stocks": indicator.stock_impact,
                "bonds": indicator.bond_impact
            },
            "investment_tips": {
                "good_value": indicator.good_value_tips,
                "bad_value": indicator.bad_value_tips,
                "surprise": indicator.surprise_impact
            },
            "related_indicators": indicator.related_indicators,
            "examples": indicator.examples
        }
```

### 7.2 Discord 統合実装

#### 7.2.1 拡張 Discord 配信

```python
async def send_enhanced_economic_indicator(
    event: Dict[str, Any],
    translation_service: TranslationService,
    info_service: IndicatorInfoService
):
    """拡張された経済指標Discord配信"""

    # 翻訳・情報取得
    japanese_name = await translation_service.translate_indicator(event["event"])
    indicator_info = await info_service.get_indicator_info(event["event"])

    # Discord埋め込み作成
    embed = discord.Embed(
        title=f"📊 経済指標: {japanese_name}",
        description=f"**{event['country']}** - {event['date']} {event['time']} JST",
        color=get_importance_color(event["importance"])
    )

    # 基本情報
    embed.add_field(
        name="📋 指標の説明",
        value=indicator_info["description"][:200] + "...",
        inline=False
    )

    # 市場への影響
    if indicator_info["market_impact"]["currency"]:
        embed.add_field(
            name="💱 通貨への影響",
            value=indicator_info["market_impact"]["currency"][:100] + "...",
            inline=True
        )

    # 投資のポイント
    if indicator_info["investment_tips"]["good_value"]:
        embed.add_field(
            name="💡 投資のポイント",
            value=indicator_info["investment_tips"]["good_value"][:100] + "...",
            inline=True
        )

    # 関連指標
    if indicator_info["related_indicators"]:
        embed.add_field(
            name="🔗 関連指標",
            value=", ".join(indicator_info["related_indicators"][:3]),
            inline=False
        )

    await discord_client.send_embed(embed)
```

### 7.3 分析機能実装

#### 7.3.1 AnalysisService

```python
class AnalysisService:
    def __init__(
        self,
        progress_repo: LearningProgressRepository,
        info_service: IndicatorInfoService
    ):
        self.progress_repo = progress_repo
        self.info_service = info_service

    async def get_analysis_content(
        self,
        indicator_name: str,
        analysis_type: str = "basic"
    ) -> Dict[str, Any]:
        """経済指標の分析コンテンツを取得"""

        # 基本情報取得
        basic_info = await self.info_service.get_indicator_info(indicator_name)

        # 分析タイプ別コンテンツ取得
        analysis_content = await self.info_service.get_analysis_content(
            indicator_name, analysis_type
        )

        # 市場影響度分析
        market_impact = await self.info_service.get_market_impact(indicator_name)

        return {
            "basic_info": basic_info,
            "analysis_content": analysis_content,
            "market_impact": market_impact,
            "analysis_type": analysis_type
        }
```

## 8. テスト戦略

### 8.1 単体テスト

#### 8.1.1 翻訳サービステスト

```python
class TestTranslationService:
    async def test_translate_indicator_master_data(self):
        """マスターデータからの翻訳テスト"""
        service = TranslationService(mock_master_repo, mock_cache_repo, mock_google_client)
        result = await service.translate_indicator("Consumer Price Index (CPI)")
        assert result == "消費者物価指数"

    async def test_translate_indicator_cache(self):
        """キャッシュからの翻訳テスト"""
        # テスト実装

    async def test_translate_indicator_api(self):
        """API翻訳テスト"""
        # テスト実装
```

#### 8.1.2 情報サービステスト

```python
class TestIndicatorInfoService:
    async def test_get_indicator_info(self):
        """指標情報取得テスト"""
        service = IndicatorInfoService(mock_master_repo)
        result = await service.get_indicator_info("Consumer Price Index (CPI)")
        assert result["japanese_name"] == "消費者物価指数"
        assert result["category"] == "インフレ"
```

### 8.2 統合テスト

#### 8.2.1 Discord 統合テスト

```python
class TestDiscordIntegration:
    async def test_enhanced_discord_message(self):
        """拡張Discord配信テスト"""
        # テスト実装
```

#### 8.2.2 データベース統合テスト

```python
class TestDatabaseIntegration:
    async def test_indicator_master_crud(self):
        """マスターデータCRUDテスト"""
        # テスト実装
```

### 8.3 E2E テスト

#### 8.3.1 完全フローテスト

```python
class TestCompleteFlow:
    async def test_economic_indicator_processing(self):
        """経済指標処理の完全フローテスト"""
        # 1. データ取得
        # 2. 翻訳処理
        # 3. 情報取得
        # 4. Discord配信
        # 5. 結果検証
```

## 9. 運用・保守

### 9.1 監視・ログ

#### 9.1.1 監視項目

- 翻訳処理成功率
- API 応答時間
- キャッシュヒット率
- エラー発生率
- システムリソース使用量

#### 9.1.2 ログ出力

```python
# 翻訳処理ログ
logger.info(f"翻訳処理開始: {indicator_name}")
logger.info(f"翻訳結果: {translated_name}")
logger.error(f"翻訳エラー: {error}")

# 情報取得ログ
logger.info(f"指標情報取得: {indicator_name}")
logger.info(f"情報取得完了: {info_count}件")
```

### 9.2 メンテナンス

#### 9.2.1 定期メンテナンス

- **日次**: ログローテーション、キャッシュクリーンアップ
- **週次**: 翻訳品質チェック、データ更新確認
- **月次**: マスターデータ更新、統計分析

#### 9.2.2 障害対応

- **翻訳 API 障害**: キャッシュ・マスターデータフォールバック
- **データベース障害**: 読み取り専用モード、復旧手順
- **外部 API 制限**: レート制限対応、待機処理

### 9.3 品質管理

#### 9.3.1 翻訳品質

- 専門用語の統一
- 文脈に応じた翻訳調整
- ユーザーフィードバック収集
- 定期的な翻訳見直し

#### 9.3.2 情報精度

- 一次情報源からの確認
- 専門家レビュー
- 市場動向との整合性確認
- 定期的な情報更新

## 10. コスト管理

### 10.1 運用コスト内訳

#### 10.1.1 月額コスト（目標: ¥5,000 以下）

- **Google Translate API**: ¥0（無料枠内）
- **OpenAI API**: ¥1,000-2,000
- **サーバー費用**: ¥0（既存システム活用）
- **データベース**: ¥0（既存システム活用）
- **監視・ログ**: ¥0（既存システム活用）

#### 10.1.2 開発コスト

- **初期開発**: ¥0（既存システム活用）
- **継続開発**: 月 20-40 時間
- **品質管理**: 月 10-20 時間

### 10.2 コスト最適化戦略

#### 10.2.1 API 利用最適化

- バッチ処理による効率化
- キャッシュによる重複呼び出し削減
- 無料枠の最大活用
- 品質に応じた API 選択

#### 10.2.2 リソース最適化

- 既存インフラの活用
- 効率的なデータ構造
- 不要な処理の削除
- 定期的なパフォーマンス監視

## 11. リスク管理

### 11.1 技術リスク

#### 11.1.1 API 制限・障害

- **リスク**: 外部 API の利用制限・障害
- **影響**: 翻訳機能の停止
- **対策**: キャッシュ・マスターデータフォールバック

#### 11.1.2 データ品質

- **リスク**: 翻訳・情報の不正確性
- **影響**: ユーザー信頼性の低下
- **対策**: 品質チェック・専門家レビュー

### 11.2 運用リスク

#### 11.2.1 コスト増大

- **リスク**: API 利用料の急増
- **影響**: プロジェクト継続困難
- **対策**: 使用量監視・制限設定

#### 11.2.2 パフォーマンス劣化

- **リスク**: システム応答時間の増大
- **影響**: ユーザビリティの低下
- **対策**: 定期的なパフォーマンス監視・最適化

### 11.3 ビジネスリスク

#### 11.3.1 競合出現

- **リスク**: 類似サービスの登場
- **影響**: 市場シェアの減少
- **対策**: 差別化機能の開発・品質向上

#### 11.3.2 規制変更

- **リスク**: データ保護規制の強化
- **影響**: システム改修が必要
- **対策**: 規制対応の継続的監視

## 12. 今後の拡張計画

### 12.1 短期計画（3-6 ヶ月）

#### 12.1.1 機能拡張

- Web ダッシュボードの開発
- モバイルアプリの開発
- API 提供の開始
- 多言語対応の拡充

#### 12.1.2 品質向上

- AI 解説生成の精度向上
- 翻訳品質の改善
- ユーザビリティの向上
- パフォーマンスの最適化

### 12.2 中期計画（6-12 ヶ月）

#### 12.2.1 収益化

- プレミアム機能の開発
- 企業向けサービスの提供
- 広告収入の導入
- パートナーシップの構築

#### 12.2.2 市場拡大

- 新規市場への進出
- 新規ユーザーの獲得
- ブランド認知度の向上
- 競合優位性の確立

### 12.3 長期計画（1-3 年）

#### 12.3.1 技術革新

- AI 分析の活用
- リアルタイム分析の実現
- 予測精度の向上
- 自動化の推進

#### 12.3.2 事業拡大

- グローバル展開
- 新規事業領域への進出
- 企業買収・合併
- IPO 準備

## 13. 成功指標

### 13.1 技術指標

#### 13.1.1 パフォーマンス

- 翻訳処理時間: 1 秒以内（目標達成率 95%）
- 情報取得時間: 500ms 以内（目標達成率 90%）
- システム稼働率: 99.5%以上
- エラー率: 1%以下

#### 13.1.2 品質

- 翻訳精度: 95%以上
- 情報正確性: 98%以上
- ユーザー満足度: 4.0/5.0 以上
- バグ発生率: 月 1 件以下

### 13.2 ビジネス指標

#### 13.2.1 利用状況

- 月間アクティブユーザー: 1,000 人以上
- 日次翻訳処理数: 10,000 件以上
- キャッシュヒット率: 80%以上
- ユーザー継続率: 70%以上

#### 13.2.2 コスト効率

- 月額運用コスト: ¥5,000 以下
- API 利用料: 予算内
- 開発工数: 計画内
- ROI: 200%以上

### 13.3 ユーザー指標

#### 13.3.1 満足度

- 機能満足度: 4.0/5.0 以上
- 使いやすさ: 4.0/5.0 以上
- 情報有用性: 4.0/5.0 以上
- 推奨意向: 70%以上

#### 13.3.2 分析効果

- 経済指標理解度向上: 30%以上
- 投資判断精度向上: 20%以上
- 分析継続率: 60%以上
- 知識定着率: 80%以上

## 14. まとめ

### 14.1 プロジェクトの価値

#### 14.1.1 ユーザー価値

- **理解促進**: 日本語表示による経済指標の理解促進
- **投資支援**: 詳細情報による投資判断支援
- **分析効果**: 段階的分析による知識向上
- **利便性**: 使いやすいインターフェース

#### 14.1.2 ビジネス価値

- **競合優位**: 差別化された機能提供
- **収益機会**: プレミアム機能・広告収入
- **市場拡大**: 新規ユーザーの獲得
- **ブランド強化**: 専門性のアピール

### 14.2 実現可能性

#### 14.2.1 技術的実現性

- **既存システム活用**: 開発コスト最小化
- **段階的実装**: リスク分散
- **品質管理**: 継続的改善
- **スケーラビリティ**: 将来拡張対応

#### 14.2.2 経済的実現性

- **低コスト運用**: 月額 ¥5,000 以下
- **段階的投資**: 効果確認後の投資判断
- **収益化可能性**: 複数の収益源
- **ROI**: 高い投資対効果

### 14.3 次のステップ

#### 14.3.1 即座に開始可能

1. **マスターデータ準備**: 主要指標 50 件の情報収集
2. **データベース設計**: テーブル作成・エンティティ実装
3. **基本翻訳機能**: 手動翻訳による初期実装
4. **Discord 統合**: 既存システムとの連携

#### 14.3.2 効果確認後の拡張

1. **AI 機能追加**: ChatGPT API 活用
2. **分析機能実装**: 分析レポート管理
3. **Web UI 開発**: ダッシュボード機能
4. **収益化機能**: プレミアム・広告機能

この経済指標日本語化・詳細情報拡張システムは、既存の investpy 経済カレンダーシステムを大幅に強化し、ユーザーにとってより価値のあるサービスを提供できるプロジェクトです。段階的な実装により、リスクを最小化しながら、高品質な機能を実現できます。

---

**作成日**: 2025 年 8 月 24 日  
**作成者**: AI Assistant  
**バージョン**: 1.0  
**ステータス**: 承認待ち

## 15. ファイル構成設計

### 15.1 全体フォルダ構成

```
investpy-economic-calendar/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── economic_indicator/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── economic_indicator.py              # 経済指標エンティティ（~200行）
│   │   │   │   ├── economic_indicator_validator.py    # バリデーション（~150行）
│   │   │   │   └── economic_indicator_factory.py      # ファクトリ（~100行）
│   │   │   ├── translation/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── translation_cache.py               # 翻訳キャッシュエンティティ（~150行）
│   │   │   │   └── translation_cache_validator.py     # バリデーション（~100行）
│   │   │   └── system_setting/
│   │   │       ├── __init__.py
│   │   │       ├── system_setting.py                  # システム設定エンティティ（~100行）
│   │   │       └── system_setting_validator.py        # バリデーション（~80行）
│   │   ├── repositories/
│   │   │   ├── economic_indicator/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── economic_indicator_repository.py   # インターフェース（~100行）
│   │   │   │   └── economic_indicator_repository_impl.py # 実装（~200行）
│   │   │   ├── translation/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── translation_cache_repository.py    # インターフェース（~100行）
│   │   │   │   └── translation_cache_repository_impl.py # 実装（~150行）
│   │   │   └── system_setting/
│   │   │       ├── __init__.py
│   │   │       ├── system_setting_repository.py       # インターフェース（~80行）
│   │   │       └── system_setting_repository_impl.py  # 実装（~120行）
│   │   └── services/
│   │       ├── translation/
│   │       │   ├── __init__.py
│   │       │   ├── translation_service.py             # 翻訳サービス（~200行）
│   │       │   ├── translation_quality_manager.py     # 品質管理（~150行）
│   │       │   └── translation_cache_manager.py       # キャッシュ管理（~120行）
│   │       ├── indicator_info/
│   │       │   ├── __init__.py
│   │       │   ├── indicator_info_service.py          # 情報サービス（~200行）
│   │       │   ├── market_impact_analyzer.py          # 市場影響分析（~180行）
│   │       │   └── investment_tips_generator.py       # 投資アドバイス生成（~150行）
│   │       └── analysis/
│   │           ├── __init__.py
│   │           ├── economic_analysis_service.py       # 分析サービス（~200行）
│   │           ├── comparison_analyzer.py             # 比較分析（~150行）
│   │           └── report_generator.py                # レポート生成（~180行）
│   ├── application/
│   │   ├── use_cases/
│   │   │   ├── translation/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── translate_indicator.py             # 翻訳ユースケース（~150行）
│   │   │   │   ├── manage_translation_cache.py        # キャッシュ管理（~120行）
│   │   │   │   └── update_translation_quality.py      # 品質更新（~100行）
│   │   │   ├── indicator_info/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── get_indicator_info.py              # 情報取得（~150行）
│   │   │   │   ├── update_indicator_info.py           # 情報更新（~120行）
│   │   │   │   └── analyze_market_impact.py           # 市場影響分析（~180行）
│   │   │   └── analysis/
│   │   │       ├── __init__.py
│   │   │       ├── generate_analysis_report.py        # 分析レポート生成（~200行）
│   │   │       ├── compare_indicators.py              # 指標比較（~150行）
│   │   │       └── create_investment_summary.py       # 投資サマリー作成（~180行）
│   │   └── services/
│   │       ├── enhanced_discord/
│   │       │   ├── __init__.py
│   │       │   ├── enhanced_discord_service.py        # 拡張Discordサービス（~250行）
│   │       │   ├── japanese_message_builder.py        # 日本語メッセージ作成（~200行）
│   │       │   └── detailed_info_formatter.py         # 詳細情報フォーマット（~180行）
│   │       └── integration/
│   │           ├── __init__.py
│   │           ├── economic_calendar_integration.py   # 既存システム統合（~200行）
│   │           └── data_sync_manager.py               # データ同期管理（~150行）
│   ├── infrastructure/
│   │   ├── database/
│   │   │   ├── models/
│   │   │   │   ├── economic_indicator/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── economic_indicator_model.py    # データベースモデル（~200行）
│   │   │   │   │   └── economic_indicator_mapper.py   # マッパー（~100行）
│   │   │   │   ├── translation/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── translation_cache_model.py     # データベースモデル（~150行）
│   │   │   │   │   └── translation_cache_mapper.py    # マッパー（~80行）
│   │   │   │   └── system_setting/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── system_setting_model.py        # データベースモデル（~100行）
│   │   │   │       └── system_setting_mapper.py       # マッパー（~80行）
│   │   │   ├── repositories/
│   │   │   │   ├── sql/
│   │   │   │   │   ├── sql_economic_indicator_repository.py    # SQL実装（~300行）
│   │   │   │   │   ├── sql_translation_cache_repository.py     # SQL実装（~250行）
│   │   │   │   │   └── sql_system_setting_repository.py        # SQL実装（~200行）
│   │   │   │   └── cache/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── redis_translation_cache.py              # Redisキャッシュ（~150行）
│   │   │   │       └── memory_translation_cache.py             # メモリキャッシュ（~120行）
│   │   │   └── migrations/
│   │   │       └── versions/
│   │   │           ├── 001_create_economic_indicators_master.py
│   │   │           ├── 002_create_translation_cache.py
│   │   │           └── 003_create_system_settings.py
│   │   ├── external/
│   │   │   ├── translation/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── google_translate_client.py         # Google翻訳クライアント（~200行）
│   │   │   │   ├── translation_error_handler.py       # エラーハンドラー（~150行）
│   │   │   │   └── translation_rate_limiter.py        # レート制限（~100行）
│   │   │   └── ai/
│   │   │       ├── __init__.py
│   │   │       ├── openai_analysis_client.py          # OpenAI分析クライアント（~200行）
│   │   │       ├── analysis_prompt_builder.py         # プロンプト作成（~150行）
│   │   │       └── analysis_response_parser.py        # 応答解析（~120行）
│   │   └── config/
│   │       ├── economic_indicator/
│   │       │   ├── __init__.py
│   │       │   ├── economic_indicator_config.py       # 設定管理（~150行）
│   │       │   └── master_data_config.py              # マスターデータ設定（~100行）
│   │       ├── translation/
│   │       │   ├── __init__.py
│   │       │   ├── translation_config.py              # 翻訳設定（~150行）
│   │       │   └── quality_config.py                  # 品質設定（~100行）
│   │       └── integration/
│   │           ├── __init__.py
│   │           ├── discord_integration_config.py      # Discord統合設定（~120行）
│   │           └── system_integration_config.py       # システム統合設定（~100行）
│   └── utils/
│       ├── translation/
│       │   ├── __init__.py
│       │   ├── translation_utils.py                   # 翻訳ユーティリティ（~150行）
│       │   ├── language_detector.py                   # 言語検出（~100行）
│       │   └── text_normalizer.py                     # テキスト正規化（~120行）
│       ├── validation/
│       │   ├── __init__.py
│       │   ├── indicator_validator.py                 # 指標バリデーション（~150行）
│       │   ├── translation_validator.py               # 翻訳バリデーション（~120行）
│       │   └── data_quality_checker.py                # データ品質チェック（~100行）
│       └── common/
│           ├── __init__.py
│           ├── constants.py                           # 定数定義（~100行）
│           ├── exceptions.py                          # 例外定義（~120行）
│           └── decorators.py                          # デコレーター（~80行）
├── config/
│   ├── economic_indicator/
│   │   ├── master_data.yaml                          # マスターデータ設定
│   │   ├── translation_rules.yaml                    # 翻訳ルール設定
│   │   └── quality_standards.yaml                    # 品質基準設定
│   ├── integration/
│   │   ├── discord_enhancement.yaml                  # Discord拡張設定
│   │   └── system_integration.yaml                   # システム統合設定
│   └── crontab/
│       └── production/
│           ├── economic_indicator_sync.cron          # 経済指標同期
│           └── translation_cache_cleanup.cron        # 翻訳キャッシュクリーンアップ
├── data/
│   ├── economic_indicators/
│   │   ├── master_data/                              # マスターデータ
│   │   │   ├── indicators.yaml                       # 主要経済指標50件
│   │   │   ├── categories.yaml                       # カテゴリ定義
│   │   │   └── countries.yaml                        # 国別設定
│   │   ├── translation_cache/                        # 翻訳キャッシュ
│   │   │   ├── en_ja_cache.json                      # 英語→日本語キャッシュ
│   │   │   └── cache_metadata.json                   # キャッシュメタデータ
│   │   └── analysis_reports/                         # 分析レポート
│   │       ├── generated/                            # 生成されたレポート
│   │       ├── templates/                            # レポートテンプレート
│   │       └── archive/                              # アーカイブ
│   └── logs/
│       ├── translation_logs/                         # 翻訳ログ
│       ├── analysis_logs/                            # 分析ログ
│       └── integration_logs/                         # 統合ログ
├── scripts/
│   ├── economic_indicator/
│   │   ├── setup_master_data.py                      # マスターデータセットアップ
│   │   ├── import_indicator_data.py                  # 指標データインポート
│   │   ├── validate_translations.py                  # 翻訳検証
│   │   └── generate_analysis_reports.py              # 分析レポート生成
│   ├── translation/
│   │   ├── batch_translate.py                        # バッチ翻訳
│   │   ├── cache_management.py                       # キャッシュ管理
│   │   ├── quality_check.py                          # 品質チェック
│   │   └── translation_cleanup.py                    # 翻訳クリーンアップ
│   ├── integration/
│   │   ├── test_discord_integration.py               # Discord統合テスト
│   │   ├── test_system_integration.py                # システム統合テスト
│   │   └── sync_with_existing_system.py              # 既存システム同期
│   └── maintenance/
│       ├── backup_master_data.py                     # マスターデータバックアップ
│       ├── restore_master_data.py                    # マスターデータ復元
│       ├── cleanup_old_data.py                       # 古いデータクリーンアップ
│       └── performance_optimization.py               # パフォーマンス最適化
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   │   ├── test_economic_indicator_entity.py     # エンティティテスト
│   │   │   ├── test_translation_service.py           # 翻訳サービステスト
│   │   │   └── test_indicator_info_service.py        # 情報サービステスト
│   │   ├── application/
│   │   │   ├── test_translate_indicator_use_case.py  # ユースケーステスト
│   │   │   └── test_enhanced_discord_service.py      # Discordサービステスト
│   │   └── infrastructure/
│   │       ├── test_sql_repositories.py              # リポジトリテスト
│   │       └── test_external_clients.py              # 外部クライアントテスト
│   ├── integration/
│   │   ├── test_translation_workflow.py              # 翻訳ワークフローテスト
│   │   ├── test_discord_integration.py               # Discord統合テスト
│   │   └── test_data_sync.py                         # データ同期テスト
│   └── e2e/
│       ├── test_complete_indicator_processing.py     # 完全処理テスト
│       └── test_system_performance.py                # システムパフォーマンステスト
└── docs/
    ├── economic_indicator/
    │   ├── api_documentation.md                      # APIドキュメント
    │   ├── database_schema.md                        # データベーススキーマ
    │   └── integration_guide.md                      # 統合ガイド
    ├── translation/
    │   ├── translation_guide.md                      # 翻訳ガイド
    │   ├── quality_standards.md                      # 品質基準
    │   └── troubleshooting.md                        # トラブルシューティング
    └── deployment/
        ├── setup_guide.md                            # セットアップガイド
        ├── deployment_guide.md                       # デプロイメントガイド
        └── maintenance_guide.md                      # メンテナンスガイド
```

### 15.2 ファイル配置の理由

#### 15.2.1 ドメイン層の配置

**`src/domain/entities/economic_indicator/`**

- 経済指標の核心エンティティを配置
- 既存の`economic_event`と区別して、マスターデータ用のエンティティとして分離
- バリデーションとファクトリを同階層に配置して責任を明確化

**`src/domain/repositories/economic_indicator/`**

- 経済指標マスターデータの永続化インターフェース
- 既存の`economic_calendar_repository`と区別
- 翻訳キャッシュとシステム設定も同様に分離

**`src/domain/services/translation/`**

- 翻訳機能を独立したサービスとして配置
- 品質管理とキャッシュ管理を分離して責任を明確化
- 将来的な多言語対応を見据えた設計

#### 15.2.2 アプリケーション層の配置

**`src/application/use_cases/translation/`**

- 翻訳関連のユースケースを集約
- キャッシュ管理と品質更新も含めて一元的に管理
- 既存のユースケースと明確に分離

**`src/application/services/enhanced_discord/`**

- 既存の Discord 機能を拡張する形で配置
- 日本語メッセージ作成と詳細情報フォーマットを分離
- 既存システムとの統合を考慮した設計

#### 15.2.3 インフラストラクチャ層の配置

**`src/infrastructure/database/models/economic_indicator/`**

- 経済指標マスターデータ用のモデルを配置
- 既存の`economic_event_model`と区別
- マッパーも同階層に配置して責任を明確化

**`src/infrastructure/external/translation/`**

- 外部翻訳 API との連携を独立したモジュールとして配置
- エラーハンドリングとレート制限を分離
- 将来的な API 変更に対応しやすい設計

#### 15.2.4 設定ファイルの配置

**`config/economic_indicator/`**

- 経済指標関連の設定を集約
- マスターデータ、翻訳ルール、品質基準を分離
- 既存の設定ファイルと明確に区別

**`config/integration/`**

- 既存システムとの統合設定を集約
- Discord 拡張とシステム統合を分離
- 段階的な統合を考慮した設計

#### 15.2.5 データファイルの配置

**`data/economic_indicators/master_data/`**

- マスターデータを YAML 形式で管理
- 翻訳キャッシュを JSON 形式で管理
- 分析レポートの生成・保存・アーカイブを分離

**`data/logs/translation_logs/`**

- 翻訳関連のログを独立して管理
- 分析ログと統合ログも分離
- 既存のログと混在しない設計

#### 15.2.6 スクリプトの配置

**`scripts/economic_indicator/`**

- 経済指標関連のスクリプトを集約
- マスターデータのセットアップ、インポート、検証を分離
- 分析レポート生成も含めて一元的に管理

**`scripts/translation/`**

- 翻訳関連のスクリプトを独立して配置
- バッチ処理、キャッシュ管理、品質チェックを分離
- メンテナンススクリプトも含めて管理

#### 15.2.7 テストの配置

**`tests/unit/domain/`**

- ドメイン層の単体テストを配置
- エンティティ、サービス、リポジトリのテストを分離
- 既存のテストと明確に区別

**`tests/integration/`**

- 統合テストを配置
- 翻訳ワークフロー、Discord 統合、データ同期のテスト
- E2E テストも含めて段階的なテスト設計

### 15.3 既存システムとの統合ポイント

#### 15.3.1 データベース統合

**既存テーブルとの関係**

- `economic_events`（既存）: 実際の経済イベントデータ
- `economic_indicators_master`（新規）: マスターデータ
- `translation_cache`（新規）: 翻訳キャッシュ
- `system_settings`（新規）: システム設定

**統合アプローチ**

- 既存の`economic_events`テーブルはそのまま維持
- 新規テーブルは独立して作成
- 必要に応じて外部キーで関連付け

#### 15.3.2 Discord 統合

**既存機能との統合**

- 既存の`discord_client.py`を拡張
- `enhanced_discord_service.py`で新機能を追加
- 既存の配信ロジックを維持しながら拡張

**統合アプローチ**

- 既存の Discord 配信はそのまま動作
- 新機能は条件付きで有効化
- 段階的な移行が可能

#### 15.3.3 スケジューラー統合

**既存 crontab との統合**

- 既存の crontab 設定はそのまま維持
- 新規 crontab を追加
- 競合しない時間帯で実行

**統合アプローチ**

- 既存の`economic_indicators_discord.py`はそのまま動作
- 新機能は別のスクリプトとして実装
- 必要に応じて統合

### 15.4 段階的実装計画

#### 15.4.1 Phase 1: 基盤構築（Week 1-3）

**Week 1: データベース・エンティティ**

```
src/domain/entities/economic_indicator/
src/domain/repositories/economic_indicator/
src/infrastructure/database/models/economic_indicator/
config/economic_indicator/
data/economic_indicators/master_data/
```

**Week 2: マスターデータ準備**

```
data/economic_indicators/master_data/indicators.yaml
scripts/economic_indicator/setup_master_data.py
scripts/economic_indicator/import_indicator_data.py
```

**Week 3: 基本サービス実装**

```
src/domain/services/translation/
src/domain/services/indicator_info/
src/infrastructure/external/translation/
```

#### 15.4.2 Phase 2: 機能統合（Week 4-6）

**Week 4: Discord 統合**

```
src/application/services/enhanced_discord/
scripts/integration/test_discord_integration.py
config/integration/discord_enhancement.yaml
```

**Week 5: 分析・解説機能実装**

```
src/domain/services/analysis/
src/application/use_cases/analysis/
scripts/economic_indicator/generate_analysis_reports.py
```

**Week 6: 品質向上**

```
src/domain/services/translation/translation_quality_manager.py
scripts/translation/quality_check.py
tests/unit/domain/test_translation_service.py
```

#### 15.4.3 Phase 3: 拡張・最適化（Week 7-8）

**Week 7: 高度機能**

```
src/application/services/integration/
scripts/integration/sync_with_existing_system.py
config/integration/system_integration.yaml
```

**Week 8: 運用準備**

```
scripts/maintenance/
docs/deployment/
tests/e2e/
```

### 15.5 ファイル命名規則

#### 15.5.1 エンティティ・モデル

- エンティティ: `economic_indicator.py`
- モデル: `economic_indicator_model.py`
- マッパー: `economic_indicator_mapper.py`
- バリデーター: `economic_indicator_validator.py`
- ファクトリ: `economic_indicator_factory.py`

#### 15.5.2 リポジトリ

- インターフェース: `economic_indicator_repository.py`
- 実装: `economic_indicator_repository_impl.py`
- SQL 実装: `sql_economic_indicator_repository.py`

#### 15.5.3 サービス

- メインサービス: `translation_service.py`
- 補助サービス: `translation_quality_manager.py`
- ユーティリティ: `translation_utils.py`

#### 15.5.4 ユースケース

- メイン: `translate_indicator.py`
- 管理: `manage_translation_cache.py`
- 更新: `update_translation_quality.py`

#### 15.5.5 テスト

- 単体テスト: `test_economic_indicator_entity.py`
- 統合テスト: `test_translation_workflow.py`
- E2E テスト: `test_complete_indicator_processing.py`

#### 15.5.6 スクリプト

- セットアップ: `setup_master_data.py`
- インポート: `import_indicator_data.py`
- 検証: `validate_translations.py`
- 生成: `generate_analysis_reports.py`

#### 15.5.7 設定ファイル

- マスターデータ: `master_data.yaml`
- 翻訳ルール: `translation_rules.yaml`
- 品質基準: `quality_standards.yaml`
- Discord 拡張: `discord_enhancement.yaml`

### 15.6 依存関係管理

#### 15.6.1 新規依存関係

```txt
# requirements/economic_indicator.txt
google-cloud-translate==3.11.1
pyyaml==6.0.1
jsonschema==4.19.2
```

#### 15.6.2 既存依存関係の活用

- `pandas`: データ処理
- `sqlalchemy`: データベース操作
- `discord-webhook`: Discord 通知
- `openai`: AI 分析
- `pytest`: テスト

#### 15.6.3 依存関係の分離

- 新機能用の依存関係は独立して管理
- 既存システムに影響を与えない設計
- 必要に応じて段階的に統合

このファイル構成により、経済指標日本語化システムを既存システムと適切に分離しながら、段階的に統合できる設計となっています。

## 16. 実装ルール・コーディング規約

### 16.1 コード品質管理

#### 16.1.1 ファイルサイズ制約

**厳格な制約**

- **最大行数**: 400 行以内（推奨 300 行以下）
- **クラス最大行数**: 200 行以内
- **メソッド最大行数**: 50 行以内
- **関数最大行数**: 30 行以内

**例外条件**

- データベースマイグレーションファイル: 500 行以内
- テストファイル: 600 行以内
- 設定ファイル: 制限なし

#### 16.1.2 Linter・フォーマッター設定

**必須ツール**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11
        args: [--line-length=88, --target-version=py311]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black, --line-length=88]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203, W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports, --disallow-untyped-defs]
```

**Flake8 設定**

```ini
# .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    .venv,
    .mypy_cache,
    .pytest_cache,
    migrations,
    node_modules
per-file-ignores =
    __init__.py:F401
    tests/*:S101,S105,S106,S107
```

**MyPy 設定**

```ini
# mypy.ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy.plugins.sqlalchemy.ext.*]
init_subclass = True
```

#### 16.1.3 型ヒント要件

**必須型ヒント**

- 全メソッド・関数の引数と戻り値
- クラス変数とインスタンス変数
- ジェネリック型の使用
- Union 型の適切な使用

**型ヒント例**

```python
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from decimal import Decimal

class TranslationService:
    def __init__(
        self,
        master_repo: EconomicIndicatorRepository,
        cache_repo: TranslationCacheRepository,
        google_client: GoogleTranslateClient
    ) -> None:
        self.master_repo: EconomicIndicatorRepository = master_repo
        self.cache_repo: TranslationCacheRepository = cache_repo
        self.google_client: GoogleTranslateClient = google_client

    async def translate_indicator(
        self,
        indicator_name: str,
        target_language: str = "ja"
    ) -> Optional[str]:
        """経済指標名を翻訳"""
        pass

    def get_translation_stats(self) -> Dict[str, Union[int, float]]:
        """翻訳統計を取得"""
        pass
```

### 16.2 アーキテクチャルルール

#### 16.2.1 依存性注入原則

**必須要件**

- 外部依存はコンストラクタで注入
- インターフェースを使用した抽象化
- テスト可能な設計

**実装例**

```python
from abc import ABC, abstractmethod
from typing import Protocol

class TranslationRepository(Protocol):
    @abstractmethod
    async def save_translation(
        self,
        original: str,
        translated: str,
        language_pair: str
    ) -> None:
        pass

class TranslationService:
    def __init__(
        self,
        repository: TranslationRepository,
        translator: TranslatorClient
    ) -> None:
        self.repository = repository
        self.translator = translator
```

#### 16.2.2 単一責任原則

**クラス設計ルール**

- 1 つのクラスは 1 つの責任のみ
- 関連する機能は同じクラスに集約
- 過度な分割は避ける

**責任分離例**

```python
# ✅ 良い例: 責任が明確
class TranslationService:
    """翻訳処理のみを担当"""
    pass

class TranslationQualityManager:
    """翻訳品質管理のみを担当"""
    pass

class TranslationCacheManager:
    """翻訳キャッシュ管理のみを担当"""
    pass

# ❌ 悪い例: 責任が混在
class TranslationManager:
    """翻訳、品質管理、キャッシュ管理を全て担当"""
    pass
```

#### 16.2.3 エラーハンドリング

**例外設計**

```python
from typing import Optional

class EconomicIndicatorError(Exception):
    """経済指標関連の基底例外"""
    pass

class TranslationError(EconomicIndicatorError):
    """翻訳処理エラー"""
    pass

class IndicatorNotFoundError(EconomicIndicatorError):
    """経済指標が見つからないエラー"""
    pass

class ValidationError(EconomicIndicatorError):
    """バリデーションエラー"""
    pass
```

**エラーハンドリング例**

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TranslationService:
    async def translate_indicator(
        self,
        indicator_name: str
    ) -> Optional[str]:
        try:
            # マスターデータ確認
            master_data = await self.master_repo.find_by_english_name(indicator_name)
            if master_data:
                return master_data.japanese_name

            # キャッシュ確認
            cached = await self.cache_repo.find_translation(indicator_name, "en-ja")
            if cached:
                return cached.translated_text

            # API翻訳
            translated = await self.google_client.translate(indicator_name, "en", "ja")

            # キャッシュ保存
            await self.cache_repo.save_translation(indicator_name, translated, "en-ja")

            return translated

        except TranslationError as e:
            logger.error(f"翻訳エラー: {indicator_name} - {e}")
            return None
        except Exception as e:
            logger.error(f"予期しないエラー: {indicator_name} - {e}")
            raise EconomicIndicatorError(f"翻訳処理でエラーが発生: {e}")
```

### 16.3 コーディングスタイル

#### 16.3.1 命名規則

**クラス名**

- PascalCase: `EconomicIndicator`, `TranslationService`
- 抽象クラス: `AbstractRepository`, `BaseService`

**メソッド・関数名**

- snake_case: `translate_indicator`, `get_master_data`
- 動詞から始める: `create_`, `update_`, `delete_`, `find_`

**変数名**

- snake_case: `indicator_name`, `translation_cache`
- 定数: UPPER_SNAKE_CASE: `MAX_CACHE_SIZE`, `DEFAULT_LANGUAGE`

**ファイル名**

- snake_case: `economic_indicator.py`, `translation_service.py`
- テストファイル: `test_economic_indicator.py`

#### 16.3.2 ドキュメンテーション

**docstring 形式**

```python
from typing import Optional, Dict, Any

class TranslationService:
    """経済指標の翻訳処理を担当するサービスクラス。

    マスターデータ、キャッシュ、外部APIを組み合わせて
    効率的な翻訳処理を提供します。
    """

    async def translate_indicator(
        self,
        indicator_name: str,
        target_language: str = "ja"
    ) -> Optional[str]:
        """経済指標名を指定された言語に翻訳します。

        Args:
            indicator_name: 翻訳対象の経済指標名（英語）
            target_language: 翻訳先言語（デフォルト: "ja"）

        Returns:
            翻訳された文字列。翻訳に失敗した場合はNone

        Raises:
            TranslationError: 翻訳処理でエラーが発生した場合
            ValidationError: 入力値が不正な場合

        Example:
            >>> service = TranslationService(repo, client)
            >>> result = await service.translate_indicator("Consumer Price Index")
            >>> print(result)
            "消費者物価指数"
        """
        pass
```

#### 16.3.3 ログ出力

**ログレベル使用基準**

```python
import logging

logger = logging.getLogger(__name__)

class TranslationService:
    async def translate_indicator(self, indicator_name: str) -> Optional[str]:
        logger.debug(f"翻訳開始: {indicator_name}")

        try:
            # マスターデータ確認
            master_data = await self.master_repo.find_by_english_name(indicator_name)
            if master_data:
                logger.info(f"マスターデータから翻訳取得: {indicator_name}")
                return master_data.japanese_name

            # キャッシュ確認
            cached = await self.cache_repo.find_translation(indicator_name, "en-ja")
            if cached:
                logger.info(f"キャッシュから翻訳取得: {indicator_name}")
                return cached.translated_text

            # API翻訳
            logger.info(f"API翻訳実行: {indicator_name}")
            translated = await self.google_client.translate(indicator_name, "en", "ja")

            # キャッシュ保存
            await self.cache_repo.save_translation(indicator_name, translated, "en-ja")
            logger.info(f"翻訳完了・キャッシュ保存: {indicator_name}")

            return translated

        except TranslationError as e:
            logger.error(f"翻訳エラー: {indicator_name} - {e}")
            return None
        except Exception as e:
            logger.error(f"予期しないエラー: {indicator_name} - {e}", exc_info=True)
            raise
```

### 16.4 テスト要件

#### 16.4.1 テストカバレッジ

**必須要件**

- **単体テスト**: 95%以上
- **統合テスト**: 90%以上
- **E2E テスト**: 80%以上

**カバレッジ設定**

```ini
# .coveragerc
[run]
source = src
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod
```

#### 16.4.2 テスト設計

**テスト構造**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

class TestTranslationService:
    """TranslationServiceのテストクラス"""

    @pytest.fixture
    def mock_master_repo(self) -> AsyncMock:
        """マスターレポジトリのモック"""
        return AsyncMock()

    @pytest.fixture
    def mock_cache_repo(self) -> AsyncMock:
        """キャッシュレポジトリのモック"""
        return AsyncMock()

    @pytest.fixture
    def mock_google_client(self) -> AsyncMock:
        """Google翻訳クライアントのモック"""
        return AsyncMock()

    @pytest.fixture
    def translation_service(
        self,
        mock_master_repo: AsyncMock,
        mock_cache_repo: AsyncMock,
        mock_google_client: AsyncMock
    ) -> TranslationService:
        """TranslationServiceのインスタンス"""
        return TranslationService(
            master_repo=mock_master_repo,
            cache_repo=mock_cache_repo,
            google_client=mock_google_client
        )

    @pytest.mark.asyncio
    async def test_translate_indicator_master_data(
        self,
        translation_service: TranslationService,
        mock_master_repo: AsyncMock
    ) -> None:
        """マスターデータからの翻訳テスト"""
        # Arrange
        indicator_name = "Consumer Price Index (CPI)"
        expected_translation = "消費者物価指数"

        mock_master_repo.find_by_english_name.return_value = MagicMock(
            japanese_name=expected_translation
        )

        # Act
        result = await translation_service.translate_indicator(indicator_name)

        # Assert
        assert result == expected_translation
        mock_master_repo.find_by_english_name.assert_called_once_with(indicator_name)

    @pytest.mark.asyncio
    async def test_translate_indicator_cache(
        self,
        translation_service: TranslationService,
        mock_master_repo: AsyncMock,
        mock_cache_repo: AsyncMock
    ) -> None:
        """キャッシュからの翻訳テスト"""
        # Arrange
        indicator_name = "Gross Domestic Product (GDP)"
        expected_translation = "国内総生産"

        mock_master_repo.find_by_english_name.return_value = None
        mock_cache_repo.find_translation.return_value = MagicMock(
            translated_text=expected_translation
        )

        # Act
        result = await translation_service.translate_indicator(indicator_name)

        # Assert
        assert result == expected_translation
        mock_cache_repo.find_translation.assert_called_once_with(indicator_name, "en-ja")

    @pytest.mark.asyncio
    async def test_translate_indicator_api(
        self,
        translation_service: TranslationService,
        mock_master_repo: AsyncMock,
        mock_cache_repo: AsyncMock,
        mock_google_client: AsyncMock
    ) -> None:
        """API翻訳テスト"""
        # Arrange
        indicator_name = "Employment Report"
        expected_translation = "雇用統計"

        mock_master_repo.find_by_english_name.return_value = None
        mock_cache_repo.find_translation.return_value = None
        mock_google_client.translate.return_value = expected_translation

        # Act
        result = await translation_service.translate_indicator(indicator_name)

        # Assert
        assert result == expected_translation
        mock_google_client.translate.assert_called_once_with(indicator_name, "en", "ja")
        mock_cache_repo.save_translation.assert_called_once_with(
            indicator_name, expected_translation, "en-ja"
        )
```

### 16.5 パフォーマンス要件

#### 16.5.1 実行時間制約

**必須要件**

- 翻訳処理: 1 秒以内
- データベースクエリ: 200ms 以内
- キャッシュアクセス: 50ms 以内
- API 呼び出し: 500ms 以内

**パフォーマンステスト例**

```python
import time
import pytest
from typing import Any

class TestTranslationServicePerformance:
    """TranslationServiceのパフォーマンステスト"""

    @pytest.mark.asyncio
    async def test_translation_performance(
        self,
        translation_service: TranslationService
    ) -> None:
        """翻訳処理のパフォーマンステスト"""
        indicator_name = "Consumer Price Index (CPI)"

        start_time = time.time()
        result = await translation_service.translate_indicator(indicator_name)
        end_time = time.time()

        execution_time = end_time - start_time

        assert result is not None
        assert execution_time < 1.0, f"翻訳処理が1秒を超過: {execution_time:.3f}秒"
```

#### 16.5.2 メモリ使用量制約

**必須要件**

- 単一処理: 100MB 以下
- バッチ処理: 500MB 以下
- キャッシュ: 1GB 以下

### 16.6 セキュリティ要件

#### 16.6.1 入力値検証

**バリデーション例**

```python
import re
from typing import Optional
from dataclasses import dataclass

@dataclass
class TranslationRequest:
    """翻訳リクエストのデータクラス"""
    original_text: str
    target_language: str
    source_language: str = "en"

    def __post_init__(self) -> None:
        """バリデーション実行"""
        self._validate_original_text()
        self._validate_language_codes()

    def _validate_original_text(self) -> None:
        """原文のバリデーション"""
        if not self.original_text:
            raise ValidationError("原文が空です")

        if len(self.original_text) > 1000:
            raise ValidationError("原文が1000文字を超過しています")

        # 危険な文字列のチェック
        dangerous_patterns = [
            r"<script.*?>",
            r"javascript:",
            r"on\w+\s*=",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, self.original_text, re.IGNORECASE):
                raise ValidationError(f"危険な文字列が含まれています: {pattern}")

    def _validate_language_codes(self) -> None:
        """言語コードのバリデーション"""
        valid_languages = {"en", "ja", "zh", "ko", "es", "fr", "de"}

        if self.source_language not in valid_languages:
            raise ValidationError(f"無効なソース言語: {self.source_language}")

        if self.target_language not in valid_languages:
            raise ValidationError(f"無効なターゲット言語: {self.target_language}")
```

#### 16.6.2 機密情報管理

**環境変数管理**

```python
import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class TranslationConfig:
    """翻訳設定クラス"""
    api_key: str
    api_url: str
    rate_limit: int
    timeout: int

    @classmethod
    def from_env(cls) -> "TranslationConfig":
        """環境変数から設定を読み込み"""
        api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_TRANSLATE_API_KEYが設定されていません")

        return cls(
            api_key=api_key,
            api_url=os.getenv("GOOGLE_TRANSLATE_API_URL", "https://translation.googleapis.com"),
            rate_limit=int(os.getenv("TRANSLATION_RATE_LIMIT", "100")),
            timeout=int(os.getenv("TRANSLATION_TIMEOUT", "30"))
        )
```

### 16.7 デプロイメント要件

#### 16.7.1 環境別設定

**設定管理**

```python
from enum import Enum
from typing import Dict, Any

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class ConfigManager:
    """設定管理クラス"""

    def __init__(self, environment: Environment) -> None:
        self.environment = environment
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """環境別設定を読み込み"""
        base_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "economic_indicators"
            },
            "cache": {
                "enabled": True,
                "ttl": 3600
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }

        if self.environment == Environment.DEVELOPMENT:
            base_config.update({
                "database": {"host": "localhost"},
                "logging": {"level": "DEBUG"}
            })
        elif self.environment == Environment.PRODUCTION:
            base_config.update({
                "database": {"host": "production-db.example.com"},
                "cache": {"enabled": True, "ttl": 7200},
                "logging": {"level": "WARNING"}
            })

        return base_config

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value
```

#### 16.7.2 ヘルスチェック

**ヘルスチェック実装**

```python
from typing import Dict, Any
import asyncio

class HealthChecker:
    """ヘルスチェッククラス"""

    def __init__(self, services: Dict[str, Any]) -> None:
        self.services = services

    async def check_health(self) -> Dict[str, Any]:
        """全サービスのヘルスチェック"""
        results = {}

        for service_name, service in self.services.items():
            try:
                start_time = asyncio.get_event_loop().time()
                status = await service.health_check()
                end_time = asyncio.get_event_loop().time()

                results[service_name] = {
                    "status": "healthy" if status else "unhealthy",
                    "response_time": end_time - start_time,
                    "timestamp": asyncio.get_event_loop().time()
                }
            except Exception as e:
                results[service_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": asyncio.get_event_loop().time()
                }

        return results

    def is_healthy(self, results: Dict[str, Any]) -> bool:
        """全体のヘルス状態を判定"""
        return all(
            result["status"] == "healthy"
            for result in results.values()
        )
```

### 16.8 監視・ログ要件

#### 16.8.1 メトリクス収集

**メトリクス定義**

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

@dataclass
class TranslationMetrics:
    """翻訳処理のメトリクス"""
    total_requests: int = 0
    successful_translations: int = 0
    failed_translations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    average_response_time: float = 0.0
    last_updated: datetime = datetime.now()

class MetricsCollector:
    """メトリクス収集クラス"""

    def __init__(self) -> None:
        self.metrics: Dict[str, TranslationMetrics] = {}

    def record_translation_request(
        self,
        service_name: str,
        success: bool,
        response_time: float,
        cache_hit: bool
    ) -> None:
        """翻訳リクエストを記録"""
        if service_name not in self.metrics:
            self.metrics[service_name] = TranslationMetrics()

        metrics = self.metrics[service_name]
        metrics.total_requests += 1

        if success:
            metrics.successful_translations += 1
        else:
            metrics.failed_translations += 1

        if cache_hit:
            metrics.cache_hits += 1
        else:
            metrics.cache_misses += 1

        # 平均応答時間の更新
        total_time = metrics.average_response_time * (metrics.total_requests - 1)
        metrics.average_response_time = (total_time + response_time) / metrics.total_requests
        metrics.last_updated = datetime.now()

    def get_metrics(self, service_name: str) -> Optional[TranslationMetrics]:
        """メトリクスを取得"""
        return self.metrics.get(service_name)

    def get_all_metrics(self) -> Dict[str, TranslationMetrics]:
        """全メトリクスを取得"""
        return self.metrics.copy()
```

これらの実装ルールにより、高品質で保守性の高いコードを実現できます。

## 17. 既存 PostgreSQL 統合戦略

### 17.1 統合アプローチ概要

#### 17.1.1 基本方針

**既存システムとの完全統合**

- 既存の PostgreSQL データベース（`economic_calendar`）を活用
- 新規テーブルを既存スキーマに追加
- 既存データとの整合性を保証
- 段階的な機能拡張によるリスク最小化

**統合の利点**

- ✅ **開発コスト削減**: 新規 DB 構築不要
- ✅ **運用効率化**: 既存インフラの活用
- ✅ **データ整合性**: 既存データとの関連性維持
- ✅ **パフォーマンス**: 既存の最適化された DB 設定を継承

#### 17.1.2 既存データベース構成

**現在の PostgreSQL 設定**

```json
{
  "database": {
    "url": "postgresql://economic_user:secure_password@postgres:5432/economic_calendar",
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600
  }
}
```

**既存テーブル構成**

```sql
-- 既存テーブル（そのまま維持）
economic_events          -- 経済イベントデータ
analysis_cache          -- 分析キャッシュ
notification_logs       -- 通知ログ
notification_history    -- 通知履歴
ai_reports             -- AI分析レポート
```

### 17.2 新規テーブル設計

#### 17.2.1 経済指標マスターテーブル

```sql
-- 新規テーブル: 経済指標マスターデータ
CREATE TABLE economic_indicators_master (
    id SERIAL PRIMARY KEY,
    indicator_code VARCHAR(100) UNIQUE NOT NULL,
    english_name TEXT NOT NULL,
    japanese_name TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    frequency VARCHAR(30),
    importance VARCHAR(20),

    -- 基本情報
    description TEXT,
    calculation_method TEXT,
    unit VARCHAR(50),
    base_year INTEGER,

    -- 市場影響
    currency_impact TEXT,
    stock_impact TEXT,
    bond_impact TEXT,
    commodity_impact TEXT,

    -- 投資判断
    good_value_tips TEXT,
    bad_value_tips TEXT,
    surprise_impact TEXT,
    threshold_values JSONB,

    -- 関連情報
    related_indicators TEXT[],
    examples JSONB,
    historical_data JSONB,

    -- メタデータ
    country VARCHAR(50) NOT NULL,
    source VARCHAR(100),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- インデックス
    CONSTRAINT idx_indicator_code UNIQUE (indicator_code),
    CONSTRAINT idx_category_country UNIQUE (category, country)
);

-- インデックス作成
CREATE INDEX idx_economic_indicators_master_category ON economic_indicators_master(category);
CREATE INDEX idx_economic_indicators_master_country ON economic_indicators_master(country);
CREATE INDEX idx_economic_indicators_master_importance ON economic_indicators_master(importance);
CREATE INDEX idx_economic_indicators_master_updated_at ON economic_indicators_master(updated_at);
```

#### 17.2.2 翻訳キャッシュテーブル

```sql
-- 新規テーブル: 翻訳キャッシュ
CREATE TABLE translation_cache (
    id SERIAL PRIMARY KEY,
    original_text TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    language_pair VARCHAR(10) NOT NULL,
    confidence_score DECIMAL(3,2),
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,

    -- 制約
    CONSTRAINT unique_translation UNIQUE(original_text, language_pair),
    CONSTRAINT check_confidence_score CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0)
);

-- インデックス作成
CREATE INDEX idx_translation_cache_language_pair ON translation_cache(language_pair);
CREATE INDEX idx_translation_cache_expires_at ON translation_cache(expires_at);
CREATE INDEX idx_translation_cache_created_at ON translation_cache(created_at);
```

#### 17.2.3 システム設定テーブル

```sql
-- 新規テーブル: システム設定
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX idx_system_settings_key ON system_settings(setting_key);
CREATE INDEX idx_system_settings_updated_at ON system_settings(updated_at);
```

### 17.3 既存テーブルとの関連性

#### 17.3.1 テーブル間の関係

```sql
-- 既存テーブルとの関連性定義
ALTER TABLE economic_events
ADD COLUMN indicator_master_id INTEGER REFERENCES economic_indicators_master(id);

-- インデックス作成
CREATE INDEX idx_economic_events_indicator_master ON economic_events(indicator_master_id);
```

#### 17.3.2 データ整合性の保証

**外部キー制約**

```sql
-- 経済イベントとマスターデータの関連
ALTER TABLE economic_events
ADD CONSTRAINT fk_economic_events_indicator_master
FOREIGN KEY (indicator_master_id)
REFERENCES economic_indicators_master(id)
ON DELETE SET NULL;

-- 翻訳キャッシュの有効期限管理
ALTER TABLE translation_cache
ADD CONSTRAINT check_expires_at_future
CHECK (expires_at > created_at);
```

### 17.4 マイグレーション戦略

#### 17.4.1 段階的マイグレーション

**Phase 1: 新規テーブル作成**

```sql
-- マイグレーション: 001_create_economic_indicators_tables.sql
BEGIN;

-- 1. 経済指標マスターテーブル作成
CREATE TABLE economic_indicators_master (
    -- テーブル定義（上記参照）
);

-- 2. 翻訳キャッシュテーブル作成
CREATE TABLE translation_cache (
    -- テーブル定義（上記参照）
);

-- 3. システム設定テーブル作成
CREATE TABLE system_settings (
    -- テーブル定義（上記参照）
);

-- 4. インデックス作成
-- （上記のインデックス定義）

COMMIT;
```

**Phase 2: 既存テーブル拡張**

```sql
-- マイグレーション: 002_extend_existing_tables.sql
BEGIN;

-- 1. economic_eventsテーブルにindicator_master_idカラム追加
ALTER TABLE economic_events
ADD COLUMN indicator_master_id INTEGER;

-- 2. 外部キー制約追加
ALTER TABLE economic_events
ADD CONSTRAINT fk_economic_events_indicator_master
FOREIGN KEY (indicator_master_id)
REFERENCES economic_indicators_master(id)
ON DELETE SET NULL;

-- 3. インデックス作成
CREATE INDEX idx_economic_events_indicator_master ON economic_events(indicator_master_id);

COMMIT;
```

**Phase 3: データ移行**

```sql
-- マイグレーション: 003_migrate_existing_data.sql
BEGIN;

-- 1. 既存の経済イベントデータをマスターテーブルに関連付け
UPDATE economic_events
SET indicator_master_id = (
    SELECT id
    FROM economic_indicators_master
    WHERE english_name = economic_events.event_name
    LIMIT 1
)
WHERE indicator_master_id IS NULL;

-- 2. 翻訳キャッシュの初期データ投入
INSERT INTO translation_cache (original_text, translated_text, language_pair, confidence_score, source)
VALUES
    ('Consumer Price Index (CPI)', '消費者物価指数', 'en-ja', 1.0, 'manual'),
    ('Gross Domestic Product (GDP)', '国内総生産', 'en-ja', 1.0, 'manual'),
    ('Employment Report', '雇用統計', 'en-ja', 1.0, 'manual');

-- 3. システム設定の初期値設定
INSERT INTO system_settings (setting_key, setting_value, description)
VALUES
    ('translation_cache_ttl', '86400', '翻訳キャッシュの有効期限（秒）'),
    ('translation_quality_threshold', '0.8', '翻訳品質の閾値'),
    ('economic_indicator_sync_enabled', 'true', '経済指標同期の有効化');

COMMIT;
```

#### 17.4.2 ロールバック戦略

**ロールバック手順**

```sql
-- ロールバック: 003_migrate_existing_data.sql
BEGIN;

-- 1. データ移行の取り消し
DELETE FROM system_settings WHERE setting_key IN (
    'translation_cache_ttl',
    'translation_quality_threshold',
    'economic_indicator_sync_enabled'
);

DELETE FROM translation_cache WHERE source = 'manual';

UPDATE economic_events SET indicator_master_id = NULL;

COMMIT;

-- ロールバック: 002_extend_existing_tables.sql
BEGIN;

-- 1. 外部キー制約削除
ALTER TABLE economic_events
DROP CONSTRAINT fk_economic_events_indicator_master;

-- 2. インデックス削除
DROP INDEX idx_economic_events_indicator_master;

-- 3. カラム削除
ALTER TABLE economic_events
DROP COLUMN indicator_master_id;

COMMIT;

-- ロールバック: 001_create_economic_indicators_tables.sql
BEGIN;

-- 1. テーブル削除
DROP TABLE IF EXISTS system_settings;
DROP TABLE IF EXISTS translation_cache;
DROP TABLE IF EXISTS economic_indicators_master;

COMMIT;
```

### 17.5 パフォーマンス最適化

#### 17.5.1 インデックス戦略

**複合インデックス**

```sql
-- 検索パフォーマンス向上のための複合インデックス
CREATE INDEX idx_economic_indicators_master_search
ON economic_indicators_master(category, country, importance);

CREATE INDEX idx_translation_cache_search
ON translation_cache(language_pair, expires_at, confidence_score);

CREATE INDEX idx_economic_events_enhanced
ON economic_events(date_utc, country, importance, indicator_master_id);
```

**部分インデックス**

```sql
-- 有効な翻訳キャッシュのみにインデックス
CREATE INDEX idx_translation_cache_active
ON translation_cache(language_pair, confidence_score)
WHERE expires_at > CURRENT_TIMESTAMP;

-- 高重要度の経済指標のみにインデックス
CREATE INDEX idx_economic_indicators_master_high_importance
ON economic_indicators_master(category, country)
WHERE importance = 'high';
```

#### 17.5.2 クエリ最適化

**効率的な検索クエリ**

```sql
-- 経済指標情報の取得（最適化版）
SELECT
    eim.indicator_code,
    eim.english_name,
    eim.japanese_name,
    eim.category,
    eim.description,
    tc.translated_text as cached_translation
FROM economic_indicators_master eim
LEFT JOIN translation_cache tc
    ON tc.original_text = eim.english_name
    AND tc.language_pair = 'en-ja'
    AND tc.expires_at > CURRENT_TIMESTAMP
WHERE eim.category = $1
    AND eim.country = $2
    AND eim.importance = $3;
```

**バッチ処理の最適化**

```sql
-- 翻訳キャッシュの一括更新
UPDATE translation_cache
SET
    translated_text = $1,
    confidence_score = $2,
    expires_at = CURRENT_TIMESTAMP + INTERVAL '1 day'
WHERE original_text = $2
    AND language_pair = $3;
```

### 17.6 監視・メンテナンス

#### 17.6.1 パフォーマンス監視

**クエリパフォーマンス監視**

```sql
-- スロークエリの特定
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
WHERE mean_time > 100  -- 100ms以上
ORDER BY mean_time DESC
LIMIT 10;
```

**テーブルサイズ監視**

```sql
-- テーブルサイズの確認
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### 17.6.2 定期メンテナンス

**自動メンテナンススクリプト**

```sql
-- 定期メンテナンス（cronで実行）
-- 1. 古い翻訳キャッシュの削除
DELETE FROM translation_cache
WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days';

-- 2. 統計情報の更新
ANALYZE economic_indicators_master;
ANALYZE translation_cache;
ANALYZE system_settings;

-- 3. 不要なインデックスの確認
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0  -- 使用されていないインデックス
ORDER BY schemaname, tablename;
```

### 17.7 セキュリティ対策

#### 17.7.1 アクセス制御

**ロールベースアクセス制御**

```sql
-- 経済指標システム専用ロール作成
CREATE ROLE economic_indicator_user;

-- 権限付与
GRANT SELECT, INSERT, UPDATE ON economic_indicators_master TO economic_indicator_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON translation_cache TO economic_indicator_user;
GRANT SELECT, INSERT, UPDATE ON system_settings TO economic_indicator_user;

-- 既存テーブルへの読み取り権限
GRANT SELECT ON economic_events TO economic_indicator_user;
GRANT SELECT ON analysis_cache TO economic_indicator_user;
```

**行レベルセキュリティ**

```sql
-- 翻訳キャッシュの行レベルセキュリティ
ALTER TABLE translation_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY translation_cache_policy ON translation_cache
    FOR ALL
    TO economic_indicator_user
    USING (expires_at > CURRENT_TIMESTAMP);
```

#### 17.7.2 データ暗号化

**機密データの暗号化**

```sql
-- 機密設定値の暗号化（pgcrypto拡張使用）
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 暗号化された設定値の保存
INSERT INTO system_settings (setting_key, setting_value, description)
VALUES (
    'encrypted_api_key',
    pgp_sym_encrypt('your_api_key_here', 'encryption_key'),
    '暗号化されたAPIキー'
);

-- 暗号化された設定値の取得
SELECT
    setting_key,
    pgp_sym_decrypt(setting_value::bytea, 'encryption_key') as decrypted_value
FROM system_settings
WHERE setting_key = 'encrypted_api_key';
```

### 17.8 バックアップ・復旧

#### 17.8.1 バックアップ戦略

**差分バックアップ**

```bash
#!/bin/bash
# 経済指標システム専用バックアップスクリプト

# 日次差分バックアップ
pg_dump -h postgres -U economic_user -d economic_calendar \
    --table=economic_indicators_master \
    --table=translation_cache \
    --table=system_settings \
    --data-only \
    --format=custom \
    --file=/app/data/backups/economic_indicators_$(date +%Y%m%d).backup

# 週次完全バックアップ
pg_dump -h postgres -U economic_user -d economic_calendar \
    --table=economic_indicators_master \
    --table=translation_cache \
    --table=system_settings \
    --format=custom \
    --file=/app/data/backups/economic_indicators_full_$(date +%Y%m%d).backup
```

**復旧手順**

```bash
#!/bin/bash
# 経済指標システム復旧スクリプト

# 特定テーブルの復旧
pg_restore -h postgres -U economic_user -d economic_calendar \
    --table=economic_indicators_master \
    --table=translation_cache \
    --table=system_settings \
    --clean \
    --if-exists \
    /app/data/backups/economic_indicators_20250824.backup
```

#### 17.8.2 データ整合性チェック

**整合性チェックスクリプト**

```sql
-- データ整合性チェック
-- 1. 外部キー制約の確認
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name IN ('economic_events', 'translation_cache');

-- 2. 孤立データの確認
SELECT COUNT(*) as orphaned_events
FROM economic_events ee
LEFT JOIN economic_indicators_master eim ON ee.indicator_master_id = eim.id
WHERE ee.indicator_master_id IS NOT NULL
    AND eim.id IS NULL;

-- 3. 重複データの確認
SELECT english_name, COUNT(*) as duplicate_count
FROM economic_indicators_master
GROUP BY english_name
HAVING COUNT(*) > 1;
```

この統合戦略により、既存の PostgreSQL データベースを最大限活用しながら、経済指標日本語化システムを安全かつ効率的に実装できます。

## 18. 並行開発・移行戦略

### 18.1 並行開発のメリット

#### 18.1.1 リスク最小化

- **既存システムへの影響なし**: 稼働中のシステムを変更しない
- **段階的移行**: 問題が発生した場合のロールバックが容易
- **品質保証**: 新システムは制約準拠で高品質に構築

#### 18.1.2 開発効率

- **並行作業**: 既存システムの保守と新システム開発を並行
- **学習効果**: 既存システムの分析から得られる知見の活用
- **品質向上**: 制約準拠による高品質コードの実現

### 18.2 移行戦略

#### 18.2.1 段階的移行計画

**Week 1-8: 新システム構築**

- 既存システム: 稼働継続
- 新システム: 並行開発・テスト

**Week 9: 並行稼働開始**

- 既存システム: 100%稼働
- 新システム: 10%稼働開始

**Week 10: 段階的移行**

- Week 1: 10% → 30%
- Week 2: 30% → 50%
- Week 3: 50% → 80%
- Week 4: 80% → 100%

#### 18.2.2 移行監視・制御

**監視項目**

- 機能比較: 既存 vs 新システムの出力比較
- パフォーマンス: 応答時間・処理時間の比較
- エラー率: エラー発生率の監視
- ユーザー満足度: 配信品質の評価

**ロールバック戦略**

- 即座ロールバック: 重大な問題発生時
- 段階的ロールバック: 軽微な問題発生時
- 部分ロールバック: 特定機能のみロールバック

### 18.3 制約準拠の重要性

#### 18.3.1 ファイルサイズ制約 (400 行以内)

**メリット**

- 可読性向上: ファイルが短く理解しやすい
- 保守性向上: 変更・修正が容易
- テスト容易性: 単体テストが書きやすい
- 責任分離: 単一責任原則の実現

**実現方法**

- ドメイン駆動設計 (DDD) の採用
- 依存性注入 (DI) の実装
- インターフェース分離原則の適用
- ファクトリーパターンの活用

#### 18.3.2 品質制約

**テストカバレッジ 95%以上**

- 単体テスト: 各クラス・メソッドのテスト
- 統合テスト: コンポーネント間の連携テスト
- E2E テスト: エンドツーエンドの動作テスト

**Linter エラー 0 件**

- コード品質の保証
- 一貫性のあるコーディングスタイル
- 潜在的なバグの早期発見

## 19. 次のステップ

### 19.1 短期目標（Week 1-3）

- [ ] 新システム基盤構築完了
- [ ] データベース・エンティティ実装
- [ ] 基本サービス実装
- [ ] 単体テスト実装

### 19.2 中期目標（Week 4-8）

- [ ] 新機能実装完了
- [ ] 統合テスト実施
- [ ] 制約準拠確認
- [ ] 品質チェック完了

### 19.3 長期目標（Week 9-10）

- [ ] 段階的移行完了
- [ ] 既存システム停止
- [ ] 新システム完全稼働
- [ ] 移行完了レポート作成

## 20. まとめ

この開発仕様書は、経済指標の日本語化・詳細情報拡張システムの並行開発・段階的移行戦略を提供します。既存システムを維持しながら、制約準拠の高品質な新システムを構築し、安全に移行する包括的な計画です。

### 20.1 主要なポイント

1. **並行開発**: リスクを最小化する並行開発アプローチ
2. **制約準拠**: 400 行以内の高品質コード
3. **段階的移行**: 安全な移行戦略
4. **品質重視**: テスト駆動開発と継続的品質管理
5. **保守性**: 明確な責任分離とドキュメント化

### 20.2 成功指標

**技術指標**

- ファイルサイズ: 全ファイル 400 行以内
- テストカバレッジ: 95%以上
- コード品質: Linter エラー 0 件
- パフォーマンス: 既存同等以上

**運用指標**

- 移行成功率: 100%
- サービス継続率: 99.9%以上
- 機能向上度: 50%以上
- 保守工数削減: 30%以上

### 20.3 今後の展望

この並行開発・段階的移行戦略により、既存システムの安定性を保ちながら、高品質な新システムを構築できます。制約準拠による保守性の向上と、段階的移行によるリスク最小化により、長期的なシステム発展が期待されます。
