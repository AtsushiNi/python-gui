"""
結果表示パネル
アプリケーションデータの表示とソート・フィルター機能を提供します
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QLineEdit,
    QPushButton,
    QLabel,
    QHeaderView,
    QMessageBox,
    QComboBox,
)

from src.models.applications_table_model import ApplicationsTableModel, ApplicationsSortFilterProxyModel
from src.logger import logger


class ResultPanel(QWidget):
    """結果表示パネル（アプリケーションデータ専用）"""

    results_cleared = Signal()  # 結果クリア時に発火

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        logger.info("結果表示パネルを初期化しました")

    def setup_ui(self):
        """UIを設定します"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # タイトル
        title_label = QLabel("アプリケーションデータ")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # コントロールパネル
        self.control_panel = self.create_control_panel()
        layout.addWidget(self.control_panel)
        
        # テーブルビュー
        self.table_view = self.create_table_view()
        layout.addWidget(self.table_view)

        # ステータスバー
        self.status_label = QLabel("結果: 0件")
        layout.addWidget(self.status_label)

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
        self.filter_edit.setPlaceholderText("タイトル、申請者、ステータスなどを検索...")
        self.filter_edit.textChanged.connect(self.on_filter_changed)
        layout.addWidget(self.filter_edit)
        
        # APIタイプフィルター
        type_label = QLabel("APIタイプ:")
        layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["すべて", "Type A", "Type B", "Type C"])
        self.type_combo.currentTextChanged.connect(self.on_type_filter_changed)
        layout.addWidget(self.type_combo)
        
        # クリアボタン
        self.clear_filter_button = QPushButton("フィルタークリア")
        self.clear_filter_button.clicked.connect(self.clear_filter)
        layout.addWidget(self.clear_filter_button)
        
        layout.addStretch()
        
        # 詳細表示ボタン
        self.detail_button = QPushButton("詳細表示")
        self.detail_button.clicked.connect(self.show_detail)
        self.detail_button.setEnabled(False)
        layout.addWidget(self.detail_button)
        
        return panel
    
    def create_table_view(self) -> QTableView:
        """テーブルビューを作成します"""
        table_view = QTableView()
        
        # モデルの設定
        self.source_model = ApplicationsTableModel()
        self.proxy_model = ApplicationsSortFilterProxyModel()
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
        table_view.setColumnWidth(0, 80)   # APIタイプ
        table_view.setColumnWidth(1, 100)  # ID
        table_view.setColumnWidth(2, 200)  # タイトル
        table_view.setColumnWidth(3, 80)   # ステータス
        table_view.setColumnWidth(4, 120)  # 申請者名
        table_view.setColumnWidth(5, 150)  # 申請日時
        table_view.setColumnWidth(6, 120)  # タイプ固有1
        table_view.setColumnWidth(7, 120)  # タイプ固有2
        table_view.setColumnWidth(8, 100)  # タイプ固有3
        
        # 選択変更時の接続
        table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        return table_view
    
    def on_filter_changed(self, text: str):
        """フィルターが変更された時の処理"""
        self.proxy_model.set_filter_text(text)
        self.update_status()
    
    def on_type_filter_changed(self, text: str):
        """APIタイプフィルターが変更された時の処理"""
        if text == "すべて":
            self.proxy_model.set_filter_api_type("")
        elif text == "Type A":
            self.proxy_model.set_filter_api_type("A")
        elif text == "Type B":
            self.proxy_model.set_filter_api_type("B")
        elif text == "Type C":
            self.proxy_model.set_filter_api_type("C")
        self.update_status()
    
    def clear_filter(self):
        """フィルターをクリアします"""
        self.filter_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self.proxy_model.set_filter_text("")
        self.proxy_model.set_filter_api_type("")
        self.update_status()
    
    def on_selection_changed(self):
        """選択が変更された時の処理"""
        has_selection = len(self.table_view.selectionModel().selectedRows()) > 0
        self.detail_button.setEnabled(has_selection)
    
    def show_detail(self):
        """アプリケーションデータの詳細を表示します"""
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            return
        
        proxy_index = selected[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        application = self.source_model.get_application(source_index.row())
        
        if not application:
            return
        
        detail_text = self._build_detail_text(application)
        
        QMessageBox.information(
            self,
            "アプリケーション詳細",
            detail_text,
            QMessageBox.Ok
        )
    
    def _build_detail_text(self, application: dict) -> str:
        """アプリケーションデータの詳細テキストを構築します"""
        lines = [
            f"APIタイプ: {application.get('api_type', 'N/A')}",
            f"ID: {application.get('id', 'N/A')}",
            f"タイトル: {application.get('title', 'N/A')}",
            f"ステータス: {application.get('status', 'N/A')}",
            f"申請日時: {application.get('createdAt', 'N/A')}",
        ]
        
        # 申請者情報
        applicant = application.get("applicant", {})
        if isinstance(applicant, dict):
            lines.append(f"申請者ID: {applicant.get('id', 'N/A')}")
            lines.append(f"申請者名: {applicant.get('name', 'N/A')}")
        
        # タイプ固有の情報
        api_type = application.get("api_type", "")
        if api_type == "A":
            lines.append(f"金額: {application.get('amount', 'N/A')} {application.get('currency', 'JPY')}")
            lines.append(f"経費カテゴリー: {application.get('expenseCategory', 'N/A')}")
            lines.append("タイプ: 経費申請")
        elif api_type == "B":
            lines.append(f"開始日: {application.get('startDate', 'N/A')}")
            lines.append(f"終了日: {application.get('endDate', 'N/A')}")
            lines.append(f"日数: {application.get('days', 'N/A')}日")
            lines.append("タイプ: 休暇申請")
        elif api_type == "C":
            lines.append(f"要求権限: {application.get('requestedRole', 'N/A')}")
            
            # 承認フローの詳細
            approval_flow = application.get("approvalFlow", [])
            if isinstance(approval_flow, list) and len(approval_flow) > 0:
                lines.append("承認フロー:")
                for i, step in enumerate(approval_flow):
                    approver = step.get("approver", {})
                    approver_name = approver.get("name", "N/A") if isinstance(approver, dict) else "N/A"
                    step_status = step.get("status", "N/A")
                    lines.append(f"  ステップ {step.get('step', i+1)}: {approver_name} - {step_status}")
            else:
                lines.append("承認フロー: なし")
            
            lines.append("タイプ: 権限申請")
        
        return "\n".join(lines)
    
    def set_results(self, results: list):
        """API実行結果からアプリケーションデータを抽出して設定します"""
        from src.api.client import ApiExecutor
        executor = ApiExecutor()
        applications = executor.extract_applications_data(results)
        self.source_model.set_applications(applications)
        self.proxy_model.invalidate()
        
        self.update_status()
        logger.info(f"アプリケーションデータに {len(applications)} 件のデータを設定しました")
    
    def clear_results(self):
        """結果をクリアします"""
        self.source_model.clear_applications()
        self.proxy_model.invalidate()
        
        self.clear_filter()
        self.update_status()
        self.results_cleared.emit()
        logger.info("結果表示パネルをクリアしました")
    
    def update_status(self):
        """ステータスを更新します"""
        total_count = self.source_model.rowCount()
        filtered_count = self.proxy_model.rowCount()
        
        if total_count == filtered_count:
            self.status_label.setText(f"アプリケーションデータ: {total_count}件")
        else:
            self.status_label.setText(f"アプリケーションデータ: {filtered_count}/{total_count}件 (フィルター中)")
    
    def get_all_applications(self) -> list:
        """すべてのアプリケーションデータを取得します"""
        return self.source_model.get_all_applications()
