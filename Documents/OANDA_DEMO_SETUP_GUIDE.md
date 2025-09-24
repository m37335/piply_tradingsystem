# OANDAデモ講座登録とStream API設定ガイド

## 📋 目次

1. [デモ講座の登録](#1-デモ講座の登録)
2. [APIアクセストークンの取得](#2-apiアクセストークンの取得)
3. [Stream APIの確認](#3-stream-apiの確認)
4. [環境変数の設定](#4-環境変数の設定)
5. [動作確認](#5-動作確認)

---

## 1. デモ講座の登録

### 1.1 新規ユーザーの場合

1. **デモ講座申込ページにアクセス**
   - [OANDA証券 無料デモ講座の開設](https://www.oanda.jp/trade/web/openAccount/mailAddressCheck?type=Demo)

2. **メールアドレス入力**
   - メールアドレスを入力して「メールを送信する」をクリック

3. **メール確認**
   - 届いたメール内のリンクをクリック
   - 利用規約の確認と必要情報の入力

4. **登録完了**
   - 「無料デモ講座を開設する」をクリック
   - ログイン情報が記載されたメールが届く

5. **サブアカウント作成**
   - [マイページ](https://www.oanda.jp/trade/web/fxTradeLogin.do)にログイン
   - サブアカウントを作成

### 1.2 既存ユーザーの場合

1. **マイページにログイン**
   - [マイページ](https://www.oanda.jp/trade/web/fxTradeLogin.do)にログイン

2. **デモ講座申込**
   - 右上の「デモ講座の新規お申し込み」をクリック
   - 申込を行う

3. **サブアカウント作成**
   - デモのマイページでサブアカウントを作成

---

## 2. APIアクセストークンの取得

### 2.1 パーソナルアクセストークンの発行

1. **マイページにログイン**
   - [マイページ](https://www.oanda.jp/trade/web/fxTradeLogin.do)にログイン

2. **APIアクセスの管理**
   - 「APIアクセスの管理」または「API設定」にアクセス

3. **トークン発行**
   - 「パーソナルアクセストークンを発行」をクリック
   - トークン名を入力（例：「Trading System」）
   - 発行ボタンをクリック

4. **トークン保存**
   - 発行されたトークンを安全な場所に保存
   - **重要**: トークンは一度しか表示されません

### 2.2 アカウントIDの確認

1. **アカウント情報の確認**
   - マイページの「アカウント情報」でアカウントIDを確認
   - 形式例：`101-001-123456-001`

---

## 3. Stream APIの確認

### 3.1 APIエンドポイント

- **デモ環境（fxTrade Practice）**:
  - REST API: `https://api-fxpractice.oanda.com`
  - Streaming API: `https://stream-fxpractice.oanda.com`

- **本番環境（fxTrade）**:
  - REST API: `https://api-fxtrade.oanda.com`
  - Streaming API: `https://stream-fxtrade.oanda.com`

### 3.2 価格ストリームのエンドポイント

```
GET /v3/accounts/{accountID}/pricing/stream
```

**パラメータ**:
- `instruments`: 通貨ペア（例：`USD_JPY`）
- `snapshot`: スナップショット取得（`true`/`false`）

**例**:
```
https://stream-fxpractice.oanda.com/v3/accounts/101-001-123456-001/pricing/stream?instruments=USD_JPY&snapshot=true
```

### 3.3 認証ヘッダー

```
Authorization: Bearer YOUR_PERSONAL_ACCESS_TOKEN
Content-Type: application/json
```

---

## 4. 環境変数の設定

### 4.1 .envファイルの更新

`/app/.env`ファイルに以下の設定を追加：

```bash
# OANDA設定
OANDA_ACCOUNT_ID=101-001-123456-001
OANDA_ACCESS_TOKEN=your_personal_access_token_here
OANDA_ENVIRONMENT=practice
```

### 4.2 設定値の説明

- `OANDA_ACCOUNT_ID`: デモ講座のアカウントID
- `OANDA_ACCESS_TOKEN`: パーソナルアクセストークン
- `OANDA_ENVIRONMENT`: `practice`（デモ環境）または `live`（本番環境）

---

## 5. 動作確認

### 5.1 基本的な接続テスト

```bash
cd /app
python -c "
import asyncio
import aiohttp
import ssl
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_oanda_connection():
    account_id = os.getenv('OANDA_ACCOUNT_ID')
    access_token = os.getenv('OANDA_ACCESS_TOKEN')
    
    if not account_id or not access_token:
        print('❌ OANDA設定が不完全です')
        print('   OANDA_ACCOUNT_ID:', account_id)
        print('   OANDA_ACCESS_TOKEN:', '設定済み' if access_token else '未設定')
        return
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    timeout = aiohttp.ClientTimeout(total=10, connect=5)
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    ) as session:
        try:
            url = f'https://stream-fxpractice.oanda.com/v3/accounts/{account_id}/pricing/stream'
            params = {'instruments': 'USD_JPY', 'snapshot': 'true'}
            
            print(f'📡 接続テスト: {url}')
            
            async with session.get(url, params=params) as response:
                print(f'📊 ステータス: {response.status}')
                
                if response.status == 200:
                    print('✅ 接続成功！')
                    count = 0
                    async for line in response.content:
                        if line and count < 2:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                print(f'📈 データ: {json.dumps(data, indent=2, ensure_ascii=False)}')
                                count += 1
                            except json.JSONDecodeError:
                                pass
                        elif count >= 2:
                            break
                else:
                    error_text = await response.text()
                    print(f'❌ 接続失敗: {error_text}')
                    
        except Exception as e:
            print(f'❌ エラー: {e}')

asyncio.run(test_oanda_connection())
"
```

### 5.2 システム統合テスト

```bash
cd /app
python -c "
import asyncio
import sys
sys.path.append('/app')

async def test():
    from modules.llm_analysis.providers.oanda_rest_client import OANDARestClient
    
    client = OANDARestClient()
    
    try:
        await client.initialize()
        
        # アカウント情報の取得
        account_info = await client.get_account_info()
        if account_info:
            print(f'✅ アカウント情報取得成功:')
            print(f'   アカウントID: {account_info.account_id}')
            print(f'   残高: {account_info.balance}')
            print(f'   通貨: {account_info.currency}')
        else:
            print('❌ アカウント情報取得失敗')
        
        # 現在価格の取得
        prices = await client.get_current_prices(['USD_JPY'])
        if prices:
            usd_jpy = prices.get('USD_JPY', {})
            print(f'✅ 現在価格取得成功:')
            print(f'   USD/JPY: {usd_jpy.get(\"mid\", 0):.5f}')
        else:
            print('❌ 現在価格取得失敗')
            
    except Exception as e:
        print(f'❌ テストエラー: {e}')
    finally:
        await client.close()

asyncio.run(test())
"
```

---

## 6. トラブルシューティング

### 6.1 よくあるエラー

**401 Unauthorized**:
- アクセストークンが正しくない
- アカウントIDが間違っている
- トークンの有効期限が切れている

**403 Forbidden**:
- アカウントにAPIアクセス権限がない
- デモ講座がアクティブでない

**404 Not Found**:
- アカウントIDが存在しない
- エンドポイントURLが間違っている

### 6.2 確認事項

1. **アカウント状態**: デモ講座がアクティブか
2. **API権限**: パーソナルアクセストークンが発行されているか
3. **ネットワーク**: ファイアウォールでAPIエンドポイントがブロックされていないか
4. **SSL証明書**: 開発環境でのSSL証明書エラー

---

## 7. 次のステップ

OANDAの設定が完了したら、以下の機能をテストできます：

1. **リアルタイム価格取得**: Stream APIによる価格データの取得
2. **取引実行**: REST APIによる注文の実行
3. **アカウント管理**: 残高・ポジションの確認
4. **システム統合**: ルールベース判定エンジンとの連携

---

**注意**: このガイドはデモ環境用です。本番環境で使用する場合は、適切なリスク管理を行ってください。
