"""
APIクライアント
requestsを使用してAPIを実行します
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple
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
                "timeout": config.timeout,
                "headers": config.headers,
                "params": config.params,
            }

            # ボディの処理
            if config.body is not None:
                if isinstance(config.body, (dict, list)):
                    request_kwargs["json"] = config.body
                    if "Content-Type" not in config.headers:
                        request_kwargs["headers"]["Content-Type"] = "application/json"
                else:
                    request_kwargs["data"] = config.body

            # リクエスト実行
            start_time = time.time()
            response = self.session.request(
                method=config.method.value,
                url=config.url,
                **request_kwargs
            )
            elapsed_time = time.time() - start_time

            logger.info(f"API応答: {config.name} - ステータス: {response.status_code}, 時間: {elapsed_time:.2f}s")

            # レスポンスの処理
            response_data = self._process_response(response, config)

            # 結果の構築
            result = {
                "api_name": config.name,
                "url": config.url,
                "method": config.method.value,
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
            error_msg = f"タイムアウト: {config.timeout}秒経過"
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

    def _process_response(self, response: requests.Response, config: ApiConfig) -> Any:
        """
        レスポンスを処理します

        Args:
            response: レスポンスオブジェクト
            config: API設定

        Returns:
            処理されたデータ
        """
        content_type = response.headers.get("Content-Type", "")

        # JSONレスポンス
        if "application/json" in content_type:
            try:
                data = response.json()

                # レスポンスパスが指定されている場合は抽出
                if config.response_path:
                    data = self._extract_by_path(data, config.response_path)

                # 平坦化が必要な場合
                if config.flatten_response and isinstance(data, list):
                    data = self._flatten_responses(data)

                return data
            except json.JSONDecodeError:
                logger.warning(f"JSON解析エラー: {config.name}")
                return {"raw_response": response.text}

        # テキストレスポンス
        elif "text/" in content_type:
            return {"text": response.text}

        # その他のレスポンス
        else:
            return {"content_type": content_type, "size": len(response.content)}

    def _extract_by_path(self, data: Any, path: str) -> Any:
        """
        指定したパスからデータを抽出します

        Args:
            data: 元データ
            path: パス（例: "data.results"）

        Returns:
            抽出されたデータ
        """
        try:
            keys = path.split(".")
            current = data
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list) and key.isdigit():
                    current = current[int(key)]
                else:
                    return None
            return current
        except (KeyError, IndexError, TypeError, ValueError):
            logger.warning(f"パス抽出エラー: {path}")
            return None

    def _flatten_responses(self, responses: List[Dict]) -> List[Dict]:
        """
        ネストされたレスポンスを平坦化します

        Args:
            responses: レスポンスリスト

        Returns:
            平坦化されたリスト
        """
        flattened = []
        for item in responses:
            if isinstance(item, dict):
                flattened.append(item)
            elif isinstance(item, list):
                flattened.extend(self._flatten_responses(item))
        return flattened

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
                api_result = result.get("data", {})
                error_data = {
                    "api_type": self._extract_api_type_from_url(api_result.get("url", "")),
                    "id": f"ERROR-{len(applications)+1:03d}",
                    "title": "API実行エラー",
                    "status": "ERROR",
                    "applicant": {"name": "システム"},
                    "createdAt": result.get("timestamp", ""),
                    "error_code": "API_ERROR",
                    "error_message": result.get("error", "不明なエラー"),
                }
                applications.append(error_data)
                continue
            
            api_result = result.get("data", {})
            response_data = api_result.get("data", {})
            
            if isinstance(response_data, dict) and "applications" in response_data:
                apps_list = response_data.get("applications", [])
                response_type = response_data.get("type")
            else:
                apps_list = response_data if isinstance(response_data, list) else []
                response_type = None
            
            if not isinstance(apps_list, list):
                apps_list = [apps_list] if apps_list else []
            
            for app in apps_list:
                if isinstance(app, dict):
                    # APIタイプを設定（レスポンスのtypeフィールドを優先、なければURLから推測）
                    api_type = app.get("type")
                    if not api_type and response_type:
                        api_type = response_type
                    if not api_type:
                        api_type = self._extract_api_type_from_url(api_result.get("url", ""))
                    
                    # api_typeフィールドを追加（applications_table_model.pyが期待するフィールド名）
                    app["api_type"] = api_type
                    
                    # 元のtypeフィールドも保持（必要に応じて）
                    if "type" not in app:
                        app["type"] = api_type
                    
                    applications.append(app)
        
        return applications
    
    def _extract_api_type_from_url(self, url: str) -> str:
        """URLからAPIタイプを抽出します"""
        if "type-a" in url:
            return "A"
        elif "type-b" in url:
            return "B"
        elif "type-c" in url:
            return "C"
        else:
            # URLからタイプを推測
            import re
            match = re.search(r'type-([abc])', url.lower())
            if match:
                return match.group(1).upper()
            return "Unknown"
