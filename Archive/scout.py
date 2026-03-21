import pandas as pd
import numpy as np

class AllPositionsCleaning:
    def __init__(self):
        folder = "CSV Files/"
        # 1. Load ALL Data Sources
        self.df_playing_time = pd.read_csv(folder + "playing_time.csv")
        self.df_standard = pd.read_csv(folder + "standard.csv")
        self.df_wages = pd.read_csv(folder + "wages.csv")
        self.df_misc = pd.read_csv(folder + "misc.csv")
        self.df_shooting = pd.read_csv(folder + "shooting.csv")
        self.df_keepers = pd.read_csv(folder + "keepers.csv")

        # 2. Universal Cleaning (Fixing currency and data types)
        self._clean_wage_values()
        self.df_standard = self._clean_any_df(self.df_standard)
        self.df_playing_time = self._clean_any_df(self.df_playing_time)
        self.df_misc = self._clean_any_df(self.df_misc)
        self.df_shooting = self._clean_any_df(self.df_shooting)
        self.df_keepers = self._clean_any_df(self.df_keepers)

        # 3. Create the Consolidated Master DataFrame
        self.master_df = self._create_master_consolidated_df()

    def _create_master_consolidated_df(self):
        """Merges all CSVs and sums/averages stats for players with multiple clubs."""
        
        # 1. Start with Standard as the base
        merged = self.df_standard.copy()

        # Helper to join without duplicating Pos/Age/Nation columns
        def safe_merge(base_df, new_df, suffix=''):
            # This ensures we don't bring in 'Weekly Wages' from other files if they exist there
            cols_to_use = new_df.columns.difference(base_df.columns).tolist() + ['Player', 'Squad']
            return pd.merge(base_df, new_df[cols_to_use], on=['Player', 'Squad'], how='outer', suffixes=('', suffix))

        # 2. Join performance files
        merged = safe_merge(merged, self.df_playing_time)
        merged = safe_merge(merged, self.df_misc)
        merged = safe_merge(merged, self.df_shooting, suffix='_shoot')
        merged = safe_merge(merged, self.df_keepers, suffix='_keep')

        # 3. THE WAGE FIX: Join on 'Player' ONLY
        # First, ensure 'Weekly Wages' isn't already in merged (to avoid Weekly Wages_x/y)
        if 'Weekly Wages' in merged.columns:
            merged = merged.drop(columns=['Weekly Wages'])
        
        # We join wages purely on the Player name. This handles mid-season transfers
        # because the wage will now attach to BOTH the old club and new club rows.
        merged = pd.merge(merged, self.df_wages[['Player', 'Weekly Wages']], on='Player', how='left')

        # 4. Convert math columns to numeric BEFORE grouping
        cols_to_fix = [
            'Min', 'Gls', 'Ast', 'G-PK', 'TklW', 'Int', 'Fld', 'Fls', 'Off',
            'SoT', 'G/Sh', 'CS', 'Saves', 'PKsv', 'GA', 'Save%', 'Min%', '+/-90', 
            'onG', 'onGA', 'Weekly Wages', 'Age', 'CrdY', 'CrdR'
        ]
        
        for col in cols_to_fix:
            if col in merged.columns:
                merged[col] = pd.to_numeric(merged[col].astype(str).str.replace(',', ''), errors='coerce')

        # 5. AGGREGATION RULES
        # Using 'max' for Weekly Wages ensures that if one row is NaN and the other has the value, 
        # the value is preserved after grouping.
        agg_rules = {
            'Min': 'sum', 'Gls': 'sum', 'Ast': 'sum', 'G-PK': 'sum',
            'CrdY': 'max', 'CrdR': 'max', 'Weekly Wages': 'max', # Preserves the wage
            'Age': 'max', 'Pos': 'first', 'Squad': 'last', 
            '+/-90': 'mean', 'onG': 'mean', 'onGA': 'mean',
            'TklW': 'sum', 'Int': 'sum', 'Fld': 'sum', 'Fls': 'sum', 'Off': 'sum',
            'SoT': 'sum', 'G/Sh': 'mean',
            'CS': 'sum', 'Saves': 'sum', 'PKsv': 'sum', 'GA': 'sum', 'Save%': 'mean'
        }

        existing_rules = {k: v for k, v in agg_rules.items() if k in merged.columns}

        master_df = merged.groupby('Player', as_index=False).agg(existing_rules)

        # 3. THE FIX: Calculate Min% based on total season minutes (2610)
        # We do this AFTER the sum to get the true league-wide availability
        total_season_mins = 2610
        master_df['Min%'] = (master_df['Min'] / total_season_mins) * 100
        
        return master_df

    def _clean_any_df(self, df):
        """Universal sanitizer for performance dataframes."""
        df = df[df["Player"] != "Player"].copy()
        
        # FIX: Force Title Case and strip whitespace for both keys
        for col in ["Player", "Squad"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.title().str.replace("’", "'")
        
        if "Pos" in df.columns:
            df["Pos"] = df["Pos"].astype(str).str.split(',').str[0].str.strip()
        
        if "Age" in df.columns:
            df["Age"] = pd.to_numeric(df["Age"].astype(str).str.split("-").str[0], errors='coerce')
            
        return df

    def _clean_wage_values(self):
        """Standardizes names and RECOVERS missing weekly wages from annual totals."""
        
        # 1. Standardize Player and Squad names
        for col in ["Player", "Squad"]:
            if col in self.df_wages.columns:
                self.df_wages[col] = self.df_wages[col].astype(str).str.strip().str.title().str.replace("’", "'")

        # 2. A 'Helper Function' to clean currency strings
        def scrub_money(value):
            if pd.isna(value) or str(value).lower() == 'nan' or str(value).strip() == '':
                return np.nan
            # Extract only the first number before any parenthesis/extra text
            clean_str = str(value).split('(')[0].replace('£', '').replace(',', '').strip()
            return pd.to_numeric(clean_str, errors='coerce')

        # 3. Clean BOTH columns (Weekly and Annual)
        # This turns "£ 27,300,000 (est)" into 27300000.0
        self.df_wages['Weekly Wages'] = self.df_wages['Weekly Wages'].apply(scrub_money)
        self.df_wages['Annual Wages'] = self.df_wages['Annual Wages'].apply(scrub_money)

        # 4. THE RECOVERY STEP:
        # If Weekly Wages is still NaN, fill it with (Annual / 52)
        # This will finally give Haaland his £525,000!
        self.df_wages['Weekly Wages'] = self.df_wages['Weekly Wages'].fillna(self.df_wages['Annual Wages'] / 52)

    # --- MULTIPLIERS ---
    def calculate_availability_multiplier(self, min_percent):
        min_percent = pd.to_numeric(min_percent, errors='coerce').fillna(0)
        conditions = [
            (min_percent >= 77.8), (min_percent >= 70.0), 
            (min_percent >= 60.0), (min_percent >= 50.0), (min_percent < 50.0)
        ]
        choices = [1.0, 0.95, 0.85, 0.70, 0.50]
        return np.select(conditions, choices, default=0.5)

    def calculate_age_multiplier(self, age):
        age = pd.to_numeric(age, errors='coerce').fillna(30)
        conditions = [(age <= 23), (age > 23) & (age <= 30), (age > 30)]
        choices = [1.2, 1.0, 0.8]
        return np.select(conditions, choices, default=1.0)

    def search_player(self, name_query):
        """Searches the master database for a player and returns their full consolidated profile."""
        # 1. Look for the name (case-insensitive)
        result = self.master_df[self.master_df['Player'].str.contains(name_query, case=False, na=False)]
        
        if result.empty:
            return f"No player found matching '{name_query}'"
        
        # 2. Return a clean summary of what the system 'sees'
        # We pick key columns to show you their 'Profile'
        cols = ['Player', 'Pos', 'Squad', 'Min', 'Min%', 'Weekly Wages', 'Age']
        # Add any other stats you want to verify
        return result[cols]
    
    def get_value_report(self, df):
        """ Calculates the expected score vs actual score using Linear Regression."""
        if df.empty:
            return df
        
        # 1. Prepare data (Filter out players with no wages)
        analysis_df = df.dropna(subset=['Weekly Wages', 'Final_Score']).copy()
        
        if len(analysis_df) < 2:
            analysis_df['Expected_Score'] = analysis_df['Final_Score']
            analysis_df['Value_Gap'] = 0
            return analysis_df

        # 2. Calculate Linear Regression: y = mx + c
        # x = Wages, y = Final_Score
        x = analysis_df['Weekly Wages']
        y = analysis_df['Final_Score']
        
        m, c = np.polyfit(x, y, 1)  # 1 means linear (degree 1)
        
        # 3. Calculate Expected Score and the 'Value Gap'
        analysis_df['Expected_Score'] = m * analysis_df['Weekly Wages'] + c
        analysis_df['Value_Gap'] = analysis_df['Final_Score'] - analysis_df['Expected_Score']
        
        # 4. Sort by Value_Gap (Best bargains at the top)
        return analysis_df.sort_values(by='Value_Gap', ascending=False)
    

class Goalkeeper(AllPositionsCleaning):
    def __init__(self):
        # Initializes the parent, which builds the master_df
        super().__init__()

    def get_keeper_report(self):
        # 1. Start with the consolidated master data
        df = self.master_df.copy()

        # 2. Filter for Goalkeepers AND Minutes >= 800
        # Since master_df already summed 'Min' from all clubs, 
        # players like a traded keeper will be captured correctly.
        df_gk = df[(df['Pos'] == 'GK') & (df['Min'] >= 800)].copy()

        # 3. Calculate Base Score
        # We normalize Save% by dividing by 100 as per your formula logic
        save_percent_decimal = pd.to_numeric(df_gk['Save%'], errors='coerce').fillna(0) / 100

        df_gk['Base_Score'] = (
            (20 * pd.to_numeric(df_gk['CS'], errors='coerce').fillna(0)) + 
            (4 * pd.to_numeric(df_gk['Saves'], errors='coerce').fillna(0)) + 
            (25 * pd.to_numeric(df_gk['PKsv'], errors='coerce').fillna(0)) + 
            (20 * save_percent_decimal) + 
            (20 * pd.to_numeric(df_gk['+/-90'], errors='coerce').fillna(0)) - 
            (5 * pd.to_numeric(df_gk['GA'], errors='coerce').fillna(0)) - 
            (3 * pd.to_numeric(df_gk['CrdY'], errors='coerce').fillna(0)) - 
            (15 * pd.to_numeric(df_gk['CrdR'], errors='coerce').fillna(0))
        )

        # 4. Apply Multipliers
        df_gk['Availability_Multiplier'] = self.calculate_availability_multiplier(df_gk['Min%'])
        df_gk['Age_Multiplier'] = self.calculate_age_multiplier(df_gk['Age'])
        
        # 5. Final Score Calculation
        df_gk['Final_Score'] = df_gk['Base_Score'] * df_gk['Availability_Multiplier'] * df_gk['Age_Multiplier']
        
        # 6. Rank and Sort
        df_gk = df_gk.sort_values(by='Final_Score', ascending=False)
        df_gk.reset_index(drop=True, inplace=True)
        df_gk.index += 1
        df_gk.index.name = 'Rank'
        
        return df_gk
    

class Defender(AllPositionsCleaning):
    def __init__(self):
        super().__init__()

    def get_defender_report(self):
        df = self.master_df.copy()
        # Filter: DF position and 800+ total minutes
        df_def = df[(df['Pos'] == 'DF') & (df['Min'] >= 800)].copy()

        # Performance Score Calculation
        df_def['Base_Score'] = (
            (5 * df_def['TklW'].fillna(0)) + 
            (7 * df_def['Int'].fillna(0)) + 
            (20 * df_def['Gls'].fillna(0)) + 
            (10 * df_def['Ast'].fillna(0)) + 
            (20 * df_def['+/-90'].fillna(0)) - 
            (2 * df_def['onGA'].fillna(0)) - 
            (2 * df_def['Fls'].fillna(0)) - 
            (3 * df_def['CrdY'].fillna(0)) - 
            (15 * df_def['CrdR'].fillna(0))
        )

        # Apply Shared Multipliers
        df_def['Availability_Multiplier'] = self.calculate_availability_multiplier(df_def['Min%'])
        df_def['Age_Multiplier'] = self.calculate_age_multiplier(df_def['Age'])
        df_def['Final_Score'] = df_def['Base_Score'] * df_def['Availability_Multiplier'] * df_def['Age_Multiplier']
        
        # Ranking Logic
        df_def = df_def.sort_values(by='Final_Score', ascending=False)
        df_def.reset_index(drop=True, inplace=True)
        df_def.index += 1
        df_def.index.name = 'Rank'
        
        return df_def
    

class Midfielder(AllPositionsCleaning):
    def __init__(self):
        super().__init__()

    def get_midfielder_report(self):
        df = self.master_df.copy()
        # Filter: MF position and 800+ total minutes
        df_mf = df[(df['Pos'] == 'MF') & (df['Min'] >= 800)].copy()

        # Performance Score Calculation
        df_mf['Base_Score'] = (
            (15 * df_mf['Ast'].fillna(0)) + 
            (20 * df_mf['Gls'].fillna(0)) + 
            (5 * df_mf['TklW'].fillna(0)) + 
            (5 * df_mf['Int'].fillna(0)) + 
            (2 * df_mf['Fld'].fillna(0)) + 
            (20 * df_mf['+/-90'].fillna(0)) - 
            (2 * df_mf['Fls'].fillna(0)) - 
            (3 * df_mf['CrdY'].fillna(0)) - 
            (15 * df_mf['CrdR'].fillna(0))
        )

        # Apply Shared Multipliers
        df_mf['Availability_Multiplier'] = self.calculate_availability_multiplier(df_mf['Min%'])
        df_mf['Age_Multiplier'] = self.calculate_age_multiplier(df_mf['Age'])
        df_mf['Final_Score'] = df_mf['Base_Score'] * df_mf['Availability_Multiplier'] * df_mf['Age_Multiplier']
        
        # Ranking Logic
        df_mf = df_mf.sort_values(by='Final_Score', ascending=False)
        df_mf.reset_index(drop=True, inplace=True)
        df_mf.index += 1
        df_mf.index.name = 'Rank'
        
        return df_mf
    

class Forward(AllPositionsCleaning):
    def __init__(self):
        super().__init__()

    def get_forward_report(self):
        df = self.master_df.copy()
        # Filter: FW position and 800+ total minutes
        df_fw = df[(df['Pos'] == 'FW') & (df['Min'] >= 800)].copy()

        # Performance Score Calculation
        df_fw['Base_Score'] = (
            (25 * df_fw['G-PK'].fillna(0)) + 
            (15 * df_fw['Ast'].fillna(0)) + 
            (3 * df_fw['SoT'].fillna(0)) + 
            (3 * df_fw['Fld'].fillna(0)) + 
            (2 * df_fw['onG'].fillna(0)) + 
            (20 * df_fw['G/Sh'].fillna(0)) + 
            (20 * df_fw['+/-90'].fillna(0)) - 
            (4 * df_fw['Off'].fillna(0)) - 
            (3 * df_fw['CrdY'].fillna(0)) - 
            (15 * df_fw['CrdR'].fillna(0))
        )

        # Apply Shared Multipliers
        df_fw['Availability_Multiplier'] = self.calculate_availability_multiplier(df_fw['Min%'])
        df_fw['Age_Multiplier'] = self.calculate_age_multiplier(df_fw['Age'])
        df_fw['Final_Score'] = df_fw['Base_Score'] * df_fw['Availability_Multiplier'] * df_fw['Age_Multiplier']
        
        # Ranking Logic
        df_fw = df_fw.sort_values(by='Final_Score', ascending=False)
        df_fw.reset_index(drop=True, inplace=True)
        df_fw.index += 1
        df_fw.index.name = 'Rank'
        
        return df_fw
                         

    

