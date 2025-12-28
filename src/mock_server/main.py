"""
モックAPIサーバー
https://api-table.free.beeceptor.com の代わりになるローカルサーバー
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="API Table Mock Server",
    description="API Table Viewer用のモックサーバー",
    version="1.0.0"
)

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# サンプルデータ生成用のユーティリティ関数
def generate_applicant() -> Dict[str, Any]:
    """ランダムな申請者を生成"""
    first_names = ["山田", "佐藤", "鈴木", "高橋", "伊藤", "渡辺", "中村", "小林", "加藤", "吉田"]
    last_names = ["太郎", "花子", "一郎", "美咲", "健太", "さくら", "直樹", "優子", "大輔", "恵"]
    
    return {
        "id": f"u{random.randint(100, 999):03d}",
        "name": f"{random.choice(first_names)}{random.choice(last_names)}"
    }

def generate_type_a_application(index: int) -> Dict[str, Any]:
    """タイプA（経費申請）のアプリケーションを生成"""
    statuses = ["SUBMITTED", "APPROVED", "REJECTED", "PENDING"]
    categories = ["TRANSPORT", "BUSINESS_TRIP", "MEAL", "OFFICE_SUPPLIES", "TRAINING"]
    
    return {
        "id": f"A-{index:03d}",
        "type": "A",
        "title": f"経費申請 {index}",
        "status": random.choice(statuses),
        "applicant": generate_applicant(),
        "createdAt": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat() + "+09:00",
        "amount": random.randint(100, 50000),
        "currency": "JPY",
        "expenseCategory": random.choice(categories)
    }

def generate_type_b_application(index: int) -> Dict[str, Any]:
    """タイプB（休暇申請）のアプリケーションを生成"""
    statuses = ["SUBMITTED", "APPROVED", "REJECTED", "PENDING"]
    
    start_date = datetime.now() + timedelta(days=random.randint(1, 60))
    end_date = start_date + timedelta(days=random.randint(1, 14))
    
    return {
        "id": f"B-{index:03d}",
        "type": "B",
        "title": f"休暇申請 {index}",
        "status": random.choice(statuses),
        "applicant": generate_applicant(),
        "createdAt": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat() + "+09:00",
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "days": (end_date - start_date).days + 1
    }

def generate_type_c_application(index: int) -> Dict[str, Any]:
    """タイプC（権限申請）のアプリケーションを生成"""
    statuses = ["SUBMITTED", "APPROVED", "REJECTED", "PENDING", "IN_REVIEW"]
    roles = ["ADMIN", "EDITOR", "VIEWER", "MANAGER", "SUPERVISOR"]
    
    # 承認フローの生成
    approval_flow = []
    for step in range(1, random.randint(2, 4)):
        step_statuses = ["APPROVED", "PENDING", "REJECTED"]
        approval_flow.append({
            "step": step,
            "approver": generate_applicant(),
            "status": random.choice(step_statuses),
            "approvedAt": (datetime.now() - timedelta(days=random.randint(0, 10))).isoformat() + "+09:00" if step == 1 else None
        })
    
    return {
        "id": f"C-{index:03d}",
        "type": "C",
        "title": f"権限申請 {index}",
        "status": random.choice(statuses),
        "applicant": generate_applicant(),
        "createdAt": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat() + "+09:00",
        "requestedRole": random.choice(roles),
        "approvalFlow": approval_flow
    }

# エンドポイント定義
@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "API Table Mock Server",
        "version": "1.0.0",
        "endpoints": {
            "/applications/type-a": "タイプAの申請データ（フィルター: status, min_amount, max_amount, category）",
            "/applications/type-b": "タイプBの申請データ（フィルター: status, start_date_from, start_date_to, min_days, max_days）", 
            "/applications/type-c": "タイプCの申請データ（フィルター: status, role, approval_status）",
            "/applications/all": "すべてのタイプの申請データ（フィルター: status, applicant_name, created_from, created_to）",
            "/health": "ヘルスチェック",
            "/docs": "APIドキュメント (Swagger UI)"
        },
        "filtering_note": "各エンドポイントはクエリパラメータでフィルタリング可能です。詳細は /docs を参照してください。"
    }

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/applications/type-a")
async def get_type_a_applications(
    count: int = 5,
    status: str = None,
    min_amount: int = None,
    max_amount: int = None,
    category: str = None
):
    """
    タイプA（経費申請）のアプリケーションデータを返す
    
    Args:
        count: 返すアプリケーション数（デフォルト: 5）
        status: ステータスでフィルタ（SUBMITTED, APPROVED, REJECTED, PENDING）
        min_amount: 最小金額
        max_amount: 最大金額
        category: 経費カテゴリー（TRANSPORT, BUSINESS_TRIP, MEAL, OFFICE_SUPPLIES, TRAINING）
    """
    applications = [generate_type_a_application(i) for i in range(1, count + 1)]
    
    # フィルタリングを適用
    filtered_applications = applications
    
    if status:
        filtered_applications = [app for app in filtered_applications if app.get("status") == status]
    
    if min_amount is not None:
        filtered_applications = [app for app in filtered_applications if app.get("amount", 0) >= min_amount]
    
    if max_amount is not None:
        filtered_applications = [app for app in filtered_applications if app.get("amount", float('inf')) <= max_amount]
    
    if category:
        filtered_applications = [app for app in filtered_applications if app.get("expenseCategory") == category]
    
    return {
        "type": "A",
        "count": len(filtered_applications),
        "total_count": len(applications),
        "filtered_count": len(filtered_applications),
        "applications": filtered_applications
    }

@app.get("/applications/type-b")
async def get_type_b_applications(
    count: int = 5,
    status: str = None,
    start_date_from: str = None,
    start_date_to: str = None,
    min_days: int = None,
    max_days: int = None
):
    """
    タイプB（休暇申請）のアプリケーションデータを返す
    
    Args:
        count: 返すアプリケーション数（デフォルト: 5）
        status: ステータスでフィルタ（SUBMITTED, APPROVED, REJECTED, PENDING）
        start_date_from: 開始日（From、YYYY-MM-DD形式）
        start_date_to: 開始日（To、YYYY-MM-DD形式）
        min_days: 最小日数
        max_days: 最大日数
    """
    applications = [generate_type_b_application(i) for i in range(1, count + 1)]
    
    # フィルタリングを適用
    filtered_applications = applications
    
    if status:
        filtered_applications = [app for app in filtered_applications if app.get("status") == status]
    
    if start_date_from:
        filtered_applications = [
            app for app in filtered_applications 
            if app.get("startDate") and app.get("startDate") >= start_date_from
        ]
    
    if start_date_to:
        filtered_applications = [
            app for app in filtered_applications 
            if app.get("startDate") and app.get("startDate") <= start_date_to
        ]
    
    if min_days is not None:
        filtered_applications = [app for app in filtered_applications if app.get("days", 0) >= min_days]
    
    if max_days is not None:
        filtered_applications = [app for app in filtered_applications if app.get("days", float('inf')) <= max_days]
    
    return {
        "type": "B",
        "count": len(filtered_applications),
        "total_count": len(applications),
        "filtered_count": len(filtered_applications),
        "applications": filtered_applications
    }

@app.get("/applications/type-c")
async def get_type_c_applications(
    count: int = 5,
    status: str = None,
    role: str = None,
    approval_status: str = None
):
    """
    タイプC（権限申請）のアプリケーションデータを返す
    
    Args:
        count: 返すアプリケーション数（デフォルト: 5）
        status: ステータスでフィルタ（SUBMITTED, APPROVED, REJECTED, PENDING, IN_REVIEW）
        role: リクエストされたロールでフィルタ（ADMIN, EDITOR, VIEWER, MANAGER, SUPERVISOR）
        approval_status: 承認フローステータスでフィルタ（APPROVED, PENDING, REJECTED）
    """
    applications = [generate_type_c_application(i) for i in range(1, count + 1)]
    
    # フィルタリングを適用
    filtered_applications = applications
    
    if status:
        filtered_applications = [app for app in filtered_applications if app.get("status") == status]
    
    if role:
        filtered_applications = [app for app in filtered_applications if app.get("requestedRole") == role]
    
    if approval_status:
        # 承認フローに指定したステータスのステップがあるかチェック
        filtered_applications = [
            app for app in filtered_applications 
            if any(
                step.get("status") == approval_status 
                for step in app.get("approvalFlow", [])
            )
        ]
    
    return {
        "type": "C",
        "count": len(filtered_applications),
        "total_count": len(applications),
        "filtered_count": len(filtered_applications),
        "applications": filtered_applications
    }

@app.get("/applications/all")
async def get_all_applications(
    count_per_type: int = 3,
    status: str = None,
    applicant_name: str = None,
    created_from: str = None,
    created_to: str = None
):
    """
    すべてのタイプのアプリケーションデータを返す
    
    Args:
        count_per_type: タイプごとのアプリケーション数（デフォルト: 3）
        status: ステータスでフィルタ（SUBMITTED, APPROVED, REJECTED, PENDING, IN_REVIEW）
        applicant_name: 申請者名（部分一致）
        created_from: 作成日（From、YYYY-MM-DD形式）
        created_to: 作成日（To、YYYY-MM-DD形式）
    """
    type_a_apps = [generate_type_a_application(i) for i in range(1, count_per_type + 1)]
    type_b_apps = [generate_type_b_application(i) for i in range(1, count_per_type + 1)]
    type_c_apps = [generate_type_c_application(i) for i in range(1, count_per_type + 1)]
    
    all_applications = type_a_apps + type_b_apps + type_c_apps
    
    # フィルタリングを適用
    filtered_applications = all_applications
    
    if status:
        filtered_applications = [app for app in filtered_applications if app.get("status") == status]
    
    if applicant_name:
        filtered_applications = [
            app for app in filtered_applications 
            if applicant_name.lower() in app.get("applicant", {}).get("name", "").lower()
        ]
    
    if created_from:
        filtered_applications = [
            app for app in filtered_applications 
            if app.get("createdAt") and app.get("createdAt")[:10] >= created_from
        ]
    
    if created_to:
        filtered_applications = [
            app for app in filtered_applications 
            if app.get("createdAt") and app.get("createdAt")[:10] <= created_to
        ]
    
    return {
        "type": "ALL",
        "count": len(filtered_applications),
        "total_count": len(all_applications),
        "filtered_count": len(filtered_applications),
        "applications": filtered_applications
    }

# エラーテスト用エンドポイント
@app.get("/applications/error")
async def get_error_response():
    """エラーレスポンスを返す（テスト用）"""
    raise HTTPException(status_code=500, detail="Internal Server Error: テスト用エラー")

@app.get("/applications/timeout")
async def get_timeout_response():
    """タイムアウトをシミュレート（テスト用）"""
    import time
    time.sleep(60)  # 60秒待機してタイムアウトを発生させる
    return {"message": "This should timeout"}

if __name__ == "__main__":
    uvicorn.run(
        "src.mock_server.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
