import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix


def apply_ml_predictions(new_df, model, features):
    X_new = new_df[features]  # replace with the feature list used during training
    predictions = model.predict(X_new)

    label_mapping = {
    0: "No issue detected - your device is working properly",
    1: '1st stage hot sump failure issue',
    # 2: "1st stage compressor start components issue",
    3: '1st stage compression failure',
    4:  '1st stage issue',
    5:  "1st stage leak issue",
    6:  "1st stage low charge issue",
    7:  '2nd stage hot sump issue',
    8: "2nd stage compressor start components issue",
    9: '2nd stage compression failure',
    10: '2nd stage issue',
    11: "2nd stage leak issue",
    12: '2nd stage insulation issue (Armaflex)',
    13:  "2nd stage low charge issue",
    14: 'Intermittent Fan Issue',
    # 15:  'VIP Panel Issues',
    16:    'HSLC',
    }
    
    new_df['Prediction_Code'] = predictions
    new_df['Prediction_Label'] = [label_mapping.get(p, "Unknown") for p in predictions]

    new_df['Final_Label'] = new_df.apply(lambda row: row['Trend_Flag'] if row['Sustained_Issue'] else row['Prediction_Label'], axis=1)

    return new_df

def run_predictions_and_summary(new_df, features, model, core_columns):
    # Apply ML predictions and combine with rule-based flags
    
    flagged = new_df[new_df['Sustained_Issue']]
    new_df = apply_ml_predictions(new_df, model, features)
    
    # Accuracy and confusion matrix
    y_true = new_df['Trend_Flag']
    y_pred = new_df['Final_Label']
    accuracy = round((accuracy_score(y_true, y_pred) * 100), 2)
    cm = confusion_matrix(y_true, y_pred)
    
    # Summary statistics
    # summary_df = calculate_summary_stats(new_df, flagged, core_columns)
    
    return {
        'accuracy': accuracy,
        'confusion_matrix': cm.tolist(),
        'flagged': flagged,
        'new_df': new_df
    }

def set_gunshot_conditions(df: pd.DataFrame) -> dict[str, bool]:
    # Condition 1: 1st stage hot sump issue
    condition_1 = (
        (get_column_safe(df, 'TC8') >= 69)  # 1st sump line
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
    
    # dictionary for gun shot events
    gun_shot_events = {
        "1st stage hot sump": condition_1,
        "2nd stage hot sump": condition_7,
        "Intermittent Fan Issue": condition_14
    }
    
    return gun_shot_events #type: ignore

def set_firstStage_conditions(df: pd.DataFrame) -> dict[str, bool]:
    # Condition 5: 1st stage leak issue
    condition_5 = (
        ((df[['TC3', 'TC4']].mean(axis=1)) != 0) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != -127) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != 127) &
        (get_column_safe(df, 'RTD_in_range') == False) &
        (get_column_safe(df, 'RTD_trend') > 0) &
        (get_column_safe(df, 'TC10_trend') > 0) &
        (get_column_safe(df, 'TC1_trend') > 0) &
        (get_column_safe(df, 'TC8_trend') > 0)
    )
    
    # Condition 4: 1st stage issue
    condition_4 = ( 
        ((df[['TC3', 'TC4']].mean(axis=1)) != 0) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != -127) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != 127) & # Check if TC3 and TC4 are not both zero
        (get_column_safe(df, 'RTD_in_range') == False) &
        (get_column_safe(df, 'RTD_trend') > 0) &
        (get_column_safe(df, 'TC10_trend') > 0) |
        (get_column_safe(df, 'TC1_trend') > 0)  # First check: if TC1_trend > 0, the condition is satisfied
    )
    
    # Condition 3: 1st stage compression failure
    condition_3 = (
        ((df[['TC3', 'TC4']].mean(axis=1)) != 0) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != -127) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != 127) &  # Check if TC3 and TC4 are not both zero
        (get_column_safe(df, 'RTD_in_range') == False) &
        (get_column_safe(df, 'RTD_trend') > 0) &    #RTD
        (get_column_safe(df, 'TC10_trend') > 0) &  # BPHX
        (get_column_safe(df, 'PUC_State') == 1) |
        (get_column_safe(df, 'TC1_trend') > 0) # First check: if TC1_trend > 0, the condition is satisfied
    )
    
    # Condition 2: 1st stage compressor start components issue
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
        "1st stage issue": condition_4,
        "1st stage compression issue": condition_3,
        "1st stage compressor start components issue": condition_2,
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
        ((df[['TC3', 'TC4']].mean(axis=1)) != 0) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != -127) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != 127) &
        (get_column_safe(df, 'TC10_trend') < 0)|
        (get_column_safe(df, 'TC6_trend') > 0) 
    )
    
    # Condition 9: 2nd stage compression failure
    condition_9 = (
        (get_column_safe(df, 'RTD_in_range') == False) &
        (get_column_safe(df, 'RTD_trend') > 0) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != 0) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != -127) &
        ((df[['TC3', 'TC4']].mean(axis=1)) != 127) &
        (get_column_safe(df, 'TC10_trend') < 0) &
        (get_column_safe(df, 'TC3_trend') > 0) &
        (get_column_safe(df, 'TC4_trend') > 0) &
        (get_column_safe(df, 'TC1_trend') < 0)
    )
    
    # Condition 8: 2nd stage compressor Start components issue
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
        "2nd stage compressor start components issue": condition_8,
        "2nd stage insulation issue (Armaflex)": condition_12
    }
    
    return second_stage_events

# conditions
def is_zigzag(trends):
    # Convert trends to direction: 1 (up), -1 (down), 0 (flat)
    directions = np.sign(trends)
    
    # Remove 0s (flat values) to focus on actual changes
    directions = directions[directions != 0]
    
    # If less than 2 non-zero directions, can't form a zig-zag
    if len(directions) < 2:
        return False
    
    # Check for alternation in directions
    return all(directions[i] != directions[i+1] for i in range(len(directions)-1))

def flag_sustained(df: pd.DataFrame, col='Trend_Flag', file_type=None, min_consecutive=None):
    """
    Flags sustained issues in the DataFrame. If file_type is 'STP' or 'STP1', min_consecutive=45, else 180.
    """
    if file_type in ('STP', 'STP1'):
        min_consecutive = 45    
    else:
        min_consecutive = 180 if min_consecutive is None else min_consecutive
    ignore = [
        'No issue detected - your device is working properly',
        'Door Open Event, Ignored'
    ]
    labels = [False] * len(df)   # final column (default False)
    current_flag = None
    count = 0
    
    for i, val in enumerate(df[col]):
        if val in ignore:
            current_flag = None
            count = 0
            continue
        
        if val == current_flag:
            count += 1
        else:
            current_flag = val
            count = 1
        
        if count >= min_consecutive:
            # mark all sustained entries as True
            for j in range(i - min_consecutive + 1, i + 1):
                labels[j] = True
    
    return labels



def get_column_safe(new_df: pd.DataFrame, column_name, default_value=0):
    return new_df[column_name] if column_name in new_df.columns else default_value

def is_sustained(df: pd.DataFrame, condition, min_duration=45) -> bool:
    """Check if a condition is sustained for at least min_duration minutes."""
    df = df.copy()
    
    df['condition_met'] = condition
    
    df['group'] = (df['condition_met'] != df['condition_met'].shift()).cumsum()
    
    sustained_groups = df[df['condition_met']].groupby('group').apply(
        lambda x: (x['Date/Time'].max() - x['Date/Time'].min()).total_seconds() / 60 > min_duration
    )
    sustained = df['group'].isin(sustained_groups[sustained_groups].index)
        
    return sustained.any()

def set_flag_conditions(df: pd.DataFrame):
    # Dynamically select all columns that end with '_trend'
    tc_trend_cols = [col for col in df.filter(regex='_trend$').columns if df[col].mean() != 0]
    
    # Apply zigzag condition row-wise output will be True or false
    df['TC_zigzag'] = df[tc_trend_cols].apply(is_zigzag, axis=1)
    
    # calculating TC10 trend class: 0 -> normal, 1 -> warming, -1 -> cooling
    df['TC10_trend_class'] = np.where(
        get_column_safe(df, 'TC10') > -35, 1,
        np.where(get_column_safe(df, 'TC10') < -45, -1, 0)
    )

    # fetching gun shot events and their coniditions
    gun_shot = set_gunshot_conditions(df)
    first_stage = set_firstStage_conditions(df)
    second_stage = set_secondStage_conditions(df)
    
    # variable for default values in trend flag sets
    default_val = "No issue detected - your device is working properly"
    
    # setting df for gun shot events first because of higher priority
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
    df['Issue_Detected'] = df['Sustained_Issue'].astype(int)

    # calculate final label based on sustained issues

    print(df)
    return df


def final_label_prediction(df: pd.DataFrame) -> pd.DataFrame:
    final_labels = []
    for trend, sustained in zip(df['Trend_Flag'], df['Sustained_Issue']):
        if sustained:
            final_labels.append(trend)   # keep the sustained issue name
        else:
            final_labels.append("No issue detected")  # replace everything else
    
    df['Final_Label'] = final_labels
    return df