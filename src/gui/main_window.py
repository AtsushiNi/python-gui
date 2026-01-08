"""
メインウィンドウ（新しいAPI定義システム対応）
"""

from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStatusBar,
    QPushButton,
    QLabel,
    QProgressBar,
    QMessageBox,
    QTableView,
    QHeaderView,
    QComboBox,
)

from src.gui.api_config_dialog import ApiConfigDialog
from src.api.client import ApiExecutor
from src.api.definitions import ApiDefinitionManager
from src.config.apis import get_api_definitions
from src.config.settings_manager import get_settings_manager
from src.models.dynamic_result_model import (
    DynamicResultTableModel, DynamicResultSortFilterProxyModel
)
from src.logger import logger


class ApiExecutionThread(QThread):
    """API実行用のスレッド（新しいシステム対応）"""
    
    execution_finished = Signal(list)
    execution_error = Signal(str)
    progress_updated = Signal(int, int)  # 現在, 合計
    
    def __init__(self, definition_manager: ApiDefinitionManager):
        super().__init__()
        self.definition_manager = definition_manager
        self.executor = ApiExecutor(self.on_progress)
    
    def on_progress(self, current, total):
        """進捗報告コールバック"""
        self.progress_updated.emit(current, total)
    
    def run(self):
        try:
            results = self.executor.execute(self.definition_manager)
            self.execution_finished.emit(results)
        except Exception as e:
            self.execution_error.emit(str(e))
        finally:
            self.executor.close()


class DynamicResultPanel(QWidget):
    """動的結果表示パネル"""
    
    results_cleared = Signal()
    
    def __init__(self, definition_manager: ApiDefinitionManager, parent=None):
        super().__init__(parent)
        self.definition_manager = definition_manager
        self.setup_ui()
        logger.info("動的結果表示パネルを初期化しました")
    
    def setup_ui(self):
        """UIを設定します"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # タイトル
        title_label = QLabel("API実行結果")
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
        
        # APIフィルター
        self.api_filter_combo = QComboBox()
        self.api_filter_combo.addItem("すべてのAPI", "")
        self.api_filter_combo.currentIndexChanged.connect(self.on_api_filter_changed)
        layout.addWidget(self.api_filter_combo)
        
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
        self.source_model = DynamicResultTableModel(self.definition_manager)
        self.proxy_model = DynamicResultSortFilterProxyModel()
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
        
        # 選択変更時の接続
        table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        return table_view
    
    
    def on_api_filter_changed(self, index: int):
        """APIフィルターが変更された時の処理"""
        api_id = self.api_filter_combo.currentData()
        # currentData()がNoneを返す可能性があるので安全に処理
        if api_id is None:
            api_id = ""
        self.proxy_model.set_filter_api_id(api_id)
        self.update_status()
    
    def clear_filter(self):
        """フィルターをクリアします"""
        self.api_filter_combo.setCurrentIndex(0)
        self.proxy_model.set_filter_api_id("")
        self.update_status()
    
    def on_selection_changed(self):
        """選択が変更された時の処理"""
        has_selection = len(self.table_view.selectionModel().selectedRows()) > 0
        self.detail_button.setEnabled(has_selection)
    
    def show_detail(self):
        """詳細を表示します"""
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            return
        
        proxy_index = selected[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        item = self.source_model.get_item(source_index.row())
        
        if not item:
            return
        
        detail_text = self._build_detail_text(item)
        
        QMessageBox.information(
            self,
            "詳細情報",
            detail_text,
            QMessageBox.Ok
        )
    
    def _build_detail_text(self, item: dict) -> str:
        """詳細テキストを構築します"""
        lines = [
            f"API名: {item.get('api_name', 'N/A')}",
            f"API ID: {item.get('api_id', 'N/A')}",
        ]
        
        # すべてのフィールドを表示
        for key, value in item.items():
            if key not in ['api_id', 'api_name']:
                lines.append(f"{key}: {value}")
        
        return "\n".join(lines)
    
    def set_results(self, results: list):
        """API実行結果を設定します"""
        self.source_model.set_results(results)
        self.proxy_model.invalidate()
        
        # APIフィルターを更新
        self._update_api_filter()
        
        self.update_status()
        logger.info(f"動的結果パネルに {len(results)} 件のAPI実行結果を設定しました")
    
    def _update_api_filter(self):
        """APIフィルターを更新します"""
        current_api_id = self.api_filter_combo.currentData()
        self.api_filter_combo.clear()
        self.api_filter_combo.addItem("すべてのAPI", "")
        
        # ユニークなAPIを取得
        api_ids = set()
        for item in self.source_model.get_all_items():
            api_id = item.get('api_id')
            api_name = item.get('api_name', api_id)
            if api_id and api_id not in api_ids:
                api_ids.add(api_id)
                self.api_filter_combo.addItem(api_name, api_id)
        
        # 以前の選択を復元
        for i in range(self.api_filter_combo.count()):
            if self.api_filter_combo.itemData(i) == current_api_id:
                self.api_filter_combo.setCurrentIndex(i)
                break
    
    def clear_results(self):
        """結果をクリアします"""
        self.source_model.clear_results()
        self.proxy_model.invalidate()
        
        self.clear_filter()
        self.update_status()
        self.results_cleared.emit()
        logger.info("動的結果パネルをクリアしました")
    
    def update_status(self):
        """ステータスを更新します"""
        total_count = self.source_model.rowCount()
        filtered_count = self.proxy_model.rowCount()
        
        if total_count == filtered_count:
            self.status_label.setText(f"結果: {total_count}件")
        else:
            self.status_label.setText(f"結果: {filtered_count}/{total_count}件 (フィルター中)")


class MainWindow(QMainWindow):
    """メインウィンドウクラス（新しいシステム対応）"""

    def __init__(self) -> None:
        super().__init__()
        logger.info("メインウィンドウを初期化します")

        # 設定の読み込み
        self.definition_manager = self._load_settings()
        
        self.execution_thread = None
        self.last_results = []  # 最後の実行結果を保存
        
        self.setup_ui()
        self.setup_connections()

        logger.info("メインウィンドウの初期化が完了しました")

    def setup_ui(self) -> None:
        """UIを設定します"""
        # ウィンドウの基本設定
        self.setWindowTitle("API Table Viewer (新システム)")
        self.setGeometry(100, 100, 1400, 800)

        # 中央ウィジェットの作成
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 結果表示パネル（動的）
        self.result_panel = self.create_result_panel()
        main_layout.addWidget(self.result_panel)

        # ステータスバー
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備完了")

        # コントロールパネル（実行ボタンなど）
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)

    def open_settings_dialog(self) -> None:
        """設定ダイアログを開きます"""
        dialog = ApiConfigDialog(self.definition_manager, self)
        dialog.configs_changed.connect(self.on_api_configs_changed)
        
        if dialog.exec():
            # OKが押された場合、設定を更新
            self.definition_manager = dialog.get_definition_manager()
            self.status_bar.showMessage("設定を適用しました", 3000)
            logger.info("設定を更新しました")
            
            # 結果パネルを更新
            self.result_panel.definition_manager = self.definition_manager
            self.result_panel.source_model.definition_manager = self.definition_manager
            self.result_panel.source_model._update_merged_fields()
            self.result_panel.source_model.layoutChanged.emit()
            
            # 設定を保存
            self._save_settings()
        else:
            # Cancelが押された場合
            self.status_bar.showMessage("設定をキャンセルしました", 3000)
            logger.info("設定をキャンセルしました")

    def create_result_panel(self) -> DynamicResultPanel:
        """結果表示パネルを作成します"""
        result_panel = DynamicResultPanel(self.definition_manager)
        result_panel.results_cleared.connect(self.on_results_cleared)
        return result_panel

    def create_control_panel(self) -> QWidget:
        """コントロールパネルを作成します"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # 設定ボタン
        self.settings_button = QPushButton("設定")
        self.settings_button.setMinimumWidth(80)
        self.settings_button.clicked.connect(self.open_settings_dialog)
        layout.addWidget(self.settings_button)

        # 実行ボタン
        self.execute_button = QPushButton("APIを実行")
        self.execute_button.setMinimumWidth(100)
        self.execute_button.clicked.connect(self.execute_apis)
        layout.addWidget(self.execute_button)

        # クリアボタン
        self.clear_button = QPushButton("結果をクリア")
        self.clear_button.setMinimumWidth(100)
        self.clear_button.clicked.connect(self.clear_results)
        layout.addWidget(self.clear_button)

        layout.addStretch()

        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # ステータスラベル
        self.status_label = QLabel("準備完了")
        layout.addWidget(self.status_label)

        return panel

    def setup_connections(self) -> None:
        """シグナルとスロットの接続を設定します"""
        # 結果クリア時の接続
        if hasattr(self, 'result_panel'):
            self.result_panel.results_cleared.connect(self.on_results_cleared)

    def on_api_configs_changed(self) -> None:
        """API設定が変更された時の処理"""
        self.status_bar.showMessage("API設定が更新されました", 3000)

    def on_results_cleared(self) -> None:
        """結果がクリアされた時の処理"""
        self.status_bar.showMessage("結果をクリアしました", 3000)

    @Slot()
    def execute_apis(self) -> None:
        """APIを実行します"""
        # 有効なAPI定義の確認
        enabled_defs = self.definition_manager.get_enabled_definitions()
        
        if not enabled_defs:
            QMessageBox.warning(self, "警告", "実行可能なAPIがありません。APIを有効にしてください。")
            return
        
        # 設定の検証（簡易）
        errors = []
        for api_def in enabled_defs:
            if not api_def.url.strip():
                errors.append(f"{api_def.name}: URLを入力してください")
            elif not api_def.url.startswith(("http://", "https://")):
                errors.append(f"{api_def.name}: URLは http:// または https:// で始まる必要があります")
        
        if errors:
            QMessageBox.warning(
                self,
                "設定エラー",
                "以下のAPIにエラーがあります:\n\n" + "\n".join(errors)
            )
            return
        
        # UIの準備
        self.set_execution_ui_state(True)
        self.status_bar.showMessage(f"{len(enabled_defs)}個のAPIを実行中...")
        
        # スレッドで実行
        self.execution_thread = ApiExecutionThread(self.definition_manager)
        self.execution_thread.execution_finished.connect(self.on_execution_finished)
        self.execution_thread.execution_error.connect(self.on_execution_error)
        self.execution_thread.progress_updated.connect(self.on_progress_updated)
        self.execution_thread.start()

    @Slot()
    def clear_results(self) -> None:
        """結果をクリアします"""
        if hasattr(self, 'result_panel'):
            self.result_panel.clear_results()
        
        # 最後の実行結果もクリア
        self.last_results = []
        
        self.status_bar.showMessage("結果をクリアしました", 3000)

    @Slot(list)
    def on_execution_finished(self, results: list) -> None:
        """API実行が完了した時の処理"""
        # 結果を保存
        self.last_results = results
        
        # 結果を表示
        if hasattr(self, 'result_panel'):
            self.result_panel.set_results(results)
        
        # 成功/失敗のカウント
        success_count = sum(1 for r in results if r.get('success', False))
        total_count = len(results)
        
        # UIの復旧
        self.set_execution_ui_state(False)
        
        # ステータス更新
        self.status_bar.showMessage(
            f"API実行完了: {success_count}/{total_count} 成功", 
            5000
        )
        
        # スレッドのクリーンアップ
        self.execution_thread = None

    @Slot(str)
    def on_execution_error(self, error_message: str) -> None:
        """API実行中にエラーが発生した時の処理"""
        # UIの復旧
        self.set_execution_ui_state(False)
        
        # エラーメッセージ表示
        self.status_bar.showMessage("API実行中にエラーが発生しました", 5000)
        QMessageBox.critical(
            self,
            "実行エラー",
            f"API実行中にエラーが発生しました:\n\n{error_message}"
        )
        
        # スレッドのクリーンアップ
        self.execution_thread = None

    @Slot(int, int)
    def on_progress_updated(self, current: int, total: int):
        """進捗が更新された時の処理"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.status_label.setText(f"実行中: {current}/{total}")
    
    def set_execution_ui_state(self, executing: bool):
        """実行中のUI状態を設定"""
        self.execute_button.setEnabled(not executing)
        self.settings_button.setEnabled(not executing)
        self.clear_button.setEnabled(not executing)
        self.progress_bar.setVisible(executing)
        
        if executing:
            self.progress_bar.setValue(0)
            self.status_label.setText("実行中...")
        else:
            self.status_label.setText("準備完了")
    
    def _load_settings(self) -> ApiDefinitionManager:
        """設定を読み込む"""
        settings_manager = get_settings_manager()
        loaded_definitions = settings_manager.load_settings()
        
        if loaded_definitions is not None:
            # 設定ファイルから読み込んだ定義を使用
            logger.info(f"設定ファイルから {len(loaded_definitions)} 個のAPI定義を読み込みました")
            return ApiDefinitionManager(loaded_definitions)
        else:
            # デフォルトの定義を使用
            logger.info("設定ファイルがないため、デフォルトのAPI定義を使用します")
            api_definitions = get_api_definitions()
            return ApiDefinitionManager(api_definitions)
    
    def _save_settings(self):
        """設定を保存"""
        try:
            settings_manager = get_settings_manager()
            success = settings_manager.save_settings(self.definition_manager)
            if success:
                logger.info("設定を保存しました")
            else:
                logger.warning("設定の保存に失敗しました")
        except Exception as e:
            logger.error(f"設定保存中にエラーが発生しました: {e}")
    
    def closeEvent(self, event):
        """ウィンドウが閉じられる時の処理"""
        logger.info("アプリケーションを終了します")
        event.accept()
