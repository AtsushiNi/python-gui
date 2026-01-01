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
                    return "N/A"
            
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
        self.filter_text = ""
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
        
        # テキストフィルター
        if not self.filter_text:
            return True
        
        search_text = self.filter_text.lower()
        
        # すべての列のデータを検索
        for col in range(model.columnCount()):
            index = model.index(source_row, col)
            display_data = model.data(index, Qt.DisplayRole)
            if search_text in str(display_data).lower():
                return True
        
        return False
    
    def set_filter_text(self, text: str) -> None:
        """フィルターテキストを設定します"""
        if text is None:
            self.filter_text = ""
        else:
            self.filter_text = text.strip().lower()
        self.invalidateFilter()
    
    def set_filter_api_id(self, api_id: str) -> None:
        """API IDフィルターを設定します"""
        if api_id is None:
            self.filter_api_id = ""
        else:
            self.filter_api_id = api_id.strip()
        self.invalidateFilter()
    
    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """ソート用の比較関数"""
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)
        
        # 数値として比較できる場合は数値比較
        try:
            # 数値部分を抽出（例: "1280 JPY" → 1280）
            import re
            left_str = str(left_data) if left_data else ""
            right_str = str(right_data) if right_data else ""
            
            left_num_match = re.search(r'(\d+\.?\d*)', left_str)
            right_num_match = re.search(r'(\d+\.?\d*)', right_str)
            
            if left_num_match and right_num_match:
                left_num = float(left_num_match.group(1))
                right_num = float(right_num_match.group(1))
                return left_num < right_num
        except (ValueError, TypeError, AttributeError):
            pass
        
        # 日付として比較できる場合は日付比較
        try:
            from datetime import datetime
            left_date = datetime.fromisoformat(str(left_data).replace('Z', '+00:00'))
            right_date = datetime.fromisoformat(str(right_data).replace('Z', '+00:00'))
            return left_date < right_date
        except (ValueError, TypeError):
            pass
        
        # 文字列として比較
        left_str = str(left_data) if left_data else ""
        right_str = str(right_data) if right_data else ""
        return left_str < right_str
