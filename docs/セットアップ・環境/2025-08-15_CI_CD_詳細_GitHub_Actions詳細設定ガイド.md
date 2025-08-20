**旧ファイル名**: `GITHUB_ACTIONS_DETAILED_SETUP.md`  

# 🔧 GitHub Actions 詳細設定ガイド

## 📋 設定手順詳細

### 1️⃣ GitHub Repository Secrets 設定

#### 🔗 アクセス方法

1. **GitHub リポジトリページにアクセス**

   ```
   https://github.com/m37335/exchangeApp
   ```

2. **Settings タブをクリック**

   - リポジトリページ上部のタブから「Settings」を選択

3. **Secrets and variables → Actions を選択**
   - 左サイドバーから「Secrets and variables」を展開
   - 「Actions」をクリック

#### 🔑 必要な Secrets 設定

**🤖 OPENAI_API_KEY の設定**:

```
1. 「New repository secret」ボタンをクリック
2. Name: OPENAI_API_KEY
3. Secret: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
4. 「Add secret」をクリック
```

**📢 DISCORD_WEBHOOK_URL の設定**:

```
1. 「New repository secret」ボタンをクリック
2. Name: DISCORD_WEBHOOK_URL
3. Secret: https://discord.com/api/webhooks/xxxxxxxx/xxxxxxxx
4. 「Add secret」をクリック
```

**📊 YAHOO_FINANCE_API_KEY の設定（オプション）**:

```
1. 「New repository secret」ボタンをクリック
2. Name: YAHOO_FINANCE_API_KEY
3. Secret: your_yahoo_finance_api_key（なければ空白可）
4. 「Add secret」をクリック
```

#### ✅ 設定確認

```
- Secrets ページに3つの項目が表示される
- 値は「***」で隠される（正常）
- 「Last updated」が現在時刻付近
```

---

### 2️⃣ GitHub Actions 有効化

#### 🚀 Actions タブにアクセス

1. **リポジトリページに戻る**

   - 「Code」タブをクリック

2. **Actions タブをクリック**
   - リポジトリページ上部の「Actions」タブを選択

#### 📋 初回有効化手順

**新規リポジトリの場合**:

```
1. 「I understand my workflows, go ahead and enable them」をクリック
2. ワークフロー一覧が表示される
3. 「🤖 Integrated AI Currency Analysis - 24/7 Cron」が表示される
```

**既存 Actions がある場合**:

```
1. 直接ワークフロー一覧が表示される
2. 最新のワークフローファイルが認識される
```

#### 🔍 ワークフロー確認

```
✅ 表示されるべき項目:
- 🤖 Integrated AI Currency Analysis - 24/7 Cron
- Status: 有効（緑色のドット）
- Last run: まだ実行されていない
```

---

### 3️⃣ 手動テスト実行

#### 🧪 手動実行手順

1. **ワークフローを選択**

   ```
   「🤖 Integrated AI Currency Analysis - 24/7 Cron」をクリック
   ```

2. **Run workflow ボタンをクリック**

   ```
   右上の「Run workflow」ボタンを押す
   ```

3. **実行設定選択**
   ```
   - Branch: main（デフォルト）
   - 「Run workflow」（緑ボタン）をクリック
   ```

#### 📊 実行状況確認

**実行中の表示**:

```
🟡 Running - 「🤖 Integrated AI Currency Analysis」
📝 ジョブ詳細:
- 🎯 統合AI相関分析 (running/completed)
- 📈 個別テクニカル分析 (pending/running/completed)
- 🔍 System Health Check (running/completed)
```

**成功時の表示**:

```
✅ Completed - 緑色のチェックマーク
⏱️ 実行時間: 約3-5分
📊 ログ: 各ステップの詳細ログ確認可能
```

**失敗時の表示**:

```
❌ Failed - 赤色のX マーク
🔍 原因確認: ログクリックでエラー詳細表示
🔧 修正必要: Secrets設定やコードエラー
```

#### 📱 実行ログ確認方法

1. **実行結果をクリック**

   ```
   ワークフロー実行履歴から特定の実行をクリック
   ```

2. **ジョブ詳細を確認**

   ```
   - 🎯 統合AI相関分析 → ログ詳細
   - 📈 個別テクニカル分析 → ログ詳細
   - 🔍 System Health Check → ログ詳細
   ```

3. **ステップ別ログ確認**
   ```
   各ステップをクリックして詳細ログ表示:
   - 📥 Checkout Repository
   - 🐍 Setup Python
   - 📦 Install Dependencies
   - 🔑 Setup Environment Variables
   - 🤖 Run Integrated AI Analysis
   ```

---

### 4️⃣ 動作確認・監視設定

#### 🔔 Discord 配信確認

**成功時の Discord メッセージ例**:

```
🎯 統合AI相関分析レポート
📊 分析時刻: 2025年8月10日 14:00 JST

◆ USD/JPY メイン通貨ペア
現在レート: 147.6930
変動: +0.41%

【相関分析】EUR/USD下落がUSD強化を示し...
【統合シナリオ】
・エントリー価格: 147.7500
・利確目標: 148.2000（50pips利益）
・損切り価格: 147.4500（30pips損失）

⚡ Powered by Exchange Analytics v4.0
```

#### 📅 スケジュール確認

**自動実行タイミング**:

```
🎯 統合AI相関分析:
- 次回実行: 16:00 JST (平日)
- 実行間隔: 2時間ごと
- 実行時刻: 8,10,12,14,16,18,20,22,0,2時

📈 個別テクニカル分析:
- 次回実行: 16:00 JST (平日)
- 実行間隔: 4時間ごと
- 実行時刻: 8,12,16,20,0時
```

#### 📊 監視ダッシュボード設定

**GitHub Actions 監視項目**:

```
1. 実行成功率確認
   - Actions タブで成功/失敗率チェック
   - 連続失敗時は原因調査

2. 実行時間監視
   - 通常実行時間: 3-5分
   - 10分超過時は timeout 確認

3. 使用時間確認
   - Settings → Billing → Actions minutes
   - 月間使用量: 880分目標（2000分以内）

4. ログ確認
   - エラーログの定期確認
   - Discord配信失敗時の原因調査
```

---

## 🚨 トラブルシューティング詳細

### ❌ よくある問題と解決策

#### **問題 1: Secrets 認識エラー**

```
エラー: OPENAI_API_KEY not found
原因: Secrets設定ミス

🔧 解決手順:
1. Settings → Secrets and variables → Actions
2. Secret名のスペルチェック（OPENAI_API_KEY）
3. 値の再設定（先頭・末尾のスペース削除）
4. Repository権限確認
```

#### **問題 2: Python 依存関係エラー**

```
エラー: ModuleNotFoundError: No module named 'xxx'
原因: requirements.txt不備

🔧 解決手順:
1. requirements/base.txt確認
2. 不足パッケージ追加
3. コミット・プッシュ
4. 再実行
```

#### **問題 3: Discord 配信失敗**

```
エラー: Discord webhook failed
原因: Webhook URL無効

🔧 解決手順:
1. Discord Webhook URL再生成
2. URLの有効性テスト（curl）
3. Secrets再設定
4. 手動テスト実行
```

#### **問題 4: タイムアウトエラー**

```
エラー: timeout 180s exceeded
原因: API応答遅延・ネットワーク問題

🔧 解決手順:
1. タイムアウト時間延長（240s）
2. API接続確認
3. リトライ機構確認
4. エラーハンドリング強化
```

---

## 📱 実践チェックリスト

### ✅ 設定完了確認

```
□ GitHub Repository Secrets 3項目設定完了
□ Actions タブでワークフロー表示確認
□ 手動実行テスト成功
□ Discord にテスト配信成功
□ ログダウンロード・確認完了
```

### 📊 運用開始確認

```
□ 平日自動実行スケジュール確認
□ 実行時間・成功率の初期ベースライン設定
□ Discord チャンネルでの定期配信確認
□ エラー時の通知・対応フロー確認
□ 月間使用時間の監視体制確立
```

---

**🎯 これで GitHub Actions による 24 時間自動稼働が完全に設定されます！**

**PC スリープに関係なく、クラウド上で確実に実行される高品質 AI 分析システムの完成です！** 🚀🌟
