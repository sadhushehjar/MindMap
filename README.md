# MindMap

Mindmap is a web based application that visualizes and analyzies data

## Prerequisites

Ensure you have Python 3.7 or later installed 

## Installation 

1. Clone this repository or download the source code.
   ```bash
   git clone <repository-url>
   cd <repository-folder>

2. Install required Python libraries from txt file 
   ```bash
   pip install -r requirements.txt
   
3. Name your data folder Watch_data_org and place it in the base of the project's directory.
   
4. Open console and CD into the base directory of the program and set FLASK_APP=run.py
   ```bash
   C:\"your directory"\MindMap>set FLASK_APP=run.py  

## Running the Applicaiton 

1. Start the Flask app
   ```bash
   flask --app run run
   
2.Open your web browser and paste the given URL
http://127.0.0.1:5000/

## Using Mindmap

1. Select Data Type: Currently only heartrate data works so select that from the dropdown
   
2. Select Participant
   
3. Select Session

## Data Format

CSV Files should follow this nameing convention:

watch_participantID_level_sublevel_randgenID_dataType.csv

## Directory Structure
```
MindMap/
├── Watch_data_org/
│   ├── heartrate_data/
│   │   ├── P#/
│   │   │   ├── Session 1/
│   │   │   │   ├── watch_P#_L1_S1_#######_heartrate.csv
│   │   │   │   ├── watch_P#_L1_S2_#######_heartrate.csv
│   │   │   ├── Session 2/
│   │   │   │   ├── watch_P#_L1_S1_#######_heartrate.csv
│   │   ├── N#/
│   │   │   ├── Session 1/
│   │   │   │   ├── watch_N#_L1_S1_#######_heartrate.csv
│   │   │   ├── Session 2/
│   │   │   │   ├── watch_N#_L1_S1_#######_heartrate.csv
│   ├── #Other data types/
├── templates/
│   ├── layout.html
├── routes.py
├── utils.py
├── requirements.txt
└── README.md
```

