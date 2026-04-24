from Archive.scout_2 import Goalkeeper, Defender, Midfielder, Forward
#find out top or bottom few players
gk_rankings = Goalkeeper().get_keeper_report()
def_rankings = Defender().get_defender_report()
mid_rankings = Midfielder().get_midfielder_report()
fwd_rankings = Forward().get_forward_report()

cols = ['Player', 'Squad', 'Min', 'Min%', 'Weekly Wages', 'Final_Score']
print(gk_rankings[cols].head(10))
print(def_rankings[cols].head(10))
print(mid_rankings[cols].head(10))
print(fwd_rankings[cols].head(10))





#Calculate how much better the top player is compared to the average
reports = {
    "Goalkeepers": Goalkeeper().get_keeper_report(),
    "Defenders": Defender().get_defender_report(),
    "Midfielders": Midfielder().get_midfielder_report(),
    "Forwards": Forward().get_forward_report()
}

print("\n" + "="*70)
print(f"{'POSITIONAL BENCHMARKING (VS LEAGUE MEAN)':^70}")
print("="*70)
print(f"{'Position':<15} | {'Avg Score':<12} | {'Top Score':<12} | {'Outperformance'}")
print("-" * 70)

for pos, df in reports.items():
    if not df.empty:
        avg_score = df['Final_Score'].mean()
        top_player = df.iloc[0]['Player']
        top_score = df.iloc[0]['Final_Score']
        

        multiplier = top_score / avg_score if avg_score > 0 else 0
        
        print(f"{pos:<15} | {avg_score:<12.2f} | {top_score:<12.2f} | {multiplier:.2f}x Average")
    else:
        print(f"{pos:<15} | No Data")

print("="*70)




#Plot all players with performance score against wage
import matplotlib.pyplot as plt
import seaborn as sns
from logic.scout_3 import Forward, Midfielder, Defender
import pandas as pd

fwd = Forward().get_forward_report(); fwd['Type'] = 'Forward'
mid = Midfielder().get_midfielder_report(); mid['Type'] = 'Midfielder'
dfn = Defender().get_defender_report(); dfn['Type'] = 'Defender'

all_players = pd.concat([fwd, mid, dfn])

# 2. Filter out anyone with NaN wages or scores for a clean plot
plot_data = all_players.dropna(subset=['Weekly Wages', 'Final_Score'])

# 3. Create the Scatter Plot
plt.figure(figsize=(12, 8))
sns.set_style("whitegrid")

scatter = sns.scatterplot(
    data=plot_data, 
    x='Weekly Wages', 
    y='Final_Score', 
    hue='Type', 
    style='Type',
    s=100, 
    alpha=0.7,
    palette='viridis'
)

# 4. Labeling the 'Outliers' (The big names)
# We'll label the top 5 scores and anyone earning > 300k
to_label = plot_data[(plot_data['Final_Score'] > plot_data['Final_Score'].quantile(0.95)) | 
                     (plot_data['Weekly Wages'] > 300000)]

for i in range(len(to_label)):
    plt.text(
        to_label.iloc[i]['Weekly Wages'] + 5000, 
        to_label.iloc[i]['Final_Score'], 
        to_label.iloc[i]['Player'], 
        fontsize=9, alpha=0.8
    )

plt.title('Premier League Value Analysis: Score vs. Wage', fontsize=16)
plt.xlabel('Weekly Wage (£)', fontsize=12)
plt.ylabel('Final Performance Score', fontsize=12)
plt.legend(title='Position')
plt.show()




from logic.scout_3 import Forward, Midfielder, Defender

#Most Valuable players with regard to Value Gap between final score and weekly wages
fwd_engine = Forward()
raw_fwd_report = fwd_engine.get_forward_report()


fwd_value_report = fwd_engine.get_value_report(raw_fwd_report)

print("\n" + "="*80)
print(f"{'VALUE ANALYSIS: FORWARDS (Surplus Value vs. Wage)':^80}")
print("="*80)
cols = ['Player', 'Weekly Wages', 'Final_Score', 'Expected_Score', 'Value_Gap']
print(fwd_value_report[cols].head(10))



import matplotlib.pyplot as plt
import seaborn as sns
from logic.scout_3 import Goalkeeper, Defender, Midfielder, Forward
import pandas as pd
###FIRST VALUE ANALYSIS PLOT
# 1. Map positions to their respective classes
position_map = {
    "Goalkeepers": Goalkeeper(),
    "Defenders": Defender(),
    "Midfielders": Midfielder(),
    "Forwards": Forward()
}

for pos_name, scout in position_map.items():
    # 2. Get the raw report and apply the Value Analysis
    raw_df = scout.get_forward_report() if pos_name == "Forwards" else \
             scout.get_midfielder_report() if pos_name == "Midfielders" else \
             scout.get_defender_report() if pos_name == "Defenders" else \
             scout.get_keeper_report()
    
    value_df = scout.get_value_report(raw_df)

    if value_df.empty:
        continue

    # 3. Setup the Plot
    plt.figure(figsize=(14, 10))
    sns.set_style("darkgrid")
    
    # Draw the regression line (Fair Value Line)
    sns.regplot(data=value_df, x='Weekly Wages', y='Final_Score', 
                scatter_kws={'s':60, 'alpha':0.5, 'color':'gray'}, 
                line_kws={'color':'red', 'label':'Fair Value Line'})

    # 4. Highlight and Label Top 20 (Bargains) and Bottom 20 (Underperformers)
    # We use the 'Value_Gap' calculated in your parent class
    top_20 = value_df.head(20)
    bottom_20 = value_df.tail(20)

    # Plot the outliers in distinct colors
    plt.scatter(top_20['Weekly Wages'], top_20['Final_Score'], color='green', s=100, label='Top 20 Bargains')
    plt.scatter(bottom_20['Weekly Wages'], bottom_20['Final_Score'], color='orange', s=100, label='Bottom 20 Underperformers')

    # Add text labels for the outliers
    # We combine them into one list to loop through
    outliers = pd.concat([top_20, bottom_20])
    for _, row in outliers.iterrows():
        plt.text(row['Weekly Wages'] + 2000, row['Final_Score'], row['Player'], 
                 fontsize=8, verticalalignment='center', alpha=0.9)

    # 5. Final Formatting
    plt.title(f'Value Analysis: {pos_name}\n(Above Red Line = Surplus Value)', fontsize=16)
    plt.xlabel('Weekly Wage (£)', fontsize=12)
    plt.ylabel('Performance Score', fontsize=12)
    plt.legend()
    
    # Save the file
    filename = f"{pos_name.lower()}_value_analysis.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close() # Close to free up memory for the next plot
    
    print(f"Successfully saved {filename}")



###SECOND VALUE ANALYSIS PLOT

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from logic.scout_3 import Goalkeeper, Defender, Midfielder, Forward

# 1. Define custom labeling thresholds based on your population sizes
thresholds = {
    "Goalkeepers": {"top": 10, "bottom": 10},   # Small sample size (23)
    "Forwards":    {"top": 15, "bottom": 10}, # Medium sample size (37)
    "Defenders":   {"top": 20, "bottom": 20}, # Large sample size
    "Midfielders": {"top": 20, "bottom": 20}  # Large sample size
}

position_map = {
    "Goalkeepers": Goalkeeper(),
    "Defenders": Defender(),
    "Midfielders": Midfielder(),
    "Forwards": Forward()
}

for pos_name, scout in position_map.items():
    # 2. Get the specific class report
    if pos_name == "Forwards": raw_df = scout.get_forward_report()
    elif pos_name == "Midfielders": raw_df = scout.get_midfielder_report()
    elif pos_name == "Defenders": raw_df = scout.get_defender_report()
    else: raw_df = scout.get_keeper_report()
    
    value_df = scout.get_value_report(raw_df)
    if value_df.empty: continue

    # 3. Apply the custom thresholds for this specific position
    n_top = thresholds[pos_name]["top"]
    n_bottom = thresholds[pos_name]["bottom"]

    top_list = value_df.head(n_top)
    bottom_list = value_df.tail(n_bottom)

    # 4. Setup the Plot
    plt.figure(figsize=(14, 10))
    sns.set_style("darkgrid")
    
    # Draw the regression line
    sns.regplot(data=value_df, x='Weekly Wages', y='Final_Score', 
                scatter_kws={'s':60, 'alpha':0.3, 'color':'gray'}, 
                line_kws={'color':'red', 'label':'Fair Value Line'})

    # 5. Highlight the Outliers
    plt.scatter(top_list['Weekly Wages'], top_list['Final_Score'], 
                color='green', s=120, label=f'Top {n_top} Bargains', edgecolors='black')
    plt.scatter(bottom_list['Weekly Wages'], bottom_list['Final_Score'], 
                color='orange', s=120, label=f'Bottom {n_bottom} Underperformers', edgecolors='black')

    # 6. Labeling Logic (Filtering to prevent overlap)
    outliers = pd.concat([top_list, bottom_list])
    for _, row in outliers.iterrows():
        plt.text(row['Weekly Wages'] + 2500, row['Final_Score'], row['Player'], 
                 fontsize=9, fontweight='bold', alpha=0.8)

    plt.title(f'Value Analysis: {pos_name}\n(Surplus Value = Distance Above Red Line)', fontsize=16)
    plt.xlabel('Weekly Wage (£)', fontsize=12)
    plt.ylabel('Performance Score', fontsize=12)
    plt.legend()
    
    # Save the file
    filename = f"{pos_name.lower()}_value_analysis2.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Generated {filename} (Top {n_top}, Bottom {n_bottom})")








###Generate website for Value Scouting Report
import pandas as pd
from logic.scout_3 import Goalkeeper, Defender, Midfielder, Forward

def generate_consolidated_report():
    # 1. Initialize scouts and positions
    positions = {
        "Goalkeepers": Goalkeeper(),
        "Defenders": Defender(),
        "Midfielders": Midfielder(),
        "Forwards": Forward()
    }
    
    # 2. Start the HTML content
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
            h1 {{ color: #1a5cff; text-align: center; border-bottom: 2px solid #1a5cff; padding-bottom: 10px; }}
            h2 {{ color: #2c3e50; margin-top: 40px; border-left: 5px solid #1a5cff; padding-left: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; }}
            th {{ background-color: #f8f9fa; color: #1a5cff; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .chart {{ text-align: center; margin: 30px 0; }}
            img {{ max-width: 90%; height: auto; border: 1px solid #ccc; box-shadow: 2px 2px 10px #aaa; }}
            .metric {{ font-weight: bold; color: green; }}
        </style>
    </head>
    <body>
        <h1>Premier League 2026: Value-Based Scouting Report</h1>
        <p style="text-align: center;"><i>Analyzing Performance Efficiency vs. Weekly Wage Market Benchmarks</i></p>
    """

    for pos_name, scout in positions.items():
        # Get raw data and value report
        if pos_name == "Forwards": raw_df = scout.get_forward_report()
        elif pos_name == "Midfielders": raw_df = scout.get_midfielder_report()
        elif pos_name == "Defenders": raw_df = scout.get_defender_report()
        else: raw_df = scout.get_keeper_report()
        
        value_df = scout.get_value_report(raw_df)
        
        if not value_df.empty:
            # Create Table for Top 5 Value Gems
            top_5 = value_df.head(5)[['Player', 'Squad', 'Weekly Wages', 'Final_Score', 'Value_Gap']]
            
            html_content += f"<h2>{pos_name}: Top 5 Value Gems</h2>"
            html_content += f"<p>These players provide the highest surplus performance relative to their salary.</p>"
            html_content += top_5.to_html(index=False, classes='table')
            
            # Link the chart image created earlier
            img_filename = f"{pos_name.lower()}_value_analysis.png"
            html_content += f"""
            <div class="chart">
                <img src="{img_filename}" alt="{pos_name} Analysis Chart">
                <p><i>Figure: {pos_name} Performance vs. Wage Regression</i></p>
            </div>
            """

    html_content += """
        <footer style="margin-top: 50px; text-align: center; font-size: 12px; color: #888;">
            Generated by Football Analysis Engine | March 2026
        </footer>
    </body>
    </html>
    """

    # Write to file
    with open("Full_Scouting_Report.html", "w") as f:
        f.write(html_content)
    
    print("✅ Full Scouting Report generated as 'Full_Scouting_Report.html'")

# Run the generator
generate_consolidated_report()




###Generation of updated files(PDF,PNG,HTML) -->  using scout_3

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from logic.scout_3 import Goalkeeper, Defender, Midfielder, Forward

# 1. Custom thresholds for outliers in the plots
thresholds = {
    "Goalkeepers": {"top": 10, "bottom": 10},
    "Defenders":   {"top": 20, "bottom": 20},
    "Midfielders": {"top": 20, "bottom": 20},
    "Forwards":    {"top": 15, "bottom": 10}
}

position_map = {
    "Goalkeepers": Goalkeeper(),
    "Defenders": Defender(),
    "Midfielders": Midfielder(),
    "Forwards": Forward()
}

for pos_name, scout in position_map.items():
    # 2. Get the specific class report data
    if pos_name == "Forwards": raw_df = scout.get_forward_report()
    elif pos_name == "Midfielders": raw_df = scout.get_midfielder_report()
    elif pos_name == "Defenders": raw_df = scout.get_defender_report()
    else: raw_df = scout.get_keeper_report()
    
    value_df = scout.get_value_report(raw_df)
    if value_df.empty: continue

    # --- Part A: Generate the Image (The Scatter Plot) ---
    plt.figure(figsize=(14, 10))
    sns.set_style("darkgrid")
    
    # Regression Line
    sns.regplot(data=value_df, x='Weekly Wages', y='Final_Score', 
                scatter_kws={'s':60, 'alpha':0.3, 'color':'gray'}, 
                line_kws={'color':'red', 'label':'Fair Value Line'})

    n_top = thresholds[pos_name]["top"]
    n_bottom = thresholds[pos_name]["bottom"]
    top_list = value_df.head(n_top)
    bottom_list = value_df.tail(n_bottom)

    # Highlight Outliers
    plt.scatter(top_list['Weekly Wages'], top_list['Final_Score'], color='green', s=120, label='Top Bargains')
    plt.scatter(bottom_list['Weekly Wages'], bottom_list['Final_Score'], color='orange', s=120, label='Underperformers')

    # Add Name Labels
    outliers = pd.concat([top_list, bottom_list])
    for _, row in outliers.iterrows():
        plt.text(row['Weekly Wages'] + 2500, row['Final_Score'], row['Player'], 
                 fontsize=9, fontweight='bold', alpha=0.8)

    plt.title(f'Value Analysis: {pos_name}\n(Above Red Line = Surplus Value)', fontsize=16)
    plt.xlabel('Weekly Wage (£)')
    plt.ylabel('Performance Score')
    plt.legend()
    
    img_name = f"{pos_name.lower()}_plot_updated.png"
    plt.savefig(img_name, dpi=300, bbox_inches='tight')
    plt.close()

    # --- Part B: Generate the HTML (The PDF Template) ---
    html_name = f"{pos_name.lower()}_value_analysis_updated.html"
    top_10_table = value_df.head(10)[['Player', 'Nation', 'Squad', 'Weekly Wages', 'Final_Score', 'Value_Gap']]
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 50px; background-color: white; }}
            .container {{ max-width: 900px; margin: auto; }}
            h1 {{ color: #1a5cff; text-align: center; border-bottom: 2px solid #1a5cff; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 30px 0; }}
            th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; }}
            th {{ background-color: #f8f9fa; color: #1a5cff; }}
            .chart-box {{ text-align: center; margin-top: 40px; }}
            img {{ width: 100%; border: 1px solid #eee; border-radius: 8px; }}
            .footer {{ margin-top: 50px; text-align: center; font-size: 11px; color: #777; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{pos_name} Efficiency Report: PL 25/26</h1>
            <p>This report identifies players performing significantly above or below their market value baseline. 
               Data includes <b>AFCON minute adjustments</b> and <b>defensive volume multipliers</b>.</p>
            
            <h3>Top 10 Value Bargains</h3>
            {top_10_table.to_html(index=False)}
            
            <div class="chart-box">
                <h3>Wage vs. Performance Regression</h3>
                <img src="{img_name}">
            </div>
            
            <div class="footer">
                Automated Scouting Intelligence | Prepared for Kesler's Portfolio
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(html_name, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ Generated: {html_name}")