#!/usr/bin/env python3
"""
新しいAPIタイプシステムのテストスクリプト
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.types import ApiType, ApiHandlerFactory
from src.models.api_config import ApiConfig, HttpMethod
from src.api.client import ApiClient, ApiExecutor

def test_api_handler_factory():
    """APIハンドラーファクトリのテスト"""
    print("=== APIハンドラーファクトリのテスト ===")
    
    # 各APIタイプのハンドラーを作成
    for api_type in [ApiType.TYPE_A, ApiType.TYPE_B, ApiType.TYPE_C]:
        try:
            handler = ApiHandlerFactory.create_handler(api_type)
            print(f"✓ {api_type.value}タイプのハンドラーを作成しました")
            print(f"  エンドポイント: {handler.get_endpoint()}")
            print(f"  デフォルトパラメータ: {handler.get_default_params()}")
            print(f"  フィルターパラメータ: {handler.get_filter_params()}")
        except Exception as e:
            print(f"✗ {api_type.value}タイプのハンドラー作成に失敗: {e}")
    
    print()

def test_api_config():
    """API設定のテスト"""
    print("=== API設定のテスト ===")
    
    # タイプAの設定
    config_a = ApiConfig(
        name="Type A Test",
        url="http://localhost:8001/applications/type-a",
        method=HttpMethod.GET,
        api_type=ApiType.TYPE_A,
        filter_params={
            "status": "APPROVED",
            "min_amount": 1000,
            "max_amount": 5000,
            "category": "TRANSPORT"
        }
    )
    
    print(f"✓ タイプAの設定を作成しました")
    print(f"  APIタイプ: {config_a.api_type}")
    print(f"  フィルターパラメータ: {config_a.filter_params}")
    
    # バリデーションのテスト
    errors = config_a.validate()
    if errors:
        print(f"✗ バリデーションエラー: {errors}")
    else:
        print(f"✓ バリデーション成功")
    
    print()

def test_api_execution():
    """API実行のテスト"""
    print("=== API実行のテスト ===")
    
    # 各APIタイプの設定を作成
    configs = []
    
    # タイプA
    configs.append(ApiConfig(
        name="Type A API",
        url="http://localhost:8001/applications/type-a",
        method=HttpMethod.GET,
        api_type=ApiType.TYPE_A,
        filter_params={"count": 3}
    ))
    
    # タイプB
    configs.append(ApiConfig(
        name="Type B API",
        url="http://localhost:8001/applications/type-b",
        method=HttpMethod.GET,
        api_type=ApiType.TYPE_B,
        filter_params={"count": 2}
    ))
    
    # タイプC
    configs.append(ApiConfig(
        name="Type C API",
        url="http://localhost:8001/applications/type-c",
        method=HttpMethod.GET,
        api_type=ApiType.TYPE_C,
        filter_params={"count": 2}
    ))
    
    # API実行
    executor = ApiExecutor()
    try:
        results = executor.execute(configs)
        
        success_count = sum(1 for r in results if r["success"])
        print(f"✓ API実行完了: {success_count}/{len(results)} 成功")
        
        # アプリケーションデータの抽出
        applications = executor.extract_applications_data(results)
        print(f"✓ アプリケーションデータ抽出: {len(applications)} 件")
        
        # APIタイプごとの集計
        type_counts = {}
        for app in applications:
            api_type = app.get("api_type", "Unknown")
            type_counts[api_type] = type_counts.get(api_type, 0) + 1
        
        print(f"  APIタイプ別集計:")
        for api_type, count in type_counts.items():
            print(f"    {api_type}: {count} 件")
        
    except Exception as e:
        print(f"✗ API実行エラー: {e}")
    
    executor.close()
    print()

def test_url_based_api_type_detection():
    """URLベースのAPIタイプ検出のテスト"""
    print("=== URLベースのAPIタイプ検出のテスト ===")
    
    test_urls = [
        ("http://localhost:8001/applications/type-a", "A"),
        ("http://localhost:8001/applications/type-b", "B"),
        ("http://localhost:8001/applications/type-c", "C"),
        ("http://example.com/api/type-a/v1", "A"),
        ("http://example.com/type-b/applications", "B"),
        ("http://example.com/type-c", "C"),
        ("http://example.com/unknown", "Unknown"),
    ]
    
    for url, expected_type in test_urls:
        handler = ApiHandlerFactory.get_handler_for_url(url)
        if handler:
            detected_type = handler.api_type.value
            status = "✓" if detected_type == expected_type else "✗"
            print(f"{status} URL: {url}")
            print(f"  検出タイプ: {detected_type}, 期待タイプ: {expected_type}")
        else:
            status = "✓" if expected_type == "Unknown" else "✗"
            print(f"{status} URL: {url}")
            print(f"  検出タイプ: None, 期待タイプ: {expected_type}")
    
    print()

def main():
    """メイン関数"""
    print("新しいAPIタイプシステムのテストを開始します\n")
    
    try:
        test_api_handler_factory()
        test_api_config()
        test_url_based_api_type_detection()
        test_api_execution()
        
        print("すべてのテストが完了しました！")
        
    except Exception as e:
        print(f"テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
