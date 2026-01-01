"""
設定管理モジュール
設定の保存・読み込み機能を提供
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict, is_dataclass

from src.api.definitions import (
    ApiDefinition, ApiFieldDefinition, FieldType, InputType, EnumMapping,
    ApiDefinitionManager
)
from src.logger import logger


class SettingsEncoder(json.JSONEncoder):
    """カスタムJSONエンコーダー（dataclass対応）"""
    
    def default(self, obj):
        if is_dataclass(obj):
            # dataclassを辞書に変換
            result = asdict(obj)
            # Enumを文字列に変換
            for key, value in result.items():
                if isinstance(value, (FieldType, InputType)):
                    result[key] = value.value
            return result
        elif isinstance(obj, (FieldType, InputType)):
            # Enumを文字列に変換
            return obj.value
        elif isinstance(obj, EnumMapping):
            # EnumMappingを辞書に変換
            return {"value": obj.value, "display_name": obj.display_name}
        return super().default(obj)


class SettingsManager:
    """設定管理クラス"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        設定マネージャーの初期化
        
        Args:
            config_dir: 設定ファイルのディレクトリ（Noneの場合はプロジェクトルート）
        """
        if config_dir is None:
            # プロジェクトルートを取得
            self.config_dir = Path(__file__).parent.parent.parent
        else:
            self.config_dir = Path(config_dir)
        
        # 設定ファイルのパス
        self.settings_file = self.config_dir / "api_settings.json"
        logger.info(f"設定ファイル: {self.settings_file}")
    
    def save_settings(self, definition_manager: ApiDefinitionManager) -> bool:
        """
        設定をファイルに保存
        
        Args:
            definition_manager: API定義マネージャー
            
        Returns:
            bool: 保存成功ならTrue
        """
        try:
            # API定義を取得
            api_definitions = definition_manager.get_all_definitions()
            
            # シリアライズ可能な形式に変換
            settings_data = {
                "api_definitions": api_definitions,
                "version": "1.0.0"
            }
            
            # 設定ファイルに保存
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, cls=SettingsEncoder, indent=2, ensure_ascii=False)
            
            logger.info(f"設定を保存しました: {self.settings_file}")
            return True
            
        except Exception as e:
            logger.error(f"設定の保存に失敗しました: {e}")
            return False
    
    def load_settings(self) -> Optional[List[ApiDefinition]]:
        """
        設定をファイルから読み込み
        
        Returns:
            Optional[List[ApiDefinition]]: 読み込んだAPI定義リスト（失敗時はNone）
        """
        try:
            if not self.settings_file.exists():
                logger.info(f"設定ファイルが存在しません: {self.settings_file}")
                return None
            
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
            
            # バージョンチェック
            if "version" not in settings_data:
                logger.warning("設定ファイルにバージョン情報がありません")
            
            # API定義をデシリアライズ
            api_definitions = []
            for api_data in settings_data.get("api_definitions", []):
                api_def = self._deserialize_api_definition(api_data)
                if api_def:
                    api_definitions.append(api_def)
            
            logger.info(f"設定を読み込みました: {len(api_definitions)}個のAPI定義")
            return api_definitions
            
        except json.JSONDecodeError as e:
            logger.error(f"設定ファイルのJSON解析に失敗しました: {e}")
            return None
        except Exception as e:
            logger.error(f"設定の読み込みに失敗しました: {e}")
            return None
    
    def _deserialize_api_definition(self, api_data: Dict[str, Any]) -> Optional[ApiDefinition]:
        """API定義をデシリアライズ"""
        try:
            # body_fieldsをデシリアライズ
            body_fields = []
            for field_data in api_data.get("body_fields", []):
                field_def = self._deserialize_field_definition(field_data)
                if field_def:
                    body_fields.append(field_def)
            
            # response_fieldsをデシリアライズ
            response_fields = []
            for field_data in api_data.get("response_fields", []):
                field_def = self._deserialize_field_definition(field_data)
                if field_def:
                    response_fields.append(field_def)
            
            # ApiDefinitionを作成
            return ApiDefinition(
                id=api_data["id"],
                name=api_data["name"],
                enabled=api_data.get("enabled", True),
                url=api_data.get("url", ""),
                method=api_data.get("method", "POST"),
                body_fields=body_fields,
                response_fields=response_fields,
            )
            
        except KeyError as e:
            logger.error(f"API定義のデシリアライズに失敗: 必須フィールドがありません: {e}")
            return None
        except Exception as e:
            logger.error(f"API定義のデシリアライズに失敗: {e}")
            return None
    
    def _deserialize_field_definition(self, field_data: Dict[str, Any]) -> Optional[ApiFieldDefinition]:
        """フィールド定義をデシリアライズ"""
        try:
            # enum_mappingsをデシリアライズ
            enum_mappings = None
            if field_data.get("enum_mappings"):
                enum_mappings = []
                for mapping_data in field_data["enum_mappings"]:
                    enum_mappings.append(
                        EnumMapping(
                            value=mapping_data["value"],
                            display_name=mapping_data["display_name"]
                        )
                    )
            
            # FieldTypeとInputTypeを文字列からEnumに変換
            field_type = FieldType(field_data["type"])
            input_type = InputType(field_data.get("input_type", "text"))
            
            return ApiFieldDefinition(
                name=field_data["name"],
                type=field_type,
                label=field_data["label"],
                default=field_data.get("default"),
                input_type=input_type,
                configurable=field_data.get("configurable", True),
                enum_mappings=enum_mappings,
                allow_multiple=field_data.get("allow_multiple", False),
                display_in_table=field_data.get("display_in_table", True),
                display_format=field_data.get("display_format"),
            )
            
        except (KeyError, ValueError) as e:
            logger.error(f"フィールド定義のデシリアライズに失敗: {e}")
            return None
    
    def has_saved_settings(self) -> bool:
        """保存された設定があるか確認"""
        return self.settings_file.exists()
    
    def delete_settings(self) -> bool:
        """設定ファイルを削除"""
        try:
            if self.settings_file.exists():
                self.settings_file.unlink()
                logger.info(f"設定ファイルを削除しました: {self.settings_file}")
                return True
            return False
        except Exception as e:
            logger.error(f"設定ファイルの削除に失敗しました: {e}")
            return False


# シングルトンインスタンス
_settings_manager = None

def get_settings_manager() -> SettingsManager:
    """設定マネージャーのシングルトンインスタンスを取得"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
