from application import app
from flask import render_template, request
from application.utils import load_watch_data, parse_filename
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import os
import pandas as pd
import numpy as np

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(current_dir, '..', 'Watch_data_org'))
data = load_watch_data(base_dir)

def get_data_type_from_filename(filename):
    """Extract the data type from the filename."""
    _, data_type = parse_filename(filename)
    return data_type

def prepare_dataframe(df, data_type):
    """Prepare dataframe by mapping columns correctly based on data type."""
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
        if not data:
            print("No data available.")
            return render_template(
                "layout.html",
                overview_plot="No data available",
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

        # Overview Plot: For now just "Average BPM" across sessions for P# and N# but I will make a more robust system later 
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

                # Calculate session average BPM
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

        # Plot overview graph
        fig = go.Figure()
        if p_data:
            p_df = pd.DataFrame(p_data)
            p_mean = p_df.groupby('Session')['Value'].mean().reset_index()
            fig.add_trace(go.Scatter(
                x=p_mean['Session'], 
                y=p_mean['Value'],
                name='ADHD Participants (P#)',
                mode='lines+markers'
            ))
        if n_data:
            n_df = pd.DataFrame(n_data)
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

        # Session-Specific Plot
        session_data = data[selected_data_type][selected_participant][selected_session]
        session_combined_df = pd.DataFrame()
        for csv_name, df in session_data.items():
            file_data_type = get_data_type_from_filename(csv_name)
            if file_data_type == selected_data_type:
                prepared_df = prepare_dataframe(df, file_data_type)
                if prepared_df is not None:
                    session_combined_df = pd.concat([session_combined_df, prepared_df])

        if not session_combined_df.empty:
            session_fig = px.line(
                session_combined_df,
                x="Time",
                y="Value",
                title=f"{selected_participant} - {selected_session} - {selected_data_type}"
            )
            session_fig.update_layout(
                xaxis_title="Time",
                yaxis_title="BPM"
            )
            session_html = pio.to_html(session_fig, full_html=False, include_plotlyjs='cdn')
        else:
            session_html = f"No valid data found for {selected_data_type} in {selected_participant}, {selected_session}"

    except Exception as e:
        import traceback
        print("Error encountered:", str(e))
        print(traceback.format_exc())
        overview_html = f"Error generating overview plot: {str(e)}\n{traceback.format_exc()}"
        session_html = f"Error generating session plot: {str(e)}\n{traceback.format_exc()}"

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