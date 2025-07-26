#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证邮编库网站查询功能
"""

from advanced_postal_lookup import AdvancedPostalCodeLookup
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_query():
    """测试单个地址查询"""
    print("开始测试单个地址查询...")
    
    lookup = AdvancedPostalCodeLookup(headless=False)  # 使用有头模式便于观察
    
    try:
        # 初始化浏览器
        lookup.setup_driver()
        
        # 访问网站
        if lookup.navigate_to_site():
            # 测试查询
            test_address = "北京市朝阳区建国门外大街1号"
            postal_codes = lookup.query_postal_code(test_address)
            
            if postal_codes:
                print(f"✅ 查询成功！地址: {test_address}")
                print(f"📮 邮政编码: {postal_codes}")
            else:
                print(f"❌ 查询失败！地址: {test_address}")
        else:
            print("❌ 无法访问网站")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
    finally:
        lookup.close_driver()

def test_multiple_queries():
    """测试多个地址查询"""
    print("\n开始测试多个地址查询...")
    
    test_addresses = [
        "上海市浦东新区陆家嘴环路1000号",
        "广州市天河区珠江新城花城大道85号",
        "深圳市南山区粤海街道科技园南区"
    ]
    
    lookup = AdvancedPostalCodeLookup(headless=True)  # 使用无头模式提高速度
    
    try:
        lookup.setup_driver()
        
        if lookup.navigate_to_site():
            for i, address in enumerate(test_addresses, 1):
                print(f"\n🔍 测试 {i}/{len(test_addresses)}: {address}")
                postal_codes = lookup.query_postal_code(address)
                
                if postal_codes:
                    print(f"✅ 找到邮政编码: {postal_codes}")
                else:
                    print(f"❌ 未找到邮政编码")
        else:
            print("❌ 无法访问网站")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
    finally:
        lookup.close_driver()

if __name__ == "__main__":
    print("🧪 邮编库网站查询功能测试")
    print("=" * 50)
    
    # 测试单个查询
    test_single_query()
    
    # 测试多个查询
    test_multiple_queries()
    
    print("\n🎯 测试完成！")
