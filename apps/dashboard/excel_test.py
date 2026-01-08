
import pandas as pd

def process_and_save_simple(input_file, output_file=None):
    """
    简化版：处理并保存Excel文件
    """
    # 设置输出文件名
    if output_file is None:
        output_file = input_file.replace('.xlsx', '_processed.xlsx')
    
    # 创建Excel写入器
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        
        # 处理并保存每个sheet
        sheets = ['Sheet1', 'Sheet2']
        
        for sheet in sheets:
            try:
                print(f"处理{sheet}...")
                
                # 读取并处理数据
                raw_data = pd.read_excel(input_file, sheet_name=sheet, header=None)
                
                # 处理表头
                headers = []
                for col_idx in range(raw_data.shape[1]):
                    col_headers = []
                    
                    # 第1行
                    level1 = raw_data.iloc[0, col_idx]
                    if pd.notna(level1):
                        col_headers.append(str(level1).strip())
                    
                    # 第2行
                    level2 = raw_data.iloc[1, col_idx]
                    if pd.notna(level2) and str(level2).strip():
                        col_headers.append(str(level2).strip())
                    
                    # 创建列名
                    if col_headers:
                        col_name = '_'.join(col_headers)
                    else:
                        col_name = f'Column_{col_idx+1}'
                    
                    headers.append(col_name)
                
                # 读取数据
                df = pd.read_excel(input_file, sheet_name=sheet, header=None, skiprows=3)
                df.columns = headers
                
                # 保存到新文件
                df.to_excel(writer, sheet_name=sheet, index=False)
                
                print(f"  {sheet}处理完成: {df.shape[0]}行 × {df.shape[1]}列")
                
            except Exception as e:
                print(f"  处理{sheet}时出错: {str(e)}")
    
    print(f"\n处理完成！已保存为: {output_file}")
    return output_file

# 使用
output_path = process_and_save_simple("/Users/baihai/test/数据录入表-2014年.xlsx")







