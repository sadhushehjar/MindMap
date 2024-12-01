import os
import pandas as pd

def parse_filename(filename):
    """Parse the filename to extract participant and data type."""
    parts = filename.replace('.csv', '').split('_')
    if len(parts) < 4:  # Adjusted as session is no longer extracted
        return None, None  # Invalid filename format

    participant = parts[1]  # Second part: Participant ID
    data_type = parts[-1]   # Last part: Data type (e.g., heartrate)
    return participant, data_type

def load_watch_data(base_dir):
    """Traverse the directory structure and load data into a nested dictionary based on folder structure."""
    data = {}

    for root, _, files in os.walk(base_dir):
        # Extract session number from folder name
        session = os.path.basename(root)
        if not session.startswith("S"):  # Assuming session folders start with 'S'
            continue

        for csv_file in files:
            if not csv_file.endswith('.csv'):
                continue

            csv_path = os.path.join(root, csv_file)
            participant, data_type = parse_filename(csv_file)
            if not participant or not data_type:
                print(f"Skipping invalid file: {csv_file}")
                continue

            # Initialize nested structure for data
            if data_type not in data:
                data[data_type] = {}
            if participant not in data[data_type]:
                data[data_type][participant] = {}
            if session not in data[data_type][participant]:
                data[data_type][participant][session] = {}

            # Load CSV into the structure
            try:
                print(f"Loading file: {csv_file} (Participant: {participant}, Session: {session}, Type: {data_type})")
                data[data_type][participant][session][csv_file] = pd.read_csv(csv_path)
            except Exception as e:
                print(f"Error loading file {csv_file}: {e}")

    return data
