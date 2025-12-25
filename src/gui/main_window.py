"""
メインウィンドウ
"""

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QStatusBar,
    QPushButton,
    QLabel,
    QProgressBar,
    QMessageBox,
)

from gui.api_panel import ApiPanel
from gui.result_panel import ResultPanel
from api.client import ApiExecutor
from logger import logger


class ApiExecutionThread(QThread):
    """API実行用のスレッド"""
    
    execution_finished = Signal(list)
    execution_error = Signal(str)
    progress_updated = Signal(int, int)  # 現在, 合計
    
    def __init__(self, configs):
        super().__init__()
        self.configs = configs
        self.executor = ApiExecutor(self.on_progress)
    
    def on_progress(self, current, total):
        """進捗報告コールバック"""
        self.progress_updated.emit(current, total)
    
    def run(self):
        try:
            results = self.executor.execute(self.configs)
            self.execution_finished.emit(results)
        except Exception as e:
            self.execution_error.emit(str(e))
        finally:
            self.executor.close()


class MainWindow(QMainWindow):
    """メインウィンドウクラス"""

    def __init__(self) -> None:
        super().__init__()
        logger.info("メインウィンドウを初期化します")

        self.api_executor = None
        self.execution_thread = None
        
        self.setup_ui()
        self.setup_connections()

        logger.info("メインウィンドウの初期化が完了しました")

    def setup_ui(self) -> None:
        """UIを設定します"""
        # ウィンドウの基本設定
        self.setWindowTitle("API Table Viewer")
        self.setGeometry(100, 100, 1200, 700)

        # 中央ウィジェットの作成
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # スプリッターで左側（設定）と右側（結果）を分割
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左側：API設定パネル
        self.api_panel = self.create_api_panel()
        self.api_panel.setMinimumWidth(400)
        splitter.addWidget(self.api_panel)

        # 右側：結果表示パネル
        self.result_panel = self.create_result_panel()
        splitter.addWidget(self.result_panel)

        # スプリッターの初期サイズ設定
        splitter.setSizes([400, 800])

        # ステータスバー
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備完了")

        # コントロールパネル（実行ボタンなど）
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)

    def create_api_panel(self) -> QWidget:
        """API設定パネルを作成します"""
        self.api_panel_widget = ApiPanel()
        self.api_panel_widget.configs_changed.connect(self.on_api_configs_changed)
        return self.api_panel_widget

    def create_result_panel(self) -> QWidget:
        """結果表示パネルを作成します"""
        self.result_panel_widget = ResultPanel()
        self.result_panel_widget.results_cleared.connect(self.on_results_cleared)
        return self.result_panel_widget

    def create_control_panel(self) -> QWidget:
        """コントロールパネルを作成します"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

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
        # API設定変更時の接続
        if hasattr(self, 'api_panel_widget'):
            self.api_panel_widget.configs_changed.connect(self.on_api_configs_changed)
        
        # 結果クリア時の接続
        if hasattr(self, 'result_panel_widget'):
            self.result_panel_widget.results_cleared.connect(self.on_results_cleared)

    def on_api_configs_changed(self) -> None:
        """API設定が変更された時の処理"""
        self.status_bar.showMessage("API設定が更新されました", 3000)

    def on_results_cleared(self) -> None:
        """結果がクリアされた時の処理"""
        self.status_bar.showMessage("結果をクリアしました", 3000)

    @Slot()
    def execute_apis(self) -> None:
        """APIを実行します"""
        # 設定の取得
        config_manager = self.api_panel_widget.get_config_manager()
        enabled_configs = config_manager.get_enabled_configs()
        
        if not enabled_configs:
            QMessageBox.warning(self, "警告", "実行可能なAPIがありません。APIを有効にしてください。")
            return
        
        # 設定の検証
        errors = config_manager.validate_all()
        if errors:
            error_messages = []
            for index, error_list in errors.items():
                error_messages.append(f"API {index + 1}: {', '.join(error_list)}")
            
            QMessageBox.warning(
                self,
                "設定エラー",
                "以下のAPIにエラーがあります:\n\n" + "\n".join(error_messages)
            )
            return
        
        # 実行前の確認
        reply = QMessageBox.question(
            self,
            "確認",
            f"{len(enabled_configs)}個のAPIを実行します。よろしいですか？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # UIの準備
        self.set_execution_ui_state(True)
        self.status_bar.showMessage(f"{len(enabled_configs)}個のAPIを実行中...")
        
        # スレッドで実行
        self.execution_thread = ApiExecutionThread(enabled_configs)
        self.execution_thread.execution_finished.connect(self.on_execution_finished)
        self.execution_thread.execution_error.connect(self.on_execution_error)
        self.execution_thread.progress_updated.connect(self.on_progress_updated)
        self.execution_thread.start()

    @Slot()
    def clear_results(self) -> None:
        """結果をクリアします"""
        if hasattr(self, 'result_panel_widget'):
            self.result_panel_widget.clear_results()
        self.status_bar.showMessage("結果をクリアしました", 3000)

    @Slot(list)
    def on_execution_finished(self, results: list) -> None:
        """API実行が完了した時の処理"""
        # 結果を表示
        if hasattr(self, 'result_panel_widget'):
            self.result_panel_widget.set_results(results)
        
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
        
        # 結果表示
        if success_count == total_count:
            QMessageBox.information(
                self,
                "完了",
                f"すべてのAPIが正常に実行されました。\n成功: {success_count}/{total_count}"
            )
        else:
            QMessageBox.warning(
                self,
                "完了",
                f"API実行が完了しました。\n成功: {success_count}/{total_count}"
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
    def on_progress_updated(self, current: int, total: int) -> None:
        """進捗状況が更新された時の処理"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"実行中: {current}/{total}")

    def set_execution_ui_state(self, executing: bool) -> None:
        """実行中のUI状態を設定します"""
        self.execute_button.setEnabled(not executing)
        self.clear_button.setEnabled(not executing)
        self.progress_bar.setVisible(executing)
        
        if executing:
            self.progress_bar.setValue(0)
            self.status_label.setText("準備中...")
        else:
            self.status_label.setText("準備完了")

    def closeEvent(self, event) -> None:
        """ウィンドウを閉じる時の処理"""
        logger.info("アプリケーションを終了します")
        event.accept()
