import os
import logging
from flask import render_template, request
from application import app
from application.utils import load_watch_data, parse_filename
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd

# Set up logging
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_summary.log")
logging.basicConfig(filename=log_file_path, level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Define base directories
current_dir = os.path.dirname(os.path.abspath(__file__))
processed_heartrate_data_dir = os.path.abspath(os.path.join(current_dir, '..', 'Processed_heartrate_sublevel_data'))
processed_heartrate_sessions_dir = os.path.abspath(os.path.join(current_dir, '..', 'Processed_heartrate_sessions_data'))
heartrate_metadata_dir = os.path.abspath(os.path.join(current_dir, '..', 'heartrate_metadata'))
data = load_watch_data(processed_heartrate_data_dir)

def get_data_type_from_filename(filename):
    _, data_type = parse_filename(filename)
    return data_type

def prepare_dataframe(df, data_type):
    prepared_df = df.copy()
    if data_type == 'heartrate':
        prepared_df['Time'] = pd.to_datetime(prepared_df['watch_timestamp'])
        prepared_df['Value'] = prepared_df['bpm']
    else:
        return None
    return prepared_df

@app.route("/", methods=["GET", "POST"])
def index():
    try:
        logging.info("Flask app started processing request.")
        overview_html = "No data available"  # Default initialization

        if not data:
            logging.warning("No data available in the processed_heartrate_data directory.")
            return render_template(
                "layout.html",
                overview_plot=overview_html,
                session_plot="No data available",
                data_types=[],
                participants=[],
                sessions=[],
                selected_data_type=None,
                selected_participant=None,
                selected_session=None,
            )

        # Data type selection
        available_data_types = list(data.keys())
        selected_data_type = request.form.get("data_type")
        if not selected_data_type or selected_data_type not in data:
            selected_data_type = available_data_types[0]

        # Participant and session selection
        available_participants = list(data[selected_data_type].keys())
        selected_participant = request.form.get("participant")
        if not selected_participant or selected_participant not in data[selected_data_type]:
            selected_participant = available_participants[0]

        available_sessions = list(data[selected_data_type][selected_participant].keys())
        selected_session = request.form.get("session")
        if not selected_session or selected_session not in data[selected_data_type][selected_participant]:
            selected_session = available_sessions[0]

        logging.info(f"Selected data type: {selected_data_type}")
        logging.info(f"Selected participant: {selected_participant}")
        logging.info(f"Selected session: {selected_session}")

        # Overview Plot: Combine data for all participants and sessions
        p_data = []  # ADHD participants
        n_data = []  # Non-ADHD participants

        for participant, sessions in data[selected_data_type].items():
            for session, csv_files in sessions.items():
                combined_df = pd.DataFrame()  # Combine all CSVs for a session
                for csv_name, df in csv_files.items():
                    file_data_type = get_data_type_from_filename(csv_name)
                    if file_data_type == selected_data_type:
                        prepared_df = prepare_dataframe(df, file_data_type)
                        if prepared_df is not None:
                            combined_df = pd.concat([combined_df, prepared_df])

                if not combined_df.empty:
                    mean_value = combined_df['Value'].mean()
                    data_point = {
                        'Participant': participant,
                        'Session': session,
                        'Value': mean_value
                    }
                    if participant.startswith('P'):
                        p_data.append(data_point)
                    elif participant.startswith('N'):
                        n_data.append(data_point)

        # Generate overview plot
        fig = go.Figure()

        #Function: Sort session names like 'Session_1', 'Session_2', ..., 'Session_13' numerically.
        def sort_sessions(session_names):
      
            return sorted(session_names, key=lambda x: int(x.split('_')[1]))

        if p_data:
            p_df = pd.DataFrame(p_data)
            p_df['Session'] = pd.Categorical(
                p_df['Session'], categories=sort_sessions(p_df['Session'].unique()), ordered=True
            )
            p_mean = p_df.groupby('Session')['Value'].mean().reset_index()
            fig.add_trace(go.Scatter(
                x=p_mean['Session'],
                y=p_mean['Value'],
                name='ADHD Participants (P#)',
                mode='lines+markers'
            ))

        if n_data:
            n_df = pd.DataFrame(n_data)
            n_df['Session'] = pd.Categorical(
                n_df['Session'], categories=sort_sessions(n_df['Session'].unique()), ordered=True
            )
            n_mean = n_df.groupby('Session')['Value'].mean().reset_index()
            fig.add_trace(go.Scatter(
                x=n_mean['Session'],
                y=n_mean['Value'],
                name='Non-ADHD Participants (N#)',
                mode='lines+markers'
            ))

        fig.update_layout(
            title=f'Average {selected_data_type} by Group',
            xaxis_title='Session',
            yaxis_title='Average BPM',
            hovermode='x unified'
        )
        overview_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')


        # Session-Specific Plot (Bottom Graph)
        session_html = ""
        if selected_data_type == 'heartrate':
            session_file_path = os.path.join(
                processed_heartrate_sessions_dir,
                selected_participant,
                f"{selected_session}.csv"  # Main session data file
            )
            logging.info(f"Looking for session file: {session_file_path}")

            if os.path.exists(session_file_path):
                session_combined_df = pd.read_csv(session_file_path)
                session_combined_df['Time'] = pd.to_datetime(session_combined_df['watch_timestamp'])

                # Load Metadata
                metadata_file_path = os.path.join(
                    heartrate_metadata_dir,
                    selected_participant,
                    selected_session,
                    f"{selected_session}_metadata.csv"  # Metadata file in subfolder
                )
                metadata = pd.DataFrame()
                if os.path.exists(metadata_file_path):
                    logging.info(f"Metadata file found: {metadata_file_path}")
                    metadata = pd.read_csv(metadata_file_path)
                    metadata['Time'] = pd.to_datetime(metadata['timestamp'])
                else:
                    logging.warning(f"No metadata file found for session: {metadata_file_path}")

                # Create the graph
                session_fig = px.line(
                    session_combined_df,
                    x="Time",
                    y="bpm",
                    title=f"{selected_participant} - {selected_session} - {selected_data_type} (Session View)"
                )
                session_fig.update_layout(
                    xaxis_title="Time",
                    yaxis_title="BPM"
                )

                # Add Metadata Markers
                if not metadata.empty:
                    for _, row in metadata.iterrows():
                        line_color = "red" if "10-minute" in row['label'].lower() else "green"
                        session_fig.add_vline(
                            x=row['Time'],
                            line=dict(color=line_color, dash="dot"),
                            name=row['label']  # Only shows in legend
                        )

                session_html = pio.to_html(session_fig, full_html=False, include_plotlyjs='cdn')
            else:
                logging.error(f"Session file not found: {session_file_path}")
                session_html = f"No processed session data found for {selected_participant}, {selected_session}"
        else:
            session_html = "No session plot available for this data type."

    except Exception as e:
        import traceback
        logging.error(f"Error encountered: {str(e)}")
        logging.debug(traceback.format_exc())
        overview_html = f"Error generating overview plot: {str(e)}"
        session_html = f"Error generating session plot: {str(e)}"

    return render_template(
        "layout.html",
        overview_plot=overview_html,
        session_plot=session_html,
        data_types=available_data_types,
        participants=available_participants,
        sessions=available_sessions,
        selected_data_type=selected_data_type,
        selected_participant=selected_participant,
        selected_session=selected_session,
    )
