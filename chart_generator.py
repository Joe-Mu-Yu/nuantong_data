import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
import warnings
from datetime import datetime

# 忽略警告
warnings.filterwarnings('ignore')


class DataProcessingConfig:
    """
    数据处理配置类
    用于存储和管理数据处理相关的配置参数
    """
    def __init__(self):
        self.time_window = '1H'  # 时间窗口大小，固定为1小时
        self.smoothing_window = 5  # 平滑窗口大小
        self.confidence_level = 0.95  # 置信水平
        self.min_non_null_ratio = 0.8  # 最小非空数据比例
        # 新增：筛选参数
        self.start_date = None  # 开始日期
        self.end_date = None  # 结束日期
        self.selected_locations = None  # 选中的位置列表
        self.selected_floors = None  # 选中的楼层列表


class ChartGenerator:
    """
    图表生成器类
    负责供热系统数据的可视化处理，生成各类图表
    """
    def __init__(self, data=None):
        """
        初始化图表生成器
        
        Args:
            data (pd.DataFrame, optional): 输入数据，默认为None
        """
        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DengXian', 'FangSong', 'KaiTi', 'Arial Unicode MS', 'DejaVu Sans', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 11
        
        self.original_data = data  # 原始数据
        self.processed_data = None  # 处理后的数据（应用了位置和楼层筛选）
        self.all_processed_data = None  # 处理后的数据（未应用位置和楼层筛选，用于所有图表）
        self.config = DataProcessingConfig()  # 数据处理配置
        
        # 颜色配置
        self.colors = {
            'original': 'lightblue',
            'smoothed': 'darkblue',
            'confidence': 'lightgray',
            'supply_temp': 'red',
            'return_temp': 'green'
        }
    
    def load_data(self):
        """
        加载数据
        检查数据是否有效
        
        Returns:
            bool: 数据加载是否成功
        """
        if self.original_data is None:
            return False
        
        # 检查数据是否为空
        if self.original_data.empty:
            return False
        
        return True
    
    def clean_and_preprocess_data(self):
        """
        数据清洗和预处理
        包括时间格式转换、数据类型转换、缺失值处理等
        
        Returns:
            bool: 数据预处理是否成功
        """
        try:
            # 创建数据副本
            df_copy = self.original_data.copy()
            
            # 1. 时间数据处理
            if '数据时间' in df_copy.columns:
                # 尝试多种时间格式转换
                time_formats = ['%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']
                datetime_converted = False
                
                for fmt in time_formats:
                    try:
                        df_copy['datetime'] = pd.to_datetime(df_copy['数据时间'], format=fmt, errors='raise')
                        datetime_converted = True
                        break
                    except ValueError:
                        continue
                
                # 如果所有格式都失败，尝试自动推断
                if not datetime_converted:
                    df_copy['datetime'] = pd.to_datetime(df_copy['数据时间'], errors='coerce')
            else:
                # 如果没有数据时间列，创建默认datetime列
                df_copy['datetime'] = pd.date_range(start='2023-01-01', periods=len(df_copy), freq='H')
            
            # 2. 处理位置和楼层信息
            # 位置列可能的名称
            location_columns = ['位置', '地点', '区域', 'location', 'area']
            floor_columns = ['楼层', 'floor', '层']
            
            # 检查并统一位置列名
            location_col_found = False
            for col in location_columns:
                if col in df_copy.columns:
                    df_copy['位置'] = df_copy[col]
                    location_col_found = True
                    break
            if not location_col_found:
                df_copy['位置'] = '默认位置'  # 添加默认值
            
            # 检查并统一楼层列名
            floor_col_found = False
            for col in floor_columns:
                if col in df_copy.columns:
                    df_copy['楼层'] = df_copy[col]
                    floor_col_found = True
                    break
            if not floor_col_found:
                df_copy['楼层'] = '1'  # 添加默认值
            
            # 确保位置和楼层列的数据类型正确
            df_copy['位置'] = df_copy['位置'].astype(str)
            df_copy['楼层'] = df_copy['楼层'].astype(str)
            
            # 3. 数据有效性检查和处理缺失值
            numeric_columns = ['室温温度(℃)', '瞬时流量(T/H)', '供温(℃)', '回温(℃)']
            
            for col in numeric_columns:
                if col in df_copy.columns:
                    # 转换数据类型，处理非数值数据
                    df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
            
            # 4. 日期范围过滤（如果配置了开始和结束日期）
            if self.config.start_date and self.config.end_date:
                mask = (df_copy['datetime'] >= self.config.start_date) & (df_copy['datetime'] <= self.config.end_date)
                df_copy = df_copy[mask]
            elif self.config.start_date:
                mask = df_copy['datetime'] >= self.config.start_date
                df_copy = df_copy[mask]
            elif self.config.end_date:
                mask = df_copy['datetime'] <= self.config.end_date
                df_copy = df_copy[mask]
            
            # 5. 按时间排序
            df_copy.sort_values('datetime', inplace=True)
            
            # 6. 生成未应用位置和楼层筛选的完整数据（用于所有图表）
            all_processed = self._resample_data(df_copy)
            
            # 7. 生成应用了位置和楼层筛选的数据（仅用于筛选逻辑）
            filtered_df = df_copy.copy()
            if self.config.selected_locations:
                filtered_df = filtered_df[filtered_df['位置'].isin(self.config.selected_locations)]
            if self.config.selected_floors:
                filtered_df = filtered_df[filtered_df['楼层'].isin(self.config.selected_floors)]
            
            filtered_processed = self._resample_data(filtered_df)
            
            # 8. 存储处理后的数据
            self.all_processed_data = all_processed
            self.processed_data = filtered_processed
            
            return True
        except Exception as e:
            print(f"数据预处理失败: {e}")
            return False
    
    def _resample_data(self, df):
        """
        时间窗口重采样处理
        用于将数据统一为1小时时间单位
        
        Args:
            df (pd.DataFrame): 输入数据
            
        Returns:
            pd.DataFrame: 重采样后的数据
        """
        # 强制使用1小时时间窗口
        time_window = '1h'
        
        # 确定需要重采样的数值列
        value_columns = ['室温温度(℃)', '瞬时流量(T/H)', '供温(℃)', '回温(℃)']
        available_columns = [col for col in value_columns if col in df.columns]
        
        if not available_columns:
            return df
        
        # 检查是否包含位置和楼层信息
        has_location_floor = '位置' in df.columns and '楼层' in df.columns
        
        # 获取全局时间范围
        min_time = df['datetime'].min()
        max_time = df['datetime'].max()
        
        # 创建连续的小时时间索引
        full_time_index = pd.date_range(start=min_time.floor('h'), end=max_time.ceil('h'), freq='h')
        
        if has_location_floor:
            # 按位置和楼层分组，然后按小时重采样
            grouped = df.groupby(['位置', '楼层'])
            
            # 存储每个分组的重采样结果
            grouped_results = []
            
            for name, group in grouped:
                # 对当前分组进行重采样
                group_hourly = group.resample(time_window, on='datetime')[available_columns].mean().reset_index()
                
                # 设置时间索引
                group_hourly.set_index('datetime', inplace=True)
                
                # 重新索引以确保连续时间范围
                group_hourly = group_hourly.reindex(full_time_index)
                
                # 添加位置和楼层信息
                group_hourly['位置'] = name[0]
                group_hourly['楼层'] = name[1]
                
                grouped_results.append(group_hourly)
            
            # 合并所有分组结果
            hourly_avg = pd.concat(grouped_results)
        else:
            # 传统重采样方式
            df_copy = df.copy()
            df_copy.set_index('datetime', inplace=True)
            hourly_avg = df_copy[available_columns].resample(time_window).mean()
            
            # 重新索引以确保连续的小时时间范围
            hourly_avg = hourly_avg.reindex(full_time_index)
        
        # 确保索引是正确的datetime格式
        hourly_avg.index = pd.to_datetime(hourly_avg.index)
        
        return hourly_avg
    
    def plot_all_charts(self, smooth=True):
        """
        生成所有类型的图表
        
        Args:
            smooth (bool): 是否启用数据平滑处理，默认为True
            
        Returns:
            dict: 包含所有生成图表的字典
        """
        charts = {}
        
        # 生成时间与室温温度图
        if '室温温度(℃)' in self.all_processed_data.columns:
            room_temp_chart = self._plot_room_temperature_chart(smooth)
            charts['room_temperature'] = room_temp_chart
        
        # 生成时间与瞬时流量图
        if '瞬时流量(T/H)' in self.all_processed_data.columns:
            flow_chart = self._plot_instant_flow_chart(smooth)
            charts['instant_flow'] = flow_chart
        
        # 生成时间与供温回温图
        if all(col in self.all_processed_data.columns for col in ['供温(℃)', '回温(℃)']):
            supply_return_chart = self._plot_supply_return_chart(smooth)
            charts['supply_return_temperature'] = supply_return_chart
        
        return charts
    
    def _plot_room_temperature_chart(self, smooth):
        """
        生成室温温度图表，支持按位置和楼层分组显示
        受位置和楼层筛选条件影响
        
        Args:
            smooth (bool): 是否启用数据平滑处理
            
        Returns:
            plt.Figure: 生成的图表对象
        """
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 使用完整数据作为基础
        data = self.all_processed_data.copy()
        
        # 应用位置和楼层筛选
        if self.config.selected_locations:
            data = data[data['位置'].isin(self.config.selected_locations)]
        if self.config.selected_floors:
            data = data[data['楼层'].isin(self.config.selected_floors)]
        
        # 获取完整数据的时间范围（不受筛选影响，确保显示合并数据集的完整时间跨度）
        full_time_range = self.all_processed_data.index
        if len(full_time_range) == 0:
            # 如果没有数据，使用默认范围
            min_time = pd.Timestamp.now() - pd.Timedelta(days=1)
            max_time = pd.Timestamp.now()
        else:
            min_time = full_time_range.min()
            max_time = full_time_range.max()
        
        # 检查是否包含位置和楼层信息
        has_location_floor = '位置' in data.columns and '楼层' in data.columns
        
        if has_location_floor and not data.empty:
            # 获取所有位置和楼层组合
            location_floor_combinations = data.groupby(['位置', '楼层']).groups.keys()
            
            # 定义颜色循环和标记循环
            colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']
            markers = ['o', 's', '^', 'v', 'D', '<', '>', 'p', '*', 'h']
            color_idx = 0
            marker_idx = 0
            
            # 为每个位置和楼层组合绘制数据
            for location, floor in location_floor_combinations:
                # 筛选当前位置和楼层的数据
                mask = (data['位置'] == location) & (data['楼层'] == floor)
                location_floor_data = data[mask]['室温温度(℃)'].dropna()
                
                # 跳过没有数据的组合
                if location_floor_data.empty:
                    continue
                
                # 生成标签
                label = f'{location} - {floor}层'
                
                # 绘制原始数据
                ax.plot(location_floor_data.index, location_floor_data,
                        color=colors[color_idx % len(colors)], alpha=0.7, linewidth=1,
                        marker=markers[marker_idx % len(markers)], markersize=3, label=label)
                
                # 绘制平滑数据和置信区间（如果启用）
                if smooth and len(location_floor_data) >= 3:
                    smoothed, lower, upper = smooth_data_with_confidence(
                        location_floor_data, window_size=self.config.smoothing_window
                    )
                    
                    # 绘制平滑数据
                    ax.plot(smoothed.index, smoothed,
                            color=colors[color_idx % len(colors)], linewidth=2, linestyle='--')
                    
                    # 绘制置信区间
                    ax.fill_between(smoothed.index, lower, upper,
                                    color=colors[color_idx % len(colors)], alpha=0.1)
                
                # 更新颜色和标记索引
                color_idx += 1
                marker_idx += 1
        else:
            # 传统绘制方式（没有位置和楼层信息或数据为空）
            room_temp_original = data['室温温度(℃)'].dropna()
            
            if not room_temp_original.empty:
                # 绘制原始数据
                ax.plot(room_temp_original.index, room_temp_original,
                        color=self.colors['original'], alpha=0.7, linewidth=1,
                        marker='o', markersize=3, label='原始数据')
                
                # 绘制平滑数据和置信区间（如果启用）
                if smooth and len(room_temp_original) >= 3:
                    room_temp_smoothed, room_temp_lower, room_temp_upper = smooth_data_with_confidence(
                        room_temp_original, window_size=self.config.smoothing_window
                    )
                    
                    # 绘制平滑数据
                    ax.plot(room_temp_smoothed.index, room_temp_smoothed,
                            color=self.colors['smoothed'], linewidth=2, label='清洗后数据')
                    
                    # 绘制置信区间
                    ax.fill_between(room_temp_smoothed.index, room_temp_lower, room_temp_upper,
                                    color=self.colors['confidence'], alpha=0.3, label='95%置信区间')
        
        # 设置图表属性
        ax.set_title('时间与温度关系', fontsize=14, pad=20)
        ax.set_xlabel('时间', fontsize=12, labelpad=10)
        ax.set_ylabel('温度 (°C)', fontsize=12, labelpad=10)
        ax.legend(loc='upper right', fontsize=10, framealpha=0.8)
        ax.grid(True, alpha=0.3)
        
        # 设置x轴限制
        ax.set_xlim(min_time, max_time)
        
        # 配置x轴刻度，只显示日期
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        # 隐藏次要刻度
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=12))
        ax.xaxis.set_minor_formatter(mdates.DateFormatter(''))
        
        # 调整刻度标签的显示
        plt.setp(ax.xaxis.get_minorticklabels(), visible=False)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha='center', fontsize=10, fontweight='bold')
        
        # 添加高峰时段（6:00-18:00）的背景色
        # 获取日期范围
        start_date = min_time.floor('D')
        end_date = max_time.ceil('D')
        
        # 遍历每一天，添加高峰时段背景
        current_date = start_date
        while current_date <= end_date:
            # 高峰时段开始和结束时间
            peak_start = current_date + pd.Timedelta(hours=6)
            peak_end = current_date + pd.Timedelta(hours=18)
            
            # 只在当前图表的时间范围内添加背景
            if peak_end >= min_time and peak_start <= max_time:
                ax.axvspan(
                    max(peak_start, min_time),
                    min(peak_end, max_time),
                    facecolor='lightcoral',
                    alpha=0.3,
                    label='高峰时段 (6:00-18:00)'
                )
            
            # 移动到下一天
            current_date += pd.Timedelta(days=1)
        
        # 确保高峰时段标签只显示一次
        handles, labels = ax.get_legend_handles_labels()
        unique_labels = dict(zip(labels, handles))
        ax.legend(unique_labels.values(), unique_labels.keys(), loc='upper right', fontsize=10, framealpha=0.8)
        
        # 确保刻度标签不会重叠
        fig.autofmt_xdate(bottom=0.2, rotation=0, ha='center')
        
        plt.tight_layout()
        
        return fig
    
    def _plot_instant_flow_chart(self, smooth):
        """
        生成瞬时流量图表，使用完整数据（不受位置和楼层筛选影响）
        
        Args:
            smooth (bool): 是否启用数据平滑处理
            
        Returns:
            plt.Figure: 生成的图表对象
        """
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 使用完整数据，不受位置和楼层筛选影响
        data = self.all_processed_data.copy()
        
        # 获取完整数据的时间范围（不受筛选影响，确保显示合并数据集的完整时间跨度）
        full_time_range = self.all_processed_data.index
        if len(full_time_range) == 0:
            # 如果没有数据，使用默认范围
            min_time = pd.Timestamp.now() - pd.Timedelta(days=1)
            max_time = pd.Timestamp.now()
        else:
            min_time = full_time_range.min()
            max_time = full_time_range.max()
        
        # 聚合所有数据的瞬时流量（按时间）
        flow_data = data.groupby(data.index)['瞬时流量(T/H)'].mean().dropna()
        
        if not flow_data.empty:
            # 绘制原始数据
            ax.plot(flow_data.index, flow_data,
                    color=self.colors['original'], alpha=0.7, linewidth=1,
                    marker='s', markersize=3, label='原始数据')
            
            # 绘制平滑数据和置信区间（如果启用）
            if smooth and len(flow_data) >= 3:
                flow_smoothed, flow_lower, flow_upper = smooth_data_with_confidence(
                    flow_data, window_size=self.config.smoothing_window
                )
                
                # 绘制平滑数据
                ax.plot(flow_smoothed.index, flow_smoothed,
                        color=self.colors['smoothed'], linewidth=2, label='清洗后数据')
                
                # 绘制置信区间
                ax.fill_between(flow_smoothed.index, flow_lower, flow_upper,
                                color=self.colors['confidence'], alpha=0.3, label='95%置信区间')
        
        # 设置图表属性
        ax.set_title('时间与瞬时流量关系', fontsize=14, pad=20)
        ax.set_xlabel('时间', fontsize=12, labelpad=10)
        ax.set_ylabel('流量 (T/H)', fontsize=12, labelpad=10)
        ax.legend(loc='upper right', fontsize=10, framealpha=0.8)
        ax.grid(True, alpha=0.3)
        
        # 设置x轴限制
        ax.set_xlim(min_time, max_time)
        
        # 配置x轴刻度，只显示日期
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        # 隐藏次要刻度
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=12))
        ax.xaxis.set_minor_formatter(mdates.DateFormatter(''))
        
        # 调整刻度标签的显示
        plt.setp(ax.xaxis.get_minorticklabels(), visible=False)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha='center', fontsize=10, fontweight='bold')
        
        # 添加高峰时段（6:00-18:00）的背景色
        # 获取日期范围
        start_date = min_time.floor('D')
        end_date = max_time.ceil('D')
        
        # 遍历每一天，添加高峰时段背景
        current_date = start_date
        while current_date <= end_date:
            # 高峰时段开始和结束时间
            peak_start = current_date + pd.Timedelta(hours=6)
            peak_end = current_date + pd.Timedelta(hours=18)
            
            # 只在当前图表的时间范围内添加背景
            if peak_end >= min_time and peak_start <= max_time:
                ax.axvspan(
                    max(peak_start, min_time),
                    min(peak_end, max_time),
                    facecolor='lightcoral',
                    alpha=0.3,
                    label='高峰时段 (6:00-18:00)'
                )
            
            # 移动到下一天
            current_date += pd.Timedelta(days=1)
        
        # 确保高峰时段标签只显示一次
        handles, labels = ax.get_legend_handles_labels()
        unique_labels = dict(zip(labels, handles))
        ax.legend(unique_labels.values(), unique_labels.keys(), loc='upper right', fontsize=10, framealpha=0.8)
        
        # 确保刻度标签不会重叠
        fig.autofmt_xdate(bottom=0.2, rotation=0, ha='center')
        
        plt.tight_layout()
        
        return fig
    
    def _plot_supply_return_chart(self, smooth):
        """
        生成供温回温关系图表，使用完整数据（不受位置和楼层筛选影响）
        
        Args:
            smooth (bool): 是否启用数据平滑处理
            
        Returns:
            plt.Figure: 生成的图表对象
        """
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 使用完整数据，不受位置和楼层筛选影响
        data = self.all_processed_data.copy()
        
        # 获取数据的完整时间范围
        full_time_range = data.index
        if len(full_time_range) == 0:
            # 如果没有数据，使用默认范围
            min_time = pd.Timestamp.now() - pd.Timedelta(days=1)
            max_time = pd.Timestamp.now()
        else:
            min_time = full_time_range.min()
            max_time = full_time_range.max()
        
        # 聚合所有数据的供温和回温（按时间）
        supply_data = data.groupby(data.index)['供温(℃)'].mean().dropna()
        return_data = data.groupby(data.index)['回温(℃)'].mean().dropna()
        
        # 绘制供温原始数据
        if not supply_data.empty:
            ax.plot(supply_data.index, supply_data,
                    color='lightcoral', alpha=0.7, linewidth=1,
                    marker='^', markersize=3, label='供温原始数据')
            
            # 绘制供温平滑数据和置信区间（如果启用）
            if smooth and len(supply_data) >= 3:
                supply_smoothed, supply_lower, supply_upper = smooth_data_with_confidence(
                    supply_data, window_size=self.config.smoothing_window
                )
                
                # 绘制供温平滑数据
                ax.plot(supply_smoothed.index, supply_smoothed,
                        color='red', linewidth=2, label='供温清洗后数据')
                
                # 绘制供温置信区间
                ax.fill_between(supply_smoothed.index, supply_lower, supply_upper,
                                color='lightcoral', alpha=0.3, label='供温95%置信区间')
        
        # 绘制回温原始数据
        if not return_data.empty:
            ax.plot(return_data.index, return_data,
                    color='lightgreen', alpha=0.7, linewidth=1,
                    marker='v', markersize=3, label='回温原始数据')
            
            # 绘制回温平滑数据和置信区间（如果启用）
            if smooth and len(return_data) >= 3:
                return_smoothed, return_lower, return_upper = smooth_data_with_confidence(
                    return_data, window_size=self.config.smoothing_window
                )
                
                # 绘制回温平滑数据
                ax.plot(return_smoothed.index, return_smoothed,
                        color='green', linewidth=2, label='回温清洗后数据')
                
                # 绘制回温置信区间
                ax.fill_between(return_smoothed.index, return_lower, return_upper,
                                color='lightgreen', alpha=0.3, label='回温95%置信区间')
        
        # 设置图表属性
        ax.set_title('时间与供温回温关系', fontsize=14, pad=20)
        ax.set_xlabel('时间', fontsize=12, labelpad=10)
        ax.set_ylabel('温度 (°C)', fontsize=12, labelpad=10)
        ax.legend(loc='upper right', fontsize=10, framealpha=0.8)
        ax.grid(True, alpha=0.3)
        
        # 设置x轴限制
        ax.set_xlim(min_time, max_time)
        
        # 配置x轴刻度，只显示日期
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        # 隐藏次要刻度
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=12))
        ax.xaxis.set_minor_formatter(mdates.DateFormatter(''))
        
        # 调整刻度标签的显示
        plt.setp(ax.xaxis.get_minorticklabels(), visible=False)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha='center', fontsize=10, fontweight='bold')
        
        # 添加高峰时段（6:00-18:00）的背景色
        # 获取日期范围
        start_date = min_time.floor('D')
        end_date = max_time.ceil('D')
        
        # 遍历每一天，添加高峰时段背景
        current_date = start_date
        while current_date <= end_date:
            # 高峰时段开始和结束时间
            peak_start = current_date + pd.Timedelta(hours=6)
            peak_end = current_date + pd.Timedelta(hours=18)
            
            # 只在当前图表的时间范围内添加背景
            if peak_end >= min_time and peak_start <= max_time:
                ax.axvspan(
                    max(peak_start, min_time),
                    min(peak_end, max_time),
                    facecolor='lightcoral',
                    alpha=0.3,
                    label='高峰时段 (6:00-18:00)'
                )
            
            # 移动到下一天
            current_date += pd.Timedelta(days=1)
        
        # 确保高峰时段标签只显示一次
        handles, labels = ax.get_legend_handles_labels()
        unique_labels = dict(zip(labels, handles))
        ax.legend(unique_labels.values(), unique_labels.keys(), loc='upper right', fontsize=10, framealpha=0.8)
        
        # 确保刻度标签不会重叠
        fig.autofmt_xdate(bottom=0.2, rotation=0, ha='center')
        
        plt.tight_layout()
        
        return fig


def smooth_data_with_confidence(data_series, window_size=5, confidence=0.95):
    """
    数据平滑处理并计算置信区间
    结合了移动平均平滑和置信区间计算方法
    
    Args:
        data_series (pd.Series): 原始数据序列
        window_size (int): 平滑窗口大小，默认为5
        confidence (float): 置信水平，默认为0.95
        
    Returns:
        tuple: 包含平滑后的数据、置信区间下限和上限的元组
    """
    # 移动平均平滑，使用中心窗口，最小周期数为窗口大小的一半
    min_periods = max(1, window_size // 2)
    smoothed = data_series.rolling(
        window=window_size, 
        center=True, 
        min_periods=min_periods
    ).mean()
    
    # 计算滚动标准差
    std = data_series.rolling(
        window=window_size, 
        center=True, 
        min_periods=min_periods
    ).std()
    
    # 计算标准误差
    n = window_size
    standard_error = std / np.sqrt(n)
    
    # 计算置信区间（使用正态分布的Z分数）
    z_score = stats.norm.ppf(1 - (1 - confidence) / 2)
    
    margin_error = z_score * standard_error
    
    confidence_lower = smoothed - margin_error
    confidence_upper = smoothed + margin_error
    
    return smoothed, confidence_lower, confidence_upper


# 单元测试
if __name__ == '__main__':
    import unittest
    
    class TestChartGenerator(unittest.TestCase):
        """
        测试图表生成器功能
        """
        
        def setUp(self):
            """
            创建测试数据
            """
            # 生成模拟数据
            dates = pd.date_range(start='2023-01-01', periods=100, freq='h')
            self.test_data = pd.DataFrame({
                '数据时间': [d.strftime('%H:%M') for d in dates],
                '室温温度(℃)': np.random.normal(22, 2, 100),
                '瞬时流量(T/H)': np.random.normal(10, 1, 100),
                '供温(℃)': np.random.normal(65, 5, 100),
                '回温(℃)': np.random.normal(45, 5, 100)
            })
            
            # 添加一些缺失值
            self.test_data.loc[10:15, '室温温度(℃)'] = np.nan
        
        def test_chart_generator_init(self):
            """
            测试图表生成器初始化
            """
            chart_gen = ChartGenerator(self.test_data)
            self.assertIsNotNone(chart_gen)
            self.assertTrue(chart_gen.load_data())
        
        def test_chart_generator_preprocess(self):
            """
            测试图表生成器数据预处理
            """
            chart_gen = ChartGenerator(self.test_data)
            chart_gen.load_data()
            self.assertTrue(chart_gen.clean_and_preprocess_data())
        
        def test_smooth_data_with_confidence(self):
            """
            测试数据平滑功能
            """
            test_series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
            smoothed, lower, upper = smooth_data_with_confidence(test_series, window_size=3)
            
            # 检查返回的数据长度是否与原始数据相同
            self.assertEqual(len(smoothed), len(test_series))
            self.assertEqual(len(lower), len(test_series))
            self.assertEqual(len(upper), len(test_series))
            
            # 检查置信区间是否合理
            self.assertTrue((upper >= smoothed).all())
            self.assertTrue((lower <= smoothed).all())
    
    # 运行单元测试
    unittest.main()

