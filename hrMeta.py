import os
import pandas as pd

# Define directories
original_base_dir = "/Users/shehjarsadhu/Desktop/UniversityOfRhodeIsland/Graduate/WBL/Project_MindGame/MindGame-at-home-study-data/Session_Organized_2/heartrate_data" #"Watch_data_org/heartrate_data"  # Original session folders
processed_base_dir = "heartrate_metadata"  # Processed sessions folder

def generate_metadata_for_session(session_path, output_path):
    """
    Generate metadata for a session based on the start of each sub-level and the 10-minute mark.
    """
    metadata = []
    total_duration = 0  # Track total time in seconds
    first_timestamp = None

    # Process each CSV file in the session folder
    for csv_file in sorted(os.listdir(session_path)):
        if csv_file.endswith(".csv"):
            file_path = os.path.join(session_path, csv_file)
            df = pd.read_csv(file_path)
            
            # Get the first timestamp from the file
            if 'watch_timestamp' in df:
                timestamp = pd.to_datetime(df['watch_timestamp'].iloc[0])
                if first_timestamp is None:
                    first_timestamp = timestamp

                # Add a metadata entry for the sub-level start
                metadata.append({"timestamp": timestamp, "label": f"Sub-level {len(metadata) + 1} Start"})

                # Update total duration based on the last timestamp in the file
                last_timestamp = pd.to_datetime(df['watch_timestamp'].iloc[-1])
                total_duration += (last_timestamp - timestamp).total_seconds()

    # Add a 10-minute mark if applicable
    if first_timestamp and total_duration >= 600:  # 600 seconds = 10 minutes
        ten_minute_mark = first_timestamp + pd.Timedelta(seconds=600)
        metadata.append({"timestamp": ten_minute_mark, "label": "10-minute mark"})

    # Save metadata as a CSV
    if metadata:
        metadata_df = pd.DataFrame(metadata)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        metadata_df.to_csv(output_path, index=False)
        print(f"Metadata saved: {output_path}")
    else:
        print(f"No valid data for metadata generation in {session_path}")

def process_all_sessions(original_base_dir, processed_base_dir):
    """
    Generate metadata for all sessions and save in the processed sessions folder.
    """
    for root, dirs, files in os.walk(original_base_dir):
        for dir_name in dirs:
            session_path = os.path.join(root, dir_name)
            relative_path = os.path.relpath(session_path, original_base_dir)
            output_path = os.path.join(processed_base_dir, relative_path, f"{dir_name}_metadata.csv")
            generate_metadata_for_session(session_path, output_path)

# Run the metadata generation
process_all_sessions(original_base_dir, processed_base_dir)
