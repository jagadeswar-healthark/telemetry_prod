import pandas as pd
import numpy as np
from io import StringIO
from datetime import datetime
from collections import defaultdict

# remove door and power events
def parse_timestamp(timestamp_str):
    timestamp_str = timestamp_str.strip().rstrip(',')

    formats = [
    # MM/DD/YYYY (US)
    "%m/%d/%Y %I:%M:%S.%f %p",   # 12-hour with AM/PM and microseconds
    "%m/%d/%Y %I:%M:%S %p",      # 12-hour with AM/PM
    "%m/%d/%Y %H:%M:%S.%f",      # 24-hour with microseconds
    "%m/%d/%Y %H:%M:%S",         # 24-hour without microseconds
    "%m/%d/%Y",                  # Date only (MM/DD/YYYY)

    # DD/MM/YYYY (International)
    "%d/%m/%Y %I:%M:%S.%f %p",   # 12-hour with AM/PM and microseconds
    "%d/%m/%Y %I:%M:%S %p",      # 12-hour with AM/PM
    "%d/%m/%Y %H:%M:%S.%f",      # 24-hour with microseconds
    "%d/%m/%Y %H:%M:%S",         # 24-hour without microseconds
    "%d/%m/%Y",                  # Date only (DD/MM/YYYY)

    # YYYY-MM-DD (ISO 8601)
    "%Y-%m-%d %I:%M:%S.%f %p",   # 12-hour with AM/PM and microseconds
    "%Y-%m-%d %I:%M:%S %p",      # 12-hour with AM/PM
    "%Y-%m-%d %H:%M:%S.%f",      # 24-hour with microseconds
    "%Y-%m-%d %H:%M:%S",         # 24-hour without microseconds
    "%Y-%m-%d",                  # Date only (YYYY-MM-DD)

    # Time only formats
    "%I:%M:%S.%f %p",            # 12-hour time with AM/PM and microseconds
    "%I:%M:%S %p",               # 12-hour time with AM/PM
    "%H:%M:%S.%f",               # 24-hour time with microseconds
    "%H:%M:%S",                  # 24-hour time without microseconds

    # Date and time in different formats
    "%Y/%m/%d %I:%M:%S.%f %p",   # 12-hour format with slashes and microseconds
    "%Y/%m/%d %I:%M:%S %p",      # 12-hour format with slashes
    "%d-%m-%Y %I:%M:%S.%f %p",   # 12-hour format with dashes
    "%d-%m-%Y %I:%M:%S %p",      # 12-hour format with dashes
    "%Y-%m-%dT%H:%M:%S.%f",      # ISO 8601 extended with microseconds
    "%Y-%m-%dT%H:%M:%S",         # ISO 8601 extended without microseconds

    # Alternative formats
    "%d/%m/%y %I:%M:%S.%f %p",   # Two-digit year, 12-hour with AM/PM and microseconds
    "%d/%m/%y %I:%M:%S %p",      # Two-digit year, 12-hour with AM/PM
    "%d/%m/%y %H:%M:%S.%f",      # Two-digit year, 24-hour with microseconds
    "%d/%m/%y %H:%M:%S",         # Two-digit year, 24-hour without microseconds
    "%Y/%m/%d %H:%M:%S.%f",      # Slashes for date and 24-hour with microseconds
    "%Y/%m/%d %H:%M:%S",         # Slashes for date and 24-hour without microseconds

    # With time zone
    "%Y-%m-%d %H:%M:%S %z",      # Date and time with time zone (e.g., +02:00)
    "%Y-%m-%d %I:%M:%S %p %z",   # 12-hour format with time zone
    "%m/%d/%Y %I:%M:%S %p %z",   # US format with time zone
    "%d/%m/%Y %I:%M:%S %p %z",   # International format with time zone

    # With timezone offset
    "%Y-%m-%dT%H:%M:%S.%f+05:30", # ISO with microseconds and Indian Standard Time offset
    "%Y-%m-%dT%H:%M:%S+05:30",    # ISO without microseconds and IST offset
    "%m/%d/%Y %H:%M:%S+05:30",    # US format with IST offset
    "%d/%m/%Y %H:%M:%S+05:30"     # International format with IST offset
    ]

    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

    return None

def detect_power_events(raw_data) -> pd.DataFrame:
    tracked_events = [
        "Power Glitch",
        "Power Failure Alarm"
    ]
    lines = raw_data.decode('utf-8').split('\n') if isinstance(raw_data, bytes) else raw_data.split('\n')
    event_data = []
    count_per_day_event = defaultdict(int)
    raw_events = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        for event in tracked_events:
            if event in line:
                timestamp_str = line.split(event)[0].strip()
                event_time = parse_timestamp(timestamp_str)
                if event_time:
                    event_date = event_time.strftime("%m/%d/%Y")
                    time_str = event_time.strftime("%I:%M:%S %p")
                    raw_events.append((event_date, event, time_str))
                    count_per_day_event[(event_date, event)] += 1
                break
    for event_date, event, time_str in raw_events:
        total_count = count_per_day_event[(event_date, event)]
        event_data.append({
            "Date of Event": event_date,
            "Event": event,
            "Total Events in Day": total_count,
            "Time of Event": time_str
        })
    return pd.DataFrame(event_data)

def detect_door_events(raw_data) -> pd.DataFrame:
    lines = raw_data.decode('utf-8').split('\n') if isinstance(raw_data, bytes) else raw_data.split('\n')
    data = []
    door_open_time = None
    door_open_date = None
    door_open_count = {}  # Track openings per date

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if "Door Open Event" in line:
            timestamp_str = line.split("Door Open Event")[0].strip()
            door_open_time = parse_timestamp(timestamp_str)
            if door_open_time:
                door_open_date = door_open_time.strftime("%m/%d/%Y")
                # Increment the count for that date
                door_open_count[door_open_date] = door_open_count.get(door_open_date, 0) + 1
            else:
                continue

        elif "Door Close Event" in line and door_open_time is not None:
            parts = line.split("Door Close Event")
            timestamp_str = parts[0].strip()
            try:
                door_close_time = parse_timestamp(timestamp_str)
                if door_close_time:
                    time_of_opening_str = door_open_time.strftime("%I:%M:%S %p")
                    time_of_closing_str = door_close_time.strftime("%I:%M:%S %p")
                    duration_secs = round((door_close_time - door_open_time).total_seconds())
                    no_of_door_openings = door_open_count.get(door_open_date, 1)
                    door_event = 'open'
                    data.append({
                        "Date of Event": door_open_date,
                        "Time of Opening": time_of_opening_str,
                        "Time of Closing": time_of_closing_str,
                        "Total Time of Opening (secs)": duration_secs,
                        "No of Door Openings": no_of_door_openings,
                        "door_event": door_event
                    })
                    door_open_time = None
                    door_open_date = None
            except (ValueError, IndexError):
                continue

    return pd.DataFrame(data)

def detect_refrigerator_failure(raw_data) -> pd.DataFrame:
    lines = raw_data.decode('utf-8').split('\n') if isinstance(raw_data, bytes) else raw_data.split('\n')
    data = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if "System Refrigeration Failure Alarm" in line:
            parts = line.split(',')
            timestamp = parts[0]
            timestamp = parse_timestamp(timestamp)
            
            if timestamp:
                # Convert to strings so JSON can handle them
                date = timestamp.date().isoformat()     # "2025-08-11"
                time = timestamp.time().strftime("%H:%M:%S")  # "09:14:29"
                
                data.append({
                    "Date": date,
                    "Time": time
                })
            
    return pd.DataFrame(data)

# function to check file type
def check_file_type(df: pd.DataFrame) -> str:
    """
    Determine file type (STP1, STP, TSX) based on column existence and mean values.
    Rules:
    - STP1: TC3,TC4,TC7,TC9,Stage1RPM,Stage2RPM exist, all means in {-127,0,127}
    - STP: Stage1/2RPM may exist, if exist means in {-127,0,127}, TC3/4/7/9 exist but means NOT in {-127,0,127}
    - TSX: Stage1/2RPM exist but means NOT in {-127,0,127}, TC3/4/7/9 exist but means NOT in {-127,0,127}, TC8 optional and valid if exists
    """
    
    valid_means = {-127, 0, 127}
    tc_columns = ['TC3', 'TC4', 'TC7', 'TC9']
    stage_columns = ['Stage 1 RPM', 'Stage 2 RPM']

    # --- 1️⃣ STP1 check ---
    if all(col in df.columns for col in tc_columns + stage_columns):
        if all(int(round(df[col].mean())) in valid_means for col in tc_columns + stage_columns):
            return "STP1"

    # --- 2️⃣ STP check ---
    # Stage columns may or may not exist
    stage_check = True
    if any(col in df.columns for col in stage_columns):
        stage_check = all(int(round(df[col].mean())) in valid_means for col in stage_columns if col in df.columns)
    
    # TC3/4/7/9 means must NOT be in valid_means
    tc_check = all(int(round(df[col].mean())) not in valid_means for col in tc_columns)
    
    if stage_check and tc_check:
        return "STP"

    # --- 3️⃣ TSX check ---
    # Stage columns exist but their means NOT in valid_means
    if all(col in df.columns for col in stage_columns):
        stage_invalid = all(int(round(df[col].mean())) not in valid_means for col in stage_columns)
        tc_invalid = all(int(round(df[col].mean())) not in valid_means for col in tc_columns)
        
        if stage_invalid and tc_invalid:
            # Optional TC8 check
            if 'TC8' in df.columns:
                if int(round(df['TC8'].mean())) in valid_means:
                    return "TSX"
            else:
                return "TSX"

    # --- 4️⃣ None matched ---
    return "File Type not Found"

def map_door_status_to_df(df: pd.DataFrame, door_event_df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['Date/Time'] = pd.to_datetime(df['Date/Time']).dt.floor('min')
    df['Door_Status'] = 0  # default

    # Prepare event times
    door_event_df = door_event_df.copy()
    door_event_df['Open_dt'] = pd.to_datetime(
        door_event_df['Date of Event'].astype(str) + ' ' + door_event_df['Time of Opening'].astype(str)
    ).dt.floor('min')
    door_event_df['Close_dt'] = pd.to_datetime(
        door_event_df['Date of Event'].astype(str) + ' ' + door_event_df['Time of Closing'].astype(str)
    ).dt.floor('min')

    # Handle cross-midnight
    mask = door_event_df['Close_dt'] < door_event_df['Open_dt']
    door_event_df.loc[mask, 'Close_dt'] += pd.Timedelta(days=1)

    # Iterate through each event and set statuses
    for _, row in door_event_df.iterrows():
        open_secs = row['Total Time of Opening (secs)']

        # Define cooldown mins based on conditions
        if open_secs < 60:
            cooldown_mins = 60     # 1 hour
        elif 60 <= open_secs <= 300:
            cooldown_mins = 180    # 3 hours
        else:
            cooldown_mins = 360    # 6 hours

        # Mark open period as 1
        mask_open = (df['Date/Time'] >= row['Open_dt']) & (df['Date/Time'] <= row['Close_dt'])
        df.loc[mask_open, 'Door_Status'] = 1

        # Mark cooldown period as -1 (only if still 0)
        cooldown_start = row['Close_dt'] + pd.Timedelta(minutes=1)
        cooldown_end = row['Close_dt'] + pd.Timedelta(minutes=cooldown_mins)
        mask_cooldown = (df['Date/Time'] >= cooldown_start) & (df['Date/Time'] <= cooldown_end)
        df.loc[mask_cooldown & (df['Door_Status'] == 0), 'Door_Status'] = -1

    return df

# Newer preprocessing function, creates events dataframes, checks file type, maps door to df, returns a tuple
def preprocess_puc_file(raw_data) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str] | None:
    columns = [
        "Date/Time", "RTD", "TC1", "TC2", "TC3", "TC4", "TC6", 
        "TC7", "TC9", "TC10", "Setpoint", "Voltage", "PUC_State", "User Offset", 
        "Warm Warning setpoint", "Cold Warning setpoint", "Stage 1 RPM", "Stage 2 RPM", 
        "HxHxRec", "Fan State", "VscRefStageMSB", "VscRefStageLSB", "BUS RTD", 
        "RSSI", "latency", "TC8"
    ]
    
    if isinstance(raw_data, bytes):
        raw_data = raw_data.decode('utf-8')

    lines = raw_data.split('\n')
    data_lines = [line for line in lines if not line.startswith('PUC_VER')]

    if not data_lines:
        return None

    expected_col_count = len(data_lines[0].split(','))
    valid_lines = [line for line in data_lines if len(line.split(',')) == expected_col_count]
    data_str = "\n".join(valid_lines)
    
    door_events = detect_door_events(raw_data)
    power_events = detect_power_events(raw_data)
    ref_df = detect_refrigerator_failure(raw_data)

    df = pd.read_csv(StringIO(data_str), header=None)
    df.columns = columns[:df.shape[1]]
    df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')
    
    file_type = check_file_type(df)
    if file_type == "STP1":
        note = "The provide file is for STP1 the product is built before 2022 there is no sufficient data for analysis. Manual analysis required."
    elif file_type == "File Type not Found":
        note = "File type not recognized. Data will be processed with default settings."
    else:
        note = f"File type detected as {file_type}."
    print(note)

    # Calculate the date 3 months before max date
    # three_months_ago = df['Date/Time'].max() - pd.DateOffset(months=3)
    
    five_months_ago = df['Date/Time'].max() - pd.DateOffset(months=5)
    before_45_days = df['Date/Time'].max() - pd.DateOffset(days=45)
    
    if before_45_days < df['Date/Time'].min():
        return None
    df = map_door_status_to_df(df, door_events)
    if five_months_ago < df['Date/Time'].min():
        return df, door_events, power_events, ref_df, file_type, note
    # df_last_3_months = df[df['Date/Time'] >= three_months_ago]
    return df, door_events, power_events, ref_df, file_type, note

def feature_engineering(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    # Add new column: difference of RTD and setpoint
    df['Diff_RTD_Setpoint'] = df['RTD'] - df['Setpoint']  # When diff is +ve, temp is increasing; else decreasing

    tcs_dict = {
        'RTD': (),
        'TC1': (-20, -15), 
        'TC2': (15, 25), 
        'TC3': (-96, -86), 
        'TC4': (-96, -86),
        'TC6': (-30, -20), 
        'TC7': (15, 26),
        'TC8': (40, 50),
        'TC9': (-np.inf, 68),
        'TC10': (-45, -35)
    }
    
    # Define tolerance for RTD relative to Setpoint
    tolerance_RTD = 1.5
    
    if 'Setpoint' in df.columns and 'User Offset' in df.columns:
        df['lower_bound_RTD'] = df['Setpoint'] + df['User Offset'] - tolerance_RTD
        df['upper_bound_RTD'] = df['Setpoint'] + df['User Offset'] + tolerance_RTD  
    else:
        print("Error: 'Setpoint' or 'User Offset' column is missing. RTD bounds cannot be calculated.")
    
    available_tcs = [tc for tc in tcs_dict if tc in df.columns]
    
    # Step 1: Flag values within normal range for other temperature channels (TC1, TC2, etc.)
    for tc in available_tcs:
        if tc == 'RTD':
            continue
        
        lower_bound, upper_bound = tcs_dict[tc]
        df[f'{tc}_in_range'] = df[tc].between(lower_bound, upper_bound)
        
        df[f'{tc}_trend'] = np.where(
            df[f'{tc}_in_range'],
            0,
            np.where(df[tc] > upper_bound, 1, -1)
        )
        
    # === RTD check: dynamically calculated based on Setpoint ===
    if 'RTD' in df.columns and 'lower_bound_RTD' in df.columns and 'upper_bound_RTD' in df.columns:
        # Check if RTD is within the defined range
        df['RTD_in_range'] = (df['RTD'] >= df['lower_bound_RTD']) & (df['RTD'] <= df['upper_bound_RTD'])
        
        # Add RTD_trend column for trend analysis
        df['RTD_trend'] = np.where(
            df['RTD_in_range'],  # If within range, assign 0
            0,
            np.where(df['RTD'] > df['upper_bound_RTD'], 1, -1)  # If greater than upper bound, trend is 1; else, -1
        )
    else:
        print("Error: 'RTD', 'lower_bound_RTD', or 'upper_bound_RTD' column is missing. RTD range check cannot be performed.")
    
    return df, tcs_dict

def preprocess_puc_filepath(path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str] | None:
    columns = [
        "Date/Time", "RTD", "TC1", "TC2", "TC3", "TC4", "TC6", 
        "TC7", "TC9", "TC10", "Setpoint", "Voltage", "PUC state", "User Offset", 
        "Warm Warning setpoint", "Cold Warning setpoint", "Stage 1 RPM", "Stage 2 RPM", 
        "HxHxRec", "Fan State", "VscRefStageMSB", "VscRefStageLSB", "BUS RTD", 
        "RSSI", "latency", "TC8"
    ]
    
    with open(path, 'rb') as f:
        raw_data = f.read().decode('utf-8')

    lines = raw_data.split('\n')
    data_lines = [line for line in lines if not line.startswith('PUC_VER')]

    if not data_lines:
        return None

    expected_col_count = len(data_lines[0].split(','))
    valid_lines = [line for line in data_lines if len(line.split(',')) == expected_col_count]
    data_str = "\n".join(valid_lines)
    
    door_events = detect_door_events(raw_data)
    power_events = detect_power_events(raw_data)
    ref_df = detect_refrigerator_failure(raw_data)

    df = pd.read_csv(StringIO(data_str), header=None)
    df.columns = columns[:df.shape[1]]
    df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')
    
    file_type = check_file_type(df)
    if file_type == "STP1":
        note = "The provide file is for STP1 the product is built before 2022 there is no sufficient data for analysis. Manual analysis required."
    elif file_type == "File Type not Found":
        note = "File type not recognized. Data will be processed with default settings."
    else:
        note = f"File type detected as {file_type}."
    print(note)

    # Calculate the date 3 months before max date
    # three_months_ago = df['Date/Time'].max() - pd.DateOffset(months=3)
    
    five_months_ago = df['Date/Time'].max() - pd.DateOffset(months=5)
    before_45_days = df['Date/Time'].max() - pd.DateOffset(days=45)
    
    if before_45_days < df['Date/Time'].min():
        return None
    df = map_door_status_to_df(df, door_events)
    if five_months_ago < df['Date/Time'].min():
        return df, door_events, power_events, ref_df, file_type, note
    # df_last_3_months = df[df['Date/Time'] >= three_months_ago]
    return df, door_events, power_events, ref_df, file_type, note