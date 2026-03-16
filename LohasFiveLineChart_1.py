import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# 設定網頁標題
st.set_page_config(page_title="樂活五線譜自動生成", layout="wide")

# 側邊欄：查詢設定
st.sidebar.header("查詢設定")
stock_id = st.sidebar.text_input("股票代號 (如: 2330 或 AAPL)", "2330")

# 修正台股代號格式
if stock_id.isdigit():
    search_id = f"{stock_id}.TW"
else:
    search_id = stock_id

start_date = st.sidebar.date_input("起始日期", datetime(2023, 6, 20))
end_date = st.sidebar.date_input("結束日期", datetime.now())
calculate_btn = st.sidebar.button("開始計算")

st.title("📈 樂活五線譜自動生成")
st.subheader(f"📊 目前分析標的: {search_id}")

if calculate_btn or stock_id:
    # 1. 抓取資料 (加入 auto_adjust=True 確保格式穩定)
    data = yf.download(search_id, start=start_date, end=end_date, auto_adjust=True)
    
    if not data.empty:
        # 關鍵修正：確保 Close 是 1D 數列
        close_prices = data['Close'].values.flatten()
        df = pd.DataFrame({'Date': data.index, 'Close': close_prices})
        df['Time_Idx'] = np.arange(len(df)) 
        
        # 2. 計算線性回歸 (使用修正後的 close_prices)
        z = np.polyfit(df['Time_Idx'], df['Close'], 1)
        p = np.poly1d(z)
        df['Trend_Line'] = p(df['Time_Idx'])
        
        # 3. 計算標準差
        std_dev = (df['Close'] - df['Trend_Line']).std()
        df['Upper_2'] = df['Trend_Line'] + 2 * std_dev
        df['Upper_1'] = df['Trend_Line'] + 1 * std_dev
        df['Lower_1'] = df['Trend_Line'] - 1 * std_dev
        df['Lower_2'] = df['Trend_Line'] - 2 * std_dev

        # 4. 繪製 Plotly 圖表
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='收盤價', line=dict(color='black', width=1.5)))
        
        colors = ['red', 'orange', 'blue', 'lightgreen', 'green']
        names = ['極端樂觀', '樂觀', '趨勢中線', '悲觀', '極端悲觀']
        lines = ['Upper_2', 'Upper_1', 'Trend_Line', 'Lower_1', 'Lower_2']
        
        for idx, line in enumerate(lines):
            fig.add_trace(go.Scatter(x=df['Date'], y=df[line], name=names[idx], 
                                     line=dict(dash='dash' if 'Trend' not in line else 'solid', 
                                               color=colors[idx], width=1)))

        fig.update_layout(height=600, hovermode='x unified', template='plotly_white',
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

        # 5. 數據摘要
        st.header("📊 數據摘要")
        last_price = df['Close'].iloc[-1]
        mid_price = df['Trend_Line'].iloc[-1]
        current_sd = (last_price - mid_price) / std_dev
        
        col1, col2, col3 = st.columns(3)
        col1.metric("最後收盤價", f"{last_price:.2f}")
        col2.metric("回歸中線", f"{mid_price:.2f}")
        col3.metric("目前區間", f"{current_sd:.2f} σ")
        
        if current_sd > 0:
            st.success("↑ 高於中線")
        else:
            st.warning("↓ 低於中線")
    else:
        st.error("找不到該股票代號的資料，請檢查代號是否正確。")