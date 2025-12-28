"""
API設定ダイアログ
6つのAPI設定を管理するGUIコンポーネント
"""

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
)

from src.models.api_config import ApiConfig, ApiConfigManager, HttpMethod
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

        # 平坦化チェックボックス
        self.flatten_checkbox = QCheckBox("レスポンスを平坦化")
        self.flatten_checkbox.setChecked(False)
        self.flatten_checkbox.stateChanged.connect(self.on_config_changed)
        form_layout.addRow("", self.flatten_checkbox)

        # フィルタリングパラメータセクション
        filter_group = QGroupBox("フィルタリングパラメータ")
        filter_layout = QFormLayout()
        filter_layout.setLabelAlignment(Qt.AlignRight)

        # ステータスフィルター
        self.status_filter_edit = QLineEdit()
        self.status_filter_edit.setPlaceholderText("例: APPROVED, PENDING")
        self.status_filter_edit.textChanged.connect(self.on_config_changed)
        filter_layout.addRow("ステータス:", self.status_filter_edit)

        # その他のフィルターパラメータ
        self.other_filters_edit = QLineEdit()
        self.other_filters_edit.setPlaceholderText("例: min_amount=1000&max_amount=5000")
        self.other_filters_edit.textChanged.connect(self.on_config_changed)
        filter_layout.addRow("その他:", self.other_filters_edit)

        filter_group.setLayout(filter_layout)
        group_layout.addWidget(filter_group)

        group_layout.addLayout(form_layout)
        layout.addWidget(group_box)

    def on_config_changed(self):
        """設定が変更された時の処理"""
        self.config_changed.emit(self.index)

    def get_config(self) -> ApiConfig:
        """現在の設定を取得します"""
        try:
            timeout = int(self.timeout_edit.text())
        except ValueError:
            timeout = 30

        # フィルタリングパラメータをparamsに追加
        params = {}
        
        # ステータスフィルター
        status_filter = self.status_filter_edit.text().strip()
        if status_filter:
            params["status"] = status_filter
        
        # その他のフィルターパラメータを解析
        other_filters = self.other_filters_edit.text().strip()
        if other_filters:
            # "key1=value1&key2=value2" 形式を解析
            for param in other_filters.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    params[key.strip()] = value.strip()
        
        return ApiConfig(
            enabled=self.enabled_checkbox.isChecked(),
            name=self.name_edit.text(),
            url=self.url_edit.text(),
            method=HttpMethod(self.method_combo.currentText()),
            timeout=timeout,
            response_path=self.response_path_edit.text() if hasattr(self, 'response_path_edit') else None,
            flatten_response=self.flatten_checkbox.isChecked() if hasattr(self, 'flatten_checkbox') else False,
            params=params,
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
        
        # flatten_responseの設定
        if hasattr(self, 'flatten_checkbox'):
            self.flatten_checkbox.setChecked(config.flatten_response)
        
        # フィルタリングパラメータの設定
        if hasattr(self, 'status_filter_edit'):
            # statusパラメータを抽出
            status_value = config.params.get("status", "")
            self.status_filter_edit.setText(status_value)
            
            # その他のパラメータを抽出（status以外）
            other_params = []
            for key, value in config.params.items():
                if key != "status":
                    other_params.append(f"{key}={value}")
            self.other_filters_edit.setText("&".join(other_params))



class ApiDialog(QDialog):
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
                    method=HttpMethod.GET,
                    timeout=30,
                    response_path="applications",  # applications配列を抽出
                    flatten_response=True,  # ネストされたレスポンスを平坦化
                ),
                ApiConfig(
                    enabled=True,
                    name="Type B API (Local Mock)",
                    url="http://localhost:8001/applications/type-b",
                    method=HttpMethod.GET,
                    timeout=30,
                    response_path="applications",  # applications配列を抽出
                    flatten_response=True,  # ネストされたレスポンスを平坦化
                ),
                ApiConfig(
                    enabled=True,
                    name="Type C API (Local Mock)",
                    url="http://localhost:8001/applications/type-c",
                    method=HttpMethod.GET,
                    timeout=30,
                    response_path="applications",  # applications配列を抽出（エラーの場合は空）
                    flatten_response=True,  # ネストされたレスポンスを平坦化
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

        # コントロールボタン
        control_layout = QHBoxLayout()
        control_layout.addStretch()

        self.save_button = QPushButton("設定を保存")
        self.save_button.clicked.connect(self.save_configs)
        control_layout.addWidget(self.save_button)

        self.load_button = QPushButton("設定を読み込み")
        self.load_button.clicked.connect(self.load_configs)
        control_layout.addWidget(self.load_button)

        layout.addLayout(control_layout)

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

    def save_configs(self):
        """設定を保存します（現在は機能未実装）"""
        QMessageBox.information(
            self,
            "情報",
            "設定保存機能は現在利用できません。\n設定はアプリケーション終了時に失われます。",
        )

    def load_configs(self):
        """設定を読み込みます（現在は機能未実装）"""
        QMessageBox.information(
            self,
            "情報",
            "設定読み込み機能は現在利用できません。",
        )


    def accept(self):
        """OKボタンが押された時の処理"""
        # 設定を更新
        for i, widget in enumerate(self.api_widgets):
            self.config_manager.set_config(i, widget.get_config())
        self.configs_changed.emit()
        super().accept()
