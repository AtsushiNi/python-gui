"""
API定義システム
APIの設定、body定義、レスポンス表示定義を一元管理
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class FieldType(str, Enum):
    """フィールドタイプ"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"
    DATE = "date"


class InputType(str, Enum):
    """入力タイプ"""
    TEXT = "text"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    DATEPICKER = "datepicker"


@dataclass
class EnumMapping:
    """enum値と表示名のマッピング"""
    value: str
    display_name: str


@dataclass
class ApiFieldDefinition:
    """APIフィールド定義"""
    name: str  # APIのフィールド名
    type: FieldType  # フィールドタイプ
    label: str  # GUI表示用ラベル（マージキー）
    default: Any = None  # デフォルト値
    input_type: InputType = InputType.TEXT  # 入力タイプ
    
    # 設定画面での表示・編集可否
    configurable: bool = True  # 設定画面で表示・編集可能か
    
    # enum/dropdown用
    enum_mappings: Optional[List[EnumMapping]] = None
    
    # 選択設定
    allow_multiple: bool = False  # 複数選択を許可するか
    
    # 表示設定
    display_in_table: bool = True  # テーブルに表示するか
    display_format: Optional[str] = None  # 表示フォーマット（例: "{value} JPY"）
    
    def get_display_value(self, value: Any) -> str:
        """値を表示用に変換"""
        if value is None:
            return "N/A"
        
        # 複数選択の場合（値がリスト）
        if isinstance(value, list):
            if not value:
                return "N/A"
            
            # enumマッピングがある場合は各値を表示名に変換
            if self.type == FieldType.ENUM and self.enum_mappings:
                display_names = []
                for v in value:
                    found = False
                    for mapping in self.enum_mappings:
                        if str(v) == mapping.value:
                            display_names.append(mapping.display_name)
                            found = True
                            break
                    if not found:
                        display_names.append(str(v))
                return ", ".join(display_names)
            else:
                return ", ".join(str(v) for v in value)
        
        # 単一値の場合
        # enumマッピングがある場合は表示名に変換
        if self.type == FieldType.ENUM and self.enum_mappings:
            for mapping in self.enum_mappings:
                if str(value) == mapping.value:
                    return mapping.display_name
        
        # 表示フォーマットがある場合は適用
        if self.display_format:
            try:
                return self.display_format.format(value=value)
            except:
                pass
        
        # デフォルトの文字列変換
        return str(value)


@dataclass 
class ApiDefinition:
    """API定義"""
    id: str  # 一意のID
    name: str  # 表示名
    enabled: bool = True  # 有効/無効
    url: str = ""  # APIエンドポイント
    method: str = "POST"  # HTTPメソッド
    
    # Body定義（オプションフィールドのみ）
    body_fields: List[ApiFieldDefinition] = field(default_factory=list)
    
    # レスポンス表示定義
    response_fields: List[ApiFieldDefinition] = field(default_factory=list)
    
    def get_body_field(self, name: str) -> Optional[ApiFieldDefinition]:
        """bodyフィールドを名前で取得"""
        for field in self.body_fields:
            if field.name == name:
                return field
        return None
    
    def get_response_field(self, name: str) -> Optional[ApiFieldDefinition]:
        """レスポンスフィールドを名前で取得"""
        for field in self.response_fields:
            if field.name == name:
                return field
        return None


@dataclass
class MergedField:
    """マージされたテーブル列（表示名ベース）"""
    label: str  # 表示名（マージキー）
    display_order: int  # 表示順序
    
    # 各APIでのフィールド定義マッピング
    api_field_mappings: Dict[str, ApiFieldDefinition] = field(default_factory=dict)
    # key: api_id, value: そのAPIでのフィールド定義
    
    @property
    def field_type(self) -> FieldType:
        """最初のAPIの型を基準とする"""
        if self.api_field_mappings:
            first_def = next(iter(self.api_field_mappings.values()))
            return first_def.type
        return FieldType.STRING
    
    def get_field_definition(self, api_id: str) -> Optional[ApiFieldDefinition]:
        """指定したAPIのフィールド定義を取得"""
        return self.api_field_mappings.get(api_id)
    
    def get_display_value(self, api_id: str, value: Any) -> str:
        """APIごとに値を表示用に変換"""
        field_def = self.get_field_definition(api_id)
        if field_def:
            return field_def.get_display_value(value)
        return "N/A"


def merge_api_definitions_by_label(api_definitions: List[ApiDefinition]) -> List[MergedField]:
    """表示名（label）でAPI定義をマージ"""
    merged_fields = {}  # label -> MergedField
    
    for api_def in api_definitions:
        for field in api_def.response_fields:
            if field.display_in_table:
                if field.label not in merged_fields:
                    merged_fields[field.label] = MergedField(
                        label=field.label,
                        display_order=len(merged_fields),
                        api_field_mappings={api_def.id: field}
                    )
                else:
                    merged_fields[field.label].api_field_mappings[api_def.id] = field
    
    # 表示順序でソート
    return sorted(merged_fields.values(), key=lambda x: x.display_order)


class ApiDefinitionManager:
    """API定義を管理するクラス"""
    
    def __init__(self, api_definitions: List[ApiDefinition]):
        self.api_definitions = {api.id: api for api in api_definitions}
        self._update_merged_fields()
    
    def _update_merged_fields(self):
        """マージされたフィールドを更新"""
        enabled_defs = self.get_enabled_definitions()
        self.merged_fields = merge_api_definitions_by_label(enabled_defs)
    
    def get_definition(self, api_id: str) -> Optional[ApiDefinition]:
        """API定義を取得"""
        return self.api_definitions.get(api_id)
    
    def get_enabled_definitions(self) -> List[ApiDefinition]:
        """有効なAPI定義を取得"""
        return [api for api in self.api_definitions.values() if api.enabled]
    
    def get_all_definitions(self) -> List[ApiDefinition]:
        """すべてのAPI定義を取得（有効/無効問わず）"""
        return list(self.api_definitions.values())
    
    def get_merged_fields(self) -> List[MergedField]:
        """マージされたテーブル列を取得"""
        return self.merged_fields
    
    def set_definition_enabled(self, api_id: str, enabled: bool):
        """API定義の有効/無効を設定"""
        if api_id in self.api_definitions:
            self.api_definitions[api_id].enabled = enabled
            self._update_merged_fields()
    
    def update_definition(self, api_id: str, definition: ApiDefinition):
        """API定義を更新"""
        self.api_definitions[api_id] = definition
        self._update_merged_fields()
