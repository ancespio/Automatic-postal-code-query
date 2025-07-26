#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版邮政编码查询脚本
专门针对 http://dey.11185.cn/web/#/idtoolkitAddress 网站
"""

import pandas as pd
import time
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimplePostalCodeLookup:
    """简化版邮政编码查询类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def query_postal_code_api(self, address: str) -> List[str]:
        """
        通过API查询邮政编码
        """
        try:
            # 尝试不同的API端点
            api_urls = [
                "http://dey.11185.cn/api/address/search",
                "http://dey.11185.cn/api/toolkit/address",
                "http://dey.11185.cn/web/api/address"
            ]
            
            for api_url in api_urls:
                try:
                    params = {
                        'address': address,
                        'query': address,
                        'keyword': address
                    }
                    
                    response = self.session.get(api_url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        postal_codes = self._extract_codes_from_api(data)
                        if postal_codes:
                            return postal_codes
                except:
                    continue
            
            return []
            
        except Exception as e:
            logger.error(f"API查询失败: {e}")
            return []
    
    def _extract_codes_from_api(self, data) -> List[str]:
        """从API响应中提取邮政编码"""
        postal_codes = []
        
        if isinstance(data, dict):
            # 递归查找可能的邮政编码字段
            for key, value in data.items():
                if key.lower() in ['postcode', 'zipcode', 'postal_code', 'code', '邮编', '邮政编码']:
                    if isinstance(value, str) and len(value) == 6 and value.isdigit():
                        postal_codes.append(value)
                elif isinstance(value, (dict, list)):
                    postal_codes.extend(self._extract_codes_from_api(value))
        elif isinstance(data, list):
            for item in data:
                postal_codes.extend(self._extract_codes_from_api(item))
        
        return list(set(postal_codes))
    
    def manual_lookup(self, address: str) -> List[str]:
        """
        手动查询邮政编码（使用已知数据）
        这是一个简化的实现，包含一些常见地址的邮政编码
        """
        # 这里可以添加一些已知的地址和邮政编码映射
        known_mappings = {
            '北京市': ['100000'],
            '上海市': ['200000'],
            '广州市': ['510000'],
            '深圳市': ['518000'],
            '杭州市': ['310000'],
            '南京市': ['210000'],
            '武汉市': ['430000'],
            '成都市': ['610000'],
            '西安市': ['710000'],
            '重庆市': ['400000']
        }
        
        for key, codes in known_mappings.items():
            if key in address:
                return codes
        
        return []
    
    def process_excel_file(self, file_path: str, address_column: str, output_column: str = "邮政编码") -> None:
        """
        处理Excel文件，查询地址对应的邮政编码
        """
        try:
            # 读取Excel文件
            logger.info(f"正在读取Excel文件: {file_path}")
            df = pd.read_excel(file_path)
            
            if address_column not in df.columns:
                raise ValueError(f"未找到地址列 '{address_column}'")
            
            # 初始化邮政编码列
            if output_column not in df.columns:
                df[output_column] = ""
            
            # 处理每一行
            for index, row in df.iterrows():
                address = str(row[address_column]).strip()
                
                if pd.isna(row[address_column]) or address == "" or address == "nan":
                    continue
                
                logger.info(f"正在查询地址: {address}")
                
                # 先尝试API查询
                postal_codes = self.query_postal_code_api(address)
                
                # 如果API查询失败，使用手动查询
                if not postal_codes:
                    postal_codes = self.manual_lookup(address)
                
                if postal_codes:
                    postal_code_str = "; ".join(postal_codes)
                    df.at[index, output_column] = postal_code_str
                    logger.info(f"找到邮政编码: {postal_code_str}")
                else:
                    df.at[index, output_column] = "未找到"
                    logger.warning(f"未找到邮政编码")
                
                # 添加延时
                time.sleep(1)
            
            # 保存结果
            output_path = self._generate_output_path(file_path)
            df.to_excel(output_path, index=False)
            logger.info(f"结果已保存到: {output_path}")
            
        except Exception as e:
            logger.error(f"处理Excel文件时发生错误: {e}")
            raise
    
    def _generate_output_path(self, original_path: str) -> str:
        """生成输出文件路径"""
        path = Path(original_path)
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        return str(parent / f"{stem}_with_postal_codes{suffix}")


def main():
    """主函数"""
    print("欢迎使用简化版邮政编码查询脚本！")
    print("=" * 50)
    
    try:
        # 获取用户输入
        file_path = input("请输入Excel文件路径: ").strip()
        
        if not file_path:
            print("错误：文件路径不能为空")
            return
        
        if not Path(file_path).exists():
            print(f"错误：文件 '{file_path}' 不存在")
            return
        
        # 读取Excel文件查看列名
        try:
            df = pd.read_excel(file_path)
            print(f"\nExcel文件包含以下列:")
            for i, col in enumerate(df.columns, 1):
                print(f"{i}. {col}")
        except Exception as e:
            print(f"错误：无法读取Excel文件 - {e}")
            return
        
        address_column = input("\n请输入地址列名: ").strip()
        
        if not address_column:
            print("错误：地址列名不能为空")
            return
        
        output_column = input("请输入邮政编码输出列名 (默认为'邮政编码'): ").strip()
        if not output_column:
            output_column = "邮政编码"
        
        # 确认信息
        print(f"\n配置信息:")
        print(f"文件路径: {file_path}")
        print(f"地址列: {address_column}")
        print(f"输出列: {output_column}")
        
        confirm = input("\n确认开始查询? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("操作已取消")
            return
        
        # 开始处理
        lookup = SimplePostalCodeLookup()
        lookup.process_excel_file(file_path, address_column, output_column)
        
        print("\n查询完成！请查看输出文件。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        logger.error(f"程序运行时发生错误: {e}")
        print(f"错误：{e}")


if __name__ == "__main__":
    main()
