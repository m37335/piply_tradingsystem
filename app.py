from flask import Flask, jsonify, request, abort
from dotenv import load_dotenv
import os
import hashlib
import hmac
import subprocess
import threading
from github import Github
import logging

# 環境変数を読み込み
load_dotenv()

# Flaskアプリケーションを作成
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GitHub設定
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')
GITHUB_REPO_OWNER = os.getenv('GITHUB_REPO_OWNER')
GITHUB_REPO_NAME = os.getenv('GITHUB_REPO_NAME')

# GitHub APIクライアント
github_client = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None


def verify_github_webhook(request_data, signature):
    """GitHubウェブフックの署名を検証"""
    if not GITHUB_WEBHOOK_SECRET:
        logger.warning("GitHub webhook secret not configured")
        return False

    expected_signature = 'sha256=' + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode('utf-8'),
        request_data,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


def perform_git_update():
    """Git pullとアプリケーション再起動を実行"""
    try:
        logger.info("Starting git update process...")

        # Git pullを実行
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            cwd='/app',
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            logger.info("Git pull successful")
            logger.info(f"Git output: {result.stdout}")

            # 依存関係の更新
            subprocess.run(
                ['pip', 'install', '-r', 'requirements.txt'],
                cwd='/app',
                capture_output=True,
                text=True,
                timeout=120
            )

            logger.info("Dependencies updated successfully")
            return True
        else:
            logger.error(f"Git pull failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("Git update process timed out")
        return False
    except Exception as e:
        logger.error(f"Error during git update: {str(e)}")
        return False


def get_repository_info():
    """GitHub APIを使用してリポジトリ情報を取得"""
    if not github_client or not GITHUB_REPO_OWNER or not GITHUB_REPO_NAME:
        return None

    try:
        repo_path = f"{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"
        repo = github_client.get_repo(repo_path)
        return {
            'name': repo.name,
            'full_name': repo.full_name,
            'description': repo.description,
            'last_updated': (repo.updated_at.isoformat()
                           if repo.updated_at else None),
            'default_branch': repo.default_branch,
            'commits_count': repo.get_commits().totalCount
        }
    except Exception as e:
        logger.error(f"Error getting repository info: {str(e)}")
        return None


@app.route('/')
def hello():
    """基本的なヘルスチェックエンドポイント"""
    return jsonify({
        'message': 'Hello from Exchanging App!',
        'status': 'healthy',
        'environment': os.getenv('FLASK_ENV', 'production')
    })


@app.route('/api/health')
def health_check():
    """詳細なヘルスチェックエンドポイント"""
    return jsonify({
        'status': 'ok',
        'service': 'exchanging-app',
        'version': '1.0.0'
    })


@app.route('/api/github/webhook', methods=['POST'])
def github_webhook():
    """GitHubウェブフックを受信して自動更新を実行"""
    try:
        # 署名を検証
        signature = request.headers.get('X-Hub-Signature-256')
        if not signature:
            logger.warning("Missing webhook signature")
            abort(400, 'Missing signature')

        if not verify_github_webhook(request.data, signature):
            logger.warning("Invalid webhook signature")
            abort(401, 'Invalid signature')

        # ペイロードを解析
        payload = request.get_json()
        if not payload:
            abort(400, 'Invalid JSON payload')

        event_type = request.headers.get('X-GitHub-Event')
        logger.info(f"Received GitHub webhook event: {event_type}")

        # pushイベントのみ処理
        if event_type == 'push':
            ref = payload.get('ref')
            if ref == 'refs/heads/main':  # mainブランチへのpushのみ
                logger.info("Processing push to main branch")

                # バックグラウンドで更新を実行
                threading.Thread(target=perform_git_update).start()

                return jsonify({
                    'status': 'accepted',
                    'message': 'Update process started',
                    'commit': payload.get('head_commit', {}).get('id')
                })
            else:
                logger.info(f"Ignoring push to branch: {ref}")
                return jsonify({
                    'status': 'ignored',
                    'reason': 'Not main branch'
                })
        else:
            logger.info(f"Ignoring event type: {event_type}")
            return jsonify({
                'status': 'ignored',
                'reason': 'Not a push event'
            })
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/github/info')
def github_info():
    """GitHub リポジトリ情報を取得"""
    try:
        repo_info = get_repository_info()
        if repo_info:
            return jsonify({
                'status': 'ok',
                'repository': repo_info,
                'configured': True
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'GitHub API not configured or repository not found',
                'configured': False
            }), 503
    except Exception as e:
        logger.error(f"Error getting GitHub info: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/github/update', methods=['POST'])
def manual_update():
    """手動でGit更新を実行"""
    try:
        logger.info("Manual update requested")

        # バックグラウンドで更新を実行
        threading.Thread(target=perform_git_update).start()

        return jsonify({
            'status': 'accepted',
            'message': 'Manual update process started'
        })

    except Exception as e:
        logger.error(f"Error starting manual update: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
