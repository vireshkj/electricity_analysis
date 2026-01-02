from typing import Tuple

from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import uuid
import os
from datetime import datetime
import calendar

from pandas import DataFrame
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    """Render HTML form for user input"""
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>CSV & Array Processor</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f7f9fc; }
            .container { max-width: 800px; margin: auto; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; }
            label { display: block; margin-top: 15px; font-weight: bold; }
            input[type="text"], input[type="file"] { width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ccc; border-radius: 4px; }
            button { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin-top: 20px; }
            button:hover { background: #2980b9; }
            pre { background: #f0f0f0; padding: 15px; border-radius: 5px; overflow-x: auto; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 CSV & Integer Array Processor</h1>
            <form method="POST" enctype="multipart/form-data">
                <label for="array_input">Enter Integer Array (e.g., [1,2,3,4]):</label>
                <input type="text" id="array_input" name="array" placeholder="e.g., [1,2,3,4]" required />

                <label for="csv_file">Upload CSV File:</label>
                <input type="file" id="csv_file" name="csv_file" accept=".csv" required />

                <button type="submit">Process Data</button>
            </form>

            {% if result %}
            <h3>✅ Result:</h3>
            <pre>{{ result }}</pre>
            {% endif %}
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_template)

@app.route('/process', methods=['POST'])
def process_data():
    try:
        # Get integer array from JSON or form
        peak_hours = request.form.get('peak_hours')
        if not peak_hours:
            return jsonify({'error': 'Array input is missing'}), 400

        # Parse array string to list of integers
        try:
            import ast
            int_array = ast.literal_eval(peak_hours)
            if not isinstance(int_array, list) or not all(isinstance(x, int) for x in int_array):
                return jsonify({'error': 'Array must contain only integers'}), 400
        except Exception as e:
            return jsonify({'error': 'Invalid array format. Use Python list syntax like [1,2,3]'}), 400

        # Get uploaded CSV file
        if 'csv_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['csv_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Only CSV files are accepted.'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)

        # Read CSV with Pandas
        df = pd.read_csv(file_path)

        #############################################################################################
        #  process df - VJ
        df, summary_df, hourly_agg, daily_agg, weekly_agg, monthly_agg = initialize_df(df)

        data = process(summary_df, int_array)
        # output = data[data['is_month_end'] == True][data['monthly_kwh'] > 0]
        output = data[data['daily_kwh'] > 0]
        output = output[
            ["datetime", "daily_kwh", "date", "day", "daily_peak_kwh", "daily_non_peak_kwh"]
            # ["datetime", "monthly_kwh", "date", "day", "monthly_peak_kwh", "monthly_non_peak_kwh"]
        ]

        ##############################################################################################

        # Example Processing: Add array values to first column
        # You can customize this logic below
        if len(output) > 0:
            # Ensure first column is numeric
            first_col = output.columns[0]
            if pd.api.types.is_numeric_dtype(output[first_col]):
                output[f'processed_{first_col}'] = output[first_col] + sum(int_array)
            else:
                # If not numeric, convert and add
                output[f'processed_{first_col}'] = output[first_col].astype(str) + "_" + str(sum(int_array))

        # Convert result to JSON
        result_json = {
            # "original_shape": output.shape,
            # "column_names": output.columns.tolist(),
            # "summary_stats": output.describe().to_dict() if output.shape[0] > 0 else {},
            "processed_data": output.to_dict(orient='records'),
            # "array_sum": sum(int_array),
            # "processing_notes": "Added array sum to first column."
        }

        # Clean up uploaded file
        os.remove(file_path)

        return jsonify(result_json)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def is_month_end(date_input):
    # accepts date_input as datetime.date, datetime.datetime, or "YYYY-MM-DD" str
    if isinstance(date_input, str):
        date = datetime.strptime(date_input, "%Y-%m-%d").date()
    elif isinstance(date_input, datetime):
        date = date_input.date()
    else:
        date = date_input  # assume datetime.date
    last_day = calendar.monthrange(date.year, date.month)[1]
    return date.day == last_day


def process(summary_df, peak_hours):
    df = summary_df
    df['hour'] = df['datetime'].dt.hour
    df['day'] = df['datetime'].dt.day
    df['month'] = df['datetime'].dt.month
    df['year'] = df['datetime'].dt.year
    df['is_month_end'] = df['datetime'].dt.is_month_end

    # Ensure date and time are properly parsed
    # df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    # Extract hour from time
    # df['hour'] = df['datetime'].dt.hour
    # Define peak hours

    # Create peak flag
    df['is_peak'] = df['hour'].isin(peak_hours)
    # Separate peak and non-peak usage
    df['peak_kwh'] = df['hourly_kwh'].where(df['is_peak'], 0)
    df['non_peak_kwh'] = df['hourly_kwh'].where(~df['is_peak'], 0)
    # Set datetime as index for resampling
    df.set_index('datetime', inplace=True)
    # Daily sums
    df_daily = df.resample('D').agg({
        'peak_kwh': 'sum',
        'non_peak_kwh': 'sum'
    }).rename(columns={'peak_kwh': 'daily_peak_kwh', 'non_peak_kwh': 'daily_non_peak_kwh'})
    # Weekly sums
    df_weekly = df.resample('W-MON').agg({
        'peak_kwh': 'sum',
        'non_peak_kwh': 'sum'
    }).rename(columns={'peak_kwh': 'weekly_peak_kwh', 'non_peak_kwh': 'weekly_non_peak_kwh'})
    # Monthly sums
    df_monthly = df.resample('ME').agg({
        'peak_kwh': 'sum',
        'non_peak_kwh': 'sum'
    }).rename(columns={'peak_kwh': 'monthly_peak_kwh', 'non_peak_kwh': 'monthly_non_peak_kwh'})
    # Merge back into original DataFrame using the index
    df.reset_index(inplace=True)
    df = pd.merge(df, df_daily[['daily_peak_kwh', 'daily_non_peak_kwh']],
                  left_on='datetime', right_index=True, how='left')
    df = pd.merge(df, df_weekly[['weekly_peak_kwh', 'weekly_non_peak_kwh']],
                  left_on='datetime', right_index=True, how='left')
    df = pd.merge(df, df_monthly[['monthly_peak_kwh', 'monthly_non_peak_kwh']],
                  left_on='datetime', right_index=True, how='left')
    # Fill NaNs with 0 (for first few days/weeks/months with no data)
    df.fillna(0, inplace=True)
    # Optional: Drop temporary columns if needed
    # df.drop(columns=['hour', 'is_peak', 'datetime'], inplace=True)
    return df

def initialize_df(df: DataFrame) -> Tuple:
    df = df.drop(columns=["ESTIMATED_ACTUAL", "REVISION_DATE", "CONSUMPTION_SURPLUSGENERATION"])
    df['USAGE_START_TIME'] = df['USAGE_START_TIME'].str.strip()
    df['USAGE_END_TIME'] = df['USAGE_END_TIME'].str.strip()
    df['hour'] = pd.to_datetime(df['USAGE_START_TIME'], format='%H:%M').dt.hour

    # Convert USAGE_DATE to datetime
    df['datetime'] = pd.to_datetime(df['USAGE_DATE'], format='%m/%d/%Y')
    # Create 15-min interval offsets (0, 15, 30, 45 minutes)
    # Assuming rows are ordered chronologically
    df['datetime'] += pd.to_timedelta(df['hour'], unit='hour')

    # Set datetime as index for resampling
    df.set_index('datetime', inplace=True)
    # Resample and sum kWh
    hourly = df['USAGE_KWH'].resample('h').sum()
    daily = df['USAGE_KWH'].resample('D').sum()
    weekly = df['USAGE_KWH'].resample('W').sum()
    monthly = df['USAGE_KWH'].resample('ME').sum()
    # yearly = df['USAGE_KWH'].resample('Y').sum()

    summary_df = pd.DataFrame({
        'hourly_kwh': hourly,
        'daily_kwh': daily,
        'weekly_kwh': weekly,
        'monthly_kwh': monthly
    }).reset_index()
    # Rename index to 'datetime'
    summary_df.rename(columns={'index': 'datetime'}, inplace=True)

    # Extract frequency labels from datetime
    df.reset_index(inplace=True)
    df['hour'] = df['datetime'].dt.hour
    df['day'] = df['datetime'].dt.date
    df['week'] = df['datetime'].dt.to_period('W')
    df['month'] = df['datetime'].dt.to_period('M')
    # Group by hour/day/week/month and aggregate
    hourly_agg = df.groupby('hour')['USAGE_KWH'].sum().rename('hourly_kwh')
    daily_agg = df.groupby('day')['USAGE_KWH'].sum().rename('daily_kwh')
    weekly_agg = df.groupby('week')['USAGE_KWH'].sum().rename('weekly_kwh')
    monthly_agg = df.groupby('month')['USAGE_KWH'].sum().rename('monthly_kwh')
    # Merge back using map
    df['hourly_kwh'] = df['hour'].map(hourly_agg)
    df['daily_kwh'] = df['day'].map(daily_agg)
    df['weekly_kwh'] = df['week'].map(weekly_agg)
    df['monthly_kwh'] = df['month'].map(monthly_agg)

    summary_df['time'] = summary_df['datetime'].dt.strftime('%H:%M')
    summary_df['date'] = summary_df['datetime'].dt.strftime('%Y-%m-%d')


    return df, summary_df, hourly_agg, daily_agg, weekly_agg, monthly_agg


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
