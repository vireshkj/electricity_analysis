# electricity_analysis

- python -m venv electricity
- source electricity/bin/activate
- pip install -r requirements.txt
- python app.py

# inputs
- csv_file:  file to be processed
- peak_hours: [7,8,9,10,11,12,13,14,15,16,17,18,19,20]

# curl
`
curl --location 'localhost:5001/process' \
--form 'csv_file=@"~/codebase/electricity_analysis/data/IntervalMeterUsage202512302103505093F4F9339E4024C89B21685CA1223B8AEEML.CSV"' \
--form 'peak_hours="[7,8,9,10,11,12,13,14,15,16,17,18,19,20]"'
`
