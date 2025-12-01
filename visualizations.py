import pandas as pd
import altair as alt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
import base64
alt.data_transformers.enable('vegafusion')  # Use data server for large datasets

# Thermocouple label mapping
TC_LABELS = {
    'RTD': 'RTD',
    'Setpoint': 'Setpoint',
    'TC1': '1st stage suction',
    'TC2': 'Air inlet',
    'TC3': 'Evaporator inlet',
    'TC4': 'Evaporator outlet',
    'TC6': '2nd stage suction',
    'TC7': 'Liquid line',
    'TC8': '1st sump',
    'TC9': '2nd sump',
    'TC10': 'BPHX',

    'RTD_trend': 'RTD Trend',
    'TC1_trend': '1st stage suction Trend',
    'TC2_trend': 'Air inlet Trend',
    'TC3_trend': 'Evaporator inlet Trend',
    'TC4_trend': 'Evaporator outlet Trend',
    'TC6_trend': '2nd stage suction Trend',
    'TC7_trend': 'Liquid line Trend',
    'TC8_trend': '1st sump Trend',
    'TC9_trend': '2nd sump Trend',
    'TC10_trend': 'BPHX Trend',
}
def make_flagged(filtered, time_tolerance="1min"):
    """
    Identify consecutive time durations where Sustained_Issue is True
    and return the maximum-duration block as a new dataframe.

    Parameters
    ----------
    filtered : pd.DataFrame
        DataFrame with at least ['Date/Time', 'Trend_Flag'] columns,
        already filtered to Sustained_Issue == True.
    time_tolerance : str or Timedelta, optional
        The max gap allowed to consider times consecutive (default '1min').

    Returns
    -------
    pd.DataFrame or None
        A dataframe with columns [Start, End, Trend_Flag, Count, Duration]
        containing the block with the maximum duration, or None if no block exists.
    """
    if filtered is None or filtered.empty:
        return None

    # Ensure datetime
    filtered = filtered.copy()
    filtered['Date/Time'] = pd.to_datetime(filtered['Date/Time'], errors="coerce")
    filtered = filtered.dropna(subset=['Date/Time'])

    if filtered.empty:
        return None

    # Sort by time
    filtered = filtered.sort_values('Date/Time').reset_index(drop=True)

    # Identify breaks in consecutive timestamps
    filtered['block'] = (filtered['Date/Time'].diff() > pd.Timedelta(time_tolerance)).cumsum()

    # Group by blocks
    groups = (
        filtered.groupby('block')
        .agg(
            Start=('Date/Time', 'first'),
            End=('Date/Time', 'last'),
            Trend_Flag=('Trend_Flag', lambda x: x.mode()[0] if not x.mode().empty else None),
            Count=('Date/Time', 'size')
        )
        .reset_index(drop=True)
    )

    if groups.empty:
        return None

    # Duration
    groups['Duration'] = groups['End'] - groups['Start']

    if groups['Duration'].dropna().empty:
        return None

    try:
        flagged = groups.loc[groups['Duration'].idxmax()].to_frame().T.reset_index(drop=True)
        return flagged
    except Exception as e:
        import logging
        logging.exception("make_flagged failed")
        return None

def plot_sensor_values(plot_df: pd.DataFrame, flagged: pd.DataFrame):
    """
    Plot sensor values over time. If a flagged dataframe (from make_flagged) 
    is provided, zoom in to a 24-hour window starting from the flagged Start time.
    """

    # Ensure 'Date/Time' is datetime
    plot_df = plot_df.copy()
    plot_df['Date/Time'] = pd.to_datetime(plot_df['Date/Time'])

    # Time filter if flagged provided
    if flagged is not None and not flagged.empty:
        flagged = flagged.copy()
        # Use 'Start' and 'End' from the flagged DataFrame
        plot_start = pd.to_datetime(flagged.loc[0, 'Start']) #type: ignore
        plot_end = pd.to_datetime(flagged.loc[0, 'End']) + pd.Timedelta(hours=24) #type: ignore
        plot_df = plot_df[(plot_df['Date/Time'] >= plot_start) & (plot_df['Date/Time'] <= plot_end)]
    else:
        plot_start = plot_end = None

    # Columns to include
    columns_to_plot = ['RTD', 'Setpoint', 'TC1', 'TC2', 'TC10', 'TC3', 'TC8', 'TC4', 'TC6']
    available_columns = [col for col in columns_to_plot if col in plot_df.columns]
    plot_df[available_columns] = plot_df[available_columns].apply(pd.to_numeric, errors='coerce')

    # Plotting
    fig, ax = plt.subplots(figsize=(16, 8))

    for col in available_columns:
        label = TC_LABELS.get(col, col)  # Use mapped label or fallback
        ax.plot(plot_df['Date/Time'], plot_df[col], label=label)

    # Format x-axis
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.xticks(rotation=45)

    ax.set_title(
        f"Sensor Trend Values from {plot_start.date()} to {plot_end.date()}" #type: ignore
        if plot_start is not None else "Sensor Trend Values"
    )
    ax.set_xlabel("Date/Time")
    ax.set_ylabel("Values")
    ax.legend()
    ax.grid(True)
    plt.tight_layout()

    # Encode to base64 for HTML embedding
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)

    return f"data:image/png;base64,{img_base64}"
    # return plt

def plot_sensor_trends(df: pd.DataFrame, flagged: pd.DataFrame) -> str | None:
    """
    Plot sensor trend values over time. If a flagged dataframe (from make_flagged)
    is provided, zoom in to a 24-hour window starting from the flagged Start time.
    """

    df = df.copy()
    df['Date/Time'] = pd.to_datetime(df['Date/Time'])

    if flagged is not None and not flagged.empty:
        flagged = flagged.copy()
        plot_start = pd.to_datetime(flagged.loc[0, 'Start']) #type: ignore
        plot_end = pd.to_datetime(flagged.loc[0, 'End']) + pd.Timedelta(hours=24) #type: ignore

        df = df[(df['Date/Time'] >= plot_start) & (df['Date/Time'] <= plot_end)].copy()
    else:
        return None

    tc_trend_cols = [
        'RTD_trend', 'TC1_trend', 'TC2_trend', 'TC10_trend',
        'TC3_trend', 'TC4_trend', 'TC6_trend', 'TC8_trend',
        'PUC_State', 'TC9_trend', 'TC7_trend'
    ]
    columns_to_plot = ['Stage 1 RPM', 'Stage 2 RPM'] + [col for col in tc_trend_cols if col in df.columns]

    plt.figure(figsize=(12, 6))

    for col in columns_to_plot:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            label = TC_LABELS.get(col, col)
            plt.plot(df['Date/Time'], df[col], label=label)

    plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.title(f"Sensor Trend Values from {plot_start.date()} to {plot_end.date()}")
    plt.xlabel("Date/Time")
    plt.ylabel("Trend Values")
    plt.legend()
    plt.tight_layout()

    # Convert to base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"

def get_absolute_df(df):
    flagged = df[df['Sustained_Issue']].copy()
    core_columns = ['RTD', 'TC1', 'TC2', 'TC8','TC10','TC3', 'TC4','TC6', 'TC9','TC7']
    column_to_absolute_df = core_columns + ['Stage 1 RPM', 'Stage 2 RPM']

    summary_absolute_df = []

    # Check if 'flagged' exists and is not empty
    if 'flagged' in locals() and not flagged.empty:
        data_source = flagged
        source_label = "Flagged Period"
    else:
        data_source = df  # fallback to full data
        source_label = "Full Dataset (No Issues Detected)"

    # Loop through each column and collect stats
    for col in column_to_absolute_df:
        if col in data_source.columns:
            min_val = data_source[col].min()
            max_val = data_source[col].max()
            mean_val = data_source[col].mean()
            min_date = data_source.loc[data_source[col].idxmin(), 'Date/Time'].strftime('%d-%m-%Y %H:%M:%S')
            max_date = data_source.loc[data_source[col].idxmax(), 'Date/Time'].strftime('%d-%m-%Y %H:%M:%S')

            summary_absolute_df.append({
                'Column': col,
                'Min': min_val,
                'Min Date': min_date,
                'Mean': mean_val,
                'Max': max_val,
                'Max Date': max_date
            })

    # Create and show summary DataFrame
    summary_absolute_df = pd.DataFrame(summary_absolute_df)
    return summary_absolute_df

def get_trend_df(df):
    flagged = df[df['Sustained_Issue']].copy()
    columns_to_plot = ['RTD_trend', 'TC1_trend', 'TC2_trend', 'TC10_trend', 'TC3_trend', 'TC4_trend', 'TC6_trend', 'TC9_trend', 'TC7_trend', 'TC8_trend']
    column_to_trend_df = [col for col in columns_to_plot if col in df.columns]
    summary_trend_df = []

    # Check if 'flagged' exists and is not empty
    if 'flagged' in locals() and not flagged.empty:
        data_source = flagged
        source_label = "Flagged Period"
    else:
        data_source = df  # fallback to full data
        source_label = "Full Dataset (No Issues Detected)"

    # Loop through each column and collect stats

    for col in column_to_trend_df:
        if col in data_source.columns:
            min_val = data_source[col].min()
            max_val = data_source[col].max()
            mean_val = data_source[col].mean()
            min_date = data_source.loc[data_source[col].idxmin(), 'Date/Time'].strftime('%Y-%m-%d %H:%M:%S')
            max_date = data_source.loc[data_source[col].idxmax(), 'Date/Time'].strftime('%Y-%m-%d %H:%M:%S')

            summary_trend_df.append({
                'Column': col,
                'Min': round(min_val, 2),
                'Min Date': min_date,
                'Mean': round(mean_val, 2),
                'Max': round(max_val, 2),
                'Max Date': max_date
            })

    # Create and show summary DataFrame
    summary_trend_df = pd.DataFrame(summary_trend_df)
    return summary_trend_df

def plot_door_histogram(df: pd.DataFrame):
    if df.empty:
        print("No door events data available for histogram.")
        return None

    aggregated_df = df.groupby('Date of Event', as_index=False)['No of Door Openings'].max()

    # Ensure correct types and drop NaN
    aggregated_df['Date of Event'] = pd.to_datetime(aggregated_df['Date of Event'], errors='coerce')
    aggregated_df['No of Door Openings'] = pd.to_numeric(aggregated_df['No of Door Openings'], errors='coerce')
    aggregated_df = aggregated_df.dropna(subset=['Date of Event', 'No of Door Openings']) #type: ignore

    # Ensure DataFrame is not empty and columns are present
    if aggregated_df.empty or 'Date of Event' not in aggregated_df.columns or 'No of Door Openings' not in aggregated_df.columns:
        print("No valid data for Altair chart.")
        return None

    # Create histogram
    hist = alt.Chart(aggregated_df).mark_bar().encode(
        x=alt.X('Date of Event:T', title='Date'),
        y=alt.Y('No of Door Openings:Q', title='No of Door Openings'),
        tooltip=['Date of Event:T', 'No of Door Openings:Q']
    ).properties(width=800, height=400)

    return hist

# def plot_trend_issue(df: pd.DataFrame):
#     from .summary import get_root_cause
#     root_cause = get_root_cause(df)
    
#     ddf = df[df['Trend_Flag'] == root_cause].copy()
#     print(f"\nHere's the ddf in plot_trend_issue:\n{ddf}\n")
    
#     ddf['Date'] = pd.to_datetime(ddf['Date/Time'])  # Ensure datetime format

#     # Create the figure and axis
#     fig, ax = plt.subplots(figsize=(16, 8))

#     # List of columns to plot
#     columns_to_plot = ['RTD', 'TC1', 'TC2', 'TC8', 'TC10', 'TC3', 'TC4', 'TC6', 'TC9', 'TC7']

#     for column in columns_to_plot:
#         if column in ddf.columns:
#             ax.plot(ddf['Date'], ddf[column], label=column)

#     ax.set_title('Trend Analysis')
#     ax.set_xlabel('Date/Time')
#     ax.set_ylabel('Value')
#     ax.legend()
#     ax.grid(True)
#     fig.autofmt_xdate()  # Rotate date labels
#     fig.tight_layout()

#     # Encode to base64 for HTML
#     buf = io.BytesIO()
#     fig.savefig(buf, format='png')
#     buf.seek(0)
#     img_base64 = base64.b64encode(buf.read()).decode('utf-8')
#     buf.close()
#     plt.close(fig)
    
#     return f"data:image/png;base64,{img_base64}"

def plot_trend_issue_altair(df: pd.DataFrame):
    from .summary import get_root_cause
    root_cause = get_root_cause(df)
    ddf = df[df['Trend_Flag'] == root_cause].copy()
    # print(f"\nHere's the ddf in plot_trend_issue_altair:\n{ddf}\n")
    
    ddf['Date'] = pd.to_datetime(ddf['Date/Time'])

    columns_to_plot = ['RTD', 'TC1', 'TC2', 'TC8', 'TC10', 'TC3', 'TC4', 'TC6', 'TC9', 'TC7']
    available_columns = [col for col in columns_to_plot if col in ddf.columns]
    if not available_columns:
        return None

    melted = ddf.melt(
        id_vars=['Date'],
        value_vars=available_columns,
        var_name='Sensor',
        value_name='Value'
    )

    chart = alt.Chart(melted).mark_line().encode(
        x=alt.X('Date:T', title='Date/Time'),
        y=alt.Y('Value:Q', title='Value'),
        color='Sensor:N',
        tooltip=['Date:T', 'Sensor:N', 'Value:Q']
    ).properties(
        title='Trend Analysis',
        width=800,
        height=400
    ).interactive()

    return chart

def plot_tc10(df, lower_bound=-45, upper_bound=-35):
    """
    Create an Altair scatter plot of TC10 with bound lines and annotations.
    
    Parameters:
        df (pd.DataFrame): Must contain 'TC10' column.
        lower_bound (float): Lower horizontal bound line.
        upper_bound (float): Upper horizontal bound line.
    
    Returns:
        dict: Vega-Lite spec (JSON-serializable).
    """
    df = df.copy()
    df["Date/Time"] = pd.to_datetime(df["Date/Time"], errors="coerce")
    df = df.dropna(subset=["Date/Time", "TC10"])
    df["TC10"] = pd.to_numeric(df["TC10"], errors="coerce")

    if df.empty:
        return None  # nothing to plot

    df["color"] = df["TC10"].apply(
        lambda x: "blue" if lower_bound <= x <= upper_bound else "red"
    )

    # Scatter points
    points = alt.Chart(df).mark_circle(size=60).encode(
        x="Date/Time:T",
        y="TC10:Q",
        color=alt.Color("color", scale=None),
        tooltip=["Date/Time:T", "TC10:Q"]
    )

    # Bound lines
    lower_rule = alt.Chart(pd.DataFrame({"y": [lower_bound]})).mark_rule(
        color="green", strokeDash=[6, 3]
    ).encode(y="y")

    upper_rule = alt.Chart(pd.DataFrame({"y": [upper_bound]})).mark_rule(
        color="orange", strokeDash=[6, 3]
    ).encode(y="y")

    annotations = alt.Chart(pd.DataFrame({
        "y": [lower_bound, upper_bound],
        "text": [f"Lower Bound = {lower_bound}", f"Upper Bound = {upper_bound}"],
        "color": ["green", "orange"]
    })).mark_text(align="left", dx=5, dy=-5).encode(
        x=alt.value(5),  # show at left
        y="y",
        text="text",
        color=alt.Color("color", scale=None)
    )

    return (points + lower_rule + upper_rule + annotations).properties(
        title="TC10 with Bound Check",
        width=600,
        height=400
    )

def plot_tc1_tc6(df: pd.DataFrame):
    """
    Create an Altair line plot for TC1 (green) and TC6 (grey).

    Parameters:
        df (pd.DataFrame): Must contain 'TC1' and 'TC6' columns.

    Returns:
        dict: Vega-Lite spec (JSON-serializable)
    """
    df = df.reset_index().rename(columns={"index": "Index"})
    
    # Reshape to long format for Altair
    df_long = df.melt(id_vars="Date/Time", value_vars=["TC1", "TC6"],
                      var_name="Series", value_name="Temperature")
    
    # Map colors to series
    color_scale = alt.Scale(domain=["TC1", "TC6"], range=["green", "grey"])
    
    chart = alt.Chart(df_long).mark_line().encode(
        x="Date/Time",
        y="Temperature",
        color=alt.Color("Series", scale=color_scale,
                        legend=alt.Legend(title="Legend", orient="top-left"))
    ).properties(
        title="TC1 and TC6 Line Plot",
        width=600,
        height=400
    )
    
    return chart