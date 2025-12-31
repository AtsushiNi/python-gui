"""
柔軟なAPIタイプシステム
typeがないAPIや動的に追加されるAPIをサポート
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import re


class ApiCategory(Enum):
    """APIカテゴリー（オプション）"""
    EXPENSE = "expense"      # 経費関連
    LEAVE = "leave"          # 休暇関連
    PERMISSION = "permission"  # 権限関連
    CUSTOM = "custom"        # カスタムAPI
    UNKNOWN = "unknown"      # 不明


@dataclass
class ApiDefinition:
    """API定義（動的に追加可能）"""
    
    # 基本情報
    name: str
    endpoint_pattern: str  # 正規表現パターン（例: r"/applications/type-a"）
    description: str = ""
    category: ApiCategory = ApiCategory.UNKNOWN
    
    # パラメータ定義
    default_params: Dict[str, Any] = field(default_factory=dict)
    supported_params: List[str] = field(default_factory=list)
    param_validators: Dict[str, Callable[[Any], List[str]]] = field(default_factory=dict)
    
    # レスポンス処理
    response_extractor: Optional[Callable[[Dict[str, Any]], List[Dict[str, Any]]]] = None
    type_field: Optional[str] = "type"  # レスポンス内のタイプフィールド名（Noneの場合は使用しない）
    
    def matches_url(self, url: str) -> bool:
        """URLがこのAPI定義にマッチするかチェック"""
        return bool(re.search(self.endpoint_pattern, url))
    
    def validate_params(self, **params) -> List[str]:
        """パラメータを検証します"""
        errors = []
        
        for key, value in params.items():
            if key in self.param_validators:
                validator = self.param_validators[key]
                param_errors = validator(value)
                errors.extend(param_errors)
        
        return errors


class FlexibleApiHandler(ABC):
    """柔軟なAPIハンドラーの基底クラス"""
    
    def __init__(self, definition: ApiDefinition):
        self.definition = definition
    
    @abstractmethod
    def process_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """レスポンスを処理してアプリケーションリストを抽出します"""
        pass
    
    def get_applications(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """アプリケーションリストを取得します（デフォルト実装）"""
        applications = []
        
        if self.definition.response_extractor:
            # カスタム抽出関数を使用
            applications = self.definition.response_extractor(response_data)
        else:
            # デフォルトの抽出ロジック
            applications = self._extract_applications_default(response_data)
        
        # APIタイプを追加
        for app in applications:
            if isinstance(app, dict):
                # カテゴリーをAPIタイプとして使用
                app["api_type"] = self.definition.category.value
                if "type" not in app and self.definition.type_field:
                    app["type"] = self.definition.category.value
        
        return applications
    
    def _extract_applications_default(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """デフォルトのアプリケーション抽出ロジック"""
        applications = []
        
        if isinstance(response_data, dict) and "applications" in response_data:
            apps_list = response_data.get("applications", [])
        else:
            apps_list = response_data if isinstance(response_data, list) else []
        
        if not isinstance(apps_list, list):
            apps_list = [apps_list] if apps_list else []
        
        for app in apps_list:
            if isinstance(app, dict):
                applications.append(app)
        
        return applications


class DefaultApiHandler(FlexibleApiHandler):
    """デフォルトのAPIハンドラー（typeがないAPI用）"""
    
    def process_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """レスポンスを処理します"""
        return self.get_applications(response_data)


class FlexibleApiRegistry:
    """柔軟なAPIレジストリ（動的にAPI定義を登録可能）"""
    
    def __init__(self):
        self.definitions: List[ApiDefinition] = []
        self._register_default_definitions()
    
    def _register_default_definitions(self):
        """デフォルトのAPI定義を登録します"""
        # タイプA: 経費申請
        self.register(ApiDefinition(
            name="Type A API",
            endpoint_pattern=r"/applications/type-a",
            description="経費申請API",
            category=ApiCategory.EXPENSE,
            default_params={"count": 5},
            supported_params=["status", "min_amount", "max_amount", "category"],
            param_validators={
                "status": lambda v: [] if v in ["SUBMITTED", "APPROVED", "REJECTED", "PENDING"] else [f"無効なstatus: {v}"],
                "min_amount": lambda v: [] if isinstance(v, (int, float)) and v >= 0 else ["min_amountは0以上の数値である必要があります"],
                "max_amount": lambda v: [] if isinstance(v, (int, float)) and v >= 0 else ["max_amountは0以上の数値である必要があります"],
                "category": lambda v: [] if v in ["TRANSPORT", "BUSINESS_TRIP", "MEAL", "OFFICE_SUPPLIES", "TRAINING"] else [f"無効なcategory: {v}"]
            }
        ))
        
        # タイプB: 休暇申請
        self.register(ApiDefinition(
            name="Type B API",
            endpoint_pattern=r"/applications/type-b",
            description="休暇申請API",
            category=ApiCategory.LEAVE,
            default_params={"count": 5},
            supported_params=["status", "start_date_from", "start_date_to", "min_days", "max_days"],
            param_validators={
                "status": lambda v: [] if v in ["SUBMITTED", "APPROVED", "REJECTED", "PENDING"] else [f"無効なstatus: {v}"],
                "start_date_from": lambda v: [] if re.match(r"\d{4}-\d{2}-\d{2}", str(v)) else ["start_date_fromはYYYY-MM-DD形式である必要があります"],
                "start_date_to": lambda v: [] if re.match(r"\d{4}-\d{2}-\d{2}", str(v)) else ["start_date_toはYYYY-MM-DD形式である必要があります"],
                "min_days": lambda v: [] if isinstance(v, (int, float)) and v >= 0 else ["min_daysは0以上の数値である必要があります"],
                "max_days": lambda v: [] if isinstance(v, (int, float)) and v >= 0 else ["max_daysは0以上の数値である必要があります"]
            }
        ))
        
        # タイプC: 権限申請
        self.register(ApiDefinition(
            name="Type C API",
            endpoint_pattern=r"/applications/type-c",
            description="権限申請API",
            category=ApiCategory.PERMISSION,
            default_params={"count": 5},
            supported_params=["status", "role", "approval_status"],
            param_validators={
                "status": lambda v: [] if v in ["SUBMITTED", "APPROVED", "REJECTED", "PENDING", "IN_REVIEW"] else [f"無効なstatus: {v}"],
                "role": lambda v: [] if v in ["ADMIN", "EDITOR", "VIEWER", "MANAGER", "SUPERVISOR"] else [f"無効なrole: {v}"],
                "approval_status": lambda v: [] if v in ["APPROVED", "PENDING", "REJECTED"] else [f"無効なapproval_status: {v}"]
            }
        ))
    
    def register(self, definition: ApiDefinition):
        """新しいAPI定義を登録します"""
        self.definitions.append(definition)
    
    def find_definition(self, url: str) -> Optional[ApiDefinition]:
        """URLにマッチするAPI定義を検索します"""
        for definition in self.definitions:
            if definition.matches_url(url):
                return definition
        
        # デフォルトのカスタムAPI定義を作成
        return self._create_custom_definition(url)
    
    def _create_custom_definition(self, url: str) -> ApiDefinition:
        """URLからカスタムAPI定義を作成します"""
        # URLから名前を生成
        name = self._extract_name_from_url(url)
        
        return ApiDefinition(
            name=name,
            endpoint_pattern=re.escape(url),  # 完全一致
            description=f"カスタムAPI: {url}",
            category=ApiCategory.CUSTOM,
            default_params={},
            supported_params=[],  # カスタムAPIはデフォルトではパラメータをサポートしない
            type_field=None  # typeフィールドがない
        )
    
    def _extract_name_from_url(self, url: str) -> str:
        """URLからAPI名を抽出します"""
        # ドメイン部分を除去
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        
        if not path or path == "/":
            return "Custom API"
        
        # パスから名前を生成
        path_parts = [p for p in path.split("/") if p]
        if path_parts:
            # 最後のパス部分を使用
            last_part = path_parts[-1]
            # ケバブケースをスペース区切りに変換
            name = last_part.replace("-", " ").replace("_", " ").title()
            return f"Custom {name} API"
        
        return "Custom API"
    
    def create_handler(self, url: str) -> FlexibleApiHandler:
        """URLに基づいて適切なハンドラーを作成します"""
        definition = self.find_definition(url)
        return DefaultApiHandler(definition)


# グローバルレジストリインスタンス
api_registry = FlexibleApiRegistry()


def get_api_handler(url: str) -> FlexibleApiHandler:
    """URLに基づいてAPIハンドラーを取得します"""
    return api_registry.create_handler(url)


def find_api_definition(url: str) -> Optional[ApiDefinition]:
    """URLにマッチするAPI定義を検索します"""
    return api_registry.find_definition(url)
