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

# requirements.txtがある場合は依存関係をインストール
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# アプリケーションコードをコピー
COPY . .

# ポート8000を公開（FlaskやFastAPI用）
EXPOSE 8000

# デフォルトコマンド（開発時はdocker-composeでオーバーライド）
CMD ["python", "app.py"]
