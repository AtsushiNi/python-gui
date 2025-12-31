"""
API設定ダイアログ
6つのAPI設定を管理するGUIコンポーネント
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QCheckBox,
    QLineEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QScrollArea,
    QFormLayout,
    QMessageBox,
    QDialogButtonBox,
    QStackedWidget,
)

from src.models.api_config import ApiConfig, ApiConfigManager, HttpMethod
from src.api.flexible_types import ApiCategory, find_api_definition, api_registry
from src.logger import logger


class ApiConfigWidget(QWidget):
    """単一のAPI設定ウィジェット"""

    config_changed = Signal(int)  # 設定変更時に発火（インデックス付き）

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.setup_ui()

    def setup_ui(self):
        """UIを設定します"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # グループボックス
        group_box = QGroupBox(f"API {self.index + 1}")
        group_layout = QVBoxLayout(group_box)

        # 有効/無効チェックボックス
        self.enabled_checkbox = QCheckBox("有効")
        self.enabled_checkbox.setChecked(True)
        self.enabled_checkbox.stateChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.enabled_checkbox)

        # フォームレイアウト
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)

        # API名
        self.name_edit = QLineEdit(f"API {self.index + 1}")
        self.name_edit.textChanged.connect(self.on_config_changed)
        form_layout.addRow("名前:", self.name_edit)

        # URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://api.example.com/endpoint")
        self.url_edit.textChanged.connect(self.on_config_changed)
        form_layout.addRow("URL:", self.url_edit)

        # HTTPメソッド
        self.method_combo = QComboBox()
        self.method_combo.addItems([method.value for method in HttpMethod])
        self.method_combo.currentTextChanged.connect(self.on_config_changed)
        form_layout.addRow("メソッド:", self.method_combo)

        # タイムアウト
        timeout_layout = QHBoxLayout()
        self.timeout_edit = QLineEdit("30")
        self.timeout_edit.setFixedWidth(60)
        self.timeout_edit.textChanged.connect(self.on_config_changed)
        timeout_layout.addWidget(self.timeout_edit)
        timeout_layout.addWidget(QLabel("秒"))
        timeout_layout.addStretch()
        form_layout.addRow("タイムアウト:", timeout_layout)

        # レスポンスパス
        self.response_path_edit = QLineEdit()
        self.response_path_edit.setPlaceholderText("例: data.results")
        self.response_path_edit.textChanged.connect(self.on_config_changed)
        form_layout.addRow("レスポンスパス:", self.response_path_edit)

        # API定義固有のフィルターパラメータセクション
        self.filter_stack = QStackedWidget()
        group_layout.addWidget(self.filter_stack)
        
        # 既知のAPI定義用のフィルターウィジェットを作成
        self.filter_widgets = {}
        
        # デフォルトのカスタムフィルターウィジェット
        self.custom_filter_widget = self.create_custom_filter_widget()
        self.filter_stack.addWidget(self.custom_filter_widget)
        
        # デフォルトはカスタムフィルターを表示
        self.filter_stack.setCurrentWidget(self.custom_filter_widget)

        group_layout.addLayout(form_layout)
        layout.addWidget(group_box)

    def create_filter_widget_for_definition(self, definition) -> QWidget:
        """API定義に基づいたフィルターウィジェットを作成します"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # グループボックス
        group_box = QGroupBox(f"{definition.name} フィルタリングパラメータ")
        group_layout = QFormLayout(group_box)
        group_layout.setLabelAlignment(Qt.AlignRight)
        
        # フィルターパラメータを動的に作成
        filter_inputs = {}
        
        for param_name in definition.supported_params:
            if param_name == "status":
                filter_inputs["status"] = QLineEdit()
                filter_inputs["status"].setPlaceholderText("例: APPROVED, PENDING")
                group_layout.addRow("ステータス:", filter_inputs["status"])
            
            elif param_name == "min_amount":
                filter_inputs["min_amount"] = QLineEdit()
                filter_inputs["min_amount"].setPlaceholderText("例: 1000")
                group_layout.addRow("最小金額:", filter_inputs["min_amount"])
            
            elif param_name == "max_amount":
                filter_inputs["max_amount"] = QLineEdit()
                filter_inputs["max_amount"].setPlaceholderText("例: 5000")
                group_layout.addRow("最大金額:", filter_inputs["max_amount"])
            
            elif param_name == "category":
                filter_inputs["category"] = QComboBox()
                filter_inputs["category"].addItems(["", "TRANSPORT", "BUSINESS_TRIP", "MEAL", "OFFICE_SUPPLIES", "TRAINING"])
                group_layout.addRow("カテゴリー:", filter_inputs["category"])
            
            elif param_name == "start_date_from":
                filter_inputs["start_date_from"] = QLineEdit()
                filter_inputs["start_date_from"].setPlaceholderText("YYYY-MM-DD")
                group_layout.addRow("開始日(From):", filter_inputs["start_date_from"])
            
            elif param_name == "start_date_to":
                filter_inputs["start_date_to"] = QLineEdit()
                filter_inputs["start_date_to"].setPlaceholderText("YYYY-MM-DD")
                group_layout.addRow("開始日(To):", filter_inputs["start_date_to"])
            
            elif param_name == "min_days":
                filter_inputs["min_days"] = QLineEdit()
                filter_inputs["min_days"].setPlaceholderText("例: 1")
                group_layout.addRow("最小日数:", filter_inputs["min_days"])
            
            elif param_name == "max_days":
                filter_inputs["max_days"] = QLineEdit()
                filter_inputs["max_days"].setPlaceholderText("例: 14")
                group_layout.addRow("最大日数:", filter_inputs["max_days"])
            
            elif param_name == "role":
                filter_inputs["role"] = QComboBox()
                filter_inputs["role"].addItems(["", "ADMIN", "EDITOR", "VIEWER", "MANAGER", "SUPERVISOR"])
                group_layout.addRow("ロール:", filter_inputs["role"])
            
            elif param_name == "approval_status":
                filter_inputs["approval_status"] = QComboBox()
                filter_inputs["approval_status"].addItems(["", "APPROVED", "PENDING", "REJECTED"])
                group_layout.addRow("承認ステータス:", filter_inputs["approval_status"])
        
        # ウィジェットにフィルター入力を保存
        widget.filter_inputs = filter_inputs
        
        # 入力変更時のイベントを接続
        for input_widget in filter_inputs.values():
            if isinstance(input_widget, QLineEdit):
                input_widget.textChanged.connect(self.on_config_changed)
            elif isinstance(input_widget, QComboBox):
                input_widget.currentTextChanged.connect(self.on_config_changed)
        
        layout.addWidget(group_box)
        layout.addStretch()
        return widget
    
    def create_custom_filter_widget(self) -> QWidget:
        """カスタムAPI用のフィルターウィジェットを作成します"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # グループボックス
        group_box = QGroupBox("カスタムAPI フィルタリングパラメータ")
        group_layout = QFormLayout(group_box)
        group_layout.setLabelAlignment(Qt.AlignRight)
        
        # 汎用フィルターパラメータ
        filter_inputs = {}
        
        # クエリパラメータ（汎用）
        filter_inputs["query_params"] = QLineEdit()
        filter_inputs["query_params"].setPlaceholderText("例: status=APPROVED&limit=10")
        group_layout.addRow("クエリパラメータ:", filter_inputs["query_params"])
        
        # ウィジェットにフィルター入力を保存
        widget.filter_inputs = filter_inputs
        
        # 入力変更時のイベントを接続
        filter_inputs["query_params"].textChanged.connect(self.on_config_changed)
        
        layout.addWidget(group_box)
        layout.addStretch()
        return widget
    
    def update_filter_widget(self, url: str):
        """URLに基づいて適切なフィルターウィジェットを表示します"""
        definition = find_api_definition(url)
        
        if definition and definition.name in self.filter_widgets:
            # 既存のウィジェットを使用
            self.filter_stack.setCurrentWidget(self.filter_widgets[definition.name])
        elif definition:
            # 新しい定義用のウィジェットを作成
            widget = self.create_filter_widget_for_definition(definition)
            self.filter_widgets[definition.name] = widget
            self.filter_stack.addWidget(widget)
            self.filter_stack.setCurrentWidget(widget)
        else:
            # カスタムAPI用のウィジェットを使用
            self.filter_stack.setCurrentWidget(self.custom_filter_widget)
    
    def on_config_changed(self):
        """設定が変更された時の処理"""
        # URLが変更された場合、API定義を検出してフィルターウィジェットを更新
        url = self.url_edit.text()
        if url:
            self.update_filter_widget(url)
        
        self.config_changed.emit(self.index)

    def get_config(self) -> ApiConfig:
        """現在の設定を取得します"""
        try:
            timeout = int(self.timeout_edit.text())
        except ValueError:
            timeout = 30
        
        # URLからAPI定義を取得
        url = self.url_edit.text()
        definition = find_api_definition(url)
        api_category = definition.category if definition else None
        api_definition_name = definition.name if definition else None
        
        # 現在表示されているフィルターウィジェットからパラメータを取得
        current_widget = self.filter_stack.currentWidget()
        filter_params = {}
        
        if current_widget and hasattr(current_widget, 'filter_inputs'):
            for key, input_widget in current_widget.filter_inputs.items():
                if isinstance(input_widget, QLineEdit):
                    value = input_widget.text().strip()
                    if value:
                        if key == "query_params":
                            # クエリパラメータを解析
                            for param in value.split("&"):
                                if "=" in param:
                                    param_key, param_value = param.split("=", 1)
                                    filter_params[param_key.strip()] = param_value.strip()
                        else:
                            # 数値パラメータの処理
                            if key in ["min_amount", "max_amount", "min_days", "max_days"]:
                                try:
                                    filter_params[key] = int(value)
                                except ValueError:
                                    # 数値変換できない場合は文字列として保持
                                    filter_params[key] = value
                            else:
                                filter_params[key] = value
                elif isinstance(input_widget, QComboBox):
                    value = input_widget.currentText().strip()
                    if value:
                        filter_params[key] = value
        
        return ApiConfig(
            enabled=self.enabled_checkbox.isChecked(),
            name=self.name_edit.text(),
            url=url,
            method=HttpMethod(self.method_combo.currentText()),
            timeout=timeout,
            response_path=self.response_path_edit.text() if hasattr(self, 'response_path_edit') else None,
            api_category=api_category,
            api_definition_name=api_definition_name,
            filter_params=filter_params,
        )

    def set_config(self, config: ApiConfig):
        """設定を反映します"""
        self.enabled_checkbox.setChecked(config.enabled)
        self.name_edit.setText(config.name)
        self.url_edit.setText(config.url)
        self.method_combo.setCurrentText(config.method.value)
        self.timeout_edit.setText(str(config.timeout))
        
        # response_pathの設定
        if hasattr(self, 'response_path_edit'):
            self.response_path_edit.setText(config.response_path or "")
        
        # URLに基づいて適切なフィルターウィジェットを表示
        if config.url:
            self.update_filter_widget(config.url)
        
        # フィルターパラメータの設定
        if hasattr(self, 'filter_stack'):
            current_widget = self.filter_stack.currentWidget()
            if current_widget and hasattr(current_widget, 'filter_inputs'):
                for key, input_widget in current_widget.filter_inputs.items():
                    if key in config.filter_params:
                        value = config.filter_params[key]
                        if isinstance(input_widget, QLineEdit):
                            input_widget.setText(str(value))
                        elif isinstance(input_widget, QComboBox):
                            # コンボボックスに値が存在するか確認
                            index = input_widget.findText(str(value))
                            if index >= 0:
                                input_widget.setCurrentIndex(index)



class ApiConfigDialog(QDialog):
    """API設定ダイアログ（3つのAPI設定を管理）"""

    configs_changed = Signal()  # 設定変更時に発火

    def __init__(self, config_manager=None, parent=None):
        super().__init__(parent)
        
        # 設定マネージャーの初期化
        if config_manager is None:
            # デフォルトのAPI設定を作成（ローカルモックサーバーを指す）
            default_configs = [
                ApiConfig(
                    enabled=True,
                    name="Type A API (Local Mock)",
                    url="http://localhost:8001/applications/type-a",
                    method=HttpMethod.POST,
                    timeout=30,
                    response_path="applications",  # applications配列を抽出
                ),
                ApiConfig(
                    enabled=True,
                    name="Type B API (Local Mock)",
                    url="http://localhost:8001/applications/type-b",
                    method=HttpMethod.POST,
                    timeout=30,
                    response_path="applications",  # applications配列を抽出
                ),
                ApiConfig(
                    enabled=True,
                    name="Type C API (Local Mock)",
                    url="http://localhost:8001/applications/type-c",
                    method=HttpMethod.POST,
                    timeout=30,
                    response_path="applications",  # applications配列を抽出（エラーの場合は空）
                ),
            ]
            self.config_manager = ApiConfigManager(max_apis=3, default_configs=default_configs)
        else:
            self.config_manager = config_manager
        
        self.setup_ui()
        logger.info("API設定ダイアログを初期化しました")

    def setup_ui(self):
        """UIを設定します"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ダイアログの基本設定
        self.setWindowTitle("API設定")
        self.setMinimumSize(600, 700)

        # タイトル
        title_label = QLabel("API設定")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # スクロールエリアのコンテンツ
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)

        # 3つのAPI設定ウィジェットを作成
        self.api_widgets = []
        for i in range(3):
            api_widget = ApiConfigWidget(i)
            api_widget.config_changed.connect(self.on_config_changed)
            self.api_widgets.append(api_widget)
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
        
        # デフォルト設定をウィジェットに反映
        for i, widget in enumerate(self.api_widgets):
            if i < len(self.config_manager.configs):
                widget.set_config(self.config_manager.configs[i])

    def on_config_changed(self, index: int):
        """設定が変更された時の処理"""
        # 設定を更新
        config = self.api_widgets[index].get_config()
        self.config_manager.set_config(index, config)
        self.configs_changed.emit()

    def get_config_manager(self) -> ApiConfigManager:
        """現在の設定マネージャーを取得します"""
        # すべてのウィジェットから設定を収集
        for i, widget in enumerate(self.api_widgets):
            self.config_manager.set_config(i, widget.get_config())
        return self.config_manager

    def set_config_manager(self, config_manager: ApiConfigManager):
        """設定マネージャーを反映します"""
        self.config_manager = config_manager
        for i, widget in enumerate(self.api_widgets):
            if i < len(config_manager.configs):
                widget.set_config(config_manager.configs[i])

    def accept(self):
        """OKボタンが押された時の処理"""
        # 設定を更新
        for i, widget in enumerate(self.api_widgets):
            self.config_manager.set_config(i, widget.get_config())
        self.configs_changed.emit()
        super().accept()
