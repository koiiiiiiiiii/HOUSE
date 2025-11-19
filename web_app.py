import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pypinyin import lazy_pinyin
import matplotlib.pyplot as plt
import time

# 1. 设置网页标题
st.set_page_config(page_title="房价监控系统", layout="centered")

# 2. 网页的大标题 (必须用 st.title 才能看见)
st.title("🏠 城市房价监控系统 (Web版)")
st.info("请在下方输入城市名字，然后点击按钮。")

# 3. 输入区域
col1, col2 = st.columns(2)
with col1:
    # 获取用户输入
    city_input = st.text_input("请输入城市 (如: 句容)", value="句容")
with col2:
    bond_yield = st.number_input("国债收益率 (%)", value=2.1)

# 4. 爬虫逻辑 (房天下版 - 兼容小城市)
def get_data(city_name):
    pinyin = "".join(lazy_pinyin(city_name))
    url = f"https://{pinyin}.esf.fang.com/"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        resp.encoding = 'gbk' # 关键：房天下防乱码
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 找价格
        price = 0
        spans = soup.find_all('span', class_='red')
        for s in spans:
            if s.text.strip().isdigit() and len(s.text.strip()) > 3:
                price = int(s.text.strip())
                break
        
        if price == 0:
            div = soup.find(class_='org bold')
            if div:
                price = int(div.text.strip())
                
        return price
    except Exception as e:
        return 0

# 5. 按钮点击后的逻辑
if st.button("🚀 开始分析", type="primary"):
    if not city_input:
        st.warning("请输入城市名字")
    else:
        with st.spinner(f"正在连接服务器查询【{city_input}】..."):
            # 运行爬虫
            price = get_data(city_input)
            time.sleep(0.5) # 模拟一点延迟让用户有感觉
            
        if price > 0:
            # 计算
            rent_est = price / 700
            yield_rate = (rent_est * 12 / price) * 100
            
            # 显示大数字 (Metrics)
            st.metric("二手房均价", f"{price} 元/㎡")
            st.metric("估算年化回报率", f"{yield_rate:.2f}%", delta=f"{yield_rate - bond_yield:.2f}% vs 国债")
            
            # 画图 (必须用 st.pyplot)
            fig, ax = plt.subplots()
            bars = ax.bar(['House', 'Bond'], [yield_rate, bond_yield], color=['#ff9999', '#66b3ff'])
            ax.set_title(f"{city_input} Yield vs Bond")
            ax.set_ylabel("Yield (%)")
            
            # 在网页上显示图表
            st.pyplot(fig)
            
        else:
            st.error("未找到数据。可能原因：1.城市拼音不对 2.该城市太小房天下没收录 3.反爬虫拦截")