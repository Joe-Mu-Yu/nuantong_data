#!/usr/bin/env python3
"""
兰天热力新世纪站数据自动合并模块
功能：自动读取指定目录下的低环数据和二网数据文件，按标准格式合并为统一Excel文件
无需手动指定文件名，通过关键词自动识别文件类型
"""

import pandas as pd
import os
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class HeatDataMerger:
    def __init__(self, data_dir='.', output_file='merged_data_result.xlsx'):
        """
        初始化数据合并器
        :param data_dir: 数据文件所在目录，默认当前目录
        :param output_file: 输出文件名，默认merged_data_result.xlsx
        """
        self.data_dir = data_dir
        self.output_file = output_file
        # 定义标准列名顺序（27列）
        self.standard_columns = [
            '序号', '管理单位', '管理所', '换热站', '测点名称', '位置', '楼层', '设备标识',
            '数据时间', '室温温度(℃)', '报警状态', '源文件', '数据类型', '环路',
            '计划热量(GJ)', '瞬时热量(GJ/H)', '热量(GJ)', '瞬时流量(T/H)',
            '单位流量(T/万㎡)', '阀门开度(%)', '设定(℃)', '反馈(℃)', '供温(℃)',
            '回温(℃)', '供压(Mpa)', '回压(Mpa)', '日期'
        ]
    
    def find_data_files(self):
        """
        通过关键词自动识别文件类型
        :return: 低环文件列表，二网文件列表
        """
        low_cycle_files = []
        two_network_files = []
        
        # 遍历目录下所有Excel文件
        for filename in os.listdir(self.data_dir):
            if (filename.endswith('.xlsx') or filename.endswith('.xls')) and not filename.startswith('~$'):  # 排除临时文件
                file_path = os.path.join(self.data_dir, filename)
                
                # 关键词识别低环数据文件（包含"低环"关键词）
                if '低环' in filename:
                    low_cycle_files.append(file_path)
                # 关键词识别二网数据文件（包含"二网"关键词）
                elif '二网' in filename:
                    two_network_files.append(file_path)
        
        return low_cycle_files, two_network_files
    
    def process_low_cycle_data(self, file_path):
        """
        处理低环数据文件
        :param file_path: 低环文件路径
        :return: 处理后的DataFrame
        """
        # 读取原始数据
        df = pd.read_excel(file_path)
        
        # 确保必要列存在
        required_columns = ['序号', '管理单位', '管理所', '换热站', '测点名称', 
                          '位置', '楼层', '设备标识', '数据时间', '室温温度(℃)', '报警状态']
        for col in required_columns:
            if col not in df.columns:
                raise Exception(f"低环文件缺少必要列：{col}")
        
        # 补充缺失的16个列
        missing_columns = [col for col in self.standard_columns if col not in df.columns]
        for col in missing_columns:
            df[col] = None
        
        # 填充标识信息
        df['源文件'] = os.path.basename(file_path)
        df['数据类型'] = '低环'
        
        # 处理时间格式
        df['数据时间'] = pd.to_datetime(df['数据时间'], errors='coerce')
        # 提取日期
        df['日期'] = df['数据时间'].dt.strftime('%Y-%m-%d')
        
        # 按标准列顺序重新排列
        df = df[self.standard_columns]
        
        return df
    
    def process_two_network_data(self, file_path):
        """
        处理二网数据文件
        :param file_path: 二网文件路径
        :return: 处理后的DataFrame
        """
        filename = os.path.basename(file_path)
        
        # 读取原始数据
        df = pd.read_excel(file_path)
        
        # 确保必要列存在
        required_columns = ['环路', '计划热量(GJ)', '瞬时热量(GJ/H)', '热量(GJ)', 
                          '瞬时流量(T/H)', '单位流量(T/万㎡)', '阀门开度(%)', 
                          '设定(℃)', '反馈(℃)', '供温(℃)', '回温(℃)', 
                          '供压(Mpa)', '回压(Mpa)', '数据时间']
        for col in required_columns:
            if col not in df.columns:
                raise Exception(f"二网文件缺少必要列：{col}")
        
        # 补充缺失的13个列
        missing_columns = [col for col in self.standard_columns if col not in df.columns]
        for col in missing_columns:
            df[col] = None
        
        # 填充标识信息
        df['源文件'] = filename
        df['数据类型'] = '二网'
        
        # 从文件名提取日期（匹配YYYY-MM-DD格式）
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if not date_match:
            raise Exception(f"无法从二网文件名提取日期：{filename}，请确保文件名包含YYYY-MM-DD格式日期")
        
        file_date = date_match.group(1)
        df['日期'] = file_date
        
        # 处理时间格式（组合日期和时间）
        def combine_datetime(row):
            if pd.notna(row['数据时间']) and str(row['数据时间']).strip():
                time_str = str(row['数据时间']).strip()
                # 处理类似"23:50"的时间格式
                if ':' in time_str:
                    return pd.to_datetime(f"{file_date} {time_str}", errors='coerce')
            return None
        
        df['数据时间'] = df.apply(combine_datetime, axis=1)
        
        # 按标准列顺序重新排列
        df = df[self.standard_columns]
        
        return df
    
    def merge_all_data(self):
        """
        合并所有数据并保存
        """
        try:
            # 1. 查找数据文件
            low_cycle_files, two_network_files = self.find_data_files()
            
            if len(low_cycle_files) == 0:
                raise Exception("未找到低环数据文件，请检查文件是否包含'低环'关键词")
            if len(two_network_files) == 0:
                raise Exception("未找到二网数据文件，请检查文件是否包含'二网'关键词")
            
            # 2. 处理低环数据（通常只有1个文件）
            low_cycle_dfs = []
            for file in low_cycle_files:
                low_cycle_dfs.append(self.process_low_cycle_data(file))
            low_cycle_combined = pd.concat(low_cycle_dfs, ignore_index=True)
            
            # 3. 处理二网数据
            two_network_dfs = []
            for file in two_network_files:
                two_network_dfs.append(self.process_two_network_data(file))
            two_network_combined = pd.concat(two_network_dfs, ignore_index=True)
            
            # 4. 合并所有数据
            all_data = pd.concat([low_cycle_combined, two_network_combined], ignore_index=True)
            
            # 5. 保存结果
            all_data.to_excel(self.output_file, index=False)
            
            return all_data
            
        except Exception as e:
            raise
    
    # 静态方法，用于处理上传的文件
    @staticmethod
    def process_uploaded_files(uploaded_files, output_file):
        """
        处理上传的文件
        :param uploaded_files: 上传的文件列表
        :param output_file: 输出文件名
        :return: 合并后的DataFrame
        """
        import tempfile
        
        try:
            # 创建临时目录保存上传的文件
            with tempfile.TemporaryDirectory() as temp_dir:
                # 保存上传的文件到临时目录
                for file in uploaded_files:
                    file_path = os.path.join(temp_dir, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                
                # 使用HeatDataMerger合并数据
                merger = HeatDataMerger(temp_dir, output_file)
                merged_data = merger.merge_all_data()
                
                return merged_data
                
        except Exception as e:
            raise