
from flask import Flask, request, render_template_string, redirect, url_for
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.background import BackgroundScheduler
import atexit




# Initialize the Flask application
app = Flask(__name__)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(r'//B01-FS-SRV/Health Data Science/STAT Docs/Fatemeh/PCV/label-random-c6decc88aa1f.json', scope)
client = gspread.authorize(creds)
sheet = client.open("Label-Random").sheet1

# Function to update the Excel data
def update_excel():
    global df, code_dict
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    code_dict = df.set_index('National Code').T.to_dict()  # Refresh the dictionary
    print("Excel data updated.")

# Initial load of data
update_excel()

# Initialize the scheduler to update every 5 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(update_excel, 'interval', minutes=5)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# Define the HTML template for the form
form_template = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Screening Code Finder</title>
    <style>
      body { display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: 'Lucida Bright', sans-serif; background-color: #f4f4f9; }
      .container { text-align: center; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); border: 3px solid #6a0dad; }
      h1 { color: #6a0dad; margin-bottom: 20px; }
      label { font-weight: bold; color: #333; }
      input[type="text"] { padding: 10px; width: 200px; border-radius: 5px; border: 1px solid #6a0dad; margin-top: 10px; }
      input[type="submit"] { padding: 10px 20px; border-radius: 5px; border: none; background-color: #6a0dad; color: white; font-size: 16px; cursor: pointer; margin-top: 20px; }
      input[type="submit"]:hover { background-color: #5e0cb6; }
    </style>
  </head>
  <body>
    <div class="container">
      <h1>Find the Screening Code</h1>
      <form method="post">
        <label for="national_code">Enter National ID:</label><br>
        <input type="text" id="national_code" name="national_code"><br><br>
        <input type="submit" value="Submit">
      </form>
    </div>
  </body>
</html>
'''

# Define the HTML template for the result page

result_template = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Screening Code Result</title>
    <style>
      body { display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: 'Lucida Bright', sans-serif; background-color: #f4f4f9; }
      .container { text-align: center; background: white; padding: 10px; border-radius: 10px; border: 3px solid #6a0dad; }
      #printableArea {
        width: 1.14in;  /* Width in inches */
        height: 2.56in; /* Height in inches */
        padding: 5px;
        border: 1px solid black; /* Border similar to your image */
        font-size: 10px; /* Adjusted font size */
        display: flex;
        flex-direction: column;
        justify-content: flex-start; /* Align items to the start */
        writing-mode: vertical-rl; /* Rotate text to vertical */
        text-align: left; /* Left align the text */
        transform: rotate(180deg); /* Rotate text back for correct reading direction */
      }
      h2 { 
        margin: 0; 
        padding: 0; 
        line-height: 1.5; /* Increase line height */
        padding-bottom: 15px; /* Increased padding between rows */
      }
      .not-found { color: red; }
      a { text-decoration: none; color: #6a0dad; font-weight: bold; }
      a:hover { color: #5e0cb6; }
      .go-back { margin-top: 20px; }  
      .print-button { 
        margin-top: 10px; 
        padding: 10px 20px; 
        border-radius: 5px; 
        border: none; 
        background-color: #6a0dad; 
        color: white; 
        cursor: pointer; 
        align-self: flex-start; /* Align the button to the left */
      }
      .print-button:hover { background-color: #5e0cb6; }

      /* Print styles */
      @media print {
        body * {
          visibility: hidden; /* Hide all elements */
        }
        #printableArea, #printableArea * {
          visibility: visible; /* Show only the printable area */
        }
        #printableArea {
          position: absolute; /* Position the printable area */
          left: 0;
          top: 0;
        }
      }
    </style>
    <script>
      function printDiv() {
        window.print();
      }
    </script>
  </head>
  <body>
    <div class="container">
      <div id="printableArea">
        {% if screening_code %}
          <h2>Randomization Code: {{ screening_code }}</h2>
          <h2>Visit Number: {{ visit_number }}</h2>
          <h2>Collection Date: {{ visit_name }}</h2>
        {% else %}
          <h2 class="not-found">National Code not found. Please try again.</h2>
        {% endif %}
      </div>
      <button class="print-button" onclick="printDiv()">Print</button>
      <a class="go-back" href="{{ url_for('index') }}">Go Back</a>
    </div>
  </body>
</html>
'''






@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        national_code = request.form.get('national_code')
        if national_code and national_code.isdigit():
            return redirect(url_for('result', national_code=national_code))
    return render_template_string(form_template)

@app.route('/result')
def result():
    national_code = request.args.get('national_code')
    try:
        national_code_int = int(national_code)
        result_data = code_dict.get(national_code_int)
    except (ValueError, TypeError):
        result_data = None
    
    return render_template_string(result_template,
                                   screening_code=result_data.get('Screening Code') if result_data else None,
                                   visit_number=result_data.get('Visit Number') if result_data else None,
                                   visit_name=result_data.get('Visit Name') if result_data else None)

if __name__ == "__main__":
    app.run()  # Only for local testing; do not use in production or on PythonAnywhere
   
