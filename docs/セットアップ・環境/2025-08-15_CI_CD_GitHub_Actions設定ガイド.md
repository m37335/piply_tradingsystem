**旧ファイル名**: `GITHUB_ACTIONS_SETUP.md`  

# 🚀 GitHub Actions 24 時間稼働設定ガイド

## 📋 概要

GitHub Actions を使用して Exchange Analytics System を**24 時間自動実行**する設定ガイドです。PC のスリープに関係なく、クラウド上で自動実行されます。

## 🎯 設定内容

### 自動実行スケジュール

**統合 AI 相関分析** (`integrated_ai_discord.py`):

- **実行時刻**: 8,10,12,14,16,18,20,22,0,2 時（2 時間間隔）
- **実行日**: 平日（月〜金）
- **実行回数**: 10 回/日

**個別テクニカル分析** (`real_ai_discord_v2.py`):

- **実行時刻**: 8,12,16,20,0 時（4 時間間隔）
- **実行日**: 平日（月〜金）
- **実行回数**: 5 回/日

## ⚙️ 設定手順

### 1. GitHub Repository Secrets 設定

GitHub リポジトリの「Settings」→「Secrets and variables」→「Actions」で以下を設定：

```
OPENAI_API_KEY = your_openai_api_key
DISCORD_WEBHOOK_URL = your_discord_webhook_url
YAHOO_FINANCE_API_KEY = (optional)
```

### 2. ワークフローファイル確認

`.github/workflows/integrated-ai-cron.yml`が正しく配置されていることを確認。

### 3. Actions 有効化

1. GitHub リポジトリの「Actions」タブにアクセス
2. 「I understand my workflows, go ahead and enable them」をクリック
3. ワークフローが表示されることを確認

### 4. 手動テスト実行

1. 「Actions」タブ → 「Integrated AI Currency Analysis」選択
2. 「Run workflow」ボタンをクリック
3. 実行結果を確認

## 🔍 監視・確認方法

### 実行状況確認

```
1. GitHubリポジトリ → Actions タブ
2. 最新の実行結果を確認
3. ログダウンロード可能（7日間保存）
```

### Discord 配信確認

```
1. Discord Webhookチャンネル確認
2. 定期的なレポート配信を確認
3. エラー時はActionsログ確認
```

## 📊 制限・注意事項

### GitHub Actions 制限

- **無料枠**: 月 2000 分
- **実行時間**: 最大 6 時間/job
- **同時実行**: 最大 20job

### 使用時間計算

```
統合分析: 3分 × 10回/日 × 22営業日 = 660分/月
個別分析: 2分 × 5回/日 × 22営業日 = 220分/月
合計使用時間: 約880分/月 (無料枠内)
```

## 🛠️ トラブルシューティング

### よくある問題

**1. Secrets 未設定**

```
エラー: OPENAI_API_KEY not found
解決: Repository Settings → Secrets設定確認
```

**2. Discord 配信失敗**

```
エラー: Discord webhook failed
解決: DISCORD_WEBHOOK_URL確認・有効性テスト
```

**3. 依存関係エラー**

```
エラー: Module not found
解決: requirements/base.txt確認・依存関係追加
```

### デバッグ方法

```bash
# 手動実行でのテスト
1. Actions → Run workflow (manual)
2. ログダウンロード・詳細確認
3. エラー原因特定・修正
```

## 🎯 メリット・デメリット

### ✅ メリット

- **完全無料**: 月 2000 分以内
- **24 時間稼働**: PC スリープ無関係
- **管理不要**: 自動実行・監視
- **ログ保存**: 7 日間自動保存
- **手動実行**: 必要時に即座実行可能

### ❌ デメリット

- **実行時間制限**: 月 2000 分
- **遅延可能性**: GitHub 混雑時
- **機能制限**: 一部システム機能制限

## 🚀 高度な設定

### 複数時間帯対応

```yaml
# アジア・欧州・米国市場対応
- cron: "0 0,2,8,10,12,14,16,18,20,22 * * 1-5"
```

### エラー通知

```yaml
# Discord通知設定
- name: Send Discord Notification
  if: failure()
  run: |
    curl -X POST ${{ secrets.DISCORD_WEBHOOK_URL }} \
    -H 'Content-Type: application/json' \
    -d '{"content": "❌ GitHub Actions実行失敗"}'
```

### 条件分岐実行

```yaml
# 市場開始時間での条件分岐
- name: Market Hours Check
  run: |
    hour=$(date +%H)
    if [ $hour -ge 8 ] && [ $hour -le 23 ]; then
      echo "Market hours: Running full analysis"
    else
      echo "Off hours: Running light monitoring"
    fi
```

## 📞 サポート

### 設定支援

GitHub Actions 設定でお困りの場合：

1. **Repository 確認**: .github/workflows/ディレクトリ
2. **Secrets 確認**: 必要な環境変数設定
3. **ログ確認**: 実行結果・エラー詳細
4. **手動テスト**: workflow_dispatch 実行

### 追加リソース

- [GitHub Actions 公式ドキュメント](https://docs.github.com/en/actions)
- [Cron 式ジェネレーター](https://crontab.guru/)
- [YAML 文法チェック](https://www.yamllint.com/)

---

**🌟 GitHub Actions 設定で 24 時間自動稼働を実現！**

**PC スリープ関係なし・完全無料・高品質 AI 分析を継続配信**
