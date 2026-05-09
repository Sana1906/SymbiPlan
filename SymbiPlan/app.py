import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- 1. CORE LOGIC ---

def get_ai_recommendation(df, selected_location):
    try:
        # Looking for '70%' which is often in the column header for SymbiPlan data
        location_col = [c for c in df.columns if '70%' in c or 'Location' in c][0]
        operator_col = [c for c in df.columns if 'Operator' in c][0]
        signal_col = [c for c in df.columns if 'Signal Strength' in c][0]
        
        subset = df[df[location_col] == selected_location]
        if subset.empty: return f"No data for {selected_location} yet."
        
        avg_signals = subset.groupby(operator_col)[signal_col].mean()
        best_op, strength = avg_signals.idxmax(), round(avg_signals.max(), 1)
        return f"AI Analysis: **{best_op}** is strongest at {selected_location} ({strength}/5)."
    except Exception:
        return "AI analysis unavailable. Please ensure signal data is reported correctly."

def recommend_data_pack(pricing_df, budget, operator):
    try:
        # Standardizing columns: Operator, Price, Data, Validity, Plan Name
        # Filtering plans within the budget for the chosen operator
        filtered = pricing_df[(pricing_df['Price'] <= budget) & (pricing_df['Operator'].str.contains(operator, case=False))]
        
        if filtered.empty:
            return None
        
        # Returns the plan with the highest price within the budget (best value)
        return filtered.sort_values(by='Price', ascending=False).iloc[0]
    except Exception:
        return "Error reading the telecom data."

def display_geospatial_map(df):
    st.write("### 📍 Live Campus Signal Hotspots")
    coords = {
        "Engineering Block": [18.6611, 73.7176], "Management Block": [18.6612, 73.7181], 
        "Admin Block":[18.6606, 73.7182], "Library":[18.6618, 73.7183], 
        "Open Cafeteria": [18.6615, 73.7183], "Nescafe":[18.6609, 73.7183], 
        "Hostel":[18.6616, 73.7162], "Amphitheatre":[18.6608, 73.7179], 
        "Canteen": [18.6605, 73.7175], "Skill Center": [18.6607, 73.7190]
    }
    m = folium.Map(location=[18.6611, 73.7176], zoom_start=18)
    try:
        l_col = [c for c in df.columns if '70%' in c or 'Location' in c][0]
        s_col = [c for c in df.columns if 'Signal Strength' in c][0]
        avg = df.groupby(l_col)[s_col].mean().reset_index()
        
        for _, r in avg.iterrows():
            if r[l_col] in coords:
                c = "red" if r[s_col] < 2.5 else "orange" if r[s_col] < 3.8 else "green"
                folium.Circle(location=coords[r[l_col]], radius=15, color=c, fill=True, popup=f"{r[l_col]}: {round(r[s_col],1)}").add_to(m)
        st_folium(m, width=700, height=400)
    except:
        st.warning("Waiting for signal data to populate map...")

# --- 2. THEME & STYLING ---
st.set_page_config(page_title="SymbiPlan", page_icon="📶", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important; }
    div.stButton > button {
        width: 100% !important; height: 80px !important;
        background: rgba(255, 255, 255, 0.7) !important;
        border-radius: 15px !important; color: #1E3A8A !important;
        font-weight: 700 !important; border: 1px solid rgba(255,255,255,0.8) !important;
        transition: 0.3s; margin-bottom: 15px;
    }
    div.stButton > button:hover { background: white !important; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    h2 { color: #1E3A8A !important; text-align: center; font-weight: 800; padding-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA CONNECTIONS ---
SIGNAL_URL = "https://docs.google.com/spreadsheets/d/1FVhzop8SMzmLylTPeqtm2PW2GxNbO1eTas4j7nYD__M/edit?usp=sharing"
TELECOM_URL = "https://docs.google.com/spreadsheets/d/1CaBmy4zwDnW4DkL72Jx8Tjxn3PgPYfN0KCNL-3rS2po/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# Initialize Session State
if 'page' not in st.session_state: st.session_state.page = 'Home'

# --- 4. NAVIGATION ---
if st.session_state.page == 'Home':
    st.markdown("<h2>📶 SymbiPlan</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 SIGNAL FINDER"): st.session_state.page = 'Signal Finder'
        if st.button("📊 LIVE HEATMAP"): st.session_state.page = 'Heatmap'
    with col2:
        if st.button("💰 SMART RECHARGE"): st.session_state.page = 'Recharge'
        if st.button("📢 REPORT SIGNAL"): st.session_state.page = 'Report'

# --- 5. PAGES ---
elif st.session_state.page == 'Signal Finder':
    if st.button("⬅️ Back to Home"): st.session_state.page = 'Home'
    st.header("🔍 Signal Finder")
    df_sig = conn.read(spreadsheet=SIGNAL_URL, ttl=60)
    loc = st.selectbox("Current Campus Location:", ["Admin Block", "Management Block", "Engineering Block", "Skill Center", "Library", "Canteen", "Open Cafeteria", "Nescafe", "Hostel Wings", "Parking", "Amphitheater"])
    if st.button("Analyze Best Operator"):
        st.info(get_ai_recommendation(df_sig, loc))

elif st.session_state.page == 'Heatmap':
    if st.button("⬅️ Back to Home"): st.session_state.page = 'Home'
    df_sig = conn.read(spreadsheet=SIGNAL_URL, ttl=60)
    display_geospatial_map(df_sig)

elif st.session_state.page == 'Recharge':
    if st.button("⬅️ Back to Home"): st.session_state.page = 'Home'
    st.header("💰 Smart Recharge Recommender")
    
    try:
        df_plans = conn.read(spreadsheet=TELECOM_URL, ttl=300)
        
        # User Inputs
        budget = st.slider("Select your Budget (₹)", 10, 1000, 299)
        operator = st.selectbox("Choose your Operator:", df_plans['Operator'].unique())
        
        if st.button("Get Best Plan"):
            best_plan = recommend_data_pack(df_plans, budget, operator)
            if best_plan is not None:
                st.success(f"### Best Match: {best_plan['Plan Name']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Price", f"₹{best_plan['Price']}")
                c2.metric("Data", best_plan['Data'])
                c3.metric("Validity", best_plan['Validity'])
            else:
                st.warning(f"No plans found for {operator} under ₹{budget}. Try increasing your budget.")
    except Exception as e:
        st.error("Could not fetch plan data. Check spreadsheet headers: 'Operator', 'Price', 'Data', 'Validity', 'Plan Name'")

elif st.session_state.page == 'Report':
    if st.button("⬅️ Back to Home"): st.session_state.page = 'Home'
    st.markdown("### Help the community! Report signal issues here.")
    st.link_button("🚀 Open Signal Reporting Form", "https://docs.google.com/forms/d/e/1FAIpQLSfmsDX0Oo2nWGt6xScoIV-X0_UPHV_qLCsYDnKQ4P07ZN5CYg/viewform")
