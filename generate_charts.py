import pandas as pd
import numpy as np
from chart_generator import ChartGenerator
import matplotlib.pyplot as plt
import os

# 创建输出目录
output_dir = r'd:/Users/joero/Desktop/qqq/1/'

# 创建测试数据，跨越7天时间范围
dates = pd.date_range(start='2023-11-20 00:00:00', end='2023-11-27 00:00:00', freq='h')
test_data = pd.DataFrame({
    '数据时间': dates.strftime('%Y-%m-%d %H:%M:%S'),
    '室温温度(℃)': np.random.normal(22, 2, len(dates)),
    '瞬时流量(T/H)': np.random.normal(10, 1, len(dates)),
    '供温(℃)': np.random.normal(65, 5, len(dates)),
    '回温(℃)': np.random.normal(45, 5, len(dates)),
    '位置': ['测试位置'] * len(dates),
    '楼层': ['1'] * len(dates)
})

# 创建图表生成器实例
chart_gen = ChartGenerator(test_data)

# 加载和预处理数据
if chart_gen.load_data():
    if chart_gen.clean_and_preprocess_data():
        # 生成所有图表
        charts = chart_gen.plot_all_charts(smooth=True)
        
        # 单独保存每个图表
        for chart_name, chart in charts.items():
            # 生成文件名
            file_name = f'{chart_name}_chart.png'
            file_path = os.path.join(output_dir, file_name)
            
            # 保存图表
            chart.savefig(file_path, dpi=150, bbox_inches='tight')
            print(f'已保存图表: {file_path}')
        
        print('已完成所有单独图表的生成和保存！')
        print('\n图表保存路径:')
        for chart_name in charts.keys():
            file_path = os.path.join(output_dir, f'{chart_name}_chart.png')
            print(f'  - {file_path}')
        
        plt.close('all')
        print('所有图表已成功生成并保存！')
    else:
        print('数据预处理失败')
else:
    print('数据加载失败')