import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- 1. CORE LOGIC ---

def get_ai_recommendation(df, selected_location):
    try:
        df.columns = df.columns.str.strip()
        location_col = [c for c in df.columns if '70%' in c or 'Location' in c][0]
        operator_col = [c for c in df.columns if 'Operator' in c][0]
        signal_col = [c for c in df.columns if 'Signal Strength' in c][0]
        subset = df[df[location_col] == selected_location]
        if subset.empty: return f"No data for {selected_location} yet."
        subset[signal_col] = pd.to_numeric(subset[signal_col], errors='coerce')
        avg_signals = subset.groupby(operator_col)[signal_col].mean()
        best_op, strength = avg_signals.idxmax(), round(avg_signals.max(), 1)
        return f"AI Analysis: **{best_op}** is strongest at {selected_location} ({strength}/5)."
    except: return "Signal data analysis error."

def recommend_data_pack(pricing_df, budget, operator):
    try:
        pricing_df.columns = pricing_df.columns.str.strip()
        col_map = {c.lower(): c for c in pricing_df.columns}
        p_col, o_col, n_col = col_map.get('price'), col_map.get('operator'), col_map.get('plan name')
        d_col, v_col = col_map.get('data'), col_map.get('validity')

        if not all([p_col, o_col, n_col]): return "Missing columns in sheet."
        
        pricing_df[p_col] = pd.to_numeric(pricing_df[p_col], errors='coerce')
        filtered = pricing_df[(pricing_df[p_col] <= budget) & (pricing_df[o_col].str.contains(operator, case=False, na=False))]
        
        if filtered.empty: return None
        best_row = filtered.sort_values(by=p_col, ascending=False).iloc[0]
        return {"name": best_row[n_col], "price": best_row[p_col], "data": best_row[d_col] if d_col else "N/A", "validity": best_row[v_col] if v_col else "N/A"}
    except: return "Error processing data."

def display_geospatial_map(df):
    st.write("### 📍 Live Campus Signal Hotspots")
    coords = {"Engineering Block": [18.6611, 73.7176], "Management Block": [18.6612, 73.7181], "Admin Block":[18.6606, 73.7182], "Library":[18.6618, 73.7183], "Open Cafeteria": [18.6615, 73.7183], "Nescafe":[18.6609, 73.7183], "Hostel":[18.6616, 73.7162], "Amphitheatre":[18.6608, 73.7179], "Canteen": [18.6605, 73.7175], "Skill Center": [18.6607, 73.7190]}
    m = folium.Map(location=[18.6611, 73.7176], zoom_start=18)
    try:
        df.columns = df.columns.str.strip()
        l_col = [c for c in df.columns if '70%' in c or 'Location' in c][0]
        s_col = [c for c in df.columns if 'Signal Strength' in c][0]
        avg = df.groupby(l_col)[s_col].mean().reset_index()
        for _, r in avg.iterrows():
            if r[l_col] in coords:
                c = "red" if r[s_col] < 2.5 else "orange" if r[s_col] < 3.8 else "green"
                folium.Circle(location=coords[r[l_col]], radius=15, color=c, fill=True).add_to(m)
        st_folium(m, width=700, height=400)
    except: st.warning("Mapping data unavailable...")

# --- 2. THEME & STYLING ---
st.set_page_config(page_title="SymbiPlan", page_icon="📶", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important; }
    
    /* Force text visibility for labels and paragraphs */
    .stMarkdown p, .stSelectbox label, .stNumberInput label, div[data-testid="stText"] {
        color: #1E3A8A !important;
        font-weight: 600 !important;
    }
    
    /* Header styling */
    h1, h2, h3 { color: #1E3A8A !important; text-align: center; }

    /* Button styling */
    div.stButton > button {
        width: 100% !important; height: 80px !important;
        background: rgba(255, 255, 255, 0.8) !important;
        border-radius: 15px !important; color: #1E3A8A !important;
        font-weight: 700 !important; border: 1px solid rgba(255,255,255,1) !important;
        transition: 0.3s;
    }
    div.stButton > button:hover { background: white !important; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA & NAVIGATION ---
SIGNAL_URL = "https://docs.google.com/spreadsheets/d/1FVhzop8SMzmLylTPeqtm2PW2GxNbO1eTas4j7nYD__M/edit?usp=sharing"
TELECOM_URL = "https://docs.google.com/spreadsheets/d/1TFgF75B7hwHIfSp9XhBwWgvCtMq8xnve81D8k6_dNFA/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)
if 'page' not in st.session_state: st.session_state.page = 'Home'

# --- 4. HOME PAGE ---
if st.session_state.page == 'Home':
    st.markdown("<h2 style='margin-top: 0px;'>SymbiPlan</h2>", unsafe_allow_html=True)
    if st.button("🔍 SIGNAL FINDER", use_container_width=True): 
        st.session_state.page = 'Signal Finder'
    if st.button("📊 LIVE HEATMAP", use_container_width=True): 
        st.session_state.page = 'Heatmap'
    if st.button("💰 SMART RECHARGE", use_container_width=True): 
        st.session_state.page = 'Recharge'
    if st.button("📢 REPORT SIGNAL", use_container_width=True): 
        st.session_state.page = 'Report'
        
# --- 5. PAGES ---
elif st.session_state.page == 'Signal Finder':
    if st.button("⬅️ Back"): st.session_state.page = 'Home'
    st.header("🔍 Signal Finder")
    try:
        df_sig = conn.read(spreadsheet=SIGNAL_URL, ttl=60)
        loc = st.selectbox("Where are you?", ["Admin Block", "Management Block", "Engineering Block", "Skill Center", "Library", "Canteen", "Open Cafeteria", "Nescafe", "Hostel Wings", "Parking", "Amphitheater"])
        if st.button("Check Strength"): st.info(get_ai_recommendation(df_sig, loc))
    except: st.error("Failed to load signal data.")

elif st.session_state.page == 'Heatmap':
    if st.button("⬅️ Back"): st.session_state.page = 'Home'
    try:
        df_sig = conn.read(spreadsheet=SIGNAL_URL, ttl=60)
        display_geospatial_map(df_sig)
    except: st.error("Failed to load map data.")

elif st.session_state.page == 'Recharge':

    if st.button("⬅️ Back"):
        st.session_state.page = 'Home'

    st.markdown("<h2>💰 Smart Recharge</h2>", unsafe_allow_html=True)

    st.markdown(
        "<p style='text-align:center;'>Find telecom plans based on your needs.</p>",
        unsafe_allow_html=True
    )

    try:

        # Read sheet
        df_plans = conn.read(
            spreadsheet=TELECOM_URL,
            ttl=300
        )

        # Clean column names
        df_plans.columns = (
            df_plans.columns
            .str.strip()
            .str.lower()
        )

        # Detect columns
        company_col = 'company'
        plan_col = 'plan_name'
        price_col = 'price'
        daily_data_col = 'data_per_day_gb'
        total_data_col = 'data_total_gb'
        validity_col = 'validity_days'

        # Convert numeric columns
        df_plans[price_col] = pd.to_numeric(
            df_plans[price_col],
            errors='coerce'
        )

        df_plans[validity_col] = pd.to_numeric(
            df_plans[validity_col],
            errors='coerce'
        )

        df_plans[daily_data_col] = pd.to_numeric(
            df_plans[daily_data_col],
            errors='coerce'
        ).fillna(0)

        df_plans[total_data_col] = pd.to_numeric(
            df_plans[total_data_col],
            errors='coerce'
        ).fillna(0)

        # Inputs
        col1, col2, col3 = st.columns(3)

        with col1:
            budget = st.number_input(
                "💵 Budget (₹)",
                min_value=10,
                value=300,
                step=10
            )

        with col2:
            daily_need = st.number_input(
                "📶 Daily Data Need (GB)",
                min_value=0.0,
                value=1.5,
                step=0.5
            )

        with col3:
            validity_need = st.number_input(
                "📅 Minimum Validity (Days)",
                min_value=1,
                value=28,
                step=1
            )

        # Button
        if st.button("🔍 Show Plans"):

            # Filter plans
            filtered = df_plans[
                (df_plans[price_col] <= budget) &
                (df_plans[validity_col] >= validity_need) &
                (
                    (df_plans[daily_data_col] >= daily_need)
                    |
                    (
                        (
                            df_plans[total_data_col]
                            /
                            df_plans[validity_col]
                        ) >= daily_need
                    )
                )
            ].copy()

            if filtered.empty:

                st.warning("❌ No matching plans found.")

            else:

                filtered = filtered.sort_values(
                    by=price_col
                )

                st.success(
                    f"✅ Found {len(filtered)} matching plans"
                )

                for _, row in filtered.iterrows():

                    # Data display
                    if row[daily_data_col] > 0:
                        data_info = (
                            f"{row[daily_data_col]} GB/day"
                        )
                    else:
                        data_info = (
                            f"{row[total_data_col]} GB Total"
                        )

                    st.markdown("---")

                    st.markdown(f"""
                    ### 📱 {row[company_col]}

                    📦 **Plan:** {row[plan_col]}

                    💰 **Price:** ₹{row[price_col]}

                    📶 **Data:** {data_info}

                    📅 **Validity:** {row[validity_col]} Days

                    📞 **Calls:** {row['calls']}

                    ✉️ **SMS:** {row['sms']}
                    """)

    except Exception as e:

        st.error("Connection Error")
        st.exception(e)
        
elif st.session_state.page == 'Report':
    if st.button("⬅️ Back"): st.session_state.page = 'Home'
    st.link_button("Open Signal Form", "https://docs.google.com/forms/d/e/1FAIpQLSfmsDX0Oo2nWGt6xScoIV-X0_UPHV_qLCsYDnKQ4P07ZN5CYg/viewform")
