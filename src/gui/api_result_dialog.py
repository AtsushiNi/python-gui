"""
API実行結果ダイアログ
API実行結果をテーブル形式で表示するダイアログ
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QLineEdit,
    QPushButton,
    QLabel,
    QHeaderView,
    QMessageBox,
    QDialogButtonBox,
)

from src.models.table_model import ApiResultTableModel, SortFilterProxyModel
from src.logger import logger


class ApiResultDialog(QDialog):
    """API実行結果を表示するダイアログ"""

    def __init__(self, results: list = None, parent=None):
        super().__init__(parent)
        self.results = results or []
        self.setup_ui()
        logger.info("API実行結果ダイアログを初期化しました")

    def setup_ui(self):
        """UIを設定します"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ダイアログの基本設定
        self.setWindowTitle("API実行結果")
        self.setMinimumSize(900, 600)

        # タイトル
        title_label = QLabel("API実行結果")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # コントロールパネル
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)

        # テーブルビュー
        self.table_view = self.create_table_view()
        layout.addWidget(self.table_view)

        # ステータスラベル
        self.status_label = QLabel(f"結果: {len(self.results)}件")
        layout.addWidget(self.status_label)

        # ダイアログボタン
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # 詳細表示ボタンを追加
        self.detail_button = QPushButton("詳細表示")
        self.detail_button.clicked.connect(self.show_detail)
        self.detail_button.setEnabled(False)
        button_box.addButton(self.detail_button, QDialogButtonBox.ActionRole)
        
        layout.addWidget(button_box)

        # 結果を設定
        if self.results:
            self.set_results(self.results)

    def create_control_panel(self) -> QWidget:
        """コントロールパネルを作成します"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # フィルターラベル
        filter_label = QLabel("フィルター:")
        layout.addWidget(filter_label)

        # フィルター入力
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("API名、URL、エラーなどを検索...")
        self.filter_edit.textChanged.connect(self.on_filter_changed)
        layout.addWidget(self.filter_edit)

        # クリアボタン
        self.clear_filter_button = QPushButton("フィルタークリア")
        self.clear_filter_button.clicked.connect(self.clear_filter)
        layout.addWidget(self.clear_filter_button)

        layout.addStretch()

        # エクスポートボタン（将来の機能拡張用）
        self.export_button = QPushButton("エクスポート")
        self.export_button.clicked.connect(self.export_results)
        layout.addWidget(self.export_button)

        return panel

    def create_table_view(self) -> QTableView:
        """テーブルビューを作成します"""
        table_view = QTableView()

        # モデルの設定
        self.source_model = ApiResultTableModel()
        self.proxy_model = SortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)

        table_view.setModel(self.proxy_model)

        # テーブルの設定
        table_view.setAlternatingRowColors(True)
        table_view.setSelectionBehavior(QTableView.SelectRows)
        table_view.setSelectionMode(QTableView.SingleSelection)
        table_view.setSortingEnabled(True)

        # ヘッダーの設定
        header = table_view.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionsMovable(True)
        header.setSectionResizeMode(QHeaderView.Interactive)

        # 列幅の設定
        table_view.setColumnWidth(0, 100)  # API名
        table_view.setColumnWidth(1, 80)   # ステータス
        table_view.setColumnWidth(2, 100)  # ステータスコード
        table_view.setColumnWidth(3, 100)  # 応答時間
        table_view.setColumnWidth(4, 80)   # メソッド
        table_view.setColumnWidth(5, 300)  # URL
        table_view.setColumnWidth(6, 150)  # 実行時刻
        table_view.setColumnWidth(7, 200)  # エラー

        # 選択変更時の接続
        table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)

        return table_view

    def set_results(self, results: list):
        """結果を設定します"""
        self.results = results
        self.source_model.set_results(results)
        self.proxy_model.invalidate()
        self.update_status()
        logger.info(f"API実行結果ダイアログに {len(results)} 件の結果を設定しました")

    def on_filter_changed(self, text: str):
        """フィルターが変更された時の処理"""
        self.proxy_model.set_filter_text(text)
        self.update_status()

    def clear_filter(self):
        """フィルターをクリアします"""
        self.filter_edit.clear()
        self.proxy_model.set_filter_text("")
        self.update_status()

    def on_selection_changed(self):
        """選択が変更された時の処理"""
        has_selection = len(self.table_view.selectionModel().selectedRows()) > 0
        self.detail_button.setEnabled(has_selection)

    def show_detail(self):
        """選択された結果の詳細を表示します"""
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            return

        proxy_index = selected[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        result = self.source_model.get_result(source_index.row())

        if not result:
            return

        detail_text = self._build_detail_text(result)

        QMessageBox.information(
            self,
            "API実行詳細",
            detail_text,
            QMessageBox.Ok
        )

    def _build_detail_text(self, result: dict) -> str:
        """詳細テキストを構築します"""
        data = result.get("data", {})
        success = result.get("success", False)
        error = result.get("error", "")

        lines = [
            f"API名: {data.get('api_name', 'N/A')}",
            f"ステータス: {'成功' if success else '失敗'}",
            f"URL: {data.get('url', 'N/A')}",
            f"メソッド: {data.get('method', 'N/A')}",
            f"ステータスコード: {data.get('status_code', 'N/A')}",
            f"応答時間: {data.get('response_time', 0):.3f}秒",
            f"実行時刻: {result.get('timestamp', 'N/A')}",
            "",
            "レスポンスヘッダー:",
        ]

        # ヘッダー
        headers = data.get("headers", {})
        for key, value in headers.items():
            lines.append(f"  {key}: {value}")

        lines.append("")
        lines.append("レスポンスデータ:")

        # レスポンスデータ
        response_data = data.get("data", {})
        if isinstance(response_data, dict):
            for key, value in response_data.items():
                lines.append(f"  {key}: {value}")
        elif isinstance(response_data, list):
            lines.append(f"  リスト ({len(response_data)}件)")
            for i, item in enumerate(response_data[:5]):  # 最初の5件のみ表示
                lines.append(f"  [{i}]: {item}")
            if len(response_data) > 5:
                lines.append(f"  ... 他 {len(response_data) - 5}件")
        else:
            lines.append(f"  {response_data}")

        if error:
            lines.append("")
            lines.append("エラー:")
            lines.append(f"  {error}")

        return "\n".join(lines)

    def export_results(self):
        """結果をエクスポートします（将来の機能拡張用）"""
        QMessageBox.information(
            self,
            "情報",
            "エクスポート機能は現在開発中です。",
            QMessageBox.Ok
        )

    def update_status(self):
        """ステータスを更新します"""
        total_count = self.source_model.rowCount()
        filtered_count = self.proxy_model.rowCount()

        if total_count == filtered_count:
            self.status_label.setText(f"結果: {total_count}件")
        else:
            self.status_label.setText(f"結果: {filtered_count}/{total_count}件 (フィルター中)")

    def get_all_results(self) -> list:
        """すべての結果を取得します"""
        return self.source_model.get_all_results()
