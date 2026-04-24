import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from logic.scout_3 import Goalkeeper, Defender, Midfielder, Forward
import base64

# --- HIGH-COLOR FOOTBALL THEME (REPAIRED) ---
def set_bg_from_local(image_file):
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode()
    
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(0, 50, 0, 0.2), rgba(0, 0, 0, 0.5)), 
                              url("data:image/png;base64,{encoded_string}");
            background-attachment: fixed;
            background-size: cover;
        }}
        
        /* Restoring the sidebar transparency */
        [data-testid="stSidebar"] {{
            background-color: rgba(5, 15, 5, 0.9) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }}

        /* Restoring the glass-morphism main container */
        .main {{
            background-color: rgba(0, 0, 0, 0.35);
            padding: 35px;
            border-radius: 25px;
            margin: 15px;
            backdrop-filter: blur(5px);
        }}

        /* FIX: White text for the info boxes */
        .stAlert p {{
            color: white !important;
            font-weight: 500;
        }}

        /* Darker background for alert boxes for high contrast */
        [data-testid="stNotification"] {{
            background-color: rgba(0, 0, 0, 0.7) !important;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Call with your local filename
set_bg_from_local("background.jpg")

# --- 1. SYSTEM CONFIGURATION ---
POSITION_METRICS = {
    "FW": ['Gls', 'Ast', 'G-PK', 'SoT', 'G/Sh', 'Off', 'Fld', '+/-90', 'Value_Gap', 'Final_Score'],
    "MF": ['Ast', 'Gls', 'TklW', 'Int', 'Fld', 'Fls', '+/-90', 'Value_Gap', 'Final_Score'],
    "DF": ['TklW', 'Int', 'onGA', 'Gls', 'Ast', 'Fls', '+/-90', 'Value_Gap', 'Final_Score'],
    "GK": ['CS', 'Saves', 'PKsv', 'Save%', 'GA', '+/-90', 'Value_Gap', 'Final_Score']
}

UNIVERSAL_METRICS = ['Weekly Wages', 'Min', 'Age', 'CrdY', 'CrdR']
LOWER_IS_BETTER = ['Off', 'Fls', 'onGA', 'GA', 'Weekly Wages', 'Age', 'CrdY', 'CrdR']

GLOSSARY = {
    "Rank": "Positional ranking based on predictive modeling fair value gap baseline.",
    "G-PK": "Non-Penalty Goals.",
    "Ast": "Assists.",
    "SoT": "Shots on Target.",
    "Fld": "Fouls Drawn.",
    "Fls": "Fouls Committed.",
    "onG": "Goals scored by team while player was on pitch.",
    "onGA": "Goals conceded by team while player was on pitch.",
    "G/Sh": "Goals per Shot.",
    "Off": "Offside.",
    "+/-90": "Net goal difference for team per 90 minutes while player is on.",
    "TklW": "Tackles Won.",
    "Int": "Interceptions.",
    "CS": "Clean Sheets.",
    "Saves": "Total shots saved by the goalkeeper.",
    "Save%": "Percentage of shots on target saved.",
    "PKsv": "Penalty Kicks saved.",
    "GA": "Goals Against (conceded by goalkeeper).",
    "Value_Gap": "Performance Score relative to Wage (Surplus Value). Higher is better.",
    "Final_Score": "Overall calculated performance rating.",
    "CrdY": "Yellow Cards.",
    "CrdR": "Red Cards."
}

mapping_rules = {
    'á': 'a', 'à': 'a', 'â': 'a', 'ä': 'a', 'ã': 'a', 'å': 'a',
    'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
    'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
    'ó': 'o', 'ò': 'o', 'ô': 'o', 'ö': 'o', 'õ': 'o', 'ø': 'o', 'œ': 'oe',
    'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
    'ñ': 'n', 'ç': 'c', 'ć': 'c', 'ß': 'ss', 'æ': 'ae', 'ð': 'd', 'Đ': 'd', 'Ð': 'd', 'ø': 'o', 'Ø': 'o', 
}

def clean_special_characters(name):
    name_clean = name.lower().strip()
    for spec, base in mapping_rules.items():
        name_clean = name_clean.replace(spec, base)
    return name_clean

def create_searchable_alias_map(player_list):
    alias_map = {}
    for p in player_list:
        clean_p = clean_special_characters(p).title()
        if clean_p.lower() != p.lower():
            alias_map[f"{p} [{clean_p}]"] = p
        else:
            alias_map[p] = p
    return alias_map

def normalize_data(target_df, metrics_list):
    norm_df = target_df.copy()
    for metric in metrics_list:
        if norm_df[metric].dtype in ['float64', 'int64'] and not norm_df[metric].isnull().all():
            max_val = norm_df[metric].max()
            min_val = norm_df[metric].min()
            inv = (metric in LOWER_IS_BETTER)
            
            if max_val == min_val:
                norm_df[metric + '_norm'] = 100.0 if max_val > 0 else 0.0
            else:
                if not inv:
                    norm_df[metric + '_norm'] = (norm_df[metric] - min_val) / (max_val - min_val) * 100
                else:
                    norm_df[metric + '_norm'] = (max_val - norm_df[metric]) / (max_val - min_val) * 100
    return norm_df

# --- 2. DATA INITIALIZATION ---
@st.cache_resource
def load_system():
    systems = {"GK": Goalkeeper(), "DF": Defender(), "MF": Midfielder(), "FW": Forward()}
    filtered_player_map = {}
    reports = {}
    
    for pos, scout in systems.items():
        if pos == "FW": report = scout.get_forward_report()
        elif pos == "MF": report = scout.get_midfielder_report()
        elif pos == "DF": report = scout.get_defender_report()
        else: report = scout.get_keeper_report()
        
        val_report = scout.get_value_report(report)
        reports[pos] = val_report
        for name in val_report['Player'].unique():
            filtered_player_map[name] = pos
            
    sorted_qualified_players = sorted(list(filtered_player_map.keys()))
    return systems, reports, sorted_qualified_players, filtered_player_map

scouts, position_reports, master_qualified_players, player_to_pos_lookup = load_system()
searchable_map = create_searchable_alias_map(master_qualified_players)

# --- 3. UI SETUP ---
st.sidebar.title("⚽ PL Scout Intelligence")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["Search Player", "Compare Players", "Value Graphs", "Leaderboards", "Draft a Team"])

with st.sidebar.expander("📖 Metric Glossary"):
    for key, val in GLOSSARY.items():
        st.write(f"**{key}:** {val}")

# --- 4. SEARCH PLAYER PAGE ---
if page == "Search Player":
    st.title("🔍 Qualified Player Search (Min 800+ Mins Played)")
    
    target_display = st.selectbox(
        "Find and Select a Player:", 
        options=sorted(searchable_map.keys()),
        index=None,
        placeholder="Type here..."
    )
    
    if target_display:
        target = searchable_map[target_display] 
        pos = player_to_pos_lookup[target]
        df = position_reports[pos]
        
        player_data = df[df['Player'] == target]
        if player_data.empty:
            st.error(f"Error: {target} not found in current dataset. Try clearing your cache.")
        else:
            data = player_data.iloc[0]
            rank = int(data['Rank'])
            total_in_pos = len(df)
            
            medal = ""
            if rank == 1: medal = "🥇 "
            elif rank == 2: medal = "🥈 "
            elif rank == 3: medal = "🥉 "
            
            st.success(f"Detected Position: **{pos}**")
            st.header(f"{medal}{target}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Positional Rank", f"#{rank} / {total_in_pos}") 
            
            val_score = data['Value_Gap']
            val_color = "#28a745" if val_score >= 0 else "#dc3545" 
            
            c2.markdown(f"""
                <div style="display: flex; flex-direction: column; margin-bottom: 1rem;">
                    <span style="font-size: 0.875rem; color: #FAFAFA; margin-bottom: 0.25rem;">Value Score</span>
                    <span style="font-size: 2.25rem; font-weight: normal; color: {val_color};">{val_score:.2f}</span>
                </div>
            """, unsafe_allow_html=True)
            
            c3.metric("Weekly Wage", f"£{data['Weekly Wages']:,.0f}")
            
            st.write("### Full Efficiency Profile")
            display_cols = ['Rank', 'Pos', 'Squad', 'Min', 'Weekly Wages', 'Age']
            active_metrics = [m for m in POSITION_METRICS[pos] if m not in ['Value_Gap', 'Final_Score']]
            display_cols.extend(active_metrics)
            display_cols.extend(['CrdY', 'CrdR'])
            for mult in ['Availability_Multiplier', 'Age_Multiplier', 'Def_Multiplier']:
                if mult in df.columns: display_cols.append(mult)
            display_cols.extend(['Final_Score', 'Value_Gap'])
            
            df_display = df[df['Player'] == target][display_cols].copy()
            df_display['Rank'] = df_display['Rank'].astype(str) + f" / {total_in_pos}"
            
            # FIXED: Updated use_container_width to width="stretch"
            st.dataframe(df_display, hide_index=True, width="stretch")

# --- 5. COMPARE PLAYERS PAGE ---
elif page == "Compare Players":
    st.title("⚔️ Head-to-Head Comparison")
    
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        p1_display = st.selectbox("Select Player 1:", sorted(searchable_map.keys()), index=None, placeholder="Type here...", key="p1")
    with col2:
        p2_display = st.selectbox("Select Player 2:", sorted(searchable_map.keys()), index=None, placeholder="Type here...", key="p2")
        
    if not p1_display or not p2_display: 
        st.info("Please select two players to begin comparison.")
    else:
        p1 = searchable_map[p1_display]
        p2 = searchable_map[p2_display]
        pos1, pos2 = player_to_pos_lookup[p1], player_to_pos_lookup[p2]
        
        if pos1 != pos2:
            st.error(f"❌ Position Mismatch: {p1}({pos1}) vs {p2}({pos2}). Must compare same roles.")
        else:
            st.success(f"Comparing two **{pos1}s**")
            scout = scouts[pos1]
            df = position_reports[pos1]
            
            available = list(set(POSITION_METRICS[pos1] + UNIVERSAL_METRICS))
            tooltip_text = "**Metric Definitions:**\n\n"
            for m in sorted(available):
                if m in GLOSSARY:
                    tooltip_text += f"- **{m}**: {GLOSSARY[m]}\n"

            metrics = st.multiselect(
                "Select Metrics to Compare:", 
                options=sorted(available), 
                default=['Value_Gap', 'Final_Score'],
                help=tooltip_text
            )
            
            if metrics:
                p1_r = df[df['Player'] == p1].iloc[0]
                p2_r = df[df['Player'] == p2].iloc[0]

                st.write("---")
                l_col, res1, res2 = st.columns([2, 1, 1])
                res1.markdown(f"<h4 style='text-align: center;'>{p1}</h4>", unsafe_allow_html=True)
                res2.markdown(f"<h4 style='text-align: center;'>{p2}</h4>", unsafe_allow_html=True)

                for m in metrics:
                    v1, v2 = p1_r[m], p2_r[m]
                    inv = (m in LOWER_IS_BETTER) 
                    
                    if v1 == v2: c1, c2 = "gray", "gray"
                    elif (v1 > v2 and not inv) or (v1 < v2 and inv): c1, c2 = "#28a745", "#dc3545"
                    else: c1, c2 = "#dc3545", "#28a745"

                    row_label, r1, r2 = st.columns([2, 1, 1])
                    row_label.markdown(f"**{m}**")
                    
                    fmt = ",.0f" if m in ['Weekly Wages', 'Min'] else ".2f"
                    r1.markdown(f"<div style='background-color:{c1}; color:white; padding:10px; border-radius:5px; text-align:center;'>{v1:{fmt}}</div>", unsafe_allow_html=True)
                    r2.markdown(f"<div style='background-color:{c2}; color:white; padding:10px; border-radius:5px; text-align:center;'>{v2:{fmt}}</div>", unsafe_allow_html=True)

                if len(metrics) >= 3:
                    st.write("### Profile Overlap (0-100 position-relative scale)")
                    df_norm = normalize_data(df, metrics)
                    p1_n = df_norm[df_norm['Player'] == p1].iloc[0]
                    p2_n = df_norm[df_norm['Player'] == p2].iloc[0]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(r=[p1_n[m + '_norm'] for m in metrics], theta=metrics, fill='toself', name=p1, line_color='#28a745'))
                    fig.add_trace(go.Scatterpolar(r=[p2_n[m + '_norm'] for m in metrics], theta=metrics, fill='toself', name=p2, line_color='#dc3545'))
                    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=8), gridcolor="gray")), showlegend=True, template="plotly_dark", margin=dict(l=80, r=80, t=20, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("ℹ️ Select at least 3 metrics to see radar visual.")

# --- 6. VALUE GRAPHS PAGE ---
elif page == "Value Graphs":
    st.title("📈 Positional Value Graphs")
    st.write("Interactive regression analysis. Hover over points to view player details.")
    
    pos_choice = st.selectbox("Select Position:", ["Forwards", "Midfielders", "Defenders", "Goalkeepers"])
    mapping = {"Forwards": "FW", "Midfielders": "MF", "Defenders": "DF", "Goalkeepers": "GK"}
    pos_code = mapping[pos_choice]
    
    df = position_reports[pos_code].copy()
    df['Color'] = np.where(df['Value_Gap'] >= 0, '#28a745', '#dc3545')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Weekly Wages'],
        y=df['Final_Score'],
        mode='markers',
        marker=dict(color=df['Color'], size=10, line=dict(width=1, color='DarkSlateGrey')),
        text=df['Player'],
        customdata=df['Value_Gap'],
        hovertemplate="<b>%{text}</b><br>Weekly Wage: £%{x:,.0f}<br>Final Score: %{y:.2f}<br>Value Gap: %{customdata:.2f}<extra></extra>",
        name='Players'
    ))
    
    df_line = df.sort_values(by='Weekly Wages')
    fig.add_trace(go.Scatter(
        x=df_line['Weekly Wages'],
        y=df_line['Expected_Score'],
        mode='lines',
        line=dict(color='red', width=2),
        name='Fair Value Line',
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title=f"Value Analysis: {pos_choice} (Above Red Line = Surplus Value)",
        xaxis_title="Weekly Wage (£)",
        yaxis_title="Final Performance Score",
        template="plotly_dark",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

# --- 7. LEADERBOARDS PAGE ---
elif page == "Leaderboards":
    st.title("🏆 Efficiency Leaderboards")
    st.write("---")
    mapping = {"Forwards": "FW", "Midfielders": "MF", "Defenders": "DF", "Goalkeepers": "GK"}
    cols_order = ['Rank', 'Player', 'Squad', 'Weekly Wages', 'Value_Gap']
    
    for pos_choice, pos_code in mapping.items():
        st.subheader(f"💎 {pos_choice} Top 10 Bargains")
        df = position_reports[pos_code]
        df_top = df.sort_values(by='Value_Gap', ascending=False).head(10)
        
        # FIXED: Updated use_container_width to width="stretch"
        st.dataframe(
            df_top[cols_order], 
            hide_index=True, 
            width="stretch", 
            column_config={
                "Weekly Wages": st.column_config.NumberColumn(
                    "Weekly Wage",
                    help="Official weekly wage in GBP",
                    format="£%,d",
                ),
                "Value_Gap": st.column_config.NumberColumn(
                    "Value Gap",
                    help="Performance surplus relative to wage",
                    format="%.2f",
                )
            }
        )
        st.write("---")


# --- 8. DRAFT A TEAM PAGE ---
elif page == "Draft a Team":
    st.title("📋 AI Squad Builder")
    
    # 1. FORMATION SELECTION
    formation_choice = st.radio("Select Tactical System:", ["4-4-2", "4-2-3-1"], horizontal=True)
    
    # 2. STANDARDIZED BOUNDS & ELITE BENCHMARK
    display_min = 250000
    absolute_max_wage = 2000000 

    if formation_choice == "4-4-2":
        reqs = {"GK": 1, "DF": 4, "MF": 4, "FW": 2}
        elite_parts = [position_reports[p].sort_values('Final_Score', ascending=False).head(count) for p, count in reqs.items()]
    else:
        mf_p = position_reports['MF']
        e_dms_pool = mf_p[mf_p['Def_Multiplier'] >= 1.1].copy()
        e_dms_pool['Ceiling_Score'] = e_dms_pool['Final_Score']
        e_dms_pool.loc[e_dms_pool['Def_Multiplier'] >= 1.2, 'Ceiling_Score'] *= 1.15
        e_dms = e_dms_pool.sort_values('Ceiling_Score', ascending=False).head(2)
        
        e_ams_p = mf_p[~mf_p['Player'].isin(e_dms['Player'])].copy()
        e_ams_p['AM_Weight'] = e_ams_p['Final_Score'] + (e_ams_p['Gls'] * 20) + (e_ams_p['Ast'] * 20)
        e_ams = e_ams_p.sort_values('AM_Weight', ascending=False).head(3)
        
        elite_parts = [
            position_reports['GK'].sort_values('Final_Score', ascending=False).head(1),
            position_reports['DF'].sort_values('Final_Score', ascending=False).head(4),
            position_reports['FW'].sort_values('Final_Score', ascending=False).head(1),
            e_dms, e_ams
        ]
    
    elite_total = int(pd.concat(elite_parts)['Weekly Wages'].sum())
    st.sidebar.success(f"💎 **Elite XI Identified**")
    st.sidebar.write(f"The best performing 11 for this system costs **£{elite_total:,.0f}**.")

    # 3. USER INPUT
    wage_limit = st.number_input(
        "Enter Total Weekly Wage Budget (£):", 
        min_value=display_min, max_value=absolute_max_wage, value=None, step=25000,
        placeholder=f"Range: £250,000 - £2,000,000"
    )

    if wage_limit:
        criteria_map = {"Goals": "Gls", "Assists": "Ast", "Tackles Won": "TklW", "Interceptions": "Int"}
        selected_criteria = st.multiselect("Optimization Bias (Optional):", list(criteria_map.keys()))
        active_cols = [criteria_map[c] for c in selected_criteria]

        if st.button("Generate Optimized XI"):
            # --- 4. POOL GENERATION & SPECIALIST BOOST ---
            pool = {}
            for pos in ["GK", "DF", "MF", "FW"]:
                df_p = position_reports[pos].copy()
                df_p['Score'] = df_p['Final_Score']
                for c in active_cols:
                    if c in df_p.columns:
                        df_p['Score'] += (df_p[c] / (df_p[c].max() + 0.1)) * 100
                
                if pos == "MF" and formation_choice == "4-2-3-1":
                    df_p['DM_Candidate_Score'] = df_p['Score']
                    df_p.loc[df_p['Def_Multiplier'] >= 1.2, 'DM_Candidate_Score'] *= 1.15
                
                pool[pos] = df_p.sort_values('Score', ascending=False)

            # --- 5. INITIAL SELECTION ---
            final_parts = [pool['GK'].head(1), pool['DF'].head(4)]
            if formation_choice == "4-2-3-1":
                final_parts.append(pool['FW'].head(1))
                dm_pool = pool['MF'][pool['MF']['Def_Multiplier'] >= 1.1].sort_values('DM_Candidate_Score', ascending=False)
                dms = dm_pool.head(2)
                am_pool = pool['MF'][~pool['MF']['Player'].isin(dms['Player'])].copy()
                am_pool['AM_Weight'] = am_pool['Score'] + (am_pool['Gls'] * 20) + (am_pool['Ast'] * 20)
                ams = am_pool.sort_values('AM_Weight', ascending=False).head(3)
                final_parts.extend([dms, ams])
                dm_names, am_names = dms['Player'].tolist(), ams['Player'].tolist()
            else:
                final_parts.extend([pool['MF'].head(4), pool['FW'].head(2)])

            # --- 6. BUDGET OPTIMIZATION ---
            current_selection = pd.concat(final_parts).drop_duplicates(subset=['Player'])
            for _ in range(150):
                if current_selection['Weekly Wages'].sum() <= wage_limit: break
                to_replace = current_selection.sort_values('Weekly Wages', ascending=False).iloc[0]
                p_name, p_pos = to_replace['Player'], to_replace['Pos']
                is_dm = (formation_choice == "4-2-3-1" and p_name in dm_names)
                
                alts_p = pool[p_pos][~pool[p_pos]['Player'].isin(current_selection['Player'])]
                if is_dm: alts_p = alts_p[alts_p['Def_Multiplier'] >= 1.1]
                
                alts = alts_p[alts_p['Weekly Wages'] < to_replace['Weekly Wages']]
                if not alts.empty:
                    current_selection = current_selection[current_selection['Player'] != p_name]
                    best_alt = alts.sort_values('DM_Candidate_Score' if is_dm else 'Score', ascending=False).iloc[0]
                    current_selection = pd.concat([current_selection, pd.DataFrame([best_alt])])
                    if is_dm:
                        dm_names.remove(p_name); dm_names.append(best_alt['Player'])

            # --- 7. FINAL MAPPING & TABLE ---
            final_df = current_selection.head(11).copy()
            specialist_12 = final_df[final_df['Def_Multiplier'] >= 1.2]['Player'].tolist()

            if formation_choice == "4-2-3-1":
                final_df['Pos'] = final_df.apply(lambda r: "DM" if r['Player'] in dm_names else ("AM" if r['Pos'] == "MF" else r['Pos']), axis=1)
            
            final_df['Player'] = final_df.apply(lambda r: f"★ {r['Player']}" if r['Player'] in specialist_12 else r['Player'], axis=1)

            pos_order = {"GK": 0, "DF": 1, "DM": 2, "AM": 3, "MF": 4, "FW": 5}
            final_df = final_df.assign(Sort=final_df['Pos'].map(pos_order)).sort_values('Sort').drop('Sort', axis=1)

            st.subheader(f"Directives Met: £{final_df['Weekly Wages'].sum():,.0f} / £{wage_limit:,.0f}")
            
            # FIXED: Updated use_container_width to width="stretch"
            st.dataframe(final_df[['Player', 'Pos', 'Squad', 'Weekly Wages', 'Final_Score']], width="stretch", hide_index=True)
            if specialist_12: st.caption("★ = Tactical Specialist (1.2 Multiplier) | Received 15% selection priority.")

            # --- 8. TACTICAL BOARD ---
            st.write("### 🏟️ Tactical Board")
            coords = {"GK": [(50,10)], "DF": [(15,30),(38,30),(62,30),(85,30)], "MF": [(15,60),(38,60),(62,60),(85,60)], "FW": [(35,85),(65,85)]} if formation_choice == "4-4-2" else {"GK": [(50,10)], "DF": [(15,25),(38,25),(62,25),(85,25)], "DM": [(35,45),(65,45)], "AM": [(20,70),(50,70),(80,70)], "FW": [(50,90)]}
            
            fig = go.Figure()
            fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, fillcolor="#228B22", line_color="white", layer="below")
            fig.add_shape(type="line", x0=0, y0=50, x1=100, y1=50, line_color="white")
            fig.add_shape(type="circle", x0=40, y0=40, x1=60, y1=60, line_color="white")

            for i, r in final_df.iterrows():
                p_role = r['Pos']
                if p_role == "MF" and formation_choice == "4-2-3-1": p_role = "AM" if len(coords["AM"]) > 0 else "DM"
                if p_role in coords and coords[p_role]:
                    x, y = coords[p_role].pop(0)
                    color = {"GK":"black", "DF":"#007BFF", "MF":"#FFD700", "DM":"#17a2b8", "AM":"#fd7e14", "FW":"#FF4136"}.get(p_role, "white")
                    fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers+text', text=[r['Player']], textposition="bottom center", marker=dict(size=22, color=color, line=dict(width=2, color="white")), textfont=dict(color="white", size=10), name=r['Player']))
            
            fig.update_layout(xaxis=dict(range=[0,100], visible=False), yaxis=dict(range=[0,100], visible=False), showlegend=False, height=600, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

            if formation_choice == "4-2-3-1":
                with st.expander("ℹ️ Tactical Methodology: DM Selection"):
                    st.write("""
                    DMs are chosen via a **Weighted Priority Matrix**:
                    * **Tier 1 (Specialist Priority):** Players with a **1.2 Def_Multiplier** receive a **15% score boost**. 
                    * **Tier 2 (Performance Fairness):** A **1.1 Multiplier** player is selected only if their raw performance is **>15% higher** than the best available Specialist.
                    * **Constraint:** Players with multipliers below 1.1 are disqualified from Double Pivot roles.
                    """)
    else:
        st.warning(f"Please enter a budget between £250,000 and £2,000,000 to begin.")