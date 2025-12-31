"""
アプリケーションデータを表示するテーブルモデル
APIから取得したapplicationsデータを共通部分と固有部分をわかりやすく表示
"""

from typing import Any, Dict, List, Optional
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QColor

from src.logger import logger


class ApplicationsTableModel(QAbstractTableModel):
    """アプリケーションデータを表示するテーブルモデル"""

    # 列定義 - 共通部分と固有部分を分けて表示
    COLUMNS = [
        ("api_type", "APIタイプ"),
        ("id", "ID"),
        ("title", "タイトル"),
        ("status", "ステータス"),
        ("applicant_name", "申請者名"),
        ("created_at", "申請日時"),
        ("type_specific_1", "タイプ固有1"),
        ("type_specific_2", "タイプ固有2"),
        ("type_specific_3", "タイプ固有3"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.applications: List[Dict[str, Any]] = []
        self.column_keys = [col[0] for col in self.COLUMNS]
        self.column_names = [col[1] for col in self.COLUMNS]

    def rowCount(self, parent=QModelIndex()) -> int:
        """行数を返します"""
        return len(self.applications)

    def columnCount(self, parent=QModelIndex()) -> int:
        """列数を返します"""
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """セルのデータを返します"""
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self.applications) or col >= len(self.COLUMNS):
            return None

        application = self.applications[row]
        column_key = self.column_keys[col]

        if role == Qt.DisplayRole:
            return self._get_display_data(application, column_key)
        elif role == Qt.TextAlignmentRole:
            return self._get_alignment(column_key)
        elif role == Qt.BackgroundRole:
            return self._get_background_color(application, column_key)
        elif role == Qt.ToolTipRole:
            return self._get_tooltip(application, column_key)

        return None

    def _get_display_data(self, application: Dict[str, Any], column_key: str) -> str:
        """表示用データを取得します"""
        if column_key == "api_type":
            return application.get("api_type", "N/A")
        elif column_key == "id":
            return application.get("id", "N/A")
        elif column_key == "title":
            return application.get("title", "N/A")
        elif column_key == "status":
            status = application.get("status", "N/A")
            # ステータスを日本語に変換
            status_map = {
                "SUBMITTED": "申請済",
                "APPROVED": "承認済",
                "REJECTED": "却下",
                "PENDING": "保留中",
            }
            return status_map.get(status, status)
        elif column_key == "applicant_name":
            applicant = application.get("applicant", {})
            return applicant.get("name", "N/A") if isinstance(applicant, dict) else "N/A"
        elif column_key == "created_at":
            created_at = application.get("createdAt", "N/A")
            # 日時を短縮表示
            if isinstance(created_at, str) and "T" in created_at:
                return created_at.replace("T", " ").split("+")[0]
            return str(created_at)
        elif column_key == "type_specific_1":
            return self._get_type_specific_data(application, 1)
        elif column_key == "type_specific_2":
            return self._get_type_specific_data(application, 2)
        elif column_key == "type_specific_3":
            return self._get_type_specific_data(application, 3)
        return ""

    def _get_type_specific_data(self, application: Dict[str, Any], index: int) -> str:
        """タイプ固有のデータを取得します"""
        api_type = application.get("api_type", "")
        
        if api_type == "A":
            if index == 1:
                amount = application.get("amount")
                currency = application.get("currency", "JPY")
                return f"{amount} {currency}" if amount is not None else "N/A"
            elif index == 2:
                return application.get("expenseCategory", "N/A")
            elif index == 3:
                return "経費申請"
        
        elif api_type == "B":
            if index == 1:
                start_date = application.get("startDate", "N/A")
                end_date = application.get("endDate", "N/A")
                if start_date == end_date:
                    return start_date
                return f"{start_date}〜{end_date}"
            elif index == 2:
                days = application.get("days")
                return f"{days}日" if days is not None else "N/A"
            elif index == 3:
                return "休暇申請"
        
        elif api_type == "C":
            if index == 1:
                # requestedRoleを表示
                requested_role = application.get("requestedRole", "N/A")
                return requested_role
            elif index == 2:
                # approvalFlowのステータスを表示
                approval_flow = application.get("approvalFlow", [])
                if isinstance(approval_flow, list) and len(approval_flow) > 0:
                    # 保留中のステップ数を表示
                    pending_steps = [step for step in approval_flow if step.get("status") == "PENDING"]
                    return f"承認フロー: {len(pending_steps)}ステップ保留"
                return "承認フロー: N/A"
            elif index == 3:
                return "権限申請"
        
        return ""

    def _get_alignment(self, column_key: str) -> int:
        """セルの配置を取得します"""
        if column_key in ["amount", "days"]:
            return Qt.AlignRight | Qt.AlignVCenter
        elif column_key == "status":
            return Qt.AlignCenter | Qt.AlignVCenter
        else:
            return Qt.AlignLeft | Qt.AlignVCenter

    def _get_background_color(self, application: Dict[str, Any], column_key: str) -> Optional[QColor]:
        """背景色を取得します"""
        api_type = application.get("api_type", "")
        
        # APIタイプごとに色分け
        if column_key == "api_type":
            if api_type == "A":
                return QColor(40, 60, 80)    # 濃い青
            elif api_type == "B":
                return QColor(40, 80, 40)    # 濃い緑
            elif api_type == "C":
                return QColor(80, 40, 40)    # 濃い赤
        
        # ステータスごとに色分け
        if column_key == "status":
            status = application.get("status", "")
            if status == "APPROVED":
                return QColor(40, 80, 40)    # 濃い緑
            elif status == "REJECTED":
                return QColor(80, 40, 40)    # 濃い赤
            elif status == "SUBMITTED":
                return QColor(80, 80, 40)    # 濃い黄緑
        
        return None

    def _get_tooltip(self, application: Dict[str, Any], column_key: str) -> str:
        """ツールチップを取得します"""
        if column_key == "type_specific_1":
            api_type = application.get("api_type", "")
            if api_type == "A":
                return "金額と通貨"
            elif api_type == "B":
                return "期間"
            elif api_type == "C":
                return "エラーコード"
        elif column_key == "type_specific_2":
            api_type = application.get("api_type", "")
            if api_type == "A":
                return "経費カテゴリー"
            elif api_type == "B":
                return "日数"
            elif api_type == "C":
                return "エラーメッセージ"
        elif column_key == "type_specific_3":
            api_type = application.get("api_type", "")
            if api_type == "A":
                return "タイプ: 経費申請"
            elif api_type == "B":
                return "タイプ: 休暇申請"
            elif api_type == "C":
                return "タイプ: エラー"
        
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

    def set_applications(self, applications: List[Dict[str, Any]]) -> None:
        """アプリケーションデータを設定します"""
        logger.info(f"アプリケーションテーブルモデルに {len(applications)} 件のデータを設定します")
        self.beginResetModel()
        self.applications = applications
        self.endResetModel()

    def add_application(self, application: Dict[str, Any]) -> None:
        """アプリケーションデータを追加します"""
        row = len(self.applications)
        self.beginInsertRows(QModelIndex(), row, row)
        self.applications.append(application)
        self.endInsertRows()

    def clear_applications(self) -> None:
        """アプリケーションデータをクリアします"""
        logger.info("アプリケーションテーブルモデルをクリアします")
        self.beginResetModel()
        self.applications = []
        self.endResetModel()

    def get_application(self, row: int) -> Optional[Dict[str, Any]]:
        """指定した行のアプリケーションデータを取得します"""
        if 0 <= row < len(self.applications):
            return self.applications[row]
        return None

    def get_all_applications(self) -> List[Dict[str, Any]]:
        """すべてのアプリケーションデータを取得します"""
        return self.applications.copy()


class ApplicationsSortFilterProxyModel(QSortFilterProxyModel):
    """アプリケーションデータのソートとフィルターを行うプロキシモデル"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_text = ""
        self.filter_api_type = ""  # A, B, C でフィルター

    def filterAcceptsRow(self, source_row: int, _source_parent: QModelIndex) -> bool:
        """行がフィルター条件を満たすかチェックします"""
        model = self.sourceModel()
        if not isinstance(model, ApplicationsTableModel):
            return True

        application = model.get_application(source_row)
        if not application:
            return False

        # APIタイプフィルター
        if self.filter_api_type:
            api_type = application.get("api_type", "")
            if api_type != self.filter_api_type:
                return False

        # テキストフィルター
        if not self.filter_text:
            return True

        search_text = self.filter_text.lower()
        
        # すべての列のデータを検索
        for column_key in model.column_keys:
            display_data = model._get_display_data(application, column_key)
            if search_text in str(display_data).lower():
                return True

        return False

    def set_filter_text(self, text: str) -> None:
        """フィルターテキストを設定します"""
        self.filter_text = text.strip().lower()
        self.invalidateFilter()

    def set_filter_api_type(self, api_type: str) -> None:
        """APIタイプフィルターを設定します"""
        self.filter_api_type = api_type.strip().upper()
        self.invalidateFilter()

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """ソート用の比較関数"""
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)

        # 数値として比較できる場合は数値比較
        try:
            # 金額（例: "1280 JPY"）から数値部分を抽出
            left_str = str(left_data) if left_data else ""
            right_str = str(right_data) if right_data else ""
            
            # 数値部分を抽出
            import re
            left_num_match = re.search(r'(\d+\.?\d*)', left_str)
            right_num_match = re.search(r'(\d+\.?\d*)', right_str)
            
            if left_num_match and right_num_match:
                left_num = float(left_num_match.group(1))
                right_num = float(right_num_match.group(1))
                return left_num < right_num
        except (ValueError, TypeError, AttributeError):
            pass
        
        # 文字列として比較
        left_str = str(left_data) if left_data else ""
        right_str = str(right_data) if right_data else ""
        return left_str < right_str
