#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建示例Excel文件用于测试
"""

import pandas as pd

def create_sample_excel():
    """创建示例Excel文件"""
    
    # 创建示例数据
    data = {
        '序号': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        '地址': [
            '北京市朝阳区建国门外大街1号',
            '上海市浦东新区陆家嘴环路1000号',
            '广州市天河区珠江新城花城大道85号',
            '深圳市南山区粤海街道科技园南区',
            '杭州市西湖区文三路259号',
            '南京市鼓楼区中山路321号',
            '武汉市武昌区中南路99号',
            '成都市锦江区红星路三段1号',
            '西安市雁塔区小寨西路232号',
            '重庆市渝中区解放碑步行街88号'
        ],
        '备注': [
            '国贸大厦',
            '上海中心',
            '广州塔附近',
            '腾讯总部',
            '阿里巴巴园区',
            '新街口商圈',
            '中南商业大楼',
            '春熙路商圈',
            '小寨赛格',
            '解放碑CBD'
        ]
    }
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 保存到Excel文件
    output_file = 'sample_addresses.xlsx'
    df.to_excel(output_file, index=False)
    
    print(f"示例Excel文件已创建: {output_file}")
    print("\n文件内容预览:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    create_sample_excel()
