"""
メインウィンドウ
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
)

from src.gui.api_dialog import ApiDialog
from src.gui.api_result_dialog import ApiResultDialog
from src.gui.result_panel import ResultPanel
from src.api.client import ApiExecutor
from src.logger import logger


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
        self.config_manager = None  # 設定マネージャー
        self.last_results = []  # 最後の実行結果を保存
        
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

        # 結果表示パネル（全画面）
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
        dialog = ApiDialog(self.config_manager, self)
        dialog.configs_changed.connect(self.on_api_configs_changed)
        
        if dialog.exec():
            # OKが押された場合、設定を更新
            self.config_manager = dialog.get_config_manager()
            self.status_bar.showMessage("設定を適用しました", 3000)
            logger.info("設定を更新しました")
        else:
            # Cancelが押された場合
            self.status_bar.showMessage("設定をキャンセルしました", 3000)
            logger.info("設定をキャンセルしました")

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

        # API実行結果表示ボタン
        self.show_results_button = QPushButton("API実行結果を表示")
        self.show_results_button.setMinimumWidth(120)
        self.show_results_button.clicked.connect(self.show_api_results)
        self.show_results_button.setEnabled(False)  # 初期状態では無効
        layout.addWidget(self.show_results_button)

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
        # 設定マネージャーの確認
        if self.config_manager is None:
            QMessageBox.warning(self, "警告", "まず設定を開いてAPIを設定してください。")
            return
        
        # 設定の取得
        enabled_configs = self.config_manager.get_enabled_configs()
        
        if not enabled_configs:
            QMessageBox.warning(self, "警告", "実行可能なAPIがありません。APIを有効にしてください。")
            return
        
        # 設定の検証
        errors = self.config_manager.validate_all()
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
        
        # 最後の実行結果もクリア
        self.last_results = []
        self.show_results_button.setEnabled(False)
        
        self.status_bar.showMessage("結果をクリアしました", 3000)

    @Slot(list)
    def on_execution_finished(self, results: list) -> None:
        """API実行が完了した時の処理"""
        # 結果を保存
        self.last_results = results
        
        # アプリケーションデータを表示
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
        
        # API実行結果表示ボタンを有効化
        self.show_results_button.setEnabled(True)
        
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
        self.show_results_button.setEnabled(not executing and len(self.last_results) > 0)
        self.progress_bar.setVisible(executing)
        
        if executing:
            self.progress_bar.setValue(0)
            self.status_label.setText("準備中...")
        else:
            self.status_label.setText("準備完了")

    def show_api_results(self) -> None:
        """API実行結果を表示します"""
        if not self.last_results:
            QMessageBox.information(
                self,
                "情報",
                "表示するAPI実行結果がありません。\nまずAPIを実行してください。"
            )
            return
        
        # 成功/失敗のカウント
        success_count = sum(1 for r in self.last_results if r.get('success', False))
        total_count = len(self.last_results)
        
        # API実行結果をダイアログで表示
        dialog = ApiResultDialog(self.last_results, self)
        dialog.setWindowTitle(f"API実行結果 ({success_count}/{total_count} 成功)")
        dialog.exec()

    def closeEvent(self, event) -> None:
        """ウィンドウを閉じる時の処理"""
        logger.info("アプリケーションを終了します")
        event.accept()
