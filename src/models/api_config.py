"""
API設定データモデル
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable

@dataclass
class ApiConfig:
    """単一のAPI設定（設定と定義を統合）"""

    # 基本設定
    enabled: bool = True
    name: str = "API"
    url: str = ""
    
    # API定義情報（元々ApiDefinitionにあったフィールド）
    description: str = ""
    
    # パラメータ定義
    default_params: Dict[str, Any] = field(default_factory=dict)
    supported_params: List[str] = field(default_factory=list)
    param_validators: Dict[str, Callable[[Any], List[str]]] = field(default_factory=dict)
    
    # フィルターパラメータ（APIタイプ固有）
    filter_params: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """設定の検証を行い、エラーメッセージのリストを返します"""
        errors = []

        if not self.name.strip():
            errors.append("API名を入力してください")

        if not self.url.strip():
            errors.append("URLを入力してください")
        elif not self.url.startswith(("http://", "https://")):
            errors.append("URLは http:// または https:// で始まる必要があります")

        return errors
    
    def get_default_params(self) -> Dict[str, Any]:
        """デフォルトのパラメータを取得します"""
        return self.default_params.copy()
    
    def validate_params(self, **params) -> List[str]:
        """パラメータを検証します（元ApiDefinitionのメソッド）"""
        errors = []
        
        for key, value in params.items():
            if key in self.param_validators:
                validator = self.param_validators[key]
                param_errors = validator(value)
                errors.extend(param_errors)
        
        return errors


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
