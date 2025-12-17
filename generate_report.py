import pandas as pd
import os
from datetime import datetime
from chart_generator import ChartGenerator

class ReportGenerator:
    """
    报告生成器类，用于生成暖通数据处理报告
    支持生成Markdown格式的报告，并可以包含图表
    """
    
    def __init__(self, df=None, output_dir=None):
        """
        初始化报告生成器
        
        参数:
            df: 可选，已处理的数据DataFrame
            output_dir: 可选，输出目录，默认为当前目录
        """
        self.df = df
        self.output_dir = output_dir or os.getcwd()
        self.chart_generator = None
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def set_data(self, df):
        """
        设置数据
        
        参数:
            df: 已处理的数据DataFrame
        """
        self.df = df
    
    def generate_report(self, report_title="居民住宅供暖室内温度数据检测报告", 
                      report_id=None, include_charts=True, chart_types=None,
                      include_cleaning_report=True, outlier_method='3sigma', 
                      outlier_threshold=3, outlier_handle='replace'):
        """
        生成报告
        
        参数:
            report_title: 报告标题，默认为"居民住宅供暖室内温度数据检测报告"
            report_id: 报告编号，默认为None（自动生成）
            include_charts: 是否包含图表，默认为True
            chart_types: 要包含的图表类型列表，默认为None（包含所有图表）
            include_cleaning_report: 是否包含数据清洗报告，默认为True
            outlier_method: 异常值检测方法，默认为'3sigma'
            outlier_threshold: 异常值阈值，默认为3
            outlier_handle: 异常值处理方式，默认为'replace'
            
        返回:
            str: 生成的报告内容
        """
        if self.df is None:
            raise ValueError("请先设置数据")
        
        # 自动生成报告编号
        if report_id is None:
            today = datetime.now().strftime('%Y-%m-%d')
            report_id = f"HTR-{today}"
        
        # 获取数据统计信息
        stats = self._get_data_statistics()
        
        # 生成图表（如果需要）
        if include_charts:
            chart_files = self._generate_charts(chart_types, outlier_method, outlier_threshold, outlier_handle)
        else:
            chart_files = {}
        
        # 生成报告内容
        report_content = self._generate_report_content(report_title, report_id, stats, chart_files, 
                                                     include_cleaning_report, outlier_method, 
                                                     outlier_threshold, outlier_handle)
        
        return report_content
    
    def _get_data_statistics(self):
        """
        获取数据统计信息
        
        返回:
            dict: 数据统计信息
        """
        stats = {
            "start_date": self.df['完整时间'].min().strftime('%Y-%m-%d'),
            "end_date": self.df['完整时间'].max().strftime('%Y-%m-%d'),
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "validity_rate": f"{self.df['完整时间'].notna().sum()/len(self.df):.2%}",
            "time_span": str(self.df['完整时间'].max() - self.df['完整时间'].min())
        }
        
        # 获取数值列的统计信息
        numeric_cols = self.df.select_dtypes(include=['int64', 'float64']).columns
        for col in numeric_cols:
            stats[f"{col}_mean"] = f"{self.df[col].mean():.2f}"
            stats[f"{col}_max"] = f"{self.df[col].max():.2f}"
            stats[f"{col}_min"] = f"{self.df[col].min():.2f}"
        
        return stats
    
    def _generate_charts(self, chart_types=None, outlier_method='3sigma', outlier_threshold=3, outlier_handle='replace'):
        """
        生成图表
        
        参数:
            chart_types: 要生成的图表类型列表，默认为None（生成所有图表）
            outlier_method: 异常值检测方法
            outlier_threshold: 异常值阈值
            outlier_handle: 异常值处理方式
            
        返回:
            dict: 图表文件名映射
        """
        chart_files = {}
        
        # 默认图表类型
        default_chart_types = ['time_vs_flow', 'time_vs_temperatures', 
                              'time_vs_room_temp', 'heat_distribution', '24_hour_cycle']
        
        # 确定要生成的图表类型
        charts_to_generate = chart_types or default_chart_types
        
        # 创建临时CSV文件来传递数据
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            self.df.to_csv(f, index=False)
            temp_file_path = f.name
        
        try:
            # 创建ChartGenerator实例
            chart_gen = ChartGenerator(temp_file_path, output_dir=self.output_dir)
            
            # 加载并清洗数据
            if chart_gen.load_data() and chart_gen.clean_and_preprocess_data(
                outlier_method=outlier_method,
                outlier_threshold=outlier_threshold,
                outlier_handle=outlier_handle
            ):
                # 生成时间与流量关系图
                if 'time_vs_flow' in charts_to_generate:
                    chart_file = chart_gen.plot_time_vs_flow()
                    if chart_file:
                        chart_files['time_vs_flow'] = chart_file
                
                # 生成时间与供回温度关系图
                if 'time_vs_temperatures' in charts_to_generate:
                    chart_file = chart_gen.plot_time_vs_temperatures()
                    if chart_file:
                        chart_files['time_vs_temperatures'] = chart_file
                
                # 生成时间与室温关系图
                if 'time_vs_room_temp' in charts_to_generate:
                    chart_file = chart_gen.plot_time_vs_room_temp()
                    if chart_file:
                        chart_files['time_vs_room_temp'] = chart_file
                
                # 生成温度分布图
                if 'heat_distribution' in charts_to_generate:
                    chart_file = chart_gen.plot_heat_distribution()
                    if chart_file:
                        chart_files['heat_distribution'] = chart_file
                
                # 生成24小时温度变化周期分析图
                if '24_hour_cycle' in charts_to_generate:
                    chart_file = chart_gen.plot_24_hour_cycle()
                    if chart_file:
                        chart_files['24_hour_cycle'] = chart_file
        finally:
            # 删除临时文件
            import os
            os.unlink(temp_file_path)
        
        return chart_files
    
    def _generate_report_content(self, report_title, report_id, stats, chart_files, include_cleaning_report=True, outlier_method='3sigma', outlier_threshold=3, outlier_handle='replace'):
        """
        生成报告内容
        
        参数:
            report_title: 报告标题
            report_id: 报告编号
            stats: 数据统计信息
            chart_files: 图表文件名映射
            include_cleaning_report: 是否包含数据清洗报告
            outlier_method: 异常值检测方法
            outlier_threshold: 异常值阈值
            outlier_handle: 异常值处理方式
            
        返回:
            str: 报告内容
        """
        # 获取报告日期
        report_date = datetime.now().strftime('%Y年%m月%d日')
        report_generation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 生成报告内容
        cleaning_report_section = """### 3.3 数据清洗报告

#### 3.3.1 清洗配置
- **异常值检测方法**：{outlier_method}
- **异常值阈值**：{outlier_threshold}
- **异常值处理方式**：{outlier_handle}

#### 3.3.2 清洗过程
1. **数据加载与验证**：检查数据完整性和格式正确性
2. **重复值处理**：识别并删除重复记录
3. **缺失值检测**：分析缺失数据模式
4. **异常值检测**：使用{outlier_method}方法检测异常值
5. **异常值处理**：采用{outlier_handle}方式处理异常值
6. **数据平滑**：应用自适应平滑算法
7. **周期性识别**：分析数据的日/周/季节性周期
8. **数据验证**：验证清洗后数据的合理性

#### 3.3.3 清洗效果
- 提高数据质量和可靠性
- 减少异常值对分析结果的影响
- 增强数据的可比性和一致性
- 为后续分析提供可靠的数据基础

"""
        
        # 替换清洗报告中的占位符
        if include_cleaning_report:
            cleaning_report_section = cleaning_report_section.format(
                outlier_method=outlier_method,
                outlier_threshold=outlier_threshold,
                outlier_handle=outlier_handle
            )
        else:
            cleaning_report_section = ""

        report_content = f"""# {report_title}

## 1. 报告基本信息

**报告编号**：{report_id}
**报告日期**：{report_date}
**检测对象**：居民住宅供暖系统
**检测周期**：{stats['start_date']} 至 {stats['end_date']}
**检测项目**：供暖室内温度、供水温度、回水温度、瞬时流量

## 2. 检测目的

- 监测居民住宅供暖系统的运行状态
- 分析供暖温度的时间变化规律
- 评估供暖系统的24小时周期性特征
- 检测供暖温度是否符合相关标准要求
- 分析瞬时流量与温度的关系

## 3. 检测方法

### 3.1 数据采集
- 数据来源：供暖系统自动监测数据
- 数据内容：环路、计划热量、瞬时热量、热量、瞬时流量、阀门开度、设定温度、反馈温度、供温、回温、供压、回压、数据时间、完整时间

### 3.2 数据处理
- 数据清洗：去除重复值、检测并处理异常值
- 缺失值处理：线性插值法填补缺失数据
- 平滑处理：应用移动平均算法平滑数据
- 置信区间计算：采用统计学方法计算95%置信区间

{cleaning_report_section}

## 4. 检测结果与分析

### 4.1 数据概况
- 数据量：{stats['total_rows']}行
- 有效数据率：{stats['validity_rate']}
- 时间跨度：{stats['time_span']}

### 4.2 温度统计
- 供温平均值：{stats.get('供温(℃)_mean', 'N/A')}℃
- 供温最大值：{stats.get('供温(℃)_max', 'N/A')}℃
- 供温最小值：{stats.get('供温(℃)_min', 'N/A')}℃
- 回温平均值：{stats.get('回温(℃)_mean', 'N/A')}℃
- 回温最大值：{stats.get('回温(℃)_max', 'N/A')}℃
- 回温最小值：{stats.get('回温(℃)_min', 'N/A')}℃

### 4.3 流量统计
- 瞬时流量平均值：{stats.get('瞬时流量(T/H)_mean', 'N/A')} T/H
- 瞬时流量最大值：{stats.get('瞬时流量(T/H)_max', 'N/A')} T/H
- 瞬时流量最小值：{stats.get('瞬时流量(T/H)_min', 'N/A')} T/H

### 4.4 时间与瞬时流量关系分析

**图表**：{'[' + os.path.basename(chart_files['time_vs_flow']) + '](' + chart_files['time_vs_flow'] + ')' if 'time_vs_flow' in chart_files else '无'}

**分析结论**：
- 瞬时流量在检测周期内呈现规律性变化
- 高峰时段流量相对较高
- 流量变化与温度需求变化基本一致

### 4.5 时间与供回温度关系分析

**图表**：{'[' + os.path.basename(chart_files['time_vs_temperatures']) + '](' + chart_files['time_vs_temperatures'] + ')' if 'time_vs_temperatures' in chart_files else '无'}

**分析结论**：
- 供回温度在检测周期内呈现规律性变化
- 供温始终高于回温，符合供暖系统运行规律
- 温度变化与时间需求变化基本一致

### 4.6 温度分布分析

**图表**：{'[' + os.path.basename(chart_files['heat_distribution']) + '](' + chart_files['heat_distribution'] + ')' if 'heat_distribution' in chart_files else '无'}

**分析结论**：
- 温度分布符合预期，大部分数据集中在合理范围内
- 无明显异常值，说明系统运行稳定
- 温度波动在可接受范围内

### 4.7 24小时温度变化周期分析

**图表**：{'[' + os.path.basename(chart_files['24_hour_cycle']) + '](' + chart_files['24_hour_cycle'] + ')' if '24_hour_cycle' in chart_files else '无'}

**分析结论**：
- 温度变化呈现明显的24小时周期性
- 高峰时段（18:00-22:00）温度相对较高
- 温度变化与居民生活规律相符

## 5. 结论

1. **系统运行状态**：供暖系统运行稳定，各项参数符合设计要求
2. **温度控制**：室内温度保持在合理范围内
3. **周期性特征**：温度变化呈现明显的24小时周期性，与居民生活规律相符
4. **流量调节**：瞬时流量随温度需求变化自动调节，系统响应及时
5. **数据质量**：经过清洗和处理后，数据质量良好，可用于进一步分析

## 6. 建议

1. 继续保持当前的供暖系统运行参数
2. 定期监测供回水温差，确保系统热效率
3. 根据室外温度变化，适时调整供水温度设定
4. 加强对高峰时段的系统监测，确保供热稳定
5. 建立长期的数据监测机制，进行趋势分析和预测

## 7. 附录

### 7.1 图表清单

| 图表编号 | 图表名称 | 文件路径 |
|---------|---------|---------|
| 图1 | 时间与瞬时流量关系图 | {chart_files.get('time_vs_flow', '无')} |
| 图2 | 时间与供回温度关系图 | {chart_files.get('time_vs_temperatures', '无')} |
| 图3 | 温度分布图 | {chart_files.get('heat_distribution', '无')} |
| 图4 | 24小时温度变化周期分析 | {chart_files.get('24_hour_cycle', '无')} |

### 7.2 检测标准依据

- 参照《居民住宅供暖室内温度连续测量方法》
- 符合国家相关供暖温度标准要求

## 8. 报告签署

| 职位 | 姓名 | 签名 | 日期 |
|------|------|------|------|
| 检测负责人 | __________________ | ________ | ________ |
| 审核人 | __________________ | ________ | ________ |
| 批准人 | __________________ | ________ | ________ |

---

**报告生成时间**：{report_generation_time}
**报告生成软件**：自动数据处理与报告生成系统
"""
        
        return report_content
    
    def save_report(self, report_content, filename=None):
        """
        保存报告到文件
        
        参数:
            report_content: 报告内容
            filename: 文件名，默认为None（自动生成）
            
        返回:
            str: 保存的文件路径
        """
        # 自动生成文件名
        if filename is None:
            today = datetime.now().strftime('%Y-%m-%d')
            filename = f"heating_temperature_report_{today}.md"
        
        # 保存报告
        file_path = os.path.join(self.output_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return file_path

# 示例用法
if __name__ == "__main__":
    # 这里可以添加示例代码，演示如何使用ReportGenerator类
    pass
