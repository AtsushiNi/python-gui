"""
結果表示パネル
テーブル表示とソート・フィルター機能を提供します
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
    QTabWidget,
    QComboBox,
)

from models.table_model import ApiResultTableModel, SortFilterProxyModel
from models.applications_table_model import ApplicationsTableModel, ApplicationsSortFilterProxyModel
from logger import logger


class ResultPanel(QWidget):
    """結果表示パネル"""

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
        title_label = QLabel("API実行結果")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # アプリケーションデータタブ（初期表示）
        self.applications_tab = self.create_applications_tab()
        self.tab_widget.addTab(self.applications_tab, "アプリケーションデータ")
        
        # API実行結果タブ
        self.api_results_tab = self.create_api_results_tab()
        self.tab_widget.addTab(self.api_results_tab, "API実行結果")
        
        layout.addWidget(self.tab_widget)

        # ステータスバー
        self.status_label = QLabel("結果: 0件")
        layout.addWidget(self.status_label)
        
        # 現在のタブを追跡
        self.current_tab_index = 0
        self.tab_widget.currentChanged.connect(self.on_tab_changed)





    # 新しいメソッドの追加
    def create_api_results_tab(self) -> QWidget:
        """API実行結果タブを作成します"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # コントロールパネル
        self.api_control_panel = self.create_api_control_panel()
        layout.addWidget(self.api_control_panel)
        
        # テーブルビュー
        self.api_table_view = self.create_api_table_view()
        layout.addWidget(self.api_table_view)
        
        return tab
    
    def create_applications_tab(self) -> QWidget:
        """アプリケーションデータタブを作成します"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # コントロールパネル
        self.app_control_panel = self.create_applications_control_panel()
        layout.addWidget(self.app_control_panel)
        
        # テーブルビュー
        self.app_table_view = self.create_applications_table_view()
        layout.addWidget(self.app_table_view)
        
        return tab
    
    def create_api_control_panel(self) -> QWidget:
        """API実行結果用のコントロールパネルを作成します"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # フィルターラベル
        filter_label = QLabel("フィルター:")
        layout.addWidget(filter_label)
        
        # フィルター入力
        self.api_filter_edit = QLineEdit()
        self.api_filter_edit.setPlaceholderText("API名、URL、エラーなどを検索...")
        self.api_filter_edit.textChanged.connect(self.on_api_filter_changed)
        layout.addWidget(self.api_filter_edit)
        
        # クリアボタン
        self.api_clear_filter_button = QPushButton("フィルタークリア")
        self.api_clear_filter_button.clicked.connect(self.clear_api_filter)
        layout.addWidget(self.api_clear_filter_button)
        
        layout.addStretch()
        
        # 詳細表示ボタン
        self.api_detail_button = QPushButton("詳細表示")
        self.api_detail_button.clicked.connect(self.show_api_detail)
        self.api_detail_button.setEnabled(False)
        layout.addWidget(self.api_detail_button)
        
        return panel
    
    def create_applications_control_panel(self) -> QWidget:
        """アプリケーションデータ用のコントロールパネルを作成します"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # フィルターラベル
        filter_label = QLabel("フィルター:")
        layout.addWidget(filter_label)
        
        # フィルター入力
        self.app_filter_edit = QLineEdit()
        self.app_filter_edit.setPlaceholderText("タイトル、申請者、ステータスなどを検索...")
        self.app_filter_edit.textChanged.connect(self.on_app_filter_changed)
        layout.addWidget(self.app_filter_edit)
        
        # APIタイプフィルター
        type_label = QLabel("APIタイプ:")
        layout.addWidget(type_label)
        
        self.app_type_combo = QComboBox()
        self.app_type_combo.addItems(["すべて", "Type A", "Type B", "Type C"])
        self.app_type_combo.currentTextChanged.connect(self.on_app_type_filter_changed)
        layout.addWidget(self.app_type_combo)
        
        # クリアボタン
        self.app_clear_filter_button = QPushButton("フィルタークリア")
        self.app_clear_filter_button.clicked.connect(self.clear_app_filter)
        layout.addWidget(self.app_clear_filter_button)
        
        layout.addStretch()
        
        # 詳細表示ボタン
        self.app_detail_button = QPushButton("詳細表示")
        self.app_detail_button.clicked.connect(self.show_app_detail)
        self.app_detail_button.setEnabled(False)
        layout.addWidget(self.app_detail_button)
        
        return panel
    
    def create_api_table_view(self) -> QTableView:
        """API実行結果用のテーブルビューを作成します"""
        table_view = QTableView()
        
        # モデルの設定
        self.api_source_model = ApiResultTableModel()
        self.api_proxy_model = SortFilterProxyModel()
        self.api_proxy_model.setSourceModel(self.api_source_model)
        
        table_view.setModel(self.api_proxy_model)
        
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
        table_view.selectionModel().selectionChanged.connect(self.on_api_selection_changed)
        
        return table_view
    
    def create_applications_table_view(self) -> QTableView:
        """アプリケーションデータ用のテーブルビューを作成します"""
        table_view = QTableView()
        
        # モデルの設定
        self.app_source_model = ApplicationsTableModel()
        self.app_proxy_model = ApplicationsSortFilterProxyModel()
        self.app_proxy_model.setSourceModel(self.app_source_model)
        
        table_view.setModel(self.app_proxy_model)
        
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
        table_view.selectionModel().selectionChanged.connect(self.on_app_selection_changed)
        
        return table_view
    
    def on_tab_changed(self, index: int):
        """タブが変更された時の処理"""
        self.current_tab_index = index
        self.update_status()
    
    def on_api_filter_changed(self, text: str):
        """API実行結果のフィルターが変更された時の処理"""
        self.api_proxy_model.set_filter_text(text)
        self.update_status()
    
    def on_app_filter_changed(self, text: str):
        """アプリケーションデータのフィルターが変更された時の処理"""
        self.app_proxy_model.set_filter_text(text)
        self.update_status()
    
    def on_app_type_filter_changed(self, text: str):
        """アプリケーションデータのAPIタイプフィルターが変更された時の処理"""
        if text == "すべて":
            self.app_proxy_model.set_filter_api_type("")
        elif text == "Type A":
            self.app_proxy_model.set_filter_api_type("A")
        elif text == "Type B":
            self.app_proxy_model.set_filter_api_type("B")
        elif text == "Type C":
            self.app_proxy_model.set_filter_api_type("C")
        self.update_status()
    
    def clear_api_filter(self):
        """API実行結果のフィルターをクリアします"""
        self.api_filter_edit.clear()
        self.api_proxy_model.set_filter_text("")
        self.update_status()
    
    def clear_app_filter(self):
        """アプリケーションデータのフィルターをクリアします"""
        self.app_filter_edit.clear()
        self.app_type_combo.setCurrentIndex(0)
        self.app_proxy_model.set_filter_text("")
        self.app_proxy_model.set_filter_api_type("")
        self.update_status()
    
    def on_api_selection_changed(self):
        """API実行結果の選択が変更された時の処理"""
        has_selection = len(self.api_table_view.selectionModel().selectedRows()) > 0
        self.api_detail_button.setEnabled(has_selection)
    
    def on_app_selection_changed(self):
        """アプリケーションデータの選択が変更された時の処理"""
        has_selection = len(self.app_table_view.selectionModel().selectedRows()) > 0
        self.app_detail_button.setEnabled(has_selection)
    
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

    def show_api_detail(self):
        """API実行結果の詳細を表示します"""
        selected = self.api_table_view.selectionModel().selectedRows()
        if not selected:
            return
        
        proxy_index = selected[0]
        source_index = self.api_proxy_model.mapToSource(proxy_index)
        result = self.api_source_model.get_result(source_index.row())
        
        if not result:
            return
        
        detail_text = self._build_detail_text(result)
        
        QMessageBox.information(
            self,
            "API実行詳細",
            detail_text,
            QMessageBox.Ok
        )
    
    def show_app_detail(self):
        """アプリケーションデータの詳細を表示します"""
        selected = self.app_table_view.selectionModel().selectedRows()
        if not selected:
            return
        
        proxy_index = selected[0]
        source_index = self.app_proxy_model.mapToSource(proxy_index)
        application = self.app_source_model.get_application(source_index.row())
        
        if not application:
            return
        
        detail_text = self._build_app_detail_text(application)
        
        QMessageBox.information(
            self,
            "アプリケーション詳細",
            detail_text,
            QMessageBox.Ok
        )
    
    def _build_app_detail_text(self, application: dict) -> str:
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
        """結果を設定します"""
        # API実行結果を設定
        self.api_source_model.set_results(results)
        self.api_proxy_model.invalidate()
        
        # applicationsデータを抽出して設定
        from api.client import ApiExecutor
        executor = ApiExecutor()
        applications = executor.extract_applications_data(results)
        self.app_source_model.set_applications(applications)
        self.app_proxy_model.invalidate()
        
        self.update_status()
        logger.info(f"結果表示パネルに {len(results)} 件の結果を設定しました")
        logger.info(f"アプリケーションデータに {len(applications)} 件のデータを設定しました")
    
    def add_result(self, result: dict):
        """結果を追加します"""
        self.api_source_model.add_result(result)
        self.api_proxy_model.invalidate()
        
        # applicationsデータも更新（簡易実装）
        from api.client import ApiExecutor
        executor = ApiExecutor()
        current_results = self.api_source_model.get_all_results()
        applications = executor.extract_applications_data(current_results)
        self.app_source_model.set_applications(applications)
        self.app_proxy_model.invalidate()
        
        self.update_status()
    
    def clear_results(self):
        """結果をクリアします"""
        self.api_source_model.clear_results()
        self.api_proxy_model.invalidate()
        self.app_source_model.clear_applications()
        self.app_proxy_model.invalidate()
        
        self.clear_api_filter()
        self.clear_app_filter()
        self.update_status()
        self.results_cleared.emit()
        logger.info("結果表示パネルをクリアしました")
    
    def update_status(self):
        """ステータスを更新します"""
        if self.current_tab_index == 0:  # API実行結果タブ
            total_count = self.api_source_model.rowCount()
            filtered_count = self.api_proxy_model.rowCount()
            
            if total_count == filtered_count:
                self.status_label.setText(f"API実行結果: {total_count}件")
            else:
                self.status_label.setText(f"API実行結果: {filtered_count}/{total_count}件 (フィルター中)")
        else:  # アプリケーションデータタブ
            total_count = self.app_source_model.rowCount()
            filtered_count = self.app_proxy_model.rowCount()
            
            if total_count == filtered_count:
                self.status_label.setText(f"アプリケーションデータ: {total_count}件")
            else:
                self.status_label.setText(f"アプリケーションデータ: {filtered_count}/{total_count}件 (フィルター中)")
    
    
    def get_all_results(self) -> list:
        """すべての結果を取得します"""
        return self.api_source_model.get_all_results()
    
    def get_all_applications(self) -> list:
        """すべてのアプリケーションデータを取得します"""
        return self.app_source_model.get_all_applications()
