#!/usr/bin/env python3
"""
モックサーバー起動スクリプト
"""

import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def main():
    """モックサーバーを起動します"""
    print("=" * 60)
    print("API Table Mock Server を起動します")
    print("=" * 60)
    
    # 依存関係の確認
    try:
        import fastapi
        import uvicorn
        print("✓ 依存関係の確認完了")
    except ImportError as e:
        print(f"✗ 依存関係のエラー: {e}")
        print("依存関係をインストールします...")
        subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn[standard]"])
        print("✓ 依存関係をインストールしました")
    
    # サーバー起動
    print("\nサーバーを起動しています...")
    print("サーバーURL: http://localhost:8001")
    print("APIドキュメント: http://localhost:8001/docs")
    print("\n利用可能なエンドポイント:")
    print("  GET /applications/type-a     - タイプAの申請データ")
    print("  GET /applications/type-b     - タイプBの申請データ")
    print("  GET /applications/type-c     - タイプCの申請データ")
    print("  GET /health                  - ヘルスチェック")
    print("\n停止するには Ctrl+C を押してください")
    print("=" * 60)
    
    # ブラウザでドキュメントを開く（オプション）
    try:
        time.sleep(2)
        webbrowser.open("http://localhost:8001/docs")
        print("ブラウザでAPIドキュメントを開きました")
    except:
        print("ブラウザの自動起動に失敗しました。手動で http://localhost:8001/docs にアクセスしてください")
    
    # サーバー起動
    try:
        import uvicorn
        uvicorn.run(
            "src.mock_server.main:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nサーバーを停止します")
    except Exception as e:
        print(f"サーバー起動エラー: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
