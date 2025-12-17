import glob
from process_excel import ExcelProcessor

# 设置测试文件夹路径
test_folder = r'd:/Users/joero/Desktop/src/1/'

# 获取所有Excel文件
all_files = glob.glob(f'{test_folder}*.xlsx')
all_files = [f for f in all_files if not f.endswith('~$')]

# 分组文件
first_group_files = [f for f in all_files if '二网历史数据表' in f]
second_group_files = [f for f in all_files if '低环历史数据' in f]

print(f"第一组文件数: {len(first_group_files)}")
print(f"第二组文件数: {len(second_group_files)}")

# 使用合并功能
merged_df = ExcelProcessor.merge_different_data_groups(first_group_files, second_group_files, verbose=True)

if merged_df is not None:
    print(f"\n=== 合并后的表格信息 ===")
    print(f"总行数: {len(merged_df)}")
    print(f"总列数: {len(merged_df.columns)}")
    print(f"\n所有列名:")
    print(', '.join(merged_df.columns))
    
    print(f"\n=== 合并后的前10行表格数据 ===")
    print(merged_df.head(10).to_string(index=False))
    
    print(f"\n=== 合并后的后10行表格数据 ===")
    print(merged_df.tail(10).to_string(index=False))
    
    # 保存合并后的表格为Excel文件
    output_file = r'd:/Users/joero/Desktop/src/merged_table_output.xlsx'
    merged_df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"\n合并后的表格已保存到: {output_file}")
