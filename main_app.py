# 导入必要的模块
import streamlit as st
import pandas as pd
import os
import tempfile
import sys
import json
import base64
from io import BytesIO
import logging
import uuid
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('heating_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 设置页面配置
st.set_page_config(
    page_title="河北科技大学建筑工程学院供热暖通系统综合分析平台",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 添加当前目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 自定义CSS样式
st.markdown("""
<style>
    /* 字体基础样式 - 跨平台兼容 */
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji', 'SimHei', 'Arial Unicode MS';
        font-synthesis: none;
        text-rendering: optimizeLegibility;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* 主标题样式 */
    .main-title {
        font-size: clamp(1.8rem, 5vw, 2.5rem);
        font-weight: 700;
        color: #ff6b6b;
        text-align: center;
        margin-bottom: 1rem;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }
    
    /* 副标题样式 */
    .sub-title {
        font-size: clamp(1.1rem, 2.5vw, 1.25rem);
        font-weight: 600;
        color: #4ecdc4;
        margin: 1.5rem 0 0.5rem 0;
        line-height: 1.3;
        letter-spacing: -0.01em;
    }
    
    /* 卡片样式 */
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
    }
    
    /* 文件上传卡片 */
    .file-upload-card {
        background-color: #f3e5f5;
        border-left: 5px solid #9c27b0;
    }
    
    /* 按钮样式 */
    .stButton > button {
        font-weight: 600;
        font-size: clamp(0.9rem, 2vw, 1rem);
    }
    
    /* 文件上传区域样式 */
    .stFileUploader > div {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        padding-top: 2rem;
    }
    
    /* 导航按钮样式 */
    .nav-button {
        width: 100%;
        margin-bottom: 0.5rem;
    }
    
    /* 文本内容样式 */
    .stMarkdown {
        font-size: clamp(0.9rem, 2vw, 1rem);
        line-height: 1.6;
        letter-spacing: 0.005em;
    }
    
    /* 数据表格样式 */
    .stDataFrame {
        font-size: clamp(0.85rem, 1.8vw, 0.95rem);
    }
    
    /* 数据概览卡片 */
    .data-overview-card {
        background-color: #e8f5e8;
        border-left: 5px solid #4caf50;
    }
    
    /* 图表卡片 */
    .chart-card {
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
    }
    
    /* 下载卡片 */
    .download-card {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
    }
    
    /* 功能介绍卡片 */
    .feature-card {
        background-color: #fafafa;
        border-radius: 8px;
        padding: 1.25rem;
        box-shadow: 0 1px 5px rgba(0, 0, 0, 0.05);
        height: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* 功能图标 */
    .feature-icon {
        font-size: clamp(1.5rem, 4vw, 2rem);
        margin-bottom: 0.5rem;
    }
    
    /* 数据格式列表 */
    .data-format-list {
        list-style-type: none;
        padding-left: 0;
    }
    
    .data-format-list li {
        margin-bottom: 0.5rem;
        padding-left: 1.5rem;
        position: relative;
        font-size: clamp(0.9rem, 2vw, 1rem);
    }
    
    .data-format-list li:before {
        content: "✓";
        color: #4caf50;
        font-weight: bold;
        position: absolute;
        left: 0;
    }
    
    /* 进度条样式 */
    .progress-container {
        margin: 1rem 0;
    }
    
    .progress-text {
        font-size: clamp(0.85rem, 1.8vw, 0.9rem);
        color: #6c757d;
        margin-bottom: 0.5rem;
    }
    
    /* 小屏幕优化 */
    @media (max-width: 768px) {
        /* 调整间距 */
        .card {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        /* 调整字体大小 */
        * {
            font-size: 14px;
        }
    }
    
    /* 大屏幕优化 */
    @media (min-width: 1200px) {
        /* 增加行高 */
        .stMarkdown {
            line-height: 1.7;
        }
    }
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "数据合并"
if 'merged_data' not in st.session_state:
    st.session_state.merged_data = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = "idle"  # idle, processing, completed, error
if 'last_error' not in st.session_state:
    st.session_state.last_error = None
if 'processing_time' not in st.session_state:
    st.session_state.processing_time = 0

# 定义数据持久化类
class SessionPersistence:
    """会话数据持久化管理类"""
    
    @staticmethod
    def save_data(key, data):
        """保存数据到会话状态"""
        try:
            st.session_state[key] = data
            logger.info(f"Saved data to session: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to save data to session: {key}, error: {str(e)}")
            return False
    
    @staticmethod
    def get_data(key, default=None):
        """从会话状态获取数据"""
        try:
            return st.session_state.get(key, default)
        except Exception as e:
            logger.error(f"Failed to get data from session: {key}, error: {str(e)}")
            return default
    
    @staticmethod
    def clear_data(key=None):
        """清除会话数据"""
        try:
            if key:
                if key in st.session_state:
                    del st.session_state[key]
                    logger.info(f"Cleared data from session: {key}")
            else:
                # 保留基本会话状态，清除数据相关状态
                basic_keys = ['current_page', 'session_id', 'uploaded_files']
                for key in list(st.session_state.keys()):
                    if key not in basic_keys:
                        del st.session_state[key]
                logger.info("Cleared all non-basic data from session")
            return True
        except Exception as e:
            logger.error(f"Failed to clear data from session, error: {str(e)}")
            return False

# 会话持久化功能 - JavaScript代码
st.markdown(f"""
<script>
// 保存会话状态到localStorage
function saveSessionState() {{
    // 收集会话状态
    const sessionState = {{
        current_page: '{st.session_state.current_page}',
        session_id: '{st.session_state.session_id}',
        timestamp: new Date().toISOString()
    }};
    
    try {{
        localStorage.setItem('heating_app_session', JSON.stringify(sessionState));
        console.log('Session state saved successfully:', sessionState);
    }} catch (e) {{
        console.error('Failed to save session state:', e);
    }}
}}

// 从localStorage恢复会话状态
function restoreSessionState() {{
    try {{
        const savedState = localStorage.getItem('heating_app_session');
        if (savedState) {{
            const sessionState = JSON.parse(savedState);
            console.log('Restored session state:', sessionState);
            
            // 恢复当前页面
            if (sessionState.current_page) {{
                // 查找对应的按钮并点击
                const buttons = window.parent.document.querySelectorAll('.stButton > button');
                buttons.forEach(button => {{
                    if (button.textContent.includes(sessionState.current_page)) {{
                        button.click();
                    }}
                );
            }}
        }}
    }} catch (e) {{
        console.error('Failed to restore session state:', e);
    }}
}}

// 页面加载时恢复会话
window.addEventListener('load', function() {{
    // 延迟恢复，确保页面完全加载
    setTimeout(restoreSessionState, 1000);
}});

// 定期保存会话状态
setInterval(saveSessionState, 3000); // 每3秒保存一次

// 页面关闭或刷新前保存会话
window.addEventListener('beforeunload', saveSessionState);

// 监听页面状态变化
const observer = new MutationObserver(saveSessionState);
observer.observe(window.parent.document.body, {{
    childList: true,
    subtree: true,
    attributes: true
}});
</script>
""", unsafe_allow_html=True)

# 页面标题
st.markdown('<div class="main-title">🔥 河北科技大学建筑工程学院供热暖通系统综合分析平台</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center; font-size: 1.1rem; color: #666; margin-bottom: 1rem;">开发者：穆昱伟</div>', unsafe_allow_html=True)
st.markdown("---")

# 侧边栏导航
with st.sidebar:
    st.header("📋 功能导航")
    
    # 导航按钮
    if st.button("📊 数据合并", use_container_width=True, type="primary" if st.session_state.current_page == "数据合并" else "secondary"):
        st.session_state.current_page = "数据合并"
    
    if st.button("📈 供热数据分析", use_container_width=True, type="primary" if st.session_state.current_page == "供热数据分析" else "secondary"):
        st.session_state.current_page = "供热数据分析"
    
    if st.button("📑 报告分析", use_container_width=True, type="primary" if st.session_state.current_page == "报告分析" else "secondary"):
        st.session_state.current_page = "报告分析"
    
    st.markdown("---")
    
    # 文件上传区域
    st.subheader("📁 文件上传")
    uploaded_files = st.file_uploader(
        "选择Excel文件",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        help="支持上传多个Excel文件，系统将自动合并处理",
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
        st.success(f"已上传 {len(uploaded_files)} 个文件")

# 主页面内容
st.markdown('<div class="sub-title">📋 文件上传</div>', unsafe_allow_html=True)
st.markdown('<div class="card file-upload-card">', unsafe_allow_html=True)

if st.session_state.uploaded_files:
    # 显示上传文件信息
    uploaded_files_info = [(file.name, len(file.getvalue())) for file in st.session_state.uploaded_files]
    st.dataframe(
        pd.DataFrame(uploaded_files_info, columns=["文件名", "文件大小 (字节)"], index=range(1, len(uploaded_files_info)+1)),
        use_container_width=True,
        hide_index=False,
        height=min(200, len(uploaded_files_info)*35 + 35)  # 动态调整高度
    )
else:
    st.info("💡 请在左侧上传Excel文件开始分析")

st.markdown('</div>', unsafe_allow_html=True)

# 页面切换逻辑
if st.session_state.current_page == "数据合并":
    st.markdown('<div class="sub-title">📊 数据合并</div>', unsafe_allow_html=True)
    
    if st.session_state.uploaded_files:
        # 添加日期范围过滤
        st.markdown("### 🔍 日期范围筛选")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期", value=None, help="选择数据分析的开始日期")
        with col2:
            end_date = st.date_input("结束日期", value=None, help="选择数据分析的结束日期")
        
        if st.button("🚀 执行数据合并", type="primary", disabled=st.session_state.processing_status == "processing"):
            # 更新处理状态
            SessionPersistence.save_data('processing_status', 'processing')
            SessionPersistence.save_data('last_error', None)
            
            import time
            start_time = time.time()
            
            try:
                # 显示进度条
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("正在准备数据...")
                progress_bar.progress(10)
                
                # 导入数据合并模块
                from merged_data_module import HeatDataMerger
                
                # 执行数据合并
                status_text.text("正在执行数据合并...")
                progress_bar.progress(60)
                
                output_file = "merged_data.xlsx"
                merged_df = HeatDataMerger.process_uploaded_files(st.session_state.uploaded_files, output_file)
                
                # 应用日期范围过滤（如果有选择日期）
                if start_date and end_date:
                    # 确保数据时间列是datetime类型
                    merged_df['数据时间'] = pd.to_datetime(merged_df['数据时间'])
                    # 过滤日期范围
                    start_datetime = pd.Timestamp(f"{start_date} 00:00:00")
                    end_datetime = pd.Timestamp(f"{end_date} 23:59:59")
                    merged_df = merged_df[(merged_df['数据时间'] >= start_datetime) & (merged_df['数据时间'] <= end_datetime)]
                    status_text.text("正在应用日期范围过滤...")
                    progress_bar.progress(90)
                
                # 保存合并结果到会话
                SessionPersistence.save_data('merged_data', merged_df)
                
                # 完成处理
                progress_bar.progress(100)
                status_text.text("数据合并完成！")
                
                # 计算处理时间
                processing_time = round(time.time() - start_time, 2)
                SessionPersistence.save_data('processing_time', processing_time)
                
                # 显示合并结果
                st.success(f"数据合并完成！耗时: {processing_time}秒")
                st.markdown(f"合并后的数据形状: {merged_df.shape}")
                st.markdown("### 合并数据预览")
                st.dataframe(merged_df.head(), use_container_width=True)
                
                # 下载选项
                st.markdown("### 下载合并数据")
                csv_data = merged_df.to_csv(index=False).encode('utf-8')
                excel_data = BytesIO()
                merged_df.to_excel(excel_data, index=False, engine='openpyxl')
                excel_data.seek(0)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📄 下载CSV格式",
                        data=csv_data,
                        file_name="merged_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col2:
                    st.download_button(
                        label="📊 下载Excel格式",
                        data=excel_data,
                        file_name="merged_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                # 更新处理状态
                SessionPersistence.save_data('processing_status', 'completed')
                logger.info(f"Data merging completed successfully, shape: {merged_df.shape}, time: {processing_time}s")
            
            except Exception as e:
                # 记录错误
                error_msg = f"数据合并失败: {str(e)}"
                logger.error(f"Data merging failed: {str(e)}\n{traceback.format_exc()}")
                
                # 更新处理状态
                SessionPersistence.save_data('processing_status', 'error')
                SessionPersistence.save_data('last_error', error_msg)
                
                # 显示错误信息
                st.error(error_msg)
                st.exception(e)
                
            finally:
                # 清理状态
                time.sleep(1)  # 让用户看到完成状态
                if 'progress_bar' in locals():
                    progress_bar.empty()
                if 'status_text' in locals():
                    status_text.empty()
    else:
        st.info("💡 请先上传Excel文件开始分析，或查看下方系统功能介绍")
        
        # 系统功能介绍
        st.markdown("---")
        st.markdown('### 📚 系统功能介绍')
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown('<div class="feature-icon">📥</div>', unsafe_allow_html=True)
            st.markdown('### 📥 数据上传')
            st.markdown('支持上传多个Excel文件，系统自动合并处理')
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown('<div class="feature-icon">🔬</div>', unsafe_allow_html=True)
            st.markdown('### 🔬 数据分析')
            st.markdown('按小时重采样，平滑处理，计算置信区间')
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col3:
            st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown('<div class="feature-icon">📊</div>', unsafe_allow_html=True)
            st.markdown('### 📊 可视化展示')
            st.markdown('生成三种关系图，直观展示数据趋势')
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 支持的数据格式
        st.markdown("---")
        st.markdown('### 📋 支持的数据格式')
        
        st.markdown('<ul class="data-format-list">', unsafe_allow_html=True)
        st.markdown('<li><strong>数据时间</strong>：数据采集时间</li>', unsafe_allow_html=True)
        st.markdown('<li><strong>室温温度(℃)</strong>：室温温度数据</li>', unsafe_allow_html=True)
        st.markdown('<li><strong>瞬时流量(T/H)</strong>：瞬时流量数据</li>', unsafe_allow_html=True)
        st.markdown('<li><strong>供温(℃)</strong>：供水温度数据</li>', unsafe_allow_html=True)
        st.markdown('<li><strong>回温(℃)</strong>：回水温度数据</li>', unsafe_allow_html=True)
        st.markdown('</ul>', unsafe_allow_html=True)

elif st.session_state.current_page == "供热数据分析":
    st.markdown('<div class="sub-title">📈 供热数据分析</div>', unsafe_allow_html=True)
    
    if st.session_state.merged_data is not None or st.session_state.uploaded_files:
        # 准备数据
        data_to_use = None
        if st.session_state.merged_data is not None:
            data_to_use = st.session_state.merged_data.copy()
        else:
            # 从上传文件中获取数据
            from merged_data_module import HeatDataMerger
            output_file = "merged_data.xlsx"
            data_to_use = HeatDataMerger.process_uploaded_files(st.session_state.uploaded_files, output_file)
        
        # 处理位置和楼层信息（如果存在）
        locations = ['全部']
        floors = ['全部']
        
        if '位置' in data_to_use.columns:
            # 获取唯一值并过滤掉None，然后排序
            unique_locations = data_to_use['位置'].unique().tolist()
            # 过滤掉None值后排序
            valid_locations = [loc for loc in unique_locations if loc is not None]
            locations += sorted(valid_locations)
        if '楼层' in data_to_use.columns:
            # 获取唯一值并过滤掉None，然后排序
            unique_floors = data_to_use['楼层'].unique().tolist()
            # 过滤掉None值后排序
            valid_floors = [floor for floor in unique_floors if floor is not None]
            floors += sorted(valid_floors)
        
        # 添加交互式筛选按钮
        st.markdown("### 🔍 数据筛选")
        
        # 位置筛选
        col1, col2 = st.columns(2)
        with col1:
            selected_location = st.selectbox(
                "选择位置",
                options=locations,
                index=0,
                help="选择要查看的位置"
            )
        
        # 楼层筛选
        with col2:
            selected_floor = st.selectbox(
                "选择楼层",
                options=floors,
                index=0,
                help="选择要查看的楼层"
            )
        
        # 应用筛选
        filtered_data = data_to_use.copy()
        
        if selected_location != '全部' and '位置' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['位置'] == selected_location]
        
        if selected_floor != '全部' and '楼层' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['楼层'] == selected_floor]
        
        # 显示筛选结果
        st.write(f"筛选结果: {len(filtered_data)} 条记录")
        
        # 数据处理选项
        st.markdown("### ⚙️ 数据处理")
        col1, col2 = st.columns(2)
        with col1:
            # 平滑处理选项
            smooth_data = st.checkbox(
                "启用数据平滑处理",
                value=True,
                help="勾选后将对数据进行平滑处理并显示95%置信区间"
            )
        
        with col2:
            # 图表类型选择
            chart_types = st.multiselect(
                "选择要生成的图表",
                options=["室温温度趋势图", "瞬时流量趋势图", "供温回温关系图"],
                default=["室温温度趋势图", "瞬时流量趋势图", "供温回温关系图"],
                help="选择您想要查看的图表类型"
            )
        
        if st.button("🚀 生成分析图表", type="primary", disabled=st.session_state.processing_status == "processing" or filtered_data.empty):
            # 更新处理状态
            SessionPersistence.save_data('processing_status', 'processing')
            SessionPersistence.save_data('last_error', None)
            
            import time
            import matplotlib.pyplot as plt
            start_time = time.time()
            
            try:
                # 显示进度条
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("正在准备数据...")
                progress_bar.progress(10)
                
                # 导入图表生成模块
                from chart_generator import ChartGenerator
                
                # 生成图表
                status_text.text("正在初始化图表生成器...")
                progress_bar.progress(50)
                
                chart_gen = ChartGenerator(filtered_data)
                
                status_text.text("正在加载和预处理数据...")
                progress_bar.progress(60)
                
                if chart_gen.load_data() and chart_gen.clean_and_preprocess_data():
                    status_text.text("正在生成图表...")
                    progress_bar.progress(80)
                    
                    charts = chart_gen.plot_all_charts(smooth=smooth_data)
                    
                    # 完成处理
                    progress_bar.progress(100)
                    status_text.text("图表生成完成！")
                    
                    # 计算处理时间
                    processing_time = round(time.time() - start_time, 2)
                    SessionPersistence.save_data('processing_time', processing_time)
                    
                    # 显示处理结果
                    st.success(f"图表生成完成！耗时: {processing_time}秒")
                    
                    # 显示图表 - 每个图表使用独立卡片
                    for chart_name, chart in charts.items():
                        if chart_name == 'room_temperature' and "室温温度趋势图" in chart_types:
                            st.markdown('<div class="card chart-card">', unsafe_allow_html=True)
                            st.markdown("### 🏠 时间与室温温度关系图")
                            st.pyplot(chart)
                            st.markdown('</div>', unsafe_allow_html=True)
                        elif chart_name == 'instant_flow' and "瞬时流量趋势图" in chart_types:
                            st.markdown('<div class="card chart-card">', unsafe_allow_html=True)
                            st.markdown("### 💧 时间与瞬时流量关系图")
                            st.pyplot(chart)
                            st.markdown('</div>', unsafe_allow_html=True)
                        elif chart_name == 'supply_return_temperature' and "供温回温关系图" in chart_types:
                            st.markdown('<div class="card chart-card">', unsafe_allow_html=True)
                            st.markdown("### 🌡️ 时间与供温回温关系图")
                            st.pyplot(chart)
                            st.markdown('</div>', unsafe_allow_html=True)
                        plt.close(chart)  # 关闭图表以释放内存
                    
                    # 更新处理状态
                    SessionPersistence.save_data('processing_status', 'completed')
                    logger.info(f"Chart generation completed successfully, time: {processing_time}s")
                else:
                    st.error("数据处理失败，请检查数据格式")
                    SessionPersistence.save_data('processing_status', 'error')
                    logger.error("Data processing failed during chart generation")
            except Exception as e:
                # 记录错误
                error_msg = f"图表生成失败: {str(e)}"
                logger.error(f"Chart generation failed: {str(e)}\n{traceback.format_exc()}")
                
                # 更新处理状态
                SessionPersistence.save_data('processing_status', 'error')
                SessionPersistence.save_data('last_error', error_msg)
                
                # 显示错误信息
                st.error(error_msg)
                st.exception(e)
            finally:
                # 清理状态
                time.sleep(1)  # 让用户看到完成状态
                if 'progress_bar' in locals():
                    progress_bar.empty()
                if 'status_text' in locals():
                    status_text.empty()
                # 确保所有图表都已关闭
                plt.close('all')
    else:
        st.info("请先上传Excel文件或完成数据合并")

elif st.session_state.current_page == "报告分析":
    st.markdown('<div class="sub-title">📑 报告分析</div>', unsafe_allow_html=True)
    
    if st.session_state.merged_data is not None or st.session_state.uploaded_files:
        if st.button("🚀 生成分析报告", type="primary", disabled=st.session_state.processing_status == "processing"):
            # 更新处理状态
            SessionPersistence.save_data('processing_status', 'processing')
            SessionPersistence.save_data('last_error', None)
            
            import time
            import matplotlib.pyplot as plt
            start_time = time.time()
            
            try:
                # 显示进度条
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("正在准备数据...")
                progress_bar.progress(10)
                
                # 导入必要的模块
                from chart_generator import ChartGenerator
                
                data_to_use = None
                
                # 确定使用的数据
                if st.session_state.merged_data is not None:
                    data_to_use = st.session_state.merged_data
                    status_text.text("正在使用已合并的数据...")
                    progress_bar.progress(20)
                else:
                    # 如果没有合并数据，先合并上传的文件
                    from merged_data_module import HeatDataMerger
                    status_text.text("正在执行数据合并...")
                    progress_bar.progress(40)
                    
                    output_file = "merged_data.xlsx"
                    data_to_use = HeatDataMerger.process_uploaded_files(st.session_state.uploaded_files, output_file)
                
                # 生成图表和报告
                status_text.text("正在初始化报告生成器...")
                progress_bar.progress(50)
                
                chart_gen = ChartGenerator(data_to_use)
                
                status_text.text("正在加载和预处理数据...")
                progress_bar.progress(60)
                
                if chart_gen.load_data() and chart_gen.clean_and_preprocess_data():
                    status_text.text("正在生成图表...")
                    progress_bar.progress(80)
                    
                    charts = chart_gen.plot_all_charts(smooth=True)
                    
                    # 完成处理
                    progress_bar.progress(100)
                    status_text.text("报告生成完成！")
                    
                    # 计算处理时间
                    processing_time = round(time.time() - start_time, 2)
                    SessionPersistence.save_data('processing_time', processing_time)
                    
                    # 显示处理结果
                    st.success(f"报告生成完成！耗时: {processing_time}秒")
                    
                    # 显示数据概览
                    st.markdown("### 📊 数据概览")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("总记录数", len(data_to_use))
                    with col2:
                        st.metric("数据列数", len(data_to_use.columns))
                    with col3:
                        if '数据时间' in data_to_use.columns:
                            start_time = data_to_use['数据时间'].min()
                            start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(start_time) else "N/A"
                            st.metric("起始时间", start_time_str)
                        else:
                            st.metric("起始时间", "N/A")
                    with col4:
                        if '数据时间' in data_to_use.columns:
                            end_time = data_to_use['数据时间'].max()
                            end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(end_time) else "N/A"
                            st.metric("结束时间", end_time_str)
                        else:
                            st.metric("结束时间", "N/A")
                    
                    # 显示数据预览
                    st.markdown("### 数据预览")
                    st.dataframe(data_to_use.head(10), use_container_width=True, height=300)
                    
                    # 显示图表
                    st.markdown("### 📈 数据分析图表")
                    for chart_name, chart in charts.items():
                        st.pyplot(chart)
                        plt.close(chart)  # 关闭图表以释放内存
                    
                    # 更新处理状态
                    SessionPersistence.save_data('processing_status', 'completed')
                    logger.info(f"Report generation completed successfully, time: {processing_time}s")
                else:
                    st.error("数据处理失败，请检查数据格式")
                    SessionPersistence.save_data('processing_status', 'error')
                    logger.error("Data processing failed during report generation")
            except Exception as e:
                # 记录错误
                error_msg = f"报告生成失败: {str(e)}"
                logger.error(f"Report generation failed: {str(e)}\n{traceback.format_exc()}")
                
                # 更新处理状态
                SessionPersistence.save_data('processing_status', 'error')
                SessionPersistence.save_data('last_error', error_msg)
                
                # 显示错误信息
                st.error(error_msg)
                st.exception(e)
            finally:
                # 清理状态
                time.sleep(1)  # 让用户看到完成状态
                if 'progress_bar' in locals():
                    progress_bar.empty()
                if 'status_text' in locals():
                    status_text.empty()
                # 确保所有图表都已关闭
                plt.close('all')
    else:
        st.info("请先上传Excel文件或完成数据合并")
