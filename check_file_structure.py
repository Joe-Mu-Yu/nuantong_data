import pandas as pd
import os

# 设置文件路径
reference_file = r'd:/Users/joero/Desktop/qqq/merged_data_simple.xlsx'
target_folder = r'd:/Users/joero/Desktop/qqq/1/'

print("=== 查看参考文件结构 ===")
try:
    # 读取参考文件
    ref_df = pd.read_excel(reference_file)
    
    print(f"参考文件形状: {ref_df.shape}")
    print(f"参考文件列名: {ref_df.columns.tolist()}")
    print(f"\n参考文件前5行数据:")
    print(ref_df.head())
    
    print(f"\n参考文件数据类型:")
    print(ref_df.dtypes)
except Exception as e:
    print(f"读取参考文件失败: {e}")

print("\n=== 查看目标文件夹中的Excel文件 ===")
# 获取目标文件夹中的所有Excel文件
excel_files = [f for f in os.listdir(target_folder) if f.endswith('.xlsx') or f.endswith('.xls')]
print(f"找到 {len(excel_files)} 个Excel文件:")
for file in excel_files:
    print(f"  - {file}")

# 查看一个有效Excel文件的结构（跳过临时文件）
valid_excel_files = [f for f in excel_files if not f.startswith('~$')]
if valid_excel_files:
    first_valid_file = os.path.join(target_folder, valid_excel_files[1])  # 查看单独日期文件
    print(f"\n=== 查看文件 {valid_excel_files[1]} 的结构 ===")
    try:
        first_df = pd.read_excel(first_valid_file)
        print(f"文件形状: {first_df.shape}")
        print(f"文件列名: {first_df.columns.tolist()}")
        print(f"\n文件前5行数据:")
        print(first_df.head())
        print(f"\n文件数据类型:")
        print(first_df.dtypes)
    except Exception as e:
        print(f"读取文件失败: {e}")
    
    # 查看综合文件的结构
    if len(valid_excel_files) > 1:
        combined_file = os.path.join(target_folder, valid_excel_files[0])  # 查看综合文件
        print(f"\n=== 查看综合文件 {valid_excel_files[0]} 的结构 ===")
        try:
            combined_df = pd.read_excel(combined_file)
            print(f"文件形状: {combined_df.shape}")
            print(f"文件列名: {combined_df.columns.tolist()}")
            print(f"\n文件前5行数据:")
            print(combined_df.head())
            print(f"\n文件数据类型:")
            print(combined_df.dtypes)
        except Exception as e:
            print(f"读取综合文件失败: {e}")