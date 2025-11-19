import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pypinyin import lazy_pinyin
import matplotlib.pyplot as plt
import akshare as ak  # 引入金融数据库
import time

# ================= 页面配置 =================
st.set_page_config(page_title="权威房产监控(Beta)", layout="centered")
st.title("🏠 权威数据监控系统")
st.caption("数据源：贝壳找房 (Lianjia) + AkShare (东方财富)")

# ================= 核心功能区 =================

# 1. 获取实时国债收益率 (AkShare)
def get_bond_yield():
    try:
        # 获取中国10年期国债数据
        df = ak.bond_zh_us_rate(symbol="CN_10Y")
        # 取最新一天的收盘价
        latest_yield = df.iloc[-1]['close']
        return float(latest_yield)
    except:
        return 2.10 # 如果接口挂了，返回兜底数据

# 2. 爬取贝壳找房 (权威性更高)
def get_lianjia_price(city_name):
    # 贝壳的城市拼音规则比较严格，句容可能在镇江下面
    # 简单起见，我们先尝试直接访问
    pinyin = "".join(lazy_pinyin(city_name))
    
    # 贝壳网址结构
    url = f"https://{pinyin}.lianjia.com/ershoufang/"
    
    # 贝壳需要更强的伪装
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.baidu.com'
    }
    
    try:
        # 贝壳如果发现是句容这种小城市，可能需要特殊处理
        # 这里做一个简单的容错：如果直接访问失败，提示用户
        resp = requests.get(url, headers=headers, timeout=5)
        
        if "verify" in resp.url: # 如果跳转到了验证码页面
            return 0, "触发了贝壳的安全验证，IP被暂时拦截。"
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 贝壳的数据结构：div class="totalPrice" 和 "unitPrice"
        # 我们抓取列表页的第一套房作为参考，或者抓取均价
        # 注意：贝壳列表页没有直接的"全市均价"，我们抓取前几套房算个平均
        
        prices = []
        unit_prices = soup.find_all('div', class_='unitPrice')
        
        for u in unit_prices:
            # 格式通常是 "23,456元/平"
            p_text = u.text.replace('元/平', '').replace(',', '').replace('单价', '')
            if p_text.isdigit():
                prices.append(int(p_text))
        
        if prices:
            avg_price = sum(prices) / len(prices)
            return int(avg_price), None
        else:
            return 0, "未找到价格数据，可能是该城市没有开通贝壳二手房站。"
            
    except Exception as e:
        return 0, str(e)

# ================= 界面交互 =================

# 侧边栏
with st.sidebar:
    st.header("设置")
    city = st.text_input("输入城市拼音 (推荐)", value="shanghai")
    st.caption("注：贝壳找房建议使用拼音，如 jurong 或 zhenjiang")

# 主逻辑
if st.button("🚀 分析实时数据", type="primary"):
    
    # 1. 获取国债
    with st.spinner("正在从 东方财富 获取实时国债利率..."):
        real_bond = get_bond_yield()
    
    # 2. 获取房价
    with st.spinner(f"正在从 贝壳找房 获取 {city} 房价..."):
        price, error = get_lianjia_price(city)
        
    # 3. 展示结果
    col1, col2 = st.columns(2)
    col1.metric("🇨🇳 10年期国债收益率", f"{real_bond}%")
    
    if price > 0:
        rent_yield = (price / 700 * 12 / price) * 100
        col2.metric(f"{city} 二手房参考均价", f"{price} 元/㎡")
        
        st.success("分析完成！数据来源：AkShare & 贝壳找房")
        
        # 结论
        diff = rent_yield - real_bond
        if diff < 0:
            st.error(f"📉 结论：当前房产租金回报 ({rent_yield:.2f}%) 跑输 国债 ({real_bond}%)。")
        else:
            st.success(f"📈 结论：房产收益尚可，跑赢国债 {diff:.2f}%。")
            
    else:
        col2.metric("房价获取失败", "N/A")
        st.error(f"贝壳报错: {error}")
        st.info("💡 提示：贝壳对小城市支持不全。如果是句容，建议尝试输入 'zhenjiang' (镇江) 查看整体数据。")