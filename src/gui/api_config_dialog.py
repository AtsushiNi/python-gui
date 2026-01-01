"""
API設定ダイアログ
6つのAPI設定を管理するGUIコンポーネント
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
)

from src.models.api_config import ApiConfig, ApiConfigManager
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

        # フィルターパラメータ
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("例: status=APPROVED&limit=10")
        self.filter_edit.textChanged.connect(self.on_config_changed)
        form_layout.addRow("フィルター:", self.filter_edit)

        group_layout.addLayout(form_layout)
        layout.addWidget(group_box)

    def on_config_changed(self):
        """設定が変更された時の処理"""
        self.config_changed.emit(self.index)

    def get_config(self) -> ApiConfig:
        """現在の設定を取得します"""
        url = self.url_edit.text()
        
        # フィルターパラメータを解析
        filter_params = {}
        filter_text = self.filter_edit.text().strip()
        if filter_text:
            for param in filter_text.split("&"):
                if "=" in param:
                    param_key, param_value = param.split("=", 1)
                    filter_params[param_key.strip()] = param_value.strip()
        
        # 基本設定を作成
        config = ApiConfig(
            enabled=self.enabled_checkbox.isChecked(),
            name=self.name_edit.text(),
            url=url,
            filter_params=filter_params,
        )
        
        return config

    def set_config(self, config: ApiConfig):
        """設定を反映します"""
        self.enabled_checkbox.setChecked(config.enabled)
        self.name_edit.setText(config.name)
        self.url_edit.setText(config.url)
        
        # フィルターパラメータを設定
        if config.filter_params:
            filter_parts = []
            for key, value in config.filter_params.items():
                filter_parts.append(f"{key}={value}")
            self.filter_edit.setText("&".join(filter_parts))
        else:
            self.filter_edit.clear()



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
                ),
                ApiConfig(
                    enabled=True,
                    name="Type B API (Local Mock)",
                    url="http://localhost:8001/applications/type-b",
                ),
                ApiConfig(
                    enabled=True,
                    name="Type C API (Local Mock)",
                    url="http://localhost:8001/applications/type-c",
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
