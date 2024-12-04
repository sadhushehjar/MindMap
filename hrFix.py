import os
import pandas as pd

# Base directories
raw_base_dir = "Watch_data_org/heartrate_data"
processed_base_dir = "Processed_watch_data_sessions"

# Ensure output directory exists
os.makedirs(processed_base_dir, exist_ok=True)

def process_combined_session_data(session_path, output_file_path):
    """
    Combines all CSVs in a session, adds break rows for gaps > 1.2 seconds, and saves the result.
    """
    combined_df = pd.DataFrame()

    # Combine all CSV files in the session directory
    for file in os.listdir(session_path):
        if file.endswith('.csv'):
            file_path = os.path.join(session_path, file)
            df = pd.read_csv(file_path)
            if 'watch_timestamp' in df and 'bpm' in df:
                df['watch_timestamp'] = pd.to_datetime(df['watch_timestamp'])
                combined_df = pd.concat([combined_df, df])

    # Skip if no valid data
    if combined_df.empty:
        print(f"No valid data in session: {session_path}")
        return

    # Sort combined data by timestamp
    combined_df = combined_df.sort_values('watch_timestamp').reset_index(drop=True)

    # Insert break rows for time gaps
    new_rows = []
    for i in range(len(combined_df) - 1):
        new_rows.append(combined_df.iloc[i].to_dict())
        time_diff = (combined_df.iloc[i + 1]['watch_timestamp'] - combined_df.iloc[i]['watch_timestamp']).total_seconds()
        if time_diff > 1.2:
            new_rows.append({
                'watch_timestamp': combined_df.iloc[i]['watch_timestamp'] + pd.Timedelta(seconds=1.2),
                'bpm': None,
            })

    # Add the last row
    new_rows.append(combined_df.iloc[-1].to_dict())

    # Save the processed session data
    processed_df = pd.DataFrame(new_rows)
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    processed_df.to_csv(output_file_path, index=False)
    print(f"Processed and saved session: {output_file_path}")

def preprocess_all_sessions(raw_base_dir, processed_base_dir):
    """
    Recursively preprocesses all sessions, combines CSVs, and adds breaks.
    """
    for root, dirs, files in os.walk(raw_base_dir):
        for dir_name in dirs:
            session_path = os.path.join(root, dir_name)
            output_file_path = os.path.join(
                processed_base_dir, os.path.relpath(session_path, raw_base_dir) + ".csv"
            )
            process_combined_session_data(session_path, output_file_path)

# Preprocess all sessions
preprocess_all_sessions(raw_base_dir, processed_base_dir)
print(f"All sessions processed and saved to {processed_base_dir}.")
