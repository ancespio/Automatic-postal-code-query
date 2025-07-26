# Copilot Instructions

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## 项目描述
这是一个Python脚本项目，用于自动化邮政编码查询。项目的主要功能包括：

1. 读取Excel表格中的地址信息
2. 自动访问邮政编码查询网站 http://dey.11185.cn/web/#/idtoolkitAddress
3. 查询每个地址对应的邮政编码
4. 将查询结果添加到Excel表格的对应行中

## 技术栈
- Python 3.x
- pandas: 用于Excel文件操作
- selenium: 用于网页自动化
- openpyxl: 用于Excel文件读写

## 编码指南
- 使用中文注释
- 遵循PEP 8编码规范
- 添加适当的错误处理和日志记录
- 支持批量处理和进度显示
