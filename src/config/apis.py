"""
API定義設定ファイル
コード修正なしでAPIを増減可能

API_DEFINITIONの設定方法

1. API定義の追加方法
   - API_DEFINITIONSリストに新しいApi定義を追加します
   - 各API定義には以下の必須フィールドがあります：
     * id: APIの一意識別子（英数字とアンダースコア）
     * name: 表示名
     * enabled: 有効/無効フラグ
     * url: APIエンドポイントURL
     * method: HTTPメソッド（GET/POSTのみサポート）
     * body_fields: リクエストボディのフィールド定義リスト
     * response_fields: レスポンスのフィールド定義リスト

2. フィールド定義（ApiFieldDefinition）の設定
   - name: リクエスト: APIのbodyのキー名, レスポンス: APIレスポンスのキー名
   - type: フィールドタイプ
   - label: リクエスト: 設定画面の表示ラベル, レスポンス: 結果表示テーブルの表示フィールド名
   - enum_mappings: ENUMタイプの場合の値と表示名のマッピング
   - input_type: (リクエストのみ) 設定画面の入力タイプ
   - default: (リクエストのみ) デフォルト値
   - display_in_table: (レスポンスのみ) テーブル表示フラグ
   - display_format: (レスポンスのみ) 表示フォーマット文字列

3. 使用可能なFieldType
   - FieldType.STRING: 文字列
   - FieldType.NUMBER: 数値
   - FieldType.DATE: 日付
   - FieldType.ENUM: 列挙型

4. 使用可能なInputType
   - InputType.TEXT: テキスト入力
   - InputType.DROPDOWN: ドロップダウン選択
   - InputType.DATEPICKER: 日付選択

5. 注意事項
   - API定義を変更した後はアプリケーションを再起動してください
   - idは一意である必要があります
   - enabled=FalseにするとAPIは無効化されます
"""

from src.api.definitions import (
    ApiDefinition, ApiFieldDefinition, FieldType, InputType, EnumMapping
)


# API定義
API_DEFINITIONS = [
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
                allow_multiple=False,  # 単一選択
            ),
            ApiFieldDefinition(
                name="amount_min",
                type=FieldType.NUMBER,
                label="最小金額",
                input_type=InputType.TEXT,
                default=0,
                configurable=False,  # 設定画面で表示・編集不可
            ),
            ApiFieldDefinition(
                name="amount_max",
                type=FieldType.NUMBER,
                label="最大金額",
                input_type=InputType.TEXT,
                default=10000,
                configurable=True,  # 設定画面で表示・編集可能
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
                allow_multiple=True,  # 複数選択を許可
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
        enabled=False,
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
    return API_DEFINITIONS.copy()


def get_api_definition(api_id: str) -> ApiDefinition | None:
    """指定したIDのAPI定義を取得"""
    for api_def in API_DEFINITIONS:
        if api_def.id == api_id:
            return api_def
    return None
