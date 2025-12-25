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
            "/applications/type-a": "タイプAの申請データ",
            "/applications/type-b": "タイプBの申請データ", 
            "/applications/type-c": "タイプCの申請データ",
            "/health": "ヘルスチェック",
            "/docs": "APIドキュメント (Swagger UI)"
        }
    }

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/applications/type-a")
async def get_type_a_applications(count: int = 5):
    """
    タイプA（経費申請）のアプリケーションデータを返す
    
    Args:
        count: 返すアプリケーション数（デフォルト: 5）
    """
    applications = [generate_type_a_application(i) for i in range(1, count + 1)]
    
    return {
        "type": "A",
        "count": len(applications),
        "applications": applications
    }

@app.get("/applications/type-b")
async def get_type_b_applications(count: int = 5):
    """
    タイプB（休暇申請）のアプリケーションデータを返す
    
    Args:
        count: 返すアプリケーション数（デフォルト: 5）
    """
    applications = [generate_type_b_application(i) for i in range(1, count + 1)]
    
    return {
        "type": "B",
        "count": len(applications),
        "applications": applications
    }

@app.get("/applications/type-c")
async def get_type_c_applications(count: int = 5):
    """
    タイプC（権限申請）のアプリケーションデータを返す
    
    Args:
        count: 返すアプリケーション数（デフォルト: 5）
    """
    applications = [generate_type_c_application(i) for i in range(1, count + 1)]
    
    return {
        "type": "C",
        "count": len(applications),
        "applications": applications
    }

@app.get("/applications/all")
async def get_all_applications(count_per_type: int = 3):
    """
    すべてのタイプのアプリケーションデータを返す
    
    Args:
        count_per_type: タイプごとのアプリケーション数（デフォルト: 3）
    """
    type_a_apps = [generate_type_a_application(i) for i in range(1, count_per_type + 1)]
    type_b_apps = [generate_type_b_application(i) for i in range(1, count_per_type + 1)]
    type_c_apps = [generate_type_c_application(i) for i in range(1, count_per_type + 1)]
    
    all_applications = type_a_apps + type_b_apps + type_c_apps
    
    return {
        "type": "ALL",
        "count": len(all_applications),
        "applications": all_applications
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
