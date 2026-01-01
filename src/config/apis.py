"""
API定義設定ファイル
コード修正なしでAPIを増減可能
"""

from src.api.definitions import (
    ApiDefinition, ApiFieldDefinition, FieldType, InputType, EnumMapping
)


# サンプルAPI定義
SAMPLE_API_DEFINITIONS = [
    ApiDefinition(
        id="expense_api",
        name="経費申請API",
        enabled=True,
        url="http://localhost:8001/applications/type-a",
        method="POST",
        body_fields=[
            ApiFieldDefinition(
                name="status",
                type=FieldType.ENUM,
                label="ステータス",
                input_type=InputType.DROPDOWN,
                enum_mappings=[
                    EnumMapping(value="SUBMITTED", display_name="申請済"),
                    EnumMapping(value="APPROVED", display_name="承認済"),
                    EnumMapping(value="REJECTED", display_name="却下"),
                    EnumMapping(value="PENDING", display_name="保留中"),
                ],
                default="SUBMITTED",
            ),
            ApiFieldDefinition(
                name="amount_min",
                type=FieldType.NUMBER,
                label="最小金額",
                input_type=InputType.TEXT,
                default=0,
            ),
            ApiFieldDefinition(
                name="amount_max",
                type=FieldType.NUMBER,
                label="最大金額",
                input_type=InputType.TEXT,
                default=10000,
            ),
        ],
        response_fields=[
            ApiFieldDefinition(
                name="id",
                type=FieldType.STRING,
                label="ID",
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="title",
                type=FieldType.STRING,
                label="タイトル",
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="status",
                type=FieldType.ENUM,
                label="ステータス",
                enum_mappings=[
                    EnumMapping(value="SUBMITTED", display_name="申請済"),
                    EnumMapping(value="APPROVED", display_name="承認済"),
                    EnumMapping(value="REJECTED", display_name="却下"),
                ],
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="amount",
                type=FieldType.NUMBER,
                label="金額",
                display_format="{value} JPY",
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="expenseCategory",
                type=FieldType.STRING,
                label="経費カテゴリー",
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="createdAt",
                type=FieldType.DATE,
                label="申請日時",
                display_in_table=True,
            ),
        ],
    ),
    ApiDefinition(
        id="vacation_api",
        name="休暇申請API",
        enabled=True,
        url="http://localhost:8001/applications/type-b",
        method="POST",
        body_fields=[
            ApiFieldDefinition(
                name="status",
                type=FieldType.ENUM,
                label="ステータス",
                input_type=InputType.DROPDOWN,
                enum_mappings=[
                    EnumMapping(value="SUBMITTED", display_name="申請済"),
                    EnumMapping(value="APPROVED", display_name="承認済"),
                    EnumMapping(value="REJECTED", display_name="却下"),
                ],
                default="SUBMITTED",
            ),
            ApiFieldDefinition(
                name="start_date",
                type=FieldType.DATE,
                label="開始日",
                input_type=InputType.DATEPICKER,
            ),
            ApiFieldDefinition(
                name="end_date",
                type=FieldType.DATE,
                label="終了日",
                input_type=InputType.DATEPICKER,
            ),
        ],
        response_fields=[
            ApiFieldDefinition(
                name="id",
                type=FieldType.STRING,
                label="ID",
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="title",
                type=FieldType.STRING,
                label="タイトル",
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="status",
                type=FieldType.ENUM,
                label="ステータス",
                enum_mappings=[
                    EnumMapping(value="SUBMITTED", display_name="申請済"),
                    EnumMapping(value="APPROVED", display_name="承認済"),
                    EnumMapping(value="REJECTED", display_name="却下"),
                ],
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="startDate",
                type=FieldType.DATE,
                label="開始日",
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="endDate",
                type=FieldType.DATE,
                label="終了日",
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="days",
                type=FieldType.NUMBER,
                label="日数",
                display_format="{value}日",
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="createdAt",
                type=FieldType.DATE,
                label="申請日時",
                display_in_table=True,
            ),
        ],
    ),
    ApiDefinition(
        id="permission_api",
        name="権限申請API",
        enabled=True,
        url="http://localhost:8001/applications/type-c",
        method="POST",
        body_fields=[
            ApiFieldDefinition(
                name="status",
                type=FieldType.ENUM,
                label="ステータス",
                input_type=InputType.DROPDOWN,
                enum_mappings=[
                    EnumMapping(value="SUBMITTED", display_name="申請済"),
                    EnumMapping(value="APPROVED", display_name="承認済"),
                    EnumMapping(value="REJECTED", display_name="却下"),
                ],
                default="SUBMITTED",
            ),
            ApiFieldDefinition(
                name="requested_role",
                type=FieldType.STRING,
                label="要求権限",
                input_type=InputType.TEXT,
                default="editor",
            ),
        ],
        response_fields=[
            ApiFieldDefinition(
                name="id",
                type=FieldType.STRING,
                label="ID",
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="title",
                type=FieldType.STRING,
                label="タイトル",
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="status",
                type=FieldType.ENUM,
                label="ステータス",
                enum_mappings=[
                    EnumMapping(value="SUBMITTED", display_name="申請済"),
                    EnumMapping(value="APPROVED", display_name="承認済"),
                    EnumMapping(value="REJECTED", display_name="却下"),
                ],
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="requestedRole",
                type=FieldType.STRING,
                label="要求権限",
                display_in_table=True,
            ),
            ApiFieldDefinition(
                name="approvalFlow",
                type=FieldType.STRING,
                label="承認フロー",
                display_in_table=False,  # テーブルには表示しない（詳細表示のみ）
            ),
            ApiFieldDefinition(
                name="createdAt",
                type=FieldType.DATE,
                label="申請日時",
                display_in_table=True,
            ),
        ],
    ),
]


def get_api_definitions() -> list[ApiDefinition]:
    """API定義リストを取得"""
    return SAMPLE_API_DEFINITIONS.copy()


def get_api_definition(api_id: str) -> ApiDefinition | None:
    """指定したIDのAPI定義を取得"""
    for api_def in SAMPLE_API_DEFINITIONS:
        if api_def.id == api_id:
            return api_def
    return None
