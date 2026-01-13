"""
動的結果表示モデル
表示名ベースでAPI結果をマージして表示
"""

from typing import Any, Dict, List, Optional
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QColor

from src.api.definitions import (
    ApiDefinition, ApiDefinitionManager, MergedField, 
    merge_api_definitions_by_label, FieldType
)
from src.logger import logger


class DynamicResultTableModel(QAbstractTableModel):
    """動的結果表示テーブルモデル（表示名ベースマージ）"""

    def __init__(self, definition_manager: ApiDefinitionManager, parent=None):
        super().__init__(parent)
        self.definition_manager = definition_manager
        self.results: List[Dict[str, Any]] = []  # API実行結果
        self.response_data: List[Dict[str, Any]] = []  # 抽出されたレスポンスデータ
        self.merged_fields: List[MergedField] = []
        
        self._update_merged_fields()
    
    def _update_merged_fields(self):
        """マージされたフィールドを更新"""
        self.merged_fields = self.definition_manager.get_merged_fields()
    
    def rowCount(self, parent=QModelIndex()) -> int:
        """行数を返します"""
        return len(self.response_data)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        """列数を返します"""
        # 基本列: API名 + マージされたフィールド
        return len(self.merged_fields) + 1  # +1 for API名列
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """セルのデータを返します"""
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        
        if row >= len(self.response_data):
            return None
        
        item = self.response_data[row]
        api_id = item.get("api_id", "")
        
        if col == 0:  # API名列
            if role == Qt.DisplayRole:
                return item.get("api_name", "N/A")
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignLeft | Qt.AlignVCenter
            elif role == Qt.BackgroundRole:
                # APIごとに色分け（簡易的なハッシュベース）
                api_hash = hash(api_id) % 5
                colors = [
                    QColor(240, 248, 255),  # aliceblue
                    QColor(255, 250, 240),  # floralwhite
                    QColor(240, 255, 240),  # honeydew
                    QColor(255, 245, 238),  # seashell
                    QColor(245, 245, 245),  # whitesmoke
                ]
                return colors[api_hash] if 0 <= api_hash < len(colors) else None
        
        else:  # マージされたフィールド列
            merged_field_idx = col - 1
            if merged_field_idx >= len(self.merged_fields):
                return None
            
            merged_field = self.merged_fields[merged_field_idx]
            
            if role == Qt.DisplayRole:
                # フィールド定義を取得
                field_def = merged_field.get_field_definition(api_id)
                if field_def:
                    # 実際のフィールド名を取得
                    field_name = field_def.name
                    value = item.get(field_name)
                    return field_def.get_display_value(value)
                else:
                    # このAPIでは定義されていないフィールド
                    return "-"
            
            elif role == Qt.TextAlignmentRole:
                field_def = merged_field.get_field_definition(api_id)
                if field_def and field_def.type == FieldType.NUMBER:
                    return Qt.AlignRight | Qt.AlignVCenter
                return Qt.AlignLeft | Qt.AlignVCenter
            
            elif role == Qt.ToolTipRole:
                field_def = merged_field.get_field_definition(api_id)
                if field_def:
                    field_name = field_def.name
                    value = item.get(field_name)
                    return f"{field_def.label}: {value}"
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """ヘッダーデータを返します"""
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return "API名"
                elif section - 1 < len(self.merged_fields):
                    merged_field = self.merged_fields[section - 1]
                    return merged_field.label
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None
    
    def set_results(self, results: List[Dict[str, Any]]) -> None:
        """API実行結果を設定します"""
        from src.api.client import ApiExecutor
        
        logger.info(f"動的結果モデルに {len(results)} 件のAPI実行結果を設定します")
        
        self.beginResetModel()
        self.results = results
        
        # レスポンスデータを抽出
        executor = ApiExecutor()
        self.response_data = executor.extract_response_data(results)
        
        # マージされたフィールドを更新
        self._update_merged_fields()
        
        self.endResetModel()
        
        logger.info(f"抽出されたレスポンスデータ: {len(self.response_data)} 件")
        logger.info(f"マージされた列: {len(self.merged_fields)} 列")
    
    def clear_results(self) -> None:
        """結果をクリアします"""
        logger.info("動的結果モデルをクリアします")
        self.beginResetModel()
        self.results = []
        self.response_data = []
        self.endResetModel()
    
    def get_item(self, row: int) -> Optional[Dict[str, Any]]:
        """指定した行のアイテムを取得します"""
        if 0 <= row < len(self.response_data):
            return self.response_data[row]
        return None
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """すべてのアイテムを取得します"""
        return self.response_data.copy()


class DynamicResultSortFilterProxyModel(QSortFilterProxyModel):
    """動的結果のソートとフィルターを行うプロキシモデル"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_api_id = ""  # API IDでフィルター
    
    def filterAcceptsRow(self, source_row: int, _source_parent: QModelIndex) -> bool:
        """行がフィルター条件を満たすかチェックします"""
        model = self.sourceModel()
        if not isinstance(model, DynamicResultTableModel):
            return True
        
        item = model.get_item(source_row)
        if not item:
            return False
        
        # API IDフィルター
        if self.filter_api_id:
            api_id = item.get("api_id", "")
            if api_id != self.filter_api_id:
                return False
        
        return True
    
    def set_filter_api_id(self, api_id: str) -> None:
        """API IDフィルターを設定します"""
        if api_id is None:
            self.filter_api_id = ""
        else:
            self.filter_api_id = api_id.strip()
        self.invalidateFilter()

    def _get_field_type_for_column(self, column: int) -> Optional[FieldType]:
        """proxyの列番号からFieldTypeを取得します。

        0列目はAPI名列のため型はNone。
        それ以外はsource modelのmerged_fieldsから型を参照します。
        """
        source_model = self.sourceModel()
        if not isinstance(source_model, DynamicResultTableModel):
            return None

        if column <= 0:
            return None

        merged_field_idx = column - 1
        if 0 <= merged_field_idx < len(source_model.merged_fields):
            return source_model.merged_fields[merged_field_idx].field_type
        return None

    @staticmethod
    def _try_parse_datetime(value: Any):
        """値をdatetimeへパースします。失敗時はNone。"""
        if value is None:
            return None

        from datetime import datetime

        # すでにdatetimeの場合
        if isinstance(value, datetime):
            return value

        s = str(value).strip()
        if not s or s in {"-", "N/A"}:
            return None

        # Z 付きISOをfromisoformatで扱えるように補正
        s = s.replace("Z", "+00:00")

        # まずISO形式を試す
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            pass

        # よくあるフォーマットもフォールバック
        for fmt in (
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue

        return None
    
    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """ソート用の比較関数"""
        source_model = self.sourceModel()
        left_data = source_model.data(left, Qt.DisplayRole)
        right_data = source_model.data(right, Qt.DisplayRole)

        # 列の型に応じて比較（重要: DATE列を数値比較に誤判定させない）
        field_type = self._get_field_type_for_column(left.column())

        # DATE
        if field_type == FieldType.DATE:
            left_dt = self._try_parse_datetime(left_data)
            right_dt = self._try_parse_datetime(right_data)

            # パースできない値は末尾に寄せる
            if left_dt is None and right_dt is None:
                return False
            if left_dt is None:
                return False
            if right_dt is None:
                return True

            return left_dt < right_dt

        # NUMBER
        if field_type == FieldType.NUMBER:
            try:
                import re

                left_str = str(left_data) if left_data is not None else ""
                right_str = str(right_data) if right_data is not None else ""

                left_num_match = re.search(r"(-?\d+(?:\.\d+)?)", left_str)
                right_num_match = re.search(r"(-?\d+(?:\.\d+)?)", right_str)

                if left_num_match and right_num_match:
                    return float(left_num_match.group(1)) < float(right_num_match.group(1))
            except (ValueError, TypeError):
                pass

        # それ以外は従来通り文字列比較
        left_str = str(left_data) if left_data is not None else ""
        right_str = str(right_data) if right_data is not None else ""
        return left_str < right_str
