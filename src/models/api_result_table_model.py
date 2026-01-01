"""
テーブルデータモデル
PySide6のQAbstractTableModelを使用してAPI結果を表示します
"""

from typing import Any, Dict, List, Optional
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QColor

from src.logger import logger


class ApiResultTableModel(QAbstractTableModel):
    """API結果を表示するテーブルモデル"""

    # 列定義
    COLUMNS = [
        ("api_name", "API名"),
        ("status", "ステータス"),
        ("status_code", "ステータスコード"),
        ("response_time", "応答時間(秒)"),
        ("url", "URL"),
        ("timestamp", "実行時刻"),
        ("error", "エラー"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.results: List[Dict[str, Any]] = []
        self.column_keys = [col[0] for col in self.COLUMNS]
        self.column_names = [col[1] for col in self.COLUMNS]

    def rowCount(self, parent=QModelIndex()) -> int:
        """行数を返します"""
        return len(self.results)

    def columnCount(self, parent=QModelIndex()) -> int:
        """列数を返します"""
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """セルのデータを返します"""
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self.results) or col >= len(self.COLUMNS):
            return None

        result = self.results[row]
        column_key = self.column_keys[col]

        if role == Qt.DisplayRole:
            return self._get_display_data(result, column_key)
        elif role == Qt.TextAlignmentRole:
            return self._get_alignment(column_key)
        elif role == Qt.BackgroundRole:
            return self._get_background_color(result, column_key)
        elif role == Qt.ForegroundRole:
            return self._get_foreground_color(result, column_key)
        elif role == Qt.ToolTipRole:
            return self._get_tooltip(result, column_key)

        return None

    def _get_display_data(self, result: Dict[str, Any], column_key: str) -> str:
        """表示用データを取得します"""
        if column_key == "api_name":
            return result.get("data", {}).get("api_name", "N/A")
        elif column_key == "status":
            success = result.get("success", False)
            return "成功" if success else "失敗"
        elif column_key == "status_code":
            return str(result.get("data", {}).get("status_code", "N/A"))
        elif column_key == "response_time":
            time_val = result.get("data", {}).get("response_time", 0)
            return f"{time_val:.3f}"
        elif column_key == "url":
            url = result.get("data", {}).get("url", "N/A")
            # URLを短縮表示
            if len(url) > 50:
                return url[:47] + "..."
            return url
        elif column_key == "timestamp":
            return result.get("timestamp", "N/A")
        elif column_key == "error":
            return result.get("error", "")
        return ""

    def _get_alignment(self, column_key: str) -> int:
        """セルの配置を取得します"""
        if column_key in ["status_code", "response_time"]:
            return Qt.AlignRight | Qt.AlignVCenter
        elif column_key == "status":
            return Qt.AlignCenter | Qt.AlignVCenter
        else:
            return Qt.AlignLeft | Qt.AlignVCenter

    def _get_background_color(self, result: Dict[str, Any], column_key: str) -> Optional[QColor]:
        """背景色を取得します"""
        success = result.get("success", False)

        if column_key == "status":
            if success:
                return QColor(40, 80, 40)    # 濃い緑
            else:
                return QColor(80, 40, 40)    # 濃い赤

        if not success:
            return QColor(60, 40, 40)        # エラー行全体用の濃い赤背景

        return None

    def _get_foreground_color(self, result: Dict[str, Any], column_key: str) -> Optional[QColor]:
        """文字色を取得します"""
        success = result.get("success", False)

        if not success and column_key == "error":
            return QColor(255, 150, 150)  # 明るい赤

        return None

    def _get_tooltip(self, result: Dict[str, Any], column_key: str) -> str:
        """ツールチップを取得します"""
        if column_key == "url":
            return result.get("data", {}).get("url", "")
        elif column_key == "error" and result.get("error"):
            return result.get("error", "")
        return ""

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """ヘッダーデータを返します"""
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < len(self.column_names):
                    return self.column_names[section]
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None

    def set_results(self, results: List[Dict[str, Any]]) -> None:
        """結果を設定します"""
        logger.info(f"テーブルモデルに {len(results)} 件の結果を設定します")
        self.beginResetModel()
        self.results = results
        self.endResetModel()

    def add_result(self, result: Dict[str, Any]) -> None:
        """結果を追加します"""
        row = len(self.results)
        self.beginInsertRows(QModelIndex(), row, row)
        self.results.append(result)
        self.endInsertRows()

    def clear_results(self) -> None:
        """結果をクリアします"""
        logger.info("テーブルモデルをクリアします")
        self.beginResetModel()
        self.results = []
        self.endResetModel()

    def get_result(self, row: int) -> Optional[Dict[str, Any]]:
        """指定した行の結果を取得します"""
        if 0 <= row < len(self.results):
            return self.results[row]
        return None

    def get_all_results(self) -> List[Dict[str, Any]]:
        """すべての結果を取得します"""
        return self.results.copy()


class SortFilterProxyModel(QSortFilterProxyModel):
    """ソートとフィルターを行うプロキシモデル"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_text = ""

    def filterAcceptsRow(self, source_row: int, _source_parent: QModelIndex) -> bool:
        """行がフィルター条件を満たすかチェックします"""
        if not self.filter_text:
            return True

        model = self.sourceModel()
        if not isinstance(model, ApiResultTableModel):
            return True

        result = model.get_result(source_row)
        if not result:
            return False

        # すべての列のデータを検索
        search_text = self.filter_text.lower()
        for column_key in model.column_keys:
            display_data = model._get_display_data(result, column_key)
            if search_text in str(display_data).lower():
                return True

        return False

    def set_filter_text(self, text: str) -> None:
        """フィルターテキストを設定します"""
        self.filter_text = text.strip().lower()
        self.invalidateFilter()

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """ソート用の比較関数"""
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)

        # 数値として比較できる場合は数値比較
        try:
            left_num = float(left_data) if left_data else 0
            right_num = float(right_data) if right_data else 0
            return left_num < right_num
        except (ValueError, TypeError):
            # 文字列として比較
            left_str = str(left_data) if left_data else ""
            right_str = str(right_data) if right_data else ""
            return left_str < right_str
