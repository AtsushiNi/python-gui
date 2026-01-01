"""
API設定ダイアログ
動的フォーム生成によるAPI設定管理
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QCheckBox,
    QLineEdit,
    QLabel,
    QScrollArea,
    QFormLayout,
    QDialogButtonBox,
    QComboBox,
    QDoubleSpinBox,
    QDateEdit,
    QHBoxLayout,
)

from datetime import datetime
from typing import Dict, Any

from src.api.definitions import (
    ApiDefinition, ApiDefinitionManager, ApiFieldDefinition,
    FieldType, InputType
)
from src.config.apis import get_api_definitions
from src.logger import logger


class DynamicFieldWidget(QWidget):
    """動的フィールドウィジェット（入力タイプに応じたウィジェットを生成）"""
    
    value_changed = Signal()
    
    def __init__(self, field_def: ApiFieldDefinition, parent=None):
        super().__init__(parent)
        self.field_def = field_def
        self.setup_ui()
    
    def setup_ui(self):
        """UIを設定します"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if self.field_def.input_type == InputType.DROPDOWN:
            self.widget = QComboBox()
            if self.field_def.enum_mappings:
                for mapping in self.field_def.enum_mappings:
                    self.widget.addItem(mapping.display_name, mapping.value)
            self.widget.currentIndexChanged.connect(self._on_value_changed)
            
        elif self.field_def.input_type == InputType.CHECKBOX:
            self.widget = QCheckBox()
            self.widget.stateChanged.connect(self._on_value_changed)
            
        elif self.field_def.input_type == InputType.DATEPICKER:
            self.widget = QDateEdit()
            self.widget.setCalendarPopup(True)
            self.widget.dateChanged.connect(self._on_value_changed)
            
        elif self.field_def.type == FieldType.NUMBER:
            self.widget = QDoubleSpinBox()
            self.widget.setRange(-999999, 999999)
            self.widget.valueChanged.connect(self._on_value_changed)
            
        else:  # TEXT or default
            self.widget = QLineEdit()
            self.widget.textChanged.connect(self._on_value_changed)
        
        layout.addWidget(self.widget)
    
    def _on_value_changed(self, *args):
        """値が変更された時の処理"""
        self.value_changed.emit()
    
    def get_value(self) -> Any:
        """現在の値を取得"""
        if self.field_def.input_type == InputType.DROPDOWN:
            return self.widget.currentData()
        elif self.field_def.input_type == InputType.CHECKBOX:
            return self.widget.isChecked()
        elif self.field_def.input_type == InputType.DATEPICKER:
            return self.widget.date().toString(Qt.ISODate)
        elif self.field_def.type == FieldType.NUMBER:
            return self.widget.value()
        else:  # TEXT or default
            return self.widget.text()
    
    def set_value(self, value: Any):
        """値を設定"""
        if value is None:
            value = self.field_def.default
        
        try:
            if self.field_def.input_type == InputType.DROPDOWN:
                if self.field_def.enum_mappings:
                    for i, mapping in enumerate(self.field_def.enum_mappings):
                        if str(value) == mapping.value:
                            self.widget.setCurrentIndex(i)
                            break
            
            elif self.field_def.input_type == InputType.CHECKBOX:
                self.widget.setChecked(bool(value))
            
            elif self.field_def.input_type == InputType.DATEPICKER:
                if isinstance(value, str):
                    date = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    self.widget.setDate(date)
            
            elif self.field_def.type == FieldType.NUMBER:
                self.widget.setValue(float(value) if value else 0)
            
            else:  # TEXT or default
                self.widget.setText(str(value) if value else "")
        except Exception as e:
            logger.warning(f"フィールド値の設定に失敗: {self.field_def.name}, 値: {value}, エラー: {e}")
            # デフォルト値を設定
            if self.field_def.default is not None:
                self.set_value(self.field_def.default)


class ApiConfigWidget(QWidget):
    """単一のAPI設定ウィジェット（動的フォーム）"""
    
    config_changed = Signal(str)  # 設定変更時に発火（API ID付き）
    
    def __init__(self, api_def: ApiDefinition, parent=None):
        super().__init__(parent)
        self.api_def = api_def
        self.field_widgets: Dict[str, DynamicFieldWidget] = {}
        self.setup_ui()
    
    def setup_ui(self):
        """UIを設定します"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # グループボックス
        group_box = QGroupBox(self.api_def.name)
        group_layout = QVBoxLayout(group_box)
        
        # 有効/無効チェックボックス
        self.enabled_checkbox = QCheckBox("有効")
        self.enabled_checkbox.setChecked(self.api_def.enabled)
        self.enabled_checkbox.stateChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.enabled_checkbox)
        
        # 基本設定フォーム
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # URL
        self.url_edit = QLineEdit(self.api_def.url)
        self.url_edit.textChanged.connect(self.on_config_changed)
        form_layout.addRow("URL:", self.url_edit)
        
        # メソッド（現状は固定）
        method_label = QLabel(self.api_def.method)
        form_layout.addRow("メソッド:", method_label)
        
        group_layout.addLayout(form_layout)
        
        # Bodyフィールド（ある場合）
        if self.api_def.body_fields:
            body_group = QGroupBox("フィルターパラメータ")
            body_layout = QFormLayout(body_group)
            body_layout.setLabelAlignment(Qt.AlignRight)
            
            for field_def in self.api_def.body_fields:
                label = QLabel(field_def.label)
                field_widget = DynamicFieldWidget(field_def)
                field_widget.value_changed.connect(self.on_config_changed)
                self.field_widgets[field_def.name] = field_widget
                body_layout.addRow(label, field_widget)
            
            group_layout.addWidget(body_group)
        
        layout.addWidget(group_box)
    
    def on_config_changed(self):
        """設定が変更された時の処理"""
        self.config_changed.emit(self.api_def.id)
    
    def get_api_definition(self) -> ApiDefinition:
        """現在の設定からAPI定義を取得"""
        # 基本設定を更新
        updated_def = ApiDefinition(
            id=self.api_def.id,
            name=self.api_def.name,
            enabled=self.enabled_checkbox.isChecked(),
            url=self.url_edit.text(),
            method=self.api_def.method,
            body_fields=self.api_def.body_fields.copy(),
            response_fields=self.api_def.response_fields.copy(),
        )
        
        return updated_def
    
    def get_body_params(self) -> Dict[str, Any]:
        """Bodyパラメータを取得"""
        params = {}
        for field_name, widget in self.field_widgets.items():
            value = widget.get_value()
            if value is not None:
                params[field_name] = value
        return params
    
    def set_body_params(self, params: Dict[str, Any]):
        """Bodyパラメータを設定"""
        for field_name, value in params.items():
            if field_name in self.field_widgets:
                self.field_widgets[field_name].set_value(value)


class ApiConfigDialog(QDialog):
    """API設定ダイアログ（動的API定義）"""
    
    configs_changed = Signal()  # 設定変更時に発火
    
    def __init__(self, definition_manager: ApiDefinitionManager = None, parent=None):
        super().__init__(parent)
        
        # API定義マネージャーの初期化
        if definition_manager is None:
            api_definitions = get_api_definitions()
            self.definition_manager = ApiDefinitionManager(api_definitions)
        else:
            self.definition_manager = definition_manager
        
        self.api_widgets: Dict[str, ApiConfigWidget] = {}
        self.setup_ui()
        logger.info("API設定ダイアログを初期化しました")
    
    def setup_ui(self):
        """UIを設定します"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # ダイアログの基本設定
        self.setWindowTitle("API設定")
        self.setMinimumSize(700, 800)
        
        # タイトル
        title_label = QLabel("API設定")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 説明
        desc_label = QLabel("各APIの設定を変更できます。BodyフィールドはAPI呼び出し時のフィルタリングに使用されます。")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # スクロールエリアのコンテンツ
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # API設定ウィジェットを作成
        api_definitions = self.definition_manager.get_enabled_definitions()
        for api_def in api_definitions:
            api_widget = ApiConfigWidget(api_def)
            api_widget.config_changed.connect(self.on_config_changed)
            self.api_widgets[api_def.id] = api_widget
            content_layout.addWidget(api_widget)
        
        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # ダイアログボタン（OK/Cancel）
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_config_changed(self, api_id: str):
        """設定が変更された時の処理"""
        if api_id in self.api_widgets:
            widget = self.api_widgets[api_id]
            updated_def = widget.get_api_definition()
            self.definition_manager.update_definition(api_id, updated_def)
            self.configs_changed.emit()
    
    def get_definition_manager(self) -> ApiDefinitionManager:
        """現在の定義マネージャーを取得"""
        # すべてのウィジェットから設定を収集
        for api_id, widget in self.api_widgets.items():
            updated_def = widget.get_api_definition()
            self.definition_manager.update_definition(api_id, updated_def)
        return self.definition_manager
    
    def set_definition_manager(self, definition_manager: ApiDefinitionManager):
        """定義マネージャーを反映"""
        self.definition_manager = definition_manager
        self.api_widgets.clear()
        
        # UIを再構築
        for child in self.findChildren(ApiConfigWidget):
            child.deleteLater()
        
        self.setup_ui()
    
    def accept(self):
        """OKボタンが押された時の処理"""
        # 設定を更新
        for api_id, widget in self.api_widgets.items():
            updated_def = widget.get_api_definition()
            self.definition_manager.update_definition(api_id, updated_def)
        
        self.configs_changed.emit()
        super().accept()
