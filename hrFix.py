import os
import pandas as pd

# Base directory (This is the only thing you need to change to make this work with yours hopefully)
raw_sublevel_dir = "Watch_data_org/heartrate_data"
processed_sublevel_dir = "Processed_heartrate_sublevel_data"
processed_session_dir = "Processed_heartrate_sessions_data"

# Check for Dircetories 
os.makedirs(processed_sublevel_dir, exist_ok=True)
os.makedirs(processed_session_dir, exist_ok=True)

# Function: Add rows for each second missed in the DataFrame, marking errors in a new column. 
def add_missing_seconds(df):

    new_rows = []
    for i in range(len(df) - 1):
        current_row = df.iloc[i].to_dict()

        # Mark ZERO error if bpm is 0
        if current_row['bpm'] == 0:
            current_row['bpm'] = None
            current_row['DATA ERROR'] = "ZERO"
        else:
            current_row['DATA ERROR'] = ""

        new_rows.append(current_row)

        # Add rows for missing seconds
        time_diff = (df.iloc[i + 1]['watch_timestamp'] - df.iloc[i]['watch_timestamp']).total_seconds()
        if time_diff > 1:
            current_time = df.iloc[i]['watch_timestamp']
            for _ in range(int(time_diff) - 1):
                current_time += pd.Timedelta(seconds=1)
                new_rows.append({
                    'watch_timestamp': current_time,
                    'bpm': None,
                    'DATA ERROR': "SR"  # Sample Rate error
                })

    # Process the last row
    last_row = df.iloc[-1].to_dict()
    if last_row['bpm'] == 0:
        last_row['bpm'] = None
        last_row['DATA ERROR'] = "ZERO"
    else:
        last_row['DATA ERROR'] = ""

    new_rows.append(last_row)
    return pd.DataFrame(new_rows)

#Function: Process a single sub-level CSV file.
def process_sublevel_csv(input_file, output_file):

    df = pd.read_csv(input_file)
    if 'watch_timestamp' not in df or 'bpm' not in df:
        print(f"Invalid file format, skipping: {input_file}")
        return

    # Convert timestamp column to datetime and sort
    df['watch_timestamp'] = pd.to_datetime(df['watch_timestamp'])
    df = df.sort_values('watch_timestamp').reset_index(drop=True)

    # Process data to handle zero values and missing seconds
    processed_df = add_missing_seconds(df)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    processed_df.to_csv(output_file, index=False)
    print(f"Processed and saved sub-level file: {output_file}")

# Function: Combine sub-level CSVs for a session and process the combined data.
def process_combined_session(session_path, output_file):

    combined_df = pd.DataFrame()

    # Combine all sub-level CSVs in the session directory
    for file in os.listdir(session_path):
        if file.endswith('.csv'):
            file_path = os.path.join(session_path, file)
            df = pd.read_csv(file_path)
            if 'watch_timestamp' in df and 'bpm' in df:
                df['watch_timestamp'] = pd.to_datetime(df['watch_timestamp'])
                combined_df = pd.concat([combined_df, df])

    if combined_df.empty:
        print(f"No valid data in session: {session_path}")
        return

    # Sort and process combined data
    combined_df = combined_df.sort_values('watch_timestamp').reset_index(drop=True)
    processed_df = add_missing_seconds(combined_df)

    # Save processed session data
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    processed_df.to_csv(output_file, index=False)
    print(f"Processed and saved session: {output_file}")

# Function: Process both sub-level and session-level data.
def process_all_data(raw_dir, sublevel_dir, session_dir):
  
    print("Processing sub-level CSV files...")
    for root, dirs, files in os.walk(raw_dir):
        for file in files:
            if file.endswith('.csv'):
                input_file = os.path.join(root, file)
                output_file = os.path.join(sublevel_dir, os.path.relpath(input_file, raw_dir))
                process_sublevel_csv(input_file, output_file)

    print("Processing session CSV files...")
    for root, dirs, files in os.walk(raw_dir):
        for dir_name in dirs:
            session_path = os.path.join(root, dir_name)
            output_file = os.path.join(session_dir, os.path.relpath(session_path, raw_dir) + ".csv")
            process_combined_session(session_path, output_file)

# Run the script
process_all_data(raw_sublevel_dir, processed_sublevel_dir, processed_session_dir)
print("Processing completed.")
