# Python 3.11をベースイメージとして使用
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージを更新し、必要なツールをインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    git \
    vim \
    nano \
    htop \
    procps \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Pythonの出力をバッファリングしない
ENV PYTHONUNBUFFERED=1

# pip を最新版にアップグレード
RUN pip install --upgrade pip

# Python 依存関係
COPY requirements/production.txt .
RUN pip install --no-cache-dir -r production.txt

# アプリケーションコードをコピー
COPY . .

# ポート8000を公開（FlaskやFastAPI用）
EXPOSE 8000

# 非rootユーザーで実行
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# デフォルトコマンド（開発時はdocker-composeでオーバーライド）
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "src.presentation.api.app:create_app()"]
