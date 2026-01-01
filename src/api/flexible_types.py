"""
柔軟なAPIタイプシステム（簡素化版）
デフォルトのApiConfigテンプレートを提供します。
"""

from typing import Any, Dict, List, Optional, Callable
import re


class ApiConfigTemplates:
    """デフォルトのApiConfigテンプレートを提供するクラス"""
    
    @staticmethod
    def create_type_a_template(name: str = "Type A API", url: str = "") -> 'ApiConfig':
        """経費申請APIのテンプレートを作成します"""
        from src.models.api_config import ApiConfig
        return ApiConfig(
            enabled=True,
            name=name,
            url=url,
            description="経費申請API",
            default_params={"count": 5},
            supported_params=["status", "min_amount", "max_amount", "category"],
            param_validators={
                "status": lambda v: [] if v in ["SUBMITTED", "APPROVED", "REJECTED", "PENDING"] else [f"無効なstatus: {v}"],
                "min_amount": lambda v: [] if isinstance(v, (int, float)) and v >= 0 else ["min_amountは0以上の数値である必要があります"],
                "max_amount": lambda v: [] if isinstance(v, (int, float)) and v >= 0 else ["max_amountは0以上の数値である必要があります"],
                "category": lambda v: [] if v in ["TRANSPORT", "BUSINESS_TRIP", "MEAL", "OFFICE_SUPPLIES", "TRAINING"] else [f"無効なcategory: {v}"]
            },
        )
    
    @staticmethod
    def create_type_b_template(name: str = "Type B API", url: str = "") -> 'ApiConfig':
        """休暇申請APIのテンプレートを作成します"""
        from src.models.api_config import ApiConfig
        return ApiConfig(
            enabled=True,
            name=name,
            url=url,
            description="休暇申請API",
            default_params={"count": 5},
            supported_params=["status", "start_date_from", "start_date_to", "min_days", "max_days"],
            param_validators={
                "status": lambda v: [] if v in ["SUBMITTED", "APPROVED", "REJECTED", "PENDING"] else [f"無効なstatus: {v}"],
                "start_date_from": lambda v: [] if re.match(r"\d{4}-\d{2}-\d{2}", str(v)) else ["start_date_fromはYYYY-MM-DD形式である必要があります"],
                "start_date_to": lambda v: [] if re.match(r"\d{4}-\d{2}-\d{2}", str(v)) else ["start_date_toはYYYY-MM-DD形式である必要があります"],
                "min_days": lambda v: [] if isinstance(v, (int, float)) and v >= 0 else ["min_daysは0以上の数値である必要があります"],
                "max_days": lambda v: [] if isinstance(v, (int, float)) and v >= 0 else ["max_amountは0以上の数値である必要があります"]
            },
        )
    
    @staticmethod
    def create_type_c_template(name: str = "Type C API", url: str = "") -> 'ApiConfig':
        """権限申請APIのテンプレートを作成します"""
        from src.models.api_config import ApiConfig
        return ApiConfig(
            enabled=True,
            name=name,
            url=url,
            description="権限申請API",
            default_params={"count": 5},
            supported_params=["status", "role", "approval_status"],
            param_validators={
                "status": lambda v: [] if v in ["SUBMITTED", "APPROVED", "REJECTED", "PENDING", "IN_REVIEW"] else [f"無効なstatus: {v}"],
                "role": lambda v: [] if v in ["ADMIN", "EDITOR", "VIEWER", "MANAGER", "SUPERVISOR"] else [f"無効なrole: {v}"],
                "approval_status": lambda v: [] if v in ["APPROVED", "PENDING", "REJECTED"] else [f"無効なapproval_status: {v}"]
            },
        )
    
    @staticmethod
    def create_custom_template(name: str = "Custom API", url: str = "") -> 'ApiConfig':
        """カスタムAPIのテンプレートを作成します"""
        from src.models.api_config import ApiConfig
        return ApiConfig(
            enabled=True,
            name=name,
            url=url,
            description="カスタムAPI",
            default_params={},
            supported_params=[],
            param_validators={},
        )
    
    @staticmethod
    def get_all_templates() -> Dict[str, 'ApiConfig']:
        """すべてのテンプレートを取得します"""
        return {
            "Type A API": ApiConfigTemplates.create_type_a_template(),
            "Type B API": ApiConfigTemplates.create_type_b_template(),
            "Type C API": ApiConfigTemplates.create_type_c_template(),
            "Custom API": ApiConfigTemplates.create_custom_template(),
        }
