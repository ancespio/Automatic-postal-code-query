#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮政编码查询脚本
功能：读取Excel表格中的地址信息，自动查询邮政编码并添加到对应行
作者：GitHub Copilot
日期：2025年7月26日
"""

import pandas as pd
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('postal_code_lookup.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PostalCodeLookup:
    """邮政编码查询类"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.base_url = "http://dey.11185.cn/web/#/idtoolkitAddress"
        
    def setup_driver(self) -> None:
        """初始化Chrome浏览器驱动"""
        try:
            logger.info("正在初始化浏览器驱动...")
            
            # Chrome选项配置
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 自动下载和设置ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            # 创建WebDriver实例
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            logger.info("浏览器驱动初始化完成")
            
        except Exception as e:
            logger.error(f"浏览器驱动初始化失败: {e}")
            raise
    
    def query_postal_code(self, address: str) -> List[str]:
        """
        查询地址对应的邮政编码
        
        Args:
            address: 要查询的地址
            
        Returns:
            邮政编码列表
        """
        try:
            logger.info(f"正在查询地址: {address}")
            
            # 访问查询网站
            self.driver.get(self.base_url)
            time.sleep(2)
            
            # 等待页面加载并查找地址输入框
            address_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            
            # 清空输入框并输入地址
            address_input.clear()
            address_input.send_keys(address)
            
            # 查找并点击查询按钮
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button, .btn, input[type='submit']"))
            )
            search_button.click()
            
            # 等待查询结果
            time.sleep(3)
            
            # 查找邮政编码结果
            postal_codes = self._extract_postal_codes()
            
            if postal_codes:
                logger.info(f"查询成功，找到邮政编码: {postal_codes}")
                return postal_codes
            else:
                logger.warning(f"未找到地址 '{address}' 的邮政编码")
                return []
                
        except TimeoutException:
            logger.error(f"查询地址 '{address}' 超时")
            return []
        except Exception as e:
            logger.error(f"查询地址 '{address}' 时发生错误: {e}")
            return []
    
    def _extract_postal_codes(self) -> List[str]:
        """从查询结果页面提取邮政编码"""
        postal_codes = []
        
        try:
            # 尝试多种可能的选择器来查找邮政编码
            selectors = [
                ".postal-code",
                ".zipcode", 
                ".post-code",
                "[class*='postal']",
                "[class*='zip']",
                "[class*='code']",
                "td:contains('编码')",
                "span:contains('编码')",
                ".result-item",
                ".search-result"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        # 检查是否包含6位数字的邮政编码
                        if text and len(text) >= 6 and text.isdigit():
                            if text not in postal_codes:
                                postal_codes.append(text)
                        # 处理包含邮政编码的文本
                        elif "编码" in text or "邮编" in text:
                            import re
                            codes = re.findall(r'\d{6}', text)
                            for code in codes:
                                if code not in postal_codes:
                                    postal_codes.append(code)
                except:
                    continue
            
            # 如果上述方法都没找到，尝试在整个页面中查找6位数字
            if not postal_codes:
                page_text = self.driver.page_source
                import re
                all_codes = re.findall(r'\b\d{6}\b', page_text)
                # 过滤掉明显不是邮政编码的数字（如年份等）
                for code in all_codes:
                    if code.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
                        if code not in postal_codes:
                            postal_codes.append(code)
                        if len(postal_codes) >= 5:  # 限制数量，避免过多无关编码
                            break
            
        except Exception as e:
            logger.error(f"提取邮政编码时发生错误: {e}")
        
        return postal_codes[:5]  # 最多返回5个邮政编码
    
    def process_excel_file(self, file_path: str, address_column: str, output_column: str = "邮政编码") -> None:
        """
        处理Excel文件，查询地址对应的邮政编码
        
        Args:
            file_path: Excel文件路径
            address_column: 地址列名
            output_column: 输出邮政编码的列名
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
            
            # 获取地址列表
            addresses = df[address_column].dropna().unique()
            total_count = len(addresses)
            
            logger.info(f"共需要查询 {total_count} 个地址")
            
            # 初始化浏览器
            self.setup_driver()
            
            # 逐个查询地址
            for idx, address in enumerate(addresses, 1):
                if pd.isna(address) or str(address).strip() == "":
                    continue
                
                address_str = str(address).strip()
                logger.info(f"正在处理 {idx}/{total_count}: {address_str}")
                
                # 查询邮政编码
                postal_codes = self.query_postal_code(address_str)
                
                if postal_codes:
                    # 将多个邮政编码用分号分隔
                    postal_code_str = "; ".join(postal_codes)
                    
                    # 更新对应行的邮政编码
                    mask = df[address_column] == address
                    df.loc[mask, output_column] = postal_code_str
                    
                    logger.info(f"已更新邮政编码: {postal_code_str}")
                else:
                    df.loc[df[address_column] == address, output_column] = "未找到"
                    logger.warning(f"未找到邮政编码，标记为'未找到'")
                
                # 添加延时，避免请求过于频繁
                time.sleep(2)
            
            # 保存结果
            output_path = self._generate_output_path(file_path)
            df.to_excel(output_path, index=False)
            logger.info(f"结果已保存到: {output_path}")
            
        except Exception as e:
            logger.error(f"处理Excel文件时发生错误: {e}")
            raise
        finally:
            self.close_driver()
    
    def _generate_output_path(self, original_path: str) -> str:
        """生成输出文件路径"""
        path = Path(original_path)
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        return str(parent / f"{stem}_with_postal_codes{suffix}")
    
    def close_driver(self) -> None:
        """关闭浏览器驱动"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器驱动已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器驱动时发生错误: {e}")


def main():
    """主函数"""
    print("欢迎使用邮政编码查询脚本！")
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
        lookup = PostalCodeLookup()
        lookup.process_excel_file(file_path, address_column, output_column)
        
        print("\n查询完成！请查看输出文件。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        logger.error(f"程序运行时发生错误: {e}")
        print(f"错误：{e}")


if __name__ == "__main__":
    main()
