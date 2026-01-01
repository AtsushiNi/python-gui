"""
APIクライアント
新しいAPI定義システムに対応
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple, Callable
import requests
from requests.exceptions import RequestException, Timeout

from src.api.definitions import ApiDefinition, ApiDefinitionManager
from src.logger import logger


class ApiClient:
    """APIクライアントクラス（新しいAPI定義システム対応）"""

    def __init__(self):
        self.session = requests.Session()
        # セッション設定
        self.session.headers.update({
            "User-Agent": "API Table Viewer/2.0",
            "Accept": "application/json",
        })

    def execute_api(
        self, 
        api_def: ApiDefinition, 
        body_params: Dict[str, Any] = None
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        単一のAPIを実行します

        Args:
            api_def: API定義
            body_params: Bodyパラメータ（GUI入力値）

        Returns:
            (成功可否, レスポンスデータ, エラーメッセージ)
        """
        if not api_def.enabled:
            return False, {}, "APIが無効です"

        # URLの検証
        if not api_def.url.strip():
            return False, {}, "URLを入力してください"
        
        if not api_def.url.startswith(("http://", "https://")):
            return False, {}, "URLは http:// または https:// で始まる必要があります"

        try:
            logger.info(f"API実行開始: {api_def.name} ({api_def.url})")

            # リクエストパラメータの準備
            request_kwargs = {
                "headers": {"Content-Type": "application/json"},
                "timeout": 30,
            }
            
            # Bodyパラメータの構築
            json_body = {}
            if body_params:
                json_body.update(body_params)
            
            # デフォルト値の追加
            for field_def in api_def.body_fields:
                if field_def.name not in json_body and field_def.default is not None:
                    json_body[field_def.name] = field_def.default
            
            if json_body:
                request_kwargs["json"] = json_body

            # リクエスト実行
            start_time = time.time()
            
            if api_def.method.upper() == "POST":
                response = self.session.post(
                    url=api_def.url,
                    **request_kwargs
                )
            elif api_def.method.upper() == "GET":
                response = self.session.get(
                    url=api_def.url,
                    **request_kwargs
                )
            else:
                return False, {}, f"未対応のHTTPメソッド: {api_def.method}"
                
            elapsed_time = time.time() - start_time

            logger.info(f"API応答: {api_def.name} - ステータス: {response.status_code}, 時間: {elapsed_time:.2f}s")

            # レスポンスの処理
            response_data = self._process_response(response)

            # 結果の構築
            result = {
                "api_id": api_def.id,
                "api_name": api_def.name,
                "api_definition": api_def,
                "url": api_def.url,
                "method": api_def.method,
                "status_code": response.status_code,
                "response_time": elapsed_time,
                "success": response.ok,
                "data": response_data,
                "request_body": json_body,
                "headers": dict(response.headers),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            if not response.ok:
                error_msg = f"HTTPエラー: {response.status_code} - {response.reason}"
                return False, result, error_msg

            return True, result, None

        except Timeout:
            error_msg = f"タイムアウト: 30秒経過"
            logger.warning(f"APIタイムアウト: {api_def.name}")
            return False, {}, error_msg

        except RequestException as e:
            error_msg = f"リクエストエラー: {str(e)}"
            logger.error(f"APIリクエストエラー: {api_def.name} - {e}")
            return False, {}, error_msg

        except Exception as e:
            error_msg = f"予期せぬエラー: {str(e)}"
            logger.error(f"API実行エラー: {api_def.name} - {e}")
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
    """API実行を管理するクラス（新しいAPI定義システム対応）"""

    def __init__(self, progress_callback=None):
        self.client = ApiClient()
        self.results: List[Dict[str, Any]] = []
        self.progress_callback = progress_callback

    def execute(
        self, 
        definition_manager: ApiDefinitionManager,
        api_body_params: Dict[str, Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        APIを実行し、結果を返します

        Args:
            definition_manager: API定義マネージャー
            api_body_params: 各APIのBodyパラメータ（API ID -> パラメータ辞書）

        Returns:
            実行結果リスト
        """
        api_definitions = definition_manager.get_enabled_definitions()
        
        if not api_definitions:
            logger.warning("実行可能なAPIがありません")
            return []
        
        logger.info(f"{len(api_definitions)}個のAPIを実行します")

        self.results = []
        
        for i, api_def in enumerate(api_definitions):
            # 進捗報告
            if self.progress_callback:
                self.progress_callback(i + 1, len(api_definitions))
            
            # Bodyパラメータの取得
            body_params = {}
            if api_body_params and api_def.id in api_body_params:
                body_params = api_body_params[api_def.id]
            
            # API実行
            success, data, error = self.client.execute_api(api_def, body_params)
            
            result = {
                "api_id": api_def.id,
                "api_name": api_def.name,
                "api_definition": api_def,
                "index": i,
                "success": success,
                "data": data,
                "error": error,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.results.append(result)

            if success:
                logger.info(f"API {i+1} 実行成功: {api_def.name}")
            else:
                logger.warning(f"API {i+1} 実行失敗: {api_def.name} - {error}")

        logger.info(f"API実行完了: {len([r for r in self.results if r['success']])}/{len(self.results)} 成功")
        return self.results

    def extract_response_data(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        API実行結果からレスポンスデータを抽出します
        
        Args:
            results: API実行結果リスト
            
        Returns:
            抽出されたレスポンスデータリスト
        """
        extracted_data = []
        
        for result in results:
            api_def = result.get("api_definition")
            if not api_def:
                continue
            
            if not result.get("success", False):
                # エラーの場合はエラー情報を追加
                error_data = {
                    "api_id": api_def.id,
                    "api_name": api_def.name,
                    "type": "error",
                    "id": f"ERROR-{len(extracted_data)+1:03d}",
                    "title": "API実行エラー",
                    "status": "ERROR",
                    "error_message": result.get("error", "不明なエラー"),
                    "timestamp": result.get("timestamp", ""),
                }
                extracted_data.append(error_data)
                continue
            
            # レスポンスデータの抽出
            api_result = result.get("data", {})
            response_data = api_result.get("data", {})
            items_list = response_data.get("applications", [])
            
            for item in items_list:
                if isinstance(item, dict):
                    # API情報を追加
                    item["api_id"] = api_def.id
                    item["api_name"] = api_def.name
                    extracted_data.append(item)
        
        return extracted_data

    def close(self):
        """リソースを解放します"""
        self.client.close()
