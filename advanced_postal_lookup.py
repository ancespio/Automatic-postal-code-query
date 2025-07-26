#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级邮政编码查询脚本
使用Selenium真正访问 http://dey.11185.cn/web/#/idtoolkitAddress 网站
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
from selenium.webdriver.common.keys import Keys
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_postal_lookup.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AdvancedPostalCodeLookup:
    """高级邮政编码查询类"""
    
    def __init__(self, headless: bool = True):
        self.driver = None
        self.wait = None
        self.base_url = "https://www.youbianku.com/"
        self.headless = headless
        
    def setup_driver(self) -> None:
        """初始化Chrome浏览器驱动"""
        try:
            logger.info("正在初始化浏览器驱动...")
            
            # Chrome选项配置
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            # 自动下载和设置ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            # 创建WebDriver实例
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 15)
            
            logger.info("浏览器驱动初始化完成")
            
        except Exception as e:
            logger.error(f"浏览器驱动初始化失败: {e}")
            raise
    
    def navigate_to_site(self) -> bool:
        """导航到查询网站"""
        try:
            logger.info(f"正在访问网站: {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # 等待页面加载完成
            self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            time.sleep(2)
            
            # 检查是否成功加载了邮编库网站
            page_title = self.driver.title
            if "邮编" in page_title or "youbianku" in page_title.lower():
                logger.info(f"成功访问邮编库网站，页面标题: {page_title}")
            else:
                logger.warning(f"页面标题不符合预期: {page_title}")
            
            logger.info("网站加载完成")
            return True
            
        except Exception as e:
            logger.error(f"访问网站失败: {e}")
            return False
    
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
            
            # 针对邮编库网站的输入框选择器
            input_selectors = [
                "#search_text",  # 邮编库的主要搜索框ID
                "input[name='q']",  # 常见的搜索框name
                "input[placeholder*='地址']",
                "input[placeholder*='请输入']", 
                "input[placeholder*='搜索']",
                "input[type='text']",
                ".search-input",
                ".search-box input",
                "input",
                "textarea"
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        input_element = elements[0]
                        logger.info(f"找到输入框，使用选择器: {selector}")
                        break
                except:
                    continue
            
            if not input_element:
                logger.error("未找到地址输入框")
                return []
            
            # 清空并输入地址
            input_element.clear()
            time.sleep(0.5)
            input_element.send_keys(address)
            time.sleep(1)
            
            # 针对邮编库网站的查询按钮选择器
            button_selectors = [
                "#search_btn",  # 邮编库的搜索按钮ID
                "input[type='submit']",
                "button[type='submit']",
                "button:contains('搜索')",
                "button:contains('查询')",
                ".search-btn",
                ".btn-search", 
                ".submit-btn",
                "button",
                "input[value*='搜索']",
                "input[value*='查询']"
            ]
            
            button_clicked = False
            for selector in button_selectors:
                try:
                    if ":contains" in selector:
                        # 使用XPath查找包含文本的按钮
                        text = selector.split("'")[1]
                        buttons = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                    else:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if buttons:
                        button = buttons[0]
                        if button.is_enabled():
                            button.click()
                            logger.info(f"点击查询按钮，使用选择器: {selector}")
                            button_clicked = True
                            break
                except:
                    continue
            
            # 如果没有找到按钮，尝试按回车键
            if not button_clicked:
                logger.info("未找到查询按钮，尝试按回车键")
                input_element.send_keys(Keys.RETURN)
            
            # 等待查询结果
            time.sleep(3)
            
            # 查找邮政编码结果
            postal_codes = self._extract_postal_codes()
            
            if postal_codes:
                logger.info(f"查询成功，找到邮政编码: {postal_codes}")
                return postal_codes
            else:
                logger.warning(f"未找到地址 '{address}' 的邮政编码")
                # 保存页面源码用于调试
                self._save_page_source(address)
                return []
                
        except Exception as e:
            logger.error(f"查询地址 '{address}' 时发生错误: {e}")
            return []
    
    def _extract_postal_codes(self) -> List[str]:
        """从查询结果页面提取邮政编码"""
        postal_codes = []
        
        try:
            # 等待结果加载
            time.sleep(3)
            
            # 针对邮编库网站的结果选择器
            selectors = [
                ".result .postal-code",  # 邮编库结果中的邮政编码
                ".result td",  # 表格中的数据
                ".search-result",
                ".postal-code",
                ".zipcode", 
                ".post-code",
                "[class*='postal']",
                "[class*='zip']", 
                "[class*='code']",
                ".result-item",
                ".result",
                ".data-item",
                "table td",  # 表格数据
                "tr td",     # 表格行数据
                "td",
                "span",
                "div"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text:
                            # 使用正则表达式查找6位数字的邮政编码
                            codes = re.findall(r'\b\d{6}\b', text)
                            for code in codes:
                                # 验证是否为有效的邮政编码（排除年份等）
                                if self._is_valid_postal_code(code) and code not in postal_codes:
                                    postal_codes.append(code)
                        
                        # 检查元素的属性中是否包含邮政编码
                        for attr_name in ['data-postcode', 'data-zipcode', 'title', 'alt']:
                            attr_value = element.get_attribute(attr_name)
                            if attr_value:
                                codes = re.findall(r'\b\d{6}\b', attr_value)
                                for code in codes:
                                    if self._is_valid_postal_code(code) and code not in postal_codes:
                                        postal_codes.append(code)
                except:
                    continue
            
            # 如果没有找到，尝试在整个页面源码中查找
            if not postal_codes:
                logger.info("尝试从页面源码中提取邮政编码")
                page_source = self.driver.page_source
                
                # 查找常见的邮政编码模式
                patterns = [
                    r'邮编[：:]\s*(\d{6})',  # 邮编: 123456
                    r'邮政编码[：:]\s*(\d{6})',  # 邮政编码: 123456
                    r'postcode[：:]\s*(\d{6})',  # postcode: 123456
                    r'\b\d{6}\b'  # 任何6位数字
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    for match in matches:
                        code = match if isinstance(match, str) else match
                        if self._is_valid_postal_code(code) and code not in postal_codes:
                            postal_codes.append(code)
                        if len(postal_codes) >= 5:  # 限制数量
                            break
                    if postal_codes:
                        break
            
        except Exception as e:
            logger.error(f"提取邮政编码时发生错误: {e}")
        
        return postal_codes[:5]  # 最多返回5个邮政编码
    
    def _is_valid_postal_code(self, code: str) -> bool:
        """验证是否为有效的中国邮政编码"""
        if len(code) != 6 or not code.isdigit():
            return False
        
        # 排除明显不是邮政编码的数字
        invalid_patterns = [
            '000000', '111111', '222222', '333333', '444444',
            '555555', '666666', '777777', '888888', '999999'
        ]
        
        if code in invalid_patterns:
            return False
        
        # 排除年份（1900-2099）
        if code.startswith(('19', '20')):
            return False
        
        # 中国邮政编码的有效范围
        # 第一位数字代表大区：1-华北，2-东北，3-华东，4-中南，5-西南，6-西北，7-台湾，8-港澳，9-新疆
        first_digit = int(code[0])
        if first_digit < 1 or first_digit > 9:
            return False
        
        # 排除一些特殊的无效编码
        if code.startswith('00') or code.endswith('0000'):
            return False
        
        return True
    
    def _save_page_source(self, address: str) -> None:
        """保存页面源码用于调试"""
        try:
            safe_filename = re.sub(r'[^\w\s-]', '', address)[:50]
            filename = f"page_source_{safe_filename}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logger.info(f"页面源码已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存页面源码失败: {e}")
    
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
            
            # 初始化浏览器
            self.setup_driver()
            
            # 访问网站
            if not self.navigate_to_site():
                raise Exception("无法访问查询网站")
            
            # 获取地址列表
            addresses = df[address_column].dropna().tolist()
            total_count = len(addresses)
            
            logger.info(f"共需要查询 {total_count} 个地址")
            
            # 逐个查询地址
            for index, row in df.iterrows():
                address = str(row[address_column]).strip()
                
                if pd.isna(row[address_column]) or address == "" or address == "nan":
                    continue
                
                logger.info(f"正在处理第 {index + 1} 行: {address}")
                
                # 查询邮政编码
                postal_codes = self.query_postal_code(address)
                
                if postal_codes:
                    # 将多个邮政编码用分号分隔
                    postal_code_str = "; ".join(postal_codes)
                    df.at[index, output_column] = postal_code_str
                    logger.info(f"已更新邮政编码: {postal_code_str}")
                else:
                    df.at[index, output_column] = "未找到"
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
    print("欢迎使用高级邮政编码查询脚本！")
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
        
        # 询问是否使用无头模式
        headless_choice = input("是否使用无头模式（不显示浏览器窗口）? (y/n，默认y): ").strip().lower()
        headless = headless_choice not in ['n', 'no', '否']
        
        # 确认信息
        print(f"\n配置信息:")
        print(f"文件路径: {file_path}")
        print(f"地址列: {address_column}")
        print(f"输出列: {output_column}")
        print(f"无头模式: {'是' if headless else '否'}")
        
        confirm = input("\n确认开始查询? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("操作已取消")
            return
        
        # 开始处理
        lookup = AdvancedPostalCodeLookup(headless=headless)
        lookup.process_excel_file(file_path, address_column, output_column)
        
        print("\n查询完成！请查看输出文件。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        logger.error(f"程序运行时发生错误: {e}")
        print(f"错误：{e}")


if __name__ == "__main__":
    main()
