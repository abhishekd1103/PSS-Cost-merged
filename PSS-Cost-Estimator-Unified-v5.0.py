import streamlit as st
import pandas as pd
import numpy as np
import math
import datetime

# Page configuration
st.set_page_config(
    page_title="DC Power Studies Cost Estimator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════════════════════════
# ACCURATE BUS COUNT CALCULATION FUNCTION (FROM DC_BUS_QUANTITY_ESTIMATER)
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_bus_count_accurate(
    it_capacity,
    mechanical_load,
    house_load,
    tier_level,
    pue=1.56,
    mech_fraction=0.70,
    ups_lineup=1.5,
    transformer_mva=3.0,
    lv_bus_mw=3.0,
    pdu_mva=0.3,
    mv_base=2,
    utility_incomers=1,
    power_factor=0.95,
    voltage_levels=2,
    backup_gens=0,
    expansion_factor=1.0,
    bus_calibration=1.0
):
    """
    Calculate bus count using component-by-component engineering method.
    Integrated from DC_Bus_Quantity_Estimater with calibration factor.
    
    Returns:
        int: Estimated bus count (rounded up)
    """
    
    # ─────────────────────────────────────────────────────────────────────
    # PHASE 1: LOAD DERIVATION (CORRECT METHOD)
    # ─────────────────────────────────────────────────────────────────────
    calc_total_mw = pue * it_capacity
    calc_it_mw = it_capacity
    non_it_mw = calc_total_mw - calc_it_mw
    
    mech_mw = mech_fraction * non_it_mw
    house_mw = non_it_mw - mech_mw
    
    # ─────────────────────────────────────────────────────────────────────
    # PHASE 2: COMPONENT COUNTING (EQUIPMENT-BASED)
    # ─────────────────────────────────────────────────────────────────────
    
    lv_it_pcc = math.ceil(calc_it_mw / lv_bus_mw)
    lv_mech_mcc = math.ceil(mech_mw / lv_bus_mw)
    lv_house_pcc = math.ceil(house_mw / lv_bus_mw)
    lv_total = lv_it_pcc + lv_mech_mcc + lv_house_pcc
    
    ups_lineups = math.ceil(calc_it_mw / ups_lineup)
    ups_output_buses = ups_lineups
    
    pdus_total = math.ceil(calc_it_mw / pdu_mva)
    
    tx_count_n = math.ceil(calc_total_mw / (transformer_mva * power_factor))
    
    mv_buses = mv_base + (utility_incomers - 1)
    
    voltage_additions = 0
    if voltage_levels > 2:
        voltage_additions = (voltage_levels - 2) * (tx_count_n + 1)
    
    generator_additions = backup_gens * 2 if backup_gens > 0 else 0
    
    # ─────────────────────────────────────────────────────────────────────
    # PHASE 3: REDUNDANCY MODELING (TIER-BASED)
    # ─────────────────────────────────────────────────────────────────────
    
    buses_core_n = (mv_buses + tx_count_n + lv_total + 
                   ups_output_buses + pdus_total + 
                   voltage_additions + generator_additions)
    
    if tier_level == "Tier I":
        total_buses = buses_core_n * expansion_factor
        
    elif tier_level == "Tier II":
        tx_count_adj = tx_count_n + 1
        buses_adj = (mv_buses + tx_count_adj + lv_total + 
                    ups_output_buses + pdus_total + 
                    voltage_additions + generator_additions)
        total_buses = buses_adj * expansion_factor * 1.10
        
    elif tier_level == "Tier III":
        tx_count_adj = tx_count_n + 1
        buses_adj = (mv_buses + tx_count_adj + lv_total + 
                    ups_output_buses + pdus_total + 
                    voltage_additions + generator_additions)
        total_buses = buses_adj * expansion_factor * 1.15
        
    elif tier_level == "Tier IV":
        mv_2n = mv_buses * 2
        tx_2n = tx_count_n * 2
        lv_2n = lv_total * 2
        ups_2n = ups_output_buses * 2
        pdus_2n = int(pdus_total * 1.5)
        extras_2n = (voltage_additions + generator_additions) * 2
        
        buses_2n = mv_2n + tx_2n + lv_2n + ups_2n + pdus_2n + extras_2n
        total_buses = buses_2n * expansion_factor
    
    else:
        tx_count_adj = tx_count_n + 1
        buses_adj = (mv_buses + tx_count_adj + lv_total + 
                    ups_output_buses + pdus_total + 
                    voltage_additions + generator_additions)
        total_buses = buses_adj * expansion_factor * 1.15
    
    # Apply calibration factor
    total_buses = total_buses * bus_calibration
    
    return max(1, math.ceil(total_buses))


# ═══════════════════════════════════════════════════════════════════════════════
# PROFESSIONAL DARK THEME CSS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .main > div {
        padding-top: 0.5rem;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
        color: #e2e8f0;
    }
    
    .main-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(51, 65, 85, 0.9) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(59, 130, 246, 0.2);
        padding: 2.5rem;
        border-radius: 16px;
        color: #f1f5f9;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #3b82f6, #06b6d4);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
    }
    
    .main-header h2 {
        font-size: 1.2rem;
        font-weight: 400;
        margin: 1rem 0 0 0;
        color: #94a3b8;
    }
    
    .developer-credit {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        padding: 1rem 2rem;
        border-radius: 12px;
        color: #f1f5f9;
        text-align: center;
        font-weight: 600;
        margin: 1rem 0 2rem 0;
        backdrop-filter: blur(10px);
    }
    
    .section-header {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(59, 130, 246, 0.3);
        color: #f1f5f9;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin: 2rem 0 1.5rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
    
    .section-header h2 {
        margin: 0;
        font-size: 1.3rem;
        font-weight: 700;
        color: #3b82f6;
    }
    
    .metric-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2);
        border-color: rgba(59, 130, 246, 0.4);
    }
    
    .metric-card h3 {
        color: #64748b;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0 0 0.5rem 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card .value {
        color: #3b82f6;
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        line-height: 1;
    }
    
    .metric-card .subtitle {
        color: #64748b;
        font-size: 0.8rem;
        margin: 0.5rem 0 0 0;
    }
    
    .study-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(71, 85, 105, 0.3);
        border-radius: 12px;
        padding: 2rem;
        margin: 1.5rem 0;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
    
    .study-card:hover {
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.15);
    }
    
    .study-card h4 {
        color: #f1f5f9;
        font-size: 1.2rem;
        font-weight: 700;
        margin: 0 0 1rem 0;
    }
    
    .study-details {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 2rem;
        margin-top: 1rem;
        align-items: center;
    }
    
    .study-detail-item {
        color: #cbd5e1;
        font-size: 0.9rem;
        line-height: 1.7;
        font-weight: 500;
    }
    
    .study-detail-item strong {
        color: #f1f5f9;
        font-weight: 600;
    }
    
    .cost-highlight {
        background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    
    .cost-highlight .amount {
        font-size: 1.4rem;
        font-weight: 800;
        margin: 0;
    }
    
    .results-container {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 2.5rem;
        margin: 2rem 0;
        backdrop-filter: blur(15px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    .stSelectbox > div > div,
    .stNumberInput > div > div > input,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        border-radius: 8px !important;
        color: #f1f5f9 !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stSelectbox > div > div:focus-within,
    .stNumberInput > div > div > input:focus,
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }
    
    .stCheckbox > label {
        color: #e2e8f0 !important;
        font-weight: 500 !important;
    }
    
    .stSlider > div > div > div {
        color: #3b82f6 !important;
    }
    
    .disclaimer-box {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
        backdrop-filter: blur(10px);
    }
    
    .disclaimer-box h4 {
        color: #f59e0b;
        margin: 0 0 1rem 0;
        font-weight: 700;
    }
    
    .disclaimer-box p {
        color: #fbbf24;
        margin: 0.8rem 0;
        line-height: 1.6;
        font-weight: 500;
    }
    
    .model-section {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
        backdrop-filter: blur(10px);
    }
    
    .work-allocation-section {
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
        backdrop-filter: blur(10px);
    }
    
    .custom-cost-section {
        background: rgba(236, 72, 153, 0.1);
        border: 1px solid rgba(236, 72, 153, 0.3);
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
        backdrop-filter: blur(10px);
    }
    
    .scope-section {
        background: rgba(168, 85, 247, 0.1);
        border: 1px solid rgba(168, 85, 247, 0.3);
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
        backdrop-filter: blur(10px);
    }
    
    .summary-section {
        background: rgba(15, 23, 42, 0.9);
        border: 2px solid rgba(59, 130, 246, 0.4);
        border-radius: 16px;
        padding: 3rem;
        margin: 3rem 0;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
    }
    
    .final-total-section {
        background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
        border-radius: 16px;
        padding: 2.5rem;
        text-align: center;
        color: white;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
        margin: 2rem 0;
    }
    
    .cost-category-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .cost-category-card:hover {
        border-color: rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    .stMarkdown, h1, h2, h3, h4, h5, h6 {
        color: #e2e8f0 !important;
    }
    
    .stRadio > div > label > div {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

if 'studies_selected' not in st.session_state:
    st.session_state.studies_selected = {
        'load_flow': True,
        'short_circuit': True,
        'pdc': True,
        'arc_flash': True,
        'harmonics': False,
        'transient': False
    }

if 'work_allocation' not in st.session_state:
    st.session_state.work_allocation = {
        'senior': 20,
        'mid': 30,
        'junior': 50
    }

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="main-header">
    <h1>Data Center Power System Studies - Cost Estimation</h1>
    <h2>Unified PSS Cost Estimation Platform v5.0</h2>
    <p>Professional Solution with Accurate Bus Count & Enhanced Costing</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="developer-credit">
    Developed by <strong>Abhishek Diwanji</strong> | Power Systems Studies Department
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# DISCLAIMER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="disclaimer-box">
    <h4>❗Important Note - Version 5.0</h4>
    <p><strong>Bus Count Calculation:</strong> This version integrates accurate component-based bus count calculation from the DC Bus Quantity Estimator. Bus counts now use engineering-based methodology with proper redundancy modeling.</p>
    <p><strong>Professional Application:</strong> Results are estimates based on industry standards. Always validate with qualified electrical engineers for actual project implementation.</p>
    <p><strong>Costing Accuracy:</strong> All existing costing formulas and rate structures have been preserved. Only bus count calculation methodology has been enhanced.</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

with st.container():
    # Project Information Section
    st.markdown("""
    <div class="section-header">
        <h2>📋 Project Information</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        project_name = st.text_input("Project Name", value="Project-Alpha")
        tier_level = st.selectbox("Tier Level", ["Tier I", "Tier II", "Tier III", "Tier IV"], index=3)
    with col2:
        it_capacity = st.number_input("IT Capacity (MW)", min_value=0.0, max_value=200.0, value=10.0, step=0.1)
        delivery_type = st.selectbox("Delivery Type", ["Standard", "Urgent"])
    with col3:
        mechanical_load = st.number_input("Mechanical Load (MW)", min_value=0.0, max_value=100.0, value=7.0, step=0.1)
        report_complexity = st.selectbox("Report Complexity", ["Basic", "Standard", "Premium"], index=1)
    with col4:
        house_load = st.number_input("House/Auxiliary Load (MW)", min_value=0.0, max_value=50.0, value=3.0, step=0.1)
        client_meetings = st.number_input("Client Meetings", min_value=0, max_value=20, value=3, step=1)

    # Customer Type Section
    st.markdown("""
    <div class="section-header">
        <h2>👤 Customer Information</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        customer_type = st.selectbox("Customer Type", ["New Customer", "Repeat Customer"])
    with col6:
        if customer_type == "Repeat Customer":
            repeat_discount = st.slider("Repeat Customer Discount (%)", 0, 25, 10, 1)
        else:
            repeat_discount = 0
    with col7:
        custom_margin = st.number_input("Project Margins (%)", min_value=0, max_value=50, value=15, step=1)
    with col8:
        pue_value = st.slider("PUE (Power Usage Effectiveness)", 1.1, 2.0, 1.56, 0.01)

    # ═══════════════════════════════════════════════════════════════════════════════
    # NEW: BUS COUNT CALCULATION METHOD TOGGLE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("""
    <div class="section-header">
        <h2>🔧 Bus Count Calculation Configuration</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="model-section">', unsafe_allow_html=True)
        
        bus_method_col1, bus_method_col2 = st.columns([2, 2])
        
        with bus_method_col1:
            st.markdown("**🎯 Bus Count Calculation Method**")
            use_custom_blocks = st.checkbox(
                "Enable Custom Equipment Block Sizing",
                value=False,
                help="Toggle ON to enter custom equipment capacities. Toggle OFF to use industry-standard block sizes."
            )
            
            if use_custom_blocks:
                st.info("✅ **Custom Block Sizing Enabled** - Enter your specific equipment capacities below")
            else:
                st.info("🔧 **Standard Block Sizing** - Using industry-standard equipment capacities")
        
        with bus_method_col2:
            st.markdown("**⚙️ Bus Count Calibration Factor**")
            bus_calibration = st.slider(
                "Calibration Multiplier",
                min_value=0.5,
                max_value=2.5,
                value=1.0,
                step=0.05,
                help="Fine-tune bus count estimate. 1.0 = no adjustment. >1.0 increases count, <1.0 decreases count."
            )
            if bus_calibration != 1.0:
                st.warning(f"⚠️ Calibration factor: **{bus_calibration}x** applied to bus count")
            else:
                st.success("✓ No calibration adjustment (1.0x)")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Equipment Block Sizing (Conditional Display)
    if use_custom_blocks:
        st.markdown("""
        <div class="section-header">
            <h2>🔩 Custom Equipment Block Capacities</h2>
        </div>
        """, unsafe_allow_html=True)
        
        equip_col1, equip_col2, equip_col3, equip_col4, equip_col5 = st.columns(5)
        
        with equip_col1:
            ups_lineup = st.slider("UPS Lineup (MW)", 0.5, 3.0, 1.5, 0.1)
        with equip_col2:
            transformer_mva = st.slider("Transformer (MVA)", 1.0, 5.0, 3.0, 0.1)
        with equip_col3:
            lv_bus_mw = st.slider("LV Bus Section (MW)", 2.0, 5.0, 3.0, 0.1)
        with equip_col4:
            pdu_mva = st.slider("PDU Capacity (MVA)", 0.2, 0.8, 0.3, 0.05)
        with equip_col5:
            power_factor = st.slider("Power Factor", 0.90, 1.0, 0.95, 0.01)
    else:
        # Use standard values
        ups_lineup = 1.5
        transformer_mva = 3.0
        lv_bus_mw = 3.0
        pdu_mva = 0.3
        power_factor = 0.95

    # Model Type & Hour Reduction Section
    st.markdown("""
    <div class="section-header">
        <h2>📐 Model Type & Hour Reduction</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="model-section">', unsafe_allow_html=True)
        
        model_col1, model_col2 = st.columns([2, 2])
        
        with model_col1:
            st.markdown("**Select Model Type**")
            model_type = st.radio(
                "Model Type",
                ["Typical Model", "ETAP Model Available"],
                index=0,
                help="ETAP Model reduces manhours due to existing system models"
            )
        
        with model_col2:
            st.markdown("**Hour Reduction Factor**")
            if model_type == "ETAP Model Available":
                hour_reduction = st.slider(
                    "Hour Reduction (%)",
                    min_value=10,
                    max_value=90,
                    value=30,
                    step=5,
                    help="Percentage reduction in manhours when ETAP model is available"
                )
                st.info(f"🎯 **{hour_reduction}% reduction** will be applied to total manhours")
            else:
                hour_reduction = 0
                st.info("🔧 **No reduction** - Using typical modeling approach")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Studies Selection Section
    st.markdown("""
    <div class="section-header">
        <h2>📊 Studies Configuration</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col_studies1, col_studies2 = st.columns([3, 1])
    
    with col_studies1:
        study_col1, study_col2, study_col3 = st.columns(3)
        
        with study_col1:
            st.session_state.studies_selected['load_flow'] = st.checkbox(
                "Load Flow Study",
                value=st.session_state.studies_selected['load_flow'],
                key="load_flow_cb"
            )
            st.session_state.studies_selected['short_circuit'] = st.checkbox(
                "Short Circuit Study",
                value=st.session_state.studies_selected['short_circuit'],
                key="short_circuit_cb"
            )
        
        with study_col2:
            st.session_state.studies_selected['pdc'] = st.checkbox(
                "Protective Device Coordination",
                value=st.session_state.studies_selected['pdc'],
                key="pdc_cb"
            )
            st.session_state.studies_selected['arc_flash'] = st.checkbox(
                "Arc Flash Study",
                value=st.session_state.studies_selected['arc_flash'],
                key="arc_flash_cb"
            )
        
        with study_col3:
            st.session_state.studies_selected['harmonics'] = st.checkbox(
                "Harmonics Study",
                value=st.session_state.studies_selected['harmonics'],
                key="harmonics_cb"
            )
            st.session_state.studies_selected['transient'] = st.checkbox(
                "Transient Analysis",
                value=st.session_state.studies_selected['transient'],
                key="transient_cb"
            )
    
    with col_studies2:
        if st.button("Select All Studies", key="select_all_studies"):
            for key in st.session_state.studies_selected:
                st.session_state.studies_selected[key] = True
            st.rerun()
        
        if st.button("Clear All Studies", key="clear_all_studies"):
            for key in st.session_state.studies_selected:
                st.session_state.studies_selected[key] = False
            st.rerun()

    # Work Allocation Section
    st.markdown("""
    <div class="section-header">
        <h2>👥 Work Allocation Configuration</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="work-allocation-section">', unsafe_allow_html=True)
        
        alloc_col1, alloc_col2, alloc_col3, alloc_col4 = st.columns(4)
        
        with alloc_col1:
            st.session_state.work_allocation['senior'] = st.slider(
                "Senior Engineer (%)", 
                5, 50, st.session_state.work_allocation['senior'], 1
            )
        
        with alloc_col2:
            st.session_state.work_allocation['mid'] = st.slider(
                "Mid-level Engineer (%)", 
                10, 60, st.session_state.work_allocation['mid'], 1
            )
        
        with alloc_col3:
            st.session_state.work_allocation['junior'] = st.slider(
                "Junior Engineer (%)", 
                10, 70, st.session_state.work_allocation['junior'], 1
            )
        
        with alloc_col4:
            if st.button("Auto Balance (20:30:50)", key="auto_balance"):
                st.session_state.work_allocation = {'senior': 20, 'mid': 30, 'junior': 50}
                st.rerun()
        
        # Normalize allocations
        total_allocation = sum(st.session_state.work_allocation.values())
        if total_allocation != 100:
            factor = 100 / total_allocation
            for key in st.session_state.work_allocation:
                st.session_state.work_allocation[key] = round(st.session_state.work_allocation[key] * factor, 1)
        
        st.success(f"✅ Current Allocation: Senior {st.session_state.work_allocation['senior']:.1f}% | Mid {st.session_state.work_allocation['mid']:.1f}% | Junior {st.session_state.work_allocation['junior']:.1f}%")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Rate Configuration Section
    st.markdown("""
    <div class="section-header">
        <h2>💰 Rate Configuration</h2>
    </div>
    """, unsafe_allow_html=True)
    
    rate_col1, rate_col2, rate_col3 = st.columns(3)
    
    with rate_col1:
        st.markdown("**Hourly Rates (₹)**")
        senior_rate = st.number_input("Senior Engineer Rate", min_value=1000, max_value=8000, value=2200, step=50)
        mid_rate = st.number_input("Mid-level Engineer Rate", min_value=500, max_value=5000, value=1200, step=25)
        junior_rate = st.number_input("Junior Engineer Rate", min_value=300, max_value=2000, value=800, step=25)
    
    with rate_col2:
        st.markdown("**Study Complexity Factors**")
        load_flow_factor = st.slider("Load Flow Factor", 0.3, 3.0, 1.0, 0.1)
        short_circuit_factor = st.slider("Short Circuit Factor", 0.3, 3.0, 1.0, 0.1)
        pdc_factor = st.slider("PDC Factor", 0.3, 3.0, 1.0, 0.1)
        arc_flash_factor = st.slider("Arc Flash Factor", 0.3, 3.0, 1.0, 0.1)
    
    with rate_col3:
        st.markdown("**Additional Study Factors**")
        harmonics_factor = st.slider("Harmonics Factor", 0.3, 3.0, 1.2, 0.1)
        transient_factor = st.slider("Transient Factor", 0.3, 3.0, 1.3, 0.1)
        urgency_multiplier = st.slider("Urgent Delivery Multiplier", 1.0, 3.0, 1.3, 0.1)
        meeting_cost = st.number_input("Cost per Meeting (₹)", min_value=2000, max_value=25000, value=8000, step=500)

    # Report Costs Section
    st.markdown("""
    <div class="section-header">
        <h2>📄 Report Configuration</h2>
    </div>
    """, unsafe_allow_html=True)
    
    report_col1, report_col2, report_col3 = st.columns(3)
    
    with report_col1:
        load_flow_report_cost = st.number_input("Load Flow Report Cost (₹)", min_value=0, max_value=150000, value=8000, step=500)
        short_circuit_report_cost = st.number_input("Short Circuit Report Cost (₹)", min_value=0, max_value=150000, value=10000, step=500)
    with report_col2:
        pdc_report_cost = st.number_input("PDC Report Cost (₹)", min_value=0, max_value=150000, value=15000, step=500)
        arc_flash_report_cost = st.number_input("Arc Flash Report Cost (₹)", min_value=0, max_value=150000, value=12000, step=500)
    with report_col3:
        harmonics_report_cost = st.number_input("Harmonics Report Cost (₹)", min_value=0, max_value=150000, value=11000, step=500)
        transient_report_cost = st.number_input("Transient Report Cost (₹)", min_value=0, max_value=150000, value=13000, step=500)

    # Additional Services Section
    st.markdown("""
    <div class="section-header">
        <h2>➕ Additional Services</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="custom-cost-section">', unsafe_allow_html=True)
        
        custom_col1, custom_col2, custom_col3, custom_col4 = st.columns(4)
        
        with custom_col1:
            site_visit_enabled = st.checkbox("Site Visits Required", value=True)
            if site_visit_enabled:
                site_visits = st.number_input("Number of Site Visits", min_value=0, max_value=20, value=2, step=1)
                site_visit_cost = st.number_input("Cost per Site Visit (₹)", min_value=0, max_value=50000, value=12000, step=500)
            else:
                site_visits = 0
                site_visit_cost = 0
        
        with custom_col2:
            af_labels_enabled = st.checkbox("Arc Flash Labels Required", value=False)
            if af_labels_enabled:
                num_labels = st.number_input("Number of Labels", min_value=0, max_value=500, value=50, step=1)
                cost_per_label = st.number_input("Cost per Label (₹)", min_value=0, max_value=500, value=150, step=10)
            else:
                num_labels = 0
                cost_per_label = 0
        
        with custom_col3:
            stickering_enabled = st.checkbox("Equipment Stickering Required", value=False)
            if stickering_enabled:
                stickering_cost = st.number_input("Stickering Cost (₹)", min_value=0, max_value=100000, value=25000, step=1000)
            else:
                stickering_cost = 0
        
        with custom_col4:
            st.markdown("**Custom Charges**")
            custom_charges_desc = st.text_input("Description", value="Additional Services", placeholder="Enter description")
            custom_charges_cost = st.number_input("Custom Charges (₹)", min_value=0, max_value=500000, value=0, step=1000)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # NEW: CUSTOM COST SECTIONS (2 ADDITIONAL)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("""
    <div class="section-header">
        <h2>💼 Custom Cost Sections</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="custom-cost-section">', unsafe_allow_html=True)
        
        custom_cost_col1, custom_cost_col2 = st.columns(2)
        
        with custom_cost_col1:
            st.markdown("**Custom Cost Item 1**")
            custom_cost_1_desc = st.text_area(
                "Description/Remark (Editable)",
                value="Custom Engineering Services",
                height=80,
                key="custom_cost_1_desc"
            )
            custom_cost_1_amount = st.number_input(
                "Amount (₹)",
                min_value=0,
                max_value=1000000,
                value=0,
                step=1000,
                key="custom_cost_1_amount"
            )
        
        with custom_cost_col2:
            st.markdown("**Custom Cost Item 2**")
            custom_cost_2_desc = st.text_area(
                "Description/Remark (Editable)",
                value="Specialized Testing & Validation",
                height=80,
                key="custom_cost_2_desc"
            )
            custom_cost_2_amount = st.number_input(
                "Amount (₹)",
                min_value=0,
                max_value=1000000,
                value=0,
                step=1000,
                key="custom_cost_2_amount"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # NEW: SCOPE DESCRIPTION SECTION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("""
    <div class="section-header">
        <h2>📝 Project Scope Description</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="scope-section">', unsafe_allow_html=True)
        
        scope_description = st.text_area(
            "Scope of Work (Editable)",
            value="""This project includes comprehensive power system studies for a data center facility:

• Complete electrical system modeling and analysis
• Detailed study reports with recommendations
• Client presentations and technical meetings
• Equipment coordination and protection settings
• Arc flash hazard analysis and labeling
• Compliance with IEEE, NFPA, and NEC standards

All deliverables will be provided in digital format with professional documentation.""",
            height=200,
            help="Enter detailed scope description, exclusions, deliverables, and assumptions"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ENGINEERING CALCULATIONS & RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="section-header">
    <h2>⚙️ Engineering Calculations & Results</h2>
</div>
""", unsafe_allow_html=True)

# Calculate bus count using accurate method
estimated_buses = calculate_bus_count_accurate(
    it_capacity=it_capacity,
    mechanical_load=mechanical_load,
    house_load=house_load,
    tier_level=tier_level,
    pue=pue_value,
    ups_lineup=ups_lineup,
    transformer_mva=transformer_mva,
    lv_bus_mw=lv_bus_mw,
    pdu_mva=pdu_mva,
    power_factor=power_factor,
    bus_calibration=bus_calibration
)

# Study complexity factors
tier_complexity_factors = {"Tier I": 1.0, "Tier II": 1.2, "Tier III": 1.5, "Tier IV": 2.0}
tier_complexity = tier_complexity_factors[tier_level]

# Work allocation percentages
senior_allocation = st.session_state.work_allocation['senior'] / 100
mid_allocation = st.session_state.work_allocation['mid'] / 100
junior_allocation = st.session_state.work_allocation['junior'] / 100

# Study definitions (EXPANDED WITH HARMONICS AND TRANSIENT)
studies_data = {
    'load_flow': {
        'name': 'Load Flow Study',
        'base_hours_per_bus': 0.8,
        'factor': load_flow_factor,
        'report_cost': load_flow_report_cost
    },
    'short_circuit': {
        'name': 'Short Circuit Study',
        'base_hours_per_bus': 1.0,
        'factor': short_circuit_factor,
        'report_cost': short_circuit_report_cost
    },
    'pdc': {
        'name': 'Protective Device Coordination',
        'base_hours_per_bus': 1.5,
        'factor': pdc_factor,
        'report_cost': pdc_report_cost
    },
    'arc_flash': {
        'name': 'Arc Flash Study',
        'base_hours_per_bus': 1.2,
        'factor': arc_flash_factor,
        'report_cost': arc_flash_report_cost
    },
    'harmonics': {
        'name': 'Harmonics Analysis',
        'base_hours_per_bus': 1.0,
        'factor': harmonics_factor,
        'report_cost': harmonics_report_cost
    },
    'transient': {
        'name': 'Transient Stability Analysis',
        'base_hours_per_bus': 1.1,
        'factor': transient_factor,
        'report_cost': transient_report_cost
    }
}

# Calculate study costs with hour reduction
total_study_hours = 0
total_study_cost = 0
total_report_cost = 0
study_results = {}

for study_key, study_data in studies_data.items():
    if st.session_state.studies_selected.get(study_key, False):
        # Calculate base study hours
        base_study_hours = estimated_buses * study_data['base_hours_per_bus'] * study_data['factor'] * tier_complexity
        
        # Apply hour reduction if ETAP model is available
        if model_type == "ETAP Model Available":
            study_hours = base_study_hours * (1 - hour_reduction/100)
            hours_saved = base_study_hours - study_hours
        else:
            study_hours = base_study_hours
            hours_saved = 0
        
        total_study_hours += study_hours
        
        # Resource allocation
        senior_hours = study_hours * senior_allocation
        mid_hours = study_hours * mid_allocation
        junior_hours = study_hours * junior_allocation
        
        # Apply multipliers
        rate_multiplier = urgency_multiplier if delivery_type == "Urgent" else 1.0
        discount_multiplier = (1 - repeat_discount/100) if customer_type == "Repeat Customer" else 1.0
        
        # Calculate costs
        senior_cost = senior_hours * senior_rate * rate_multiplier * discount_multiplier
        mid_cost = mid_hours * mid_rate * rate_multiplier * discount_multiplier
        junior_cost = junior_hours * junior_rate * rate_multiplier * discount_multiplier
        
        study_total_cost = senior_cost + mid_cost + junior_cost
        total_study_cost += study_total_cost
        
        # Report cost
        report_multipliers = {"Basic": 0.8, "Standard": 1.0, "Premium": 1.5}
        study_report_cost = study_data['report_cost'] * report_multipliers[report_complexity]
        total_report_cost += study_report_cost
        
        study_results[study_key] = {
            'name': study_data['name'],
            'base_hours': base_study_hours,
            'hours': study_hours,
            'hours_saved': hours_saved,
            'senior_hours': senior_hours,
            'mid_hours': mid_hours,
            'junior_hours': junior_hours,
            'senior_cost': senior_cost,
            'mid_cost': mid_cost,
            'junior_cost': junior_cost,
            'total_cost': study_total_cost,
            'report_cost': study_report_cost
        }

# Calculate additional costs
total_site_visit_cost = site_visits * site_visit_cost if site_visit_enabled else 0
total_label_cost = num_labels * cost_per_label if af_labels_enabled else 0
total_meeting_cost = client_meetings * meeting_cost
total_additional_costs = (total_site_visit_cost + total_label_cost + 
                         stickering_cost + custom_charges_cost + 
                         custom_cost_1_amount + custom_cost_2_amount)

# Final calculations
subtotal = total_study_cost + total_meeting_cost + total_report_cost + total_additional_costs
total_cost = subtotal * (1 + custom_margin/100)

# Calculate total hours saved
total_hours_saved = sum(study['hours_saved'] for study in study_results.values())

# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

if study_results:
    # Main metrics display
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>IT Load</h3>
            <p class="value">{it_capacity:.1f}</p>
            <p class="subtitle">MW</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Bus Count</h3>
            <p class="value">{estimated_buses}</p>
            <p class="subtitle">buses</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total Hours</h3>
            <p class="value">{total_study_hours:.0f}</p>
            <p class="subtitle">eng hours</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Hours Saved</h3>
            <p class="value">{total_hours_saved:.0f}</p>
            <p class="subtitle">{model_type[:7]}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Studies</h3>
            <p class="value">{len(study_results)}</p>
            <p class="subtitle">selected</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Discount</h3>
            <p class="value">{repeat_discount}%</p>
            <p class="subtitle">{customer_type.split()[0]}</p>
        </div>
        """, unsafe_allow_html=True)

    # Bus Count Calculation Method Info
    if use_custom_blocks:
        st.info(f"🔧 **Bus Count Method**: Custom block sizing with {bus_calibration}x calibration | UPS: {ups_lineup}MW | TX: {transformer_mva}MVA | LV: {lv_bus_mw}MW | PDU: {pdu_mva}MVA")
    else:
        st.info(f"🔧 **Bus Count Method**: Standard block sizing with {bus_calibration}x calibration | PUE: {pue_value} | Tier: {tier_level}")

    # Model Type Impact Display
    if model_type == "ETAP Model Available" and total_hours_saved > 0:
        savings_amount = total_hours_saved * ((senior_rate * senior_allocation) + (mid_rate * mid_allocation) + (junior_rate * junior_allocation))
        st.success(f"🎯 **ETAP Model Benefit**: {hour_reduction}% reduction saved {total_hours_saved:.0f} hours (₹{savings_amount:,.0f})")

    # Study-wise breakdown
    st.markdown("### 📊 Study-wise Cost Analysis")
    
    for study_key, study in study_results.items():
        reduction_info = ""
        if study['hours_saved'] > 0:
            reduction_info = f"<br><span style='color: #10b981; font-weight: 600;'>Hours Saved: {study['hours_saved']:.1f}h ({hour_reduction}% reduction)</span>"
        
        st.markdown(f"""
        <div class="study-card">
            <h4>{study['name']}</h4>
            <p style="color: #94a3b8; margin: 0 0 1rem 0; font-weight: 500;">
                {study['hours']:.1f} total engineering hours{reduction_info}
            </p>
            <div class="study-details">
                <div class="study-detail-item">
                    <strong>Senior Engineer:</strong> {study['senior_hours']:.1f}h × ₹{senior_rate:,}/hr = ₹{study['senior_cost']:,.0f}<br>
                    <strong>Mid-level Engineer:</strong> {study['mid_hours']:.1f}h × ₹{mid_rate:,}/hr = ₹{study['mid_cost']:,.0f}<br>
                    <strong>Junior Engineer:</strong> {study['junior_hours']:.1f}h × ₹{junior_rate:,}/hr = ₹{study['junior_cost']:,.0f}<br>
                    <strong>Report Cost ({report_complexity}):</strong> ₹{study['report_cost']:,.0f}
                </div>
                <div class="cost-highlight">
                    <p class="amount">₹{study['total_cost'] + study['report_cost']:,.0f}</p>
                    <small>Total Study Cost</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Final Cost Summary Grid
    st.markdown("### 💰 Cost Breakdown")
    
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    
    with summary_col1:
        st.markdown(f"""
        <div class="cost-category-card">
            <h4 style="color: #3b82f6; margin: 0; font-weight: 700;">Studies</h4>
            <p style="color: #f1f5f9; font-size: 1.4rem; font-weight: 700; margin: 0.5rem 0;">₹{total_study_cost:,.0f}</p>
            <p style="color: #64748b; margin: 0; font-size: 0.8rem;">Engineering Services</p>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col2:
        st.markdown(f"""
        <div class="cost-category-card">
            <h4 style="color: #06b6d4; margin: 0; font-weight: 700;">Reports</h4>
            <p style="color: #f1f5f9; font-size: 1.4rem; font-weight: 700; margin: 0.5rem 0;">₹{total_report_cost:,.0f}</p>
            <p style="color: #64748b; margin: 0; font-size: 0.8rem;">{report_complexity} Format</p>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col3:
        st.markdown(f"""
        <div class="cost-category-card">
            <h4 style="color: #8b5cf6; margin: 0; font-weight: 700;">Meetings</h4>
            <p style="color: #f1f5f9; font-size: 1.4rem; font-weight: 700; margin: 0.5rem 0;">₹{total_meeting_cost:,.0f}</p>
            <p style="color: #64748b; margin: 0; font-size: 0.8rem;">{client_meetings} Sessions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col4:
        st.markdown(f"""
        <div class="cost-category-card">
            <h4 style="color: #ec4899; margin: 0; font-weight: 700;">Additional</h4>
            <p style="color: #f1f5f9; font-size: 1.4rem; font-weight: 700; margin: 0.5rem 0;">₹{total_additional_costs:,.0f}</p>
            <p style="color: #64748b; margin: 0; font-size: 0.8rem;">Extra Services</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Additional Services Breakdown
    if total_additional_costs > 0:
        st.markdown("### 📋 Additional Services Detail")
        
        add_serv_col1, add_serv_col2, add_serv_col3, add_serv_col4 = st.columns(4)
        
        with add_serv_col1:
            if total_site_visit_cost > 0:
                st.info(f"**Site Visits**: {site_visits} × ₹{site_visit_cost:,} = ₹{total_site_visit_cost:,.0f}")
        
        with add_serv_col2:
            if total_label_cost > 0:
                st.info(f"**Arc Flash Labels**: {num_labels} × ₹{cost_per_label:,} = ₹{total_label_cost:,.0f}")
        
        with add_serv_col3:
            if stickering_cost > 0:
                st.info(f"**Equipment Stickering**: ₹{stickering_cost:,.0f}")
        
        with add_serv_col4:
            if custom_charges_cost > 0:
                st.info(f"**{custom_charges_desc}**: ₹{custom_charges_cost:,.0f}")
        
        # Custom Cost Items
        if custom_cost_1_amount > 0 or custom_cost_2_amount > 0:
            custom_detail_col1, custom_detail_col2 = st.columns(2)
            
            with custom_detail_col1:
                if custom_cost_1_amount > 0:
                    st.info(f"**Custom Item 1**: {custom_cost_1_desc[:50]}... = ₹{custom_cost_1_amount:,.0f}")
            
            with custom_detail_col2:
                if custom_cost_2_amount > 0:
                    st.info(f"**Custom Item 2**: {custom_cost_2_desc[:50]}... = ₹{custom_cost_2_amount:,.0f}")

    # Cost Breakdown
    breakdown_col1, breakdown_col2, breakdown_col3 = st.columns(3)
    
    with breakdown_col1:
        st.info(f"**Subtotal**: ₹{subtotal:,.0f}")
    
    with breakdown_col2:
        st.info(f"**Margin ({custom_margin}%)**: ₹{total_cost - subtotal:,.0f}")
    
    with breakdown_col3:
        st.info(f"**Discount Applied**: {repeat_discount}%")

    # FINAL TOTAL
    st.markdown(f"""
    <div class="final-total-section">
        <h1 style="color: white; margin: 0; font-weight: 800; font-size: 2rem;">TOTAL PROJECT COST</h1>
        <p style="color: white; font-size: 3.5rem; font-weight: 900; margin: 1rem 0;">₹{total_cost:,.0f}</p>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.1rem; margin: 0; font-weight: 500;">
            {project_name} | {tier_level} Data Center | {customer_type} | {model_type}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Scope Description Display
    if scope_description.strip():
        st.markdown("### 📝 Project Scope")
        st.info(scope_description)

else:
    st.warning("⚠️ Please select at least one study type to generate cost estimates.")

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

current_time = datetime.datetime.now()

st.markdown(f"""
<div style="text-align: center; color: #64748b; padding: 3rem 2rem 2rem 2rem; margin-top: 4rem; 
     border-top: 2px solid rgba(59, 130, 246, 0.3); 
     background: rgba(15, 23, 42, 0.8); border-radius: 12px; backdrop-filter: blur(10px);">
    <p style="font-size: 1.2rem; font-weight: 700; color: #3b82f6; margin: 0 0 0.5rem 0;">
        Data Center Power System Studies - Unified Cost Estimation Platform
    </p>
    <p style="margin: 0.5rem 0; font-weight: 600; color: #06b6d4;">
        Developed by <strong>Abhishek Diwanji</strong> | Power Systems Studies Department
    </p>
    <p style="margin: 0; font-size: 0.9rem; color: #64748b;">
        Cal-Version 5.0 | Enhanced with Accurate Bus Count Calculation, Custom Block Sizing, Harmonics/Transient Studies, Custom Cost Sections & Scope Description
    </p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; color: #475569;">
        Generated on: {current_time.strftime("%B %d, %Y at %I:%M %p IST")}
    </p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem; color: #475569; font-style: italic;">
        Bus Count Algorithm: Component-Based Engineering Methodology | PUE: {pue_value} | Calibration: {bus_calibration}x
    </p>
</div>
""", unsafe_allow_html=True)
