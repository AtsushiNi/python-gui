#!/usr/bin/env python3
"""
柔軟なAPIタイプシステムのテストスクリプト
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.flexible_types import (
    ApiCategory, ApiDefinition, FlexibleApiRegistry,
    register_api_definition, find_api_definition, get_api_handler
)

def test_api_registry():
    """APIレジストリのテスト"""
    print("=== APIレジストリのテスト ===")
    
    # 新しいレジストリを作成
    registry = FlexibleApiRegistry()
    
    print(f"登録済みAPI定義数: {len(registry.definitions)}")
    
    # 既知のURLをテスト
    test_urls = [
        ("http://localhost:8001/applications/type-a", "Type A API"),
        ("http://localhost:8001/applications/type-b", "Type B API"),
        ("http://localhost:8001/applications/type-c", "Type C API"),
        ("http://example.com/api/v1/users", "Custom Users API"),  # カスタムAPI
        ("http://example.com/data", "Custom Data API"),  # カスタムAPI
    ]
    
    for url, expected_name in test_urls:
        definition = registry.find_definition(url)
        if definition:
            print(f"✓ URL: {url}")
            print(f"  検出名: {definition.name}")
            print(f"  カテゴリー: {definition.category.value}")
            print(f"  サポートパラメータ: {definition.supported_params}")
        else:
            print(f"✗ URL: {url} - 定義が見つかりません")
    
    print()

def test_custom_api_definition():
    """カスタムAPI定義のテスト"""
    print("=== カスタムAPI定義のテスト ===")
    
    # カスタムAPI定義を作成
    custom_definition = ApiDefinition(
        name="Weather API",
        endpoint_pattern=r"/weather/forecast",
        description="天気予報API",
        category=ApiCategory.CUSTOM,
        default_params={"units": "metric", "lang": "ja"},
        supported_params=["city", "days", "units"],
        param_validators={
            "city": lambda v: [] if isinstance(v, str) and v else ["cityは文字列である必要があります"],
            "days": lambda v: [] if isinstance(v, int) and 1 <= v <= 7 else ["daysは1〜7の整数である必要があります"],
            "units": lambda v: [] if v in ["metric", "imperial"] else ["unitsは'metric'または'imperial'である必要があります"]
        }
    )
    
    # レジストリに登録
    register_api_definition(custom_definition)
    
    # テスト
    test_url = "http://api.example.com/weather/forecast"
    definition = find_api_definition(test_url)
    
    if definition and definition.name == "Weather API":
        print(f"✓ カスタムAPI定義が正常に登録されました")
        print(f"  名前: {definition.name}")
        print(f"  カテゴリー: {definition.category.value}")
        print(f"  デフォルトパラメータ: {definition.default_params}")
        
        # パラメータ検証のテスト
        valid_params = {"city": "Tokyo", "days": 3, "units": "metric"}
        invalid_params = {"city": "", "days": 10, "units": "unknown"}
        
        valid_errors = definition.validate_params(**valid_params)
        invalid_errors = definition.validate_params(**invalid_params)
        
        print(f"  有効パラメータ検証: {'成功' if not valid_errors else f'失敗: {valid_errors}'}")
        print(f"  無効パラメータ検証: {'期待通り失敗' if invalid_errors else '予期せず成功'}")
    else:
        print(f"✗ カスタムAPI定義の登録に失敗")
    
    print()

def test_api_handler():
    """APIハンドラーのテスト"""
    print("=== APIハンドラーのテスト ===")
    
    # 既知のAPI用のハンドラー
    known_urls = [
        "http://localhost:8001/applications/type-a",
        "http://localhost:8001/applications/type-b",
        "http://localhost:8001/applications/type-c",
    ]
    
    for url in known_urls:
        try:
            handler = get_api_handler(url)
            definition = handler.definition
            print(f"✓ URL: {url}")
            print(f"  ハンドラー: {handler.__class__.__name__}")
            print(f"  定義: {definition.name}")
            print(f"  カテゴリー: {definition.category.value}")
        except Exception as e:
            print(f"✗ URL: {url} - ハンドラー取得エラー: {e}")
    
    # カスタムAPI用のハンドラー
    custom_url = "http://example.com/api/unknown-endpoint"
    try:
        handler = get_api_handler(custom_url)
        definition = handler.definition
        print(f"✓ カスタムURL: {custom_url}")
        print(f"  ハンドラー: {handler.__class__.__name__}")
        print(f"  定義: {definition.name}")
        print(f"  カテゴリー: {definition.category.value}")
        print(f"  タイプフィールド: {definition.type_field}")
    except Exception as e:
        print(f"✗ カスタムURL: {custom_url} - ハンドラー取得エラー: {e}")
    
    print()

def test_dynamic_api_addition():
    """動的API追加のテスト"""
    print("=== 動的API追加のテスト ===")
    
    # 実行時に新しいAPI定義を追加
    new_definition = ApiDefinition(
        name="Inventory API",
        endpoint_pattern=r"/api/inventory",
        description="在庫管理API",
        category=ApiCategory.CUSTOM,
        default_params={"limit": 100, "offset": 0},
        supported_params=["sku", "category", "min_stock", "max_stock"],
        param_validators={
            "sku": lambda v: [] if isinstance(v, str) else ["skuは文字列である必要があります"],
            "category": lambda v: [] if v in ["electronics", "clothing", "food"] else ["無効なカテゴリー"],
            "min_stock": lambda v: [] if isinstance(v, int) and v >= 0 else ["min_stockは0以上の整数である必要があります"],
            "max_stock": lambda v: [] if isinstance(v, int) and v >= 0 else ["max_stockは0以上の整数である必要があります"]
        }
    )
    
    # 登録
    register_api_definition(new_definition)
    
    # テストURL
    test_urls = [
        "http://example.com/api/inventory",
        "http://api.company.com/api/inventory?sku=ABC123",
        "http://localhost:8080/api/inventory",
    ]
    
    for url in test_urls:
        definition = find_api_definition(url)
        if definition and definition.name == "Inventory API":
            print(f"✓ 動的追加APIが検出されました: {url}")
            print(f"  名前: {definition.name}")
            print(f"  サポートパラメータ: {definition.supported_params}")
        else:
            print(f"✗ 動的追加APIが検出されませんでした: {url}")
    
    print()

def test_url_pattern_matching():
    """URLパターンマッチングのテスト"""
    print("=== URLパターンマッチングのテスト ===")
    
    # 様々なURLパターンをテスト
    test_cases = [
        ("http://localhost:8001/applications/type-a", True, "Type A API"),
        ("http://localhost:8001/applications/type-a/v2", True, "Type A API"),
        ("http://api.example.com/applications/type-a", True, "Type A API"),
        ("http://localhost:8001/applications/type-b", True, "Type B API"),
        ("http://localhost:8001/applications/type-c", True, "Type C API"),
        ("http://example.com/api/health", False, "Custom Health API"),
        ("http://example.com/data/metrics", False, "Custom Metrics API"),
        ("http://example.com/", False, "Custom API"),
    ]
    
    for url, should_match_known, expected_name in test_cases:
        definition = find_api_definition(url)
        
        if should_match_known:
            if definition and definition.name == expected_name:
                print(f"✓ {url} - 期待通り既知APIにマッチ")
            else:
                print(f"✗ {url} - 既知APIにマッチせず")
        else:
            if definition:
                print(f"✓ {url} - カスタムAPIとして検出: {definition.name}")
            else:
                print(f"✗ {url} - 定義が見つかりません")
    
    print()

def main():
    """メイン関数"""
    print("柔軟なAPIタイプシステムのテストを開始します\n")
    
    try:
        test_api_registry()
        test_custom_api_definition()
        test_api_handler()
        test_dynamic_api_addition()
        test_url_pattern_matching()
        
        print("すべてのテストが完了しました！")
        print("\n=== システムの特徴 ===")
        print("1. 動的API定義登録: 実行時に新しいAPIを追加可能")
        print("2. 柔軟なURLマッチング: 正規表現パターンによるURLマッチング")
        print("3. カスタムAPIサポート: typeがないAPIも自動的にカスタムAPIとして処理")
        print("4. パラメータ検証: API定義ごとにカスタムバリデーション")
        print("5. プラグイン可能: register_api_definition()で簡単に拡張可能")
        
    except Exception as e:
        print(f"テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
