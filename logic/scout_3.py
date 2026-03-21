import pandas as pd
import numpy as np

class AllPositionsCleaning:
    def __init__(self):
        folder = "CSV Files/"
        # Load Data Sources
        self.df_playing_time = pd.read_csv(folder + "playing_time.csv")
        self.df_standard = pd.read_csv(folder + "standard.csv")
        self.df_wages = pd.read_csv(folder + "wages.csv")
        self.df_misc = pd.read_csv(folder + "misc.csv")
        self.df_shooting = pd.read_csv(folder + "shooting.csv")
        self.df_keepers = pd.read_csv(folder + "keepers.csv")

        self._clean_wage_values()
        self.df_standard = self._clean_any_df(self.df_standard)
        self.df_playing_time = self._clean_any_df(self.df_playing_time)
        self.df_misc = self._clean_any_df(self.df_misc)
        self.df_shooting = self._clean_any_df(self.df_shooting)
        self.df_keepers = self._clean_any_df(self.df_keepers)

        self.master_df = self._create_master_consolidated_df()

    def _create_master_consolidated_df(self):
        """Merges all CSVs and applies AFCON/Nation cleaning logic."""
        # Standard as base
        merged = self.df_standard.copy()

        def safe_merge(base_df, new_df, suffix=''):
            cols_to_use = new_df.columns.difference(base_df.columns).tolist() + ['Player', 'Squad']
            return pd.merge(base_df, new_df[cols_to_use], on=['Player', 'Squad'], how='outer', suffixes=('', suffix))

        merged = safe_merge(merged, self.df_playing_time)
        merged = safe_merge(merged, self.df_misc)
        merged = safe_merge(merged, self.df_shooting, suffix='_shoot')
        merged = safe_merge(merged, self.df_keepers, suffix='_keep')

        if 'Weekly Wages' in merged.columns:
            merged = merged.drop(columns=['Weekly Wages'])
        merged = pd.merge(merged, self.df_wages[['Player', 'Weekly Wages']], on='Player', how='left')

        # Numeric conversion
        cols_to_fix = [
            'Min', 'Gls', 'Ast', 'G-PK', 'TklW', 'Int', 'Fld', 'Fls', 'Off',
            'SoT', 'G/Sh', 'CS', 'Saves', 'PKsv', 'GA', 'Save%', 'Min%', '+/-90', 
            'onG', 'onGA', 'Weekly Wages', 'Age', 'CrdY', 'CrdR'
        ]
        for col in cols_to_fix:
            if col in merged.columns:
                merged[col] = pd.to_numeric(merged[col].astype(str).str.replace(',', ''), errors='coerce')

        # AGGREGATION RULES
        agg_rules = {
            'Min': 'sum', 'Gls': 'sum', 'Ast': 'sum', 'G-PK': 'sum',
            'CrdY': 'max', 'CrdR': 'max', 'Weekly Wages': 'max',
            'Age': 'max', 'Pos': 'first', 'Squad': 'last', 'Nation': 'first',
            '+/-90': 'mean', 'onG': 'mean', 'onGA': 'mean',
            'TklW': 'sum', 'Int': 'sum', 'Fld': 'sum', 'Fls': 'sum', 'Off': 'sum',
            'SoT': 'sum', 'G/Sh': 'mean',
            'CS': 'sum', 'Saves': 'sum', 'PKsv': 'sum', 'GA': 'sum', 'Save%': 'mean'
        }

        existing_rules = {k: v for k, v in agg_rules.items() if k in merged.columns}
        master_df = merged.groupby('Player', as_index=False).agg(existing_rules)

        def clean_nation(val):
            val = str(val).strip()
            return val.split(" ")[-1].upper() if " " in val else val.upper()
        master_df['Nation'] = master_df['Nation'].apply(clean_nation)

        afcon_codes = ['BFA', 'NGA', 'CMR', 'COD', 'RSA', 'TUN', 'SEN', 'EGY', 'ALG', 'CIV', 'MAR', 'MLI', 'MOZ', 'ZIM']
        afcon_players = [
            "Dango Ouattara", "Frank Onyeka", "Carlos Baleba", "Axel Tuanzebe", 
            "Lyle Foster", "Hannibal Mejbri", "Ismaïla Sarr", "Idrissa Gueye", 
            "Iliman Ndiaye", "Calvin Bassey", "Alex Iwobi", "Samuel Chukwueze", 
            "Mohamed Salah", "Rayan Aït-Nouri", "Omar Marmoush", "Bryan Mbeumo", 
            "Amad Diallo", "Noussair Mazraoui", "Willy Boly", "Ibrahim Sangaré", 
            "Bertrand Traoré", "Arthur Masuaka", "Noah Sadiki", "Chemsdine Talbi", 
            "Reinildo", "Habib Diarra", "Yves Bissouma", "Pape Matar Sarr", 
            "Aaron Wan-Bissaka", "El Hadji Malick Diouf", "Emmanuel Agbadou", "Tawanda Chirewa"
        ]

        def get_denominator(row):
            is_afcon = (row['Nation'] in afcon_codes) or (str(row['Player']).title() in [p.title() for p in afcon_players])
            return 2610 - 360 if is_afcon else 2610

        master_df['Season_Total_Mins'] = master_df.apply(get_denominator, axis=1)
        master_df['Min%'] = (master_df['Min'] / master_df['Season_Total_Mins']) * 100
        
        return master_df

    def _clean_any_df(self, df):
        df = df[df["Player"] != "Player"].copy()
        for col in ["Player", "Squad"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.title().str.replace("’", "'")
        if "Pos" in df.columns:
            df["Pos"] = df["Pos"].astype(str).str.split(',').str[0].str.strip()
        if "Age" in df.columns:
            df["Age"] = pd.to_numeric(df["Age"].astype(str).str.split("-").str[0], errors='coerce')
        return df

    def _clean_wage_values(self):
        for col in ["Player", "Squad"]:
            if col in self.df_wages.columns:
                self.df_wages[col] = self.df_wages[col].astype(str).str.strip().str.title().str.replace("’", "'")
        def scrub_money(value):
            if pd.isna(value) or str(value).lower() == 'nan' or str(value).strip() == '': return np.nan
            clean_str = str(value).split('(')[0].replace('£', '').replace(',', '').strip()
            return pd.to_numeric(clean_str, errors='coerce')
        self.df_wages['Weekly Wages'] = self.df_wages['Weekly Wages'].apply(scrub_money)
        self.df_wages['Annual Wages'] = self.df_wages['Annual Wages'].apply(scrub_money)
        self.df_wages['Weekly Wages'] = self.df_wages['Weekly Wages'].fillna(self.df_wages['Annual Wages'] / 52)

    def calculate_availability_multiplier(self, min_percent):
        min_percent = pd.to_numeric(min_percent, errors='coerce').fillna(0)
        conditions = [ (min_percent >= 77.8), (min_percent >= 70.0), (min_percent >= 60.0), (min_percent >= 50.0), (min_percent < 50.0) ]
        choices = [1.0, 0.95, 0.85, 0.70, 0.50]
        return np.select(conditions, choices, default=0.5)

    def calculate_age_multiplier(self, age):
        age = pd.to_numeric(age, errors='coerce').fillna(30)
        conditions = [(age <= 23), (age > 23) & (age <= 30), (age > 30)]
        choices = [1.2, 1.0, 0.8]
        return np.select(conditions, choices, default=1.0)
    
    # Softer multipliers (NUS refined)
    def calculate_defensive_multiplier(self, tkl, intel, mins):
        if pd.isna(mins) or mins < 200: return 1.0
        da_p90 = ((tkl + intel) / mins) * 90
        
        if da_p90 >= 3.5: return 1.20    
        elif da_p90 >= 2.5: return 1.10  
        elif da_p90 >= 1.5: return 1.05  
        return 1.0 

    # --- Linear Regression for Value Reporting ---
    def get_value_report(self, df):
        if df.empty: return df
        analysis_df = df.dropna(subset=['Weekly Wages', 'Final_Score']).copy()
        
        if len(analysis_df) < 2:
            analysis_df['Expected_Score'] = analysis_df['Final_Score']
            analysis_df['Value_Gap'] = 0
            # Literal Rank first visually
            analysis_df.insert(0, 'Rank', np.nan)
            return analysis_df
            
        m, c = np.polyfit(analysis_df['Weekly Wages'], analysis_df['Final_Score'], 1)
        analysis_df['Expected_Score'] = m * analysis_df['Weekly Wages'] + c
        analysis_df['Value_Gap'] = analysis_df['Final_Score'] - analysis_df['Expected_Score']
        
        # New Ranking Logic: Sort by Value_Gap, reset ID index, and create literal 'Rank' column
        analysis_df = analysis_df.sort_values(by='Value_Gap', ascending=False).reset_index(drop=True)
        analysis_df.insert(0, 'Rank', range(1, len(analysis_df) + 1))
        
        return analysis_df
    

class Goalkeeper(AllPositionsCleaning):
    def __init__(self):
        super().__init__()

    def get_keeper_report(self):
        df_gk = self.master_df[(self.master_df['Pos'] == 'GK') & (self.master_df['Min'] >= 800)].copy()
        save_percent_decimal = pd.to_numeric(df_gk['Save%'], errors='coerce').fillna(0) / 100
        df_gk['Base_Score'] = (
            (50 * pd.to_numeric(df_gk['CS'], errors='coerce').fillna(0)) + 
            (5 * pd.to_numeric(df_gk['Saves'], errors='coerce').fillna(0)) + 
            (40 * pd.to_numeric(df_gk['PKsv'], errors='coerce').fillna(0)) + 
            (20 * save_percent_decimal) + 
            (20 * pd.to_numeric(df_gk['+/-90'], errors='coerce').fillna(0)) - 
            (5 * pd.to_numeric(df_gk['GA'], errors='coerce').fillna(0)) - 
            (3 * pd.to_numeric(df_gk['CrdY'], errors='coerce').fillna(0)) - 
            (15 * pd.to_numeric(df_gk['CrdR'], errors='coerce').fillna(0))
        )
        df_gk['Availability_Multiplier'] = self.calculate_availability_multiplier(df_gk['Min%'])
        df_gk['Age_Multiplier'] = self.calculate_age_multiplier(df_gk['Age'])
        df_gk['Final_Score'] = df_gk['Base_Score'] * df_gk['Availability_Multiplier'] * df_gk['Age_Multiplier']
        return df_gk


class Defender(AllPositionsCleaning):
    def __init__(self):
        super().__init__()

    def get_defender_report(self):
        df_def = self.master_df[(self.master_df['Pos'] == 'DF') & (self.master_df['Min'] >= 800)].copy()
        df_def['Base_Score'] = (
            (5 * df_def['TklW'].fillna(0)) + (5 * df_def['Int'].fillna(0)) + 
            (50 * df_def['Gls'].fillna(0)) + (30 * df_def['Ast'].fillna(0)) + 
            (20 * df_def['+/-90'].fillna(0)) - (2 * df_def['onGA'].fillna(0)) - 
            (2 * df_def['Fls'].fillna(0)) - (3 * df_def['CrdY'].fillna(0)) - 
            (15 * df_def['CrdR'].fillna(0))
        )
        df_def['Availability_Multiplier'] = self.calculate_availability_multiplier(df_def['Min%'])
        df_def['Age_Multiplier'] = self.calculate_age_multiplier(df_def['Age'])
        df_def['Final_Score'] = df_def['Base_Score'] * df_def['Availability_Multiplier'] * df_def['Age_Multiplier']
        # Explicit removal logic to prevent keeper stats and keep-suffix from appearing
        cols_to_drop = [c for c in df_def.columns if c.endswith('_keep') or c in ['Saves', 'PKsv', 'CS', 'GA', 'Save%']]
        return df_def.drop(columns=cols_to_drop)


class Midfielder(AllPositionsCleaning):
    def __init__(self):
        super().__init__()

    def get_midfielder_report(self):
        df_mf = self.master_df[(self.master_df['Pos'] == 'MF') & (self.master_df['Min'] >= 800)].copy()
        df_mf['Base_Score'] = (
            (30 * df_mf['Ast'].fillna(0)) + (50 * df_mf['Gls'].fillna(0)) + 
            (5 * df_mf['TklW'].fillna(0)) + (5 * df_mf['Int'].fillna(0)) + 
            (2 * df_mf['Fld'].fillna(0)) + (20 * df_mf['+/-90'].fillna(0)) - 
            (2 * df_mf['Fls'].fillna(0)) - (3 * df_mf['CrdY'].fillna(0)) - 
            (15 * df_mf['CrdR'].fillna(0))
        )
        df_mf['Availability_Multiplier'] = self.calculate_availability_multiplier(df_mf['Min%'])
        df_mf['Age_Multiplier'] = self.calculate_age_multiplier(df_mf['Age'])
        df_mf['Def_Multiplier'] = df_mf.apply(lambda x: self.calculate_defensive_multiplier(x['TklW'], x['Int'], x['Min']), axis=1)
        df_mf['Final_Score'] = df_mf['Base_Score'] * df_mf['Availability_Multiplier'] * df_mf['Age_Multiplier'] * df_mf['Def_Multiplier']
        # Explicit removal logic to prevent keeper stats appearing
        cols_to_drop = [c for c in df_mf.columns if c.endswith('_keep') or c in ['Saves', 'PKsv', 'CS', 'GA', 'Save%']]
        return df_mf.drop(columns=cols_to_drop)


class Forward(AllPositionsCleaning):
    def __init__(self):
        super().__init__()

    def get_forward_report(self):
        df_fw = self.master_df[(self.master_df['Pos'] == 'FW') & (self.master_df['Min'] >= 800)].copy()
        df_fw['Base_Score'] = (
            (50 * df_fw['G-PK'].fillna(0)) + (30 * df_fw['Ast'].fillna(0)) + 
            (3 * df_fw['SoT'].fillna(0)) + (3 * df_fw['Fld'].fillna(0)) + 
            (2 * df_fw['onG'].fillna(0)) + (20 * df_fw['G/Sh'].fillna(0)) + 
            (20 * df_fw['+/-90'].fillna(0)) - (5 * df_fw['Off'].fillna(0)) - 
            (3 * df_fw['CrdY'].fillna(0)) - (15 * df_fw['CrdR'].fillna(0))
        )
        df_fw['Availability_Multiplier'] = self.calculate_availability_multiplier(df_fw['Min%'])
        df_fw['Age_Multiplier'] = self.calculate_age_multiplier(df_fw['Age'])
        df_fw['Final_Score'] = df_fw['Base_Score'] * df_fw['Availability_Multiplier'] * df_fw['Age_Multiplier']
        # Explicit removal logic to prevent keeper stats appearing
        cols_to_drop = [c for c in df_fw.columns if c.endswith('_keep') or c in ['Saves', 'PKsv', 'CS', 'GA', 'Save%']]
        return df_fw.drop(columns=cols_to_drop)