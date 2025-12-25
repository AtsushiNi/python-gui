"""
ロギングシステム
INFOレベルまでのログを出力します。
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "api_table_viewer",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    ロガーを設定します。

    Args:
        name: ロガー名
        level: ログレベル（デフォルト: INFO）
        log_file: ログファイルのパス（指定しない場合はコンソールのみ）

    Returns:
        設定済みのロガー
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 既存のハンドラーをクリア
    logger.handlers.clear()

    # フォーマッターの設定
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラー（指定がある場合）
    if log_file:
        # ログディレクトリを作成
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# デフォルトロガー
logger = setup_logger()
