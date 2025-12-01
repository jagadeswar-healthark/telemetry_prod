from .predictions import get_column_safe, is_zigzag, is_sustained, flag_sustained
import pandas as pd
import numpy as np

def set_gunShot_conditions(df: pd.DataFrame) -> dict[str, bool]:
    #  Condition 16: HSLC
    condition_16 = (
        ((df[['Stage 1 RPM', 'Stage 2 RPM']].mean(axis=1)) != 0) &
        (get_column_safe(df, 'Stage 1 RPM') >= 4000) &
        (get_column_safe(df, 'Stage 2 RPM') >= 4000) 
    )
    
    # Condition 7: 2nd stage hot sump issue
    condition_7 = (
        (get_column_safe(df, 'TC9') >= 69)  # 2nd sump line
    )
    
    # Condition 14: Intermittent Fan Issue
    condition_14 = (
        (get_column_safe(df, 'RTD_in_range') == False) &
        (get_column_safe(df, 'RTD_trend') > 0) &        # RTD
        (get_column_safe(df, 'TC7_trend') > 0) &        # liquid line
        (get_column_safe(df, 'TC2_trend') > 0) &        # Air inlet
        (get_column_safe(df, 'Diff_TC2_&_TC7') > 10) # Check if the absolute difference between TC2 and TC7 is lesser than 10
    )
    
    tsx_events = {
        "2nd stage hot sump": condition_7,
        "HSLC": condition_16,
        "Intermittent Fan Issue": condition_14
    }
    
    return tsx_events #type: ignore

def set_firstStage_conditions(df: pd.DataFrame, count_ref_df: int) -> dict[str, bool]:
    # Condition 5: 1st stage leak issue
    condition_5 = ( 
        ((df[['TC3', 'TC4']].mean(axis=1)) != 0) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != -127) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != 127) &
        (get_column_safe(df, 'RTD_in_range') == False) &
        (get_column_safe(df, 'RTD_trend') > 0) &
        (get_column_safe(df, 'TC10_trend') > 0) & 
        (get_column_safe(df, 'TC1') > (df['TC1'].mean() + 15)) &  # Check if TC1 is outside ±10 of its average
        ((df[['Stage 1 RPM', 'Stage 2 RPM']].mean(axis=1)) != 0) 
        # (get_column_safe(df, 'Stage 1 RPM') >= 4000) &
        # (get_column_safe(df, 'Stage 2 RPM') >= 4000) # |
        # (get_column_safe(df, 'TC1_trend') > 0)  # First check: if TC1_trend > 0, the condition is satisfied
    )
     # Condition 3: 1st stage compression failure

    condition_3 = (
        (get_column_safe(df, 'RTD_in_range') == False) &
        (get_column_safe(df, 'RTD_trend') > 0) &    #RTD
        (get_column_safe(df, 'TC10_trend') > 0) &  # BPHX
        ((df[['Stage 1 RPM', 'Stage 2 RPM']].mean(axis=1)) != 0) &
        # (get_column_safe(df, 'stage 1 RPM') >= 4000) &
        # (get_column_safe(df, 'stage 2 RPM') >= 4000) &
        (count_ref_df > 0) # |
        # (get_column_safe(df, 'TC1_trend') > 0) # First check: if TC1_trend > 0, the condition is satisfied
    )
    # Condition 4: 1st stage issue
    condition_4 = ( 
        (get_column_safe(df, 'RTD_in_range') == False) &
        (get_column_safe(df, 'RTD_trend') > 0) &
        (get_column_safe(df, 'TC10_trend') > 0) &
        ((get_column_safe(df, 'TC1') >= (df['TC1'].mean() - 10)) & 
        (get_column_safe(df, 'TC1') <= (df['TC1'].mean() + 10)) ) &  # Check if TC1 is within ±10 of its average
        ((df[['Stage 1 RPM', 'Stage 2 RPM']].mean(axis=1)) != 0) 
        # (get_column_safe(df, 'stage 1 RPM') >= 4000) &
        # (get_column_safe(df, 'stage 2 RPM') >= 4000) # |
        # (get_column_safe(df, 'TC1_trend') > 0)  # First check: if TC1_trend > 0, the condition is satisfied
    )
    
   
    
    
    # Condition 2: 1st stage compressor inverter issue
    condition_2 = (
        (get_column_safe(df, 'RTD_in_range') == False) &
        (get_column_safe(df, 'RTD_trend') > 0) &
        (get_column_safe(df, 'TC_zigzag') == True) &
        (get_column_safe(df, 'TC10_trend') > 0) &
        (get_column_safe(df, 'TC1_trend') > 0) &
        (get_column_safe(df, 'TC1') >= 70)   
    )
    
    first_stage_events = {
        "1st stage leak issue": condition_5,
        "1st stage compression issue": condition_3,
        "1st stage issue": condition_4,
        "1st stage compressor inverter issue": condition_2,
    }
    
    return first_stage_events

def set_secondStage_conditions(df: pd.DataFrame) -> dict[str, bool]:
    # Condition 11: 2nd stage leak issue
    condition_11 = (
        (get_column_safe(df, 'RTD_in_range') == False) &
        (get_column_safe(df, 'RTD_trend') > 0) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != 0) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != -127) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != 127) &
        (get_column_safe(df, 'TC3_trend') < 0) &
        (get_column_safe(df, 'TC4_trend') > 0) &
        (get_column_safe(df, 'TC6_trend') > 0) &
        (get_column_safe(df, 'TC10_trend') < 0) &
        (get_column_safe(df, 'TC1_trend') < 0) &
        (abs(df['TC3'] - df['TC4']) > 5)   # Check if the absolute difference between TC3 and TC4 is greater than 5   
    )
    
    # Condition 10: 2nd stage issue
    condition_10 = (
        (get_column_safe(df, 'RTD_in_range') == False) &                                                 
        (get_column_safe(df, 'RTD_trend') > 0) &
        (get_column_safe(df, 'TC10_trend') < 0) &
        (get_column_safe(df, 'TC1_trend') < 0) # |
        # (get_column_safe(df, 'TC6_trend') > 0) 
    )
    
    # Condition 9: 2nd stage compression failure
    condition_9 = (
        (get_column_safe(df, 'RTD_in_range') == False) &
        (get_column_safe(df, 'RTD_trend') > 0) &
        (get_column_safe(df, 'TC10_trend') < 0) &
        (get_column_safe(df, 'TC3_trend') > 0) &
        (get_column_safe(df, 'TC4_trend') > 0) &
        (get_column_safe(df, 'TC1_trend') < 0) 
    )
    
    # Condition 8: 2nd stage compressor inverter issue
    condition_8 = (
        (get_column_safe(df, 'RTD_in_range') == False) &
        (get_column_safe(df, 'RTD_trend') > 0) &
        (get_column_safe(df, 'TC_zigzag') == True) &
        (get_column_safe(df, 'TC10_trend') < 0) &
        (get_column_safe(df, 'TC1_trend') < 0) 
    )

    # Condition 12: 2nd stage insulation issue (Armaflex)
    condition_12 = (
        (get_column_safe(df, 'RTD_in_range') == False) &
        (get_column_safe(df, 'RTD_trend') > 0) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != 0) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != -127) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != 127) &
        (get_column_safe(df, 'TC3_in_range') == True) &
        (get_column_safe(df, 'TC4_trend') > 0) &
        (get_column_safe(df, 'TC1_in_range') == True) &
        (get_column_safe(df, 'TC10_in_range') == True)  
    )

    #  Condition 15: VIP Panel Issues
    # condition_15 = (
    #     (get_column_safe(df, 'RTD_in_range') == False) &
    #     (get_column_safe(df, 'RTD_trend') > 0) &
    #     (get_column_safe(df, 'TC3_trend') > 0) &
    #     (get_column_safe(df, 'TC4_trend') > 0) 
    # )
    
    second_stage_events = {
        "2nd stage leak issue": condition_11,
        "2nd stage issue": condition_10,
        "2nd stage compression issue": condition_9,
        "2nd stage compressor inverter issue": condition_8,
        "2nd stage insulation issue (Armaflex)": condition_12,
        # "VIP Panel Issues": condition_15
    }
    
    return second_stage_events

def set_flag_conditions(df: pd.DataFrame, ref_df: pd.DataFrame) -> pd.DataFrame:
    # Dynamically select all columns that end with '_trend'
    tc_trend_cols = [col for col in df.filter(regex='_trend$').columns if df[col].mean() != 0]
    
    # Apply zigzag condition row-wise output will be True or false
    df['TC_zigzag'] = df[tc_trend_cols].apply(is_zigzag, axis=1)
    
    # calculating TC10 trend class: 0 -> normal, 1 -> warming, -1 -> cooling
    df['TC10_trend_class'] = np.where(
        get_column_safe(df, 'TC10') > -35, 1,
        np.where(get_column_safe(df, 'TC10') < -45, -1, 0)
    )
    
    column=ref_df.columns.to_list()
    if ref_df is not None and column:
        for col in column:
            count=int(ref_df[col].count()) 
            break
    else:
        count=0 

    gun_shot = set_gunShot_conditions(df)
    first_stage = set_firstStage_conditions(df, count) #type: ignore
    second_stage = set_secondStage_conditions(df)
    
    # variable for default values in trend flag sets
    default_val = "No issue detected - your device is working properly"
    
    df['Trend_Flag'] = np.where(
        df['Door_Status'] != -1,
        np.select(
            [condition for condition in gun_shot.values()],
            [key for key in gun_shot],
            default = default_val
        ),
        "Door Open Event, Ignored"
    )
    
    # Sustained conditions for TC10
    sustained_warming = is_sustained(df, get_column_safe(df, 'TC10') > -35)
    sustained_cooling = is_sustained(df, get_column_safe(df, 'TC10') < -45)
    
    if sustained_warming:
        df['Trend_Flag'] = np.where(
            df['Trend_Flag'] == default_val,
            np.select(
                [condition for condition in first_stage.values()],
                [key for key in first_stage],
                default=default_val
            ),
            df['Trend_Flag']
        )
    
    if sustained_cooling:
        df['Trend_Flag'] = np.where(
            df['Trend_Flag'] == default_val,
            np.select(
                [condition for condition in second_stage.values()],
                [key for key in second_stage],
                default=default_val
            ),
            df['Trend_Flag']
        )
    
    df['Sustained_Issue'] = flag_sustained(df)
    # df['Issue_Detected'] = df['Sustained_Issue'].astype(int)
    print(df)
    return df