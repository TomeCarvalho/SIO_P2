## How to Run

### Linux (With Bash Scripts)

Open two terminal tabs/windows.

Run the Django application

`./run_app.sh`

Run the Flask application

`./run_uap.sh`



### Linux (Manual)

##### Virtual Environment and Requirements

Create Virtual Environment

`python3 -m venv venv`

Activate Virtual Environment

`source venv/bin/activate`

Install Requirements

`pip install -r requirements.txt`

##### **Django Application**

Run the Application

`python3 app_sec/manage.py runserver {port}`

If not specified, the default port 8000 will be used.

##### Flask Application

Move to the application directory

`cd uap`

Run the Application

`flask run`



### Windows #TODO 

$env:FLASK_APP = "uap"
python -m flask run