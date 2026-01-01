"""
APIクライアント
requestsを使用してAPIを実行します
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple, Callable
import requests
from requests.exceptions import RequestException, Timeout

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.api_config import ApiConfig
from logger import logger


class ApiClient:
    """APIクライアントクラス"""

    def __init__(self):
        self.session = requests.Session()
        # セッション設定
        self.session.headers.update({
            "User-Agent": "API Table Viewer/1.0",
            "Accept": "application/json",
        })

    def execute_api(self, config: ApiConfig) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        単一のAPIを実行します

        Args:
            config: API設定

        Returns:
            (成功可否, レスポンスデータ, エラーメッセージ)
        """
        if not config.enabled:
            return False, {}, "APIが無効です"

        # 設定の検証
        errors = config.validate()
        if errors:
            return False, {}, f"設定エラー: {', '.join(errors)}"

        try:
            logger.info(f"API実行開始: {config.name} ({config.url})")

            # リクエストパラメータの準備
            request_kwargs = {
                "headers": {"Content-Type": "application/json"},
                "json": config.filter_params or {},
            }

            # リクエスト実行
            start_time = time.time()
            response = self.session.post(
                url=config.url,
                **request_kwargs
            )
            elapsed_time = time.time() - start_time

            logger.info(f"API応答: {config.name} - ステータス: {response.status_code}, 時間: {elapsed_time:.2f}s")

            # レスポンスの処理
            response_data = self._process_response(response)

            # 結果の構築
            result = {
                "api_name": config.name,
                "url": config.url,
                "method": "POST",
                "status_code": response.status_code,
                "response_time": elapsed_time,
                "success": response.ok,
                "data": response_data,
                "headers": dict(response.headers),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            if not response.ok:
                error_msg = f"HTTPエラー: {response.status_code} - {response.reason}"
                return False, result, error_msg

            return True, result, None

        except Timeout:
            error_msg = f"タイムアウト: 30秒経過"
            logger.warning(f"APIタイムアウト: {config.name}")
            return False, {}, error_msg

        except RequestException as e:
            error_msg = f"リクエストエラー: {str(e)}"
            logger.error(f"APIリクエストエラー: {config.name} - {e}")
            return False, {}, error_msg

        except Exception as e:
            error_msg = f"予期せぬエラー: {str(e)}"
            logger.error(f"API実行エラー: {config.name} - {e}")
            return False, {}, error_msg

    def _process_response(self, response: requests.Response) -> Any:
        """
        レスポンスを処理します

        Args:
            response: レスポンスオブジェクト

        Returns:
            処理されたデータ
        """
        content_type = response.headers.get("Content-Type", "")

        # JSONレスポンス
        if "application/json" in content_type:
            try:
                return response.json()
            except json.JSONDecodeError:
                logger.warning(f"JSON解析エラー")
                return {"raw_response": response.text}

        # テキストレスポンス
        elif "text/" in content_type:
            return {"text": response.text}

        # その他のレスポンス
        else:
            return {"content_type": content_type, "size": len(response.content)}

    def close(self):
        """セッションを閉じます"""
        self.session.close()
        logger.info("APIセッションを閉じました")


class ApiExecutor:
    """API実行を管理するクラス"""

    def __init__(self, progress_callback=None):
        self.client = ApiClient()
        self.results: List[Dict[str, Any]] = []
        self.progress_callback = progress_callback

    def execute(self, configs: List[ApiConfig]) -> List[Dict[str, Any]]:
        """
        APIを実行し、結果を返します

        Args:
            configs: API設定リスト

        Returns:
            実行結果リスト
        """
        logger.info(f"{len(configs)}個のAPIを実行します")

        self.results = []
        
        for i, config in enumerate(configs):
            # 進捗報告
            if self.progress_callback:
                self.progress_callback(i + 1, len(configs))
            
            # API実行
            success, data, error = self.client.execute_api(config)
            
            result = {
                "index": i,
                "success": success,
                "data": data,
                "error": error,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.results.append(result)

            if success:
                logger.info(f"API {i+1} 実行成功: {config.name}")
            else:
                logger.warning(f"API {i+1} 実行失敗: {config.name} - {error}")

        logger.info(f"API実行完了: {len([r for r in self.results if r['success']])}/{len(self.results)} 成功")
        return self.results

    def close(self):
        """リソースを解放します"""
        self.client.close()

    def extract_applications_data(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        API実行結果からapplicationsデータを抽出します
        
        Args:
            results: API実行結果リスト
            
        Returns:
            抽出されたapplicationsデータリスト
        """
        applications = []
        
        for result in results:
            if not result.get("success", False):
                # エラーの場合はエラー情報をapplicationsとして追加
                error_data = {
                    "api_type": "error",
                    "id": f"ERROR-{len(applications)+1:03d}",
                    "title": "API実行エラー",
                    "status": "ERROR",
                    "applicant": {"name": "システム"},
                    "createdAt": result.get("timestamp", ""),
                    "error_message": result.get("error", "不明なエラー"),
                }
                applications.append(error_data)
                continue
            
            api_result = result.get("data", {})
            response_data = api_result.get("data", {})
            
            # レスポンスデータからapplicationsを抽出
            apps_list = []
            if isinstance(response_data, dict) and "applications" in response_data:
                apps_list = response_data.get("applications", [])
            elif isinstance(response_data, list):
                apps_list = response_data
            
            if not isinstance(apps_list, list):
                apps_list = [apps_list] if apps_list else []
            
            # APIタイプを追加（デフォルト値）
            api_type = "unknown"
            
            for app in apps_list:
                if isinstance(app, dict):
                    app["api_type"] = api_type
                    applications.append(app)
        
        return applications
