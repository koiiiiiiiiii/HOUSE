import requests
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO  # 新增工具，用来消除那个红色的警告

# --- 1. 设置部分 ---
CITY_URL = "https://www.numbeo.com/property-investment/in/jurong"
BOND_YIELD = 2.1  # 国债收益率

def get_house_data():
    print(f"正在尝试获取上海的数据: {CITY_URL} ...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(CITY_URL, headers=headers, timeout=10)
        
        # 修复警告：用 StringIO 包装一下网页内容
        tables = pd.read_html(StringIO(response.text))
        
        df = tables[1]
        df.columns = ['指标名称', '数值']
        return df
        
    except Exception as e:
        print(f"获取数据出错：{e}")
        return None

def analyze_data(df):
    if df is None:
        return
    
    print("\n--- 获取成功！数据清洗中 ---")
    
    try:
        # 寻找包含 'Gross Rental Yield' (租金收益率) 的那一行
        # regex=True 表示模糊匹配
        yield_row = df[df['指标名称'].str.contains('Gross Rental Yield \(City Centre\)', regex=True)]
        
        if not yield_row.empty:
            # --- 关键修复在这里 ---
            # 拿到原始文字 (例如 "1.55%")
            raw_value = str(yield_row.iloc[0]['数值'])
            
            # 把 '%' 替换为空白，然后去除首尾空格
            clean_value = raw_value.replace('%', '').strip()
            
            # 变成数字
            rental_yield = float(clean_value)
            
            print(f"\n📊 上海市中心租金收益率: {rental_yield}%")
            print(f"💰 国债无风险收益率: {BOND_YIELD}%")
            
            diff = rental_yield - BOND_YIELD
            print("-" * 30)
            if diff > 0:
                print(f"✅ 结论：买房收租比买国债划算，高出 {diff:.2f}%")
            else:
                print(f"❌ 结论：买房不如买国债！房产收益低了 {abs(diff):.2f}%")
            print("-" * 30)
                
            # 画图
            names = ['House Yield', 'Bond Yield']
            values = [rental_yield, BOND_YIELD]
            
            plt.figure(figsize=(6, 4)) # 设置图片大小
            # 柱状图：房产用红色(危险?)，国债用绿色(安全?)
            bars = plt.bar(names, values, color=['#FF6B6B', '#4ECDC4'])
            
            # 在柱子上标数字
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height}%', ha='center', va='bottom')

            plt.title('Shanghai Property vs China 10Y Bond')
            plt.ylabel('Annual Yield (%)')
            plt.show()
            
        else:
            print("没找到租金收益率数据，可能网页结构变了。")
            print("当前表格内容：")
            print(df)
            
    except Exception as e:
        print(f"分析时出错: {e}")

# --- 运行程序 ---
if __name__ == "__main__":
    data = get_house_data()
    analyze_data(data)