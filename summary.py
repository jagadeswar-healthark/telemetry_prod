# this file is meant to generate summary and the generate_summary() function is exported
from turtle import st
import pandas as pd
from .visualizations import get_absolute_df, get_trend_df

excel_path = r"C:\TFS Telemetry Production\Final App07_08\Final App\Issues Actual.xlsx"

# helper functions to set variables
def set_trend_dict(df: pd.DataFrame, tcs_list: dict) -> dict:
    trends = {}
    for tc in tcs_list:
        if tc in df.columns:
            trends[tc] = 'Decreasing' if df[f'{tc}_trend'].mean() < 0 else 'Increasing'
            
    return trends
    
def get_root_cause(df: pd.DataFrame):
    if df.empty:
        root_cause = "Not Applicable"
    
    if df['Trend_Flag'].notnull().any():
        final_label = df.loc[
            ~df['Trend_Flag'].isin([
                "No issue detected - your device is working properly",
                "Door Open Event, Ignored"
            ]),
            'Trend_Flag'
        ]

        if not final_label.empty:
            root_cause = final_label.value_counts().idxmax()
        else:
            root_cause = "No issue detected - your device is working properly"
    else:
        root_cause = "Not Applicable"
    
    return root_cause
# end of helper functions

# fetches observations
def get_observation(df: pd.DataFrame, trends: dict, root_cause):
    # Read supporting sheets
    condition = pd.read_excel(excel_path, sheet_name='Condition')
    verification = pd.read_excel(excel_path, sheet_name='Verification')

    # Normalize root_cause into a clean list
    if isinstance(root_cause, str):
        root_cause_list = [rc.strip() for rc in root_cause.split(",")]
    elif isinstance(root_cause, list):
        root_cause_list = [str(rc).strip() for rc in root_cause]
    else:
        root_cause_list = [str(root_cause).strip()]

    # --- Collect TCs from all root causes ---
    TC_list = []

    for rc in root_cause_list:
        filtered_con = condition[condition['Issue'] == rc]

        if filtered_con.empty:
            continue

        tc_string = filtered_con.iloc[0]['TC Involved']
        tc_split = [tc.strip() for tc in tc_string.split(",") if tc.strip()]
        TC_list.extend(tc_split)

    # Deduplicate
    TC_list = list(set(TC_list))

    # Construct header text
    total_days = (df['Date/Time'].max() - df['Date/Time'].min()).days + 1

    obs_text = f"""
        The uploaded file has been analyzed from {df['Date/Time'].min()} to {df['Date/Time'].max()}.
        Total number of days analyzed: {total_days} days.

        <b>Verification Method:</b>
        """

    # If no TCs found, return
    if not TC_list:
        return obs_text + "No TC Involved"

    text_list = []

    # Iterate through all TCs involved
    for tc in TC_list:
        if tc not in trends:
            continue

        trend = trends[tc]

        # Fetch matching row in Verification sheet
        filtered_ver = verification[verification['TCs'] == tc]
        if filtered_ver.empty:
            continue

        text = filtered_ver.iloc[0][trend]
        actual_name = filtered_ver.iloc[0]['Actual Name']

        text_to_add = f"""
            - {actual_name} ({tc}) was {trend}.
                Impact: {text}
            """
        text_list.append(text_to_add)

    return obs_text + "".join(text_list)

def event_summary(door_events_df: pd.DataFrame, power_events_df: pd.DataFrame, ref_df: pd.DataFrame, duration_df: pd.DataFrame):
    Door_opening_count = 0
    Door_opening_max_time = 0
    Door_opening_avg_time = 0
    Door_opening_min_time = 0
    Door_openings_avg_per_day = 0
    last_door_opening = "N/A"
    power_event_exceeds_threshold_sum = 0
    
    # isolating average door opening time
    if not door_events_df.empty:
        Door_opening_count = door_events_df['No of Door Openings'].sum()
        Door_opening_count_morethan_six = door_events_df[door_events_df['No of Door Openings'] > 6]['No of Door Openings'].nunique()
        Door_opening_count_morethan_six_Count = door_events_df[door_events_df['No of Door Openings'] > 6]['No of Door Openings'].count()
        Door_opening_max_time = door_events_df['Total Time of Opening (secs)'].max()
        Door_opening_avg_time = door_events_df['Total Time of Opening (secs)'].mean()
        Door_opening_min_time = door_events_df['Total Time of Opening (secs)'].min()
        df_60 = door_events_df[door_events_df['Total Time of Opening (secs)'] > 60]
        Door_openings_morethan_sixty_sec = df_60['Date of Event'].nunique()  # count unique days
        Door_openings_morethan_sixty_sec_Count = df_60[df_60['Total Time of Opening (secs)'] > 60]['No of Door Openings'].count()  # Actual count days
        Door_opening_avg_time = round(Door_opening_avg_time, 2)
        Door_openings_avg_per_day = round(door_events_df['No of Door Openings'].mean(), 2)

        last_door_opening = door_events_df['Date of Event'].max()
        
    power_summary_text = ""
    power_event_days = 0 
    if not power_events_df.empty:
        power_event_days = power_events_df[power_events_df['Event'] == 'Power Failure Alarm']['Date of Event'].nunique()
        filtered_df = power_events_df[
            (power_events_df['Event'] == 'Power Failure Alarm') &
            (power_events_df['Count of This Event on Day'] >= 2)
        ].copy()

        if not filtered_df.empty:
            filtered_df['Exceeds Threshold By'] = filtered_df['Count of This Event on Day'] - 1
            power_events_df_sum = power_events_df[power_events_df['Event'] == 'Power Failure Alarm']
            power_event_exceeds_threshold_sum = int(power_events_df_sum['Count of This Event on Day'].sum())
            
            # Format each row as "YYYY-MM-DD: N"
            power_summary_lines = [
                f"{row['Date of Event']}: {row['Exceeds Threshold By']}"
                for _, row in filtered_df.iterrows()
            ]
            power_summary_text = "\n".join(power_summary_lines)
        else:
            power_summary_text = "No instances of power failure alarms exceeding the set threshold."
    else:
        power_summary_text = "No power events data available."
        
    issues_detected = ','.join(duration_df['Trend_Flag'].unique().tolist())

    # Build detailed issue summary per flag
    duration_df['Date/Time'] = pd.to_datetime(duration_df['Date/Time'])
    duration_df = duration_df.sort_values(['Trend_Flag', 'Date/Time']).reset_index(drop=True)

    issue_summaries = []
    for flag, group in duration_df.groupby('Trend_Flag'):
        group['block'] = (group['Date/Time'].diff() > pd.Timedelta(minutes=1)).cumsum()
        blocks = (
            group.groupby('block')
            .agg(Start=('Date/Time', 'first'), End=('Date/Time', 'last'))
            .reset_index(drop=True)
        )
        block_strings = [
            f"{row.Start.strftime('%Y-%m-%d %H:%M')} - {row.End.strftime('%Y-%m-%d %H:%M')}" #type: ignore
            for row in blocks.itertuples()
        ]
        issue_summaries.append(f"{flag}: {', '.join(block_strings)}")

    issues_summary_text = "\n        ".join(issue_summaries)

    # Add into your existing summary
    final_summary = f"""
    Door Events:
        Door Opening Count Across Uploaded Files: {Door_opening_count} times.
        Door Opening More Than Threshold (Count is 6): {Door_opening_count_morethan_six} Days.
        Door Opening More Than Threshold (Actual Count): {Door_opening_count_morethan_six_Count} times.
        Door Opening Average Time: {Door_opening_avg_time} seconds.
        Door Opening Max Time: {Door_opening_max_time} seconds.
        Door Opening Min Time: {Door_opening_min_time} seconds.
        Door Openings Count More Than Sixty Seconds: {Door_openings_morethan_sixty_sec} in days.
        Door Openings More Than Sixty Seconds (Actual Count): {Door_openings_morethan_sixty_sec_Count} times.
        Average Door Openings per Day: {Door_openings_avg_per_day}.
        Last Door Closing Date: {last_door_opening}.

    Power Events:
        Total Distinct Days with Power Failure Alarms Across Uploaded Files:
        {power_event_days}.

        Power Failure Alarm Dates where Threshold (2 per day) was Exceeded:
        {power_summary_text}

        Total Number of Power Failure Alarm Events (Only Counting Above Threshold Occurrences):
        {power_event_exceeds_threshold_sum}.
        
    Event Duration:
        Detected Issues: {issues_detected}

        Detailed Issues:
            {issues_summary_text}
    """
        
    if not ref_df.empty:
        add = f"""
        Refrigeration Events:
            Total Count: {ref_df['Date'].count()}
        """
        final_summary = final_summary + add

    return final_summary, power_event_exceeds_threshold_sum

# generates explanation of root cause
def generate_cause_explanation(root_cause, excel_path=excel_path):

    data = pd.read_excel(excel_path, sheet_name='Issues')

    filtered_data = data[data['Issue'] == root_cause]

    if not filtered_data.empty:
        suggestion = str(filtered_data['Suggestions'].iloc[0])
    else:
        suggestion = "No suggestions available for this issue."
    # action = str(filtered_data['Preventive Action'].iloc[0])
    
    summary_sugg_var = f"""
        Issue Detected: {root_cause}
        Suggestions: {suggestion}
    """
    
    return summary_sugg_var

# def generate_cause_explanation(issues_detected, excel_path=excel_path):
#     """
#     Generates suggestions for one or more issues.
    
#     issues_detected: list of issues OR single string
#     """
#     data = pd.read_excel(excel_path, sheet_name='Issues')
    
#     # Ensure it's a list
#     if isinstance(issues_detected, str):
#         issues_detected = [issues_detected]
    
#     explanations = []
    
#     for issue in issues_detected:
#         filtered_data = data[data['Issue'] == issue]
#         if not filtered_data.empty:
#             suggestion = str(filtered_data['Suggestions'].iloc[0])
#         else:
#             suggestion = "No suggestions available for this issue."
        
#         explanations.append(f"Issue Detected: {issue}\nSuggestions: {suggestion}")
    
#     # Join all explanations into a single string
#     summary_sugg_var = "\n\n".join(explanations)
    
#     return summary_sugg_var

# main function to be implemented. Import this wherever required
def generate_summary(df: pd.DataFrame, door_events_df: pd.DataFrame, power_events_df: pd.DataFrame, 
                     original_door_df: pd.DataFrame, tcs_list: dict[str, tuple], ref_df: pd.DataFrame,
                     duration_df: pd.DataFrame
                    ):
    
    events, sum_power_threshold = event_summary(original_door_df, power_events_df, ref_df, duration_df)
    
    root_cause = get_root_cause(df) if sum_power_threshold < 2 else "Power Failure Issue Detected"
    
    trends = set_trend_dict(df, tcs_list)
    
    absolute_df = get_absolute_df(df)
    absolute_df = absolute_df[absolute_df['Mean'] != 0]
    
    trend_df = get_trend_df(df)
    trend_df = trend_df[trend_df['Mean'] != 0]
    
    # this will be our title
    title = "📊 GenAI Summary: Telemetry-Based Preventive Maintenance Analysis"
    
    # observation block
    observation = get_observation(df, trends, root_cause)
    
    # door summary text
    door_events_summary = door_events_df.to_dict(orient='records') if not door_events_df.empty else []
    
    # event summary text
    power_events_summary = power_events_df.to_dict(orient='records') if not power_events_df.empty else []
    
    # refrigeration dataframe
    ref_events_df = ref_df.to_dict(orient="records") if not ref_df.empty else []
    
    # cause explanation block
    cause_explanation = generate_cause_explanation(root_cause)

    return {
        "title": title,
        "observation": observation,
        "door_df": door_events_summary,
        "power_df": power_events_summary,
        "ref_df": ref_events_df,
        "Summary: Events": events,
        "🧠 Root Cause Explanation:": cause_explanation,
        "absolute_df": absolute_df.to_dict(orient="records"),
        "trend_df": trend_df.to_dict(orient="records")
    }