"""
API Table Viewer - メインエントリーポイント
"""

import sys
import os
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# PySide6のインポート
from PySide6.QtWidgets import QApplication

# プロジェクトモジュールのインポート
from src.gui.main_window import MainWindow
from src.logger import logger


def main() -> None:
    """アプリケーションのメインエントリーポイント"""
    logger.info("API Table Viewer を起動します")

    try:
        # QApplicationの作成
        app = QApplication(sys.argv)
        app.setApplicationName("API Table Viewer")
        app.setOrganizationName("API Table Viewer")

        # メインウィンドウの作成と表示
        window = MainWindow()
        window.show()

        logger.info("アプリケーションの起動が完了しました")

        # イベントループの開始
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"アプリケーションの起動に失敗しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
