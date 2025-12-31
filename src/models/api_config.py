"""
API設定データモデル
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from src.api.flexible_types import ApiCategory, find_api_definition, get_api_handler


class HttpMethod(Enum):
    """HTTPメソッドの列挙型"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"


@dataclass
class ApiConfig:
    """単一のAPI設定"""

    # 基本設定
    enabled: bool = True
    name: str = "API"
    url: str = ""
    api_category: Optional[ApiCategory] = None  # APIカテゴリー
    api_definition_name: Optional[str] = None  # API定義名

    # リクエスト設定
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None
    timeout: int = 30  # 秒

    # レスポンス処理
    response_path: Optional[str] = None  # JSONパス（例: "data.results"）

    # フィルターパラメータ（APIタイプ固有）
    filter_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初期化後の処理：URLからAPI定義を推測"""
        if (self.api_category is None or self.api_definition_name is None) and self.url:
            definition = find_api_definition(self.url)
            if definition:
                self.api_category = definition.category
                self.api_definition_name = definition.name

    def validate(self) -> List[str]:
        """設定の検証を行い、エラーメッセージのリストを返します"""
        errors = []

        if not self.name.strip():
            errors.append("API名を入力してください")

        if not self.url.strip():
            errors.append("URLを入力してください")
        elif not self.url.startswith(("http://", "https://")):
            errors.append("URLは http:// または https:// で始まる必要があります")

        if self.timeout <= 0:
            errors.append("タイムアウトは正の数である必要があります")

        # API定義固有のパラメータ検証
        if self.url and self.filter_params:
            definition = find_api_definition(self.url)
            if definition:
                param_errors = definition.validate_params(**self.filter_params)
                errors.extend(param_errors)

        return errors
    
    def get_default_params(self) -> Dict[str, Any]:
        """デフォルトのパラメータを取得します"""
        if not self.url:
            return {}
        definition = find_api_definition(self.url)
        if definition:
            return definition.default_params
        return {}


class ApiConfigManager:
    """複数のAPI設定を管理するクラス"""

    def __init__(self, max_apis: int = 3, default_configs: Optional[List[ApiConfig]] = None):
        self.max_apis = max_apis
        if default_configs:
            self.configs = default_configs[:max_apis]
            # 不足している分を追加
            while len(self.configs) < max_apis:
                self.configs.append(ApiConfig(name=f"API {len(self.configs)+1}"))
        else:
            self.configs: List[ApiConfig] = [
                ApiConfig(name=f"API {i+1}") for i in range(max_apis)
            ]

    def get_config(self, index: int) -> ApiConfig:
        """指定したインデックスの設定を取得します"""
        if 0 <= index < len(self.configs):
            return self.configs[index]
        raise IndexError(f"インデックス {index} は範囲外です")

    def set_config(self, index: int, config: ApiConfig) -> None:
        """指定したインデックスに設定を設定します"""
        if 0 <= index < len(self.configs):
            self.configs[index] = config
        else:
            raise IndexError(f"インデックス {index} は範囲外です")

    def get_enabled_configs(self) -> List[ApiConfig]:
        """有効な設定のみを取得します"""
        return [config for config in self.configs if config.enabled]

    def validate_all(self) -> Dict[int, List[str]]:
        """すべての設定を検証し、エラーを返します"""
        errors = {}
        for i, config in enumerate(self.configs):
            if config.enabled:
                config_errors = config.validate()
                if config_errors:
                    errors[i] = config_errors
        return errors
