import streamlit as st
import pandas as pd
import akshare as ak
import matplotlib.pyplot as plt
from datetime import datetime

# ================= 权威数据获取模块 (使用缓存，提高性能) =================

@st.cache_data(ttl=3600)  # 数据缓存1小时，减少API调用和加载时间
def fetch_city_hpi_data(city_name):
    """
    获取指定城市的商品住宅销售价格指数。
    数据源：官方指数聚合（如中国银行/东方财富），稳定且权威。
    """
    try:
        # 1. 获取所有地级市的房价指数数据 (AkShare 权威接口)
        df_all = ak.macro_china_city_hpi()
        
        # 2. 预处理
        df_all.columns = ['日期', '城市', '指数']
        df_all['日期'] = pd.to_datetime(df_all['日期'])
        
        # 3. 筛选用户指定的城市 (使用模糊匹配)
        # 例如：输入"镇江"可以匹配到"江苏-镇江"
        # 这一步解决了小城市如句容的查询问题
        df_city = df_all[df_all['城市'].str.contains(city_name, case=False, na=False)]
        
        if df_city.empty:
            return None, f"数据集中未找到包含 '{city_name}' 的城市指数。"
        
        return df_city, None
        
    except Exception as e:
        # 如果 AkShare 接口访问失败（例如网络超时），捕获错误
        return None, f"数据接口连接失败或处理错误: {e}"

# ================= 网站界面布局与逻辑 =================

st.set_page_config(page_title="权威房价指数监控", layout="centered", page_icon="📈")

st.title("🏙️ 权威数据中心：城市房价指数")
st.caption("数据来源：国家统计局 / 金融数据聚合。稳定可靠。")
st.markdown("---")

# 侧边栏/输入框
with st.sidebar:
    st.header("城市选择")
    city_input = st.text_input("请输入城市名称", value="镇江")
    st.info("💡 提示：县级市（如句容）请尝试输入其所属**地级市**（如镇江）查询官方指数。")

# 主逻辑
if st.button("🚀 分析城市房价指数", type="primary"):
    
    if not city_input:
        st.warning("请输入城市名称才能分析！")
        st.stop()
        
    # 启用加载动画
    with st.spinner(f"正在查询【{city_input}】的权威房价指数..."):
        df_city_hpi, error = fetch_city_hpi_data(city_input)
        
    if df_city_hpi is not None:
        # 提取城市全名（例如 "江苏-镇江"）
        full_city_name = df_city_hpi['城市'].iloc[-1]
        
        st.success(f"【{full_city_name}】指数获取成功！")
        
        # 1. 显示趋势图表
        st.subheader(f"📈 {full_city_name} 房价指数趋势")
        st.line_chart(df_city_hpi.set_index('日期')['指数'], use_container_width=True)
        
        # 2. 显示最新数据表
        st.subheader("📑 最新数据 (最近12个月)")
        df_display = df_city_hpi[['日期', '指数', '城市']].tail(12)
        st.dataframe(df_display, hide_index=True)
        
    else:
        st.error(f"数据获取失败: {error}")
        st.info("请尝试输入该城市所在的地级市名称。")