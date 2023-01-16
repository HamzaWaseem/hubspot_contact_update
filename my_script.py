import psycopg2
import requests
import json
import time
from faker import Faker
from celery import Celery
import credentials

app = Celery('tasks', broker=credentials.CELERY_BROKER_URL)
app.config_from_object('celery_config')

faker = Faker()
mydb = psycopg2.connect(
    host=credentials.POSTGRESQL_HOST,
    user=credentials.POSTGRESQL_USER,
    password=credentials.POSTGRESQL_PASSWORD,
    database=credentials.POSTGRESQL_DATABASE
)

# HubSpot API credentials
api_key = credentials.HUBSPOT_API_KEY
client_secret = credentials.HUBSPOT_CLIENT_SECRET
redirect_url = credentials.HUBSPOT_REDIRECT_URL
hubspot_base_url=credentials.HUBSPOT_BASE_URL
# Create tables if they do not exist
def create_table():
    cursor = mydb.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS husbpot_contacts (id INT AUTO_INCREMENT PRIMARY KEY, first_name VARCHAR(255), last_name VARCHAR(255), email VARCHAR(255), hubspot_id VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    mydb.commit()
    cursor.close()
    print("Tables created successfully.")

# Create two random records in each table
def create_random_record():
    cursor = mydb.cursor()
    first_name = faker.first_name()
    last_name = faker.last_name()
    email = f"{first_name}{last_name}@example.com"
    cursor.execute("INSERT INTO husbpot_contacts (first_name, last_name, email) VALUES ('"+first_name+"', '"+last_name+"', '"+email+"')")
    mydb.commit()
    cursor.close()
    print("Records created successfully.")
    return {'email': email, 'first_name': first_name, last_name: last_name}

# Get updated access token from HubSpot
def get_access_token():
    url = f"{hubspot_base_url}/oauth/v1/token?grant_type=authorization_code&client_id={api_key}&client_secret={client_secret}&redirect_uri={redirect_url}"
    response = requests.post(url)
    access_token = json.loads(response.text)["access_token"]
    return access_token

# Search for contact in HubSpot and create/update record
def create_or_update_contact(first_name, last_name, email, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    url = f"{hubspot_base_url}/contacts/v1/contact/createOrUpdate/email/{email}/"
    data = {
        "properties": [
            {
                "property": "firstname",
                "value": first_name
            },
            {
                "property": "lastname",
                "value": last_name
            }
        ]
    }
    response = requests.post(
        url,
        data,
        headers=headers
    )
    print("Updated contact on Hubspot")
    return response["id"]


def update_hubspot_id_in_database(hubspot_id, email):
    cursor = mydb.cursor()
    cursor.execute("UPDATE hubspot_contacts SET hubspot_id = "+hubspot_id+" WHERE email = '"+email+"';")
    mydb.commit()
    cursor.close()
    print("Row updated successfully.")



@app.task
def my_task():
    print("===== Starting Task =====")
    create_table()
    access_token = get_access_token()
    number_of_records = 0
    while number_of_records < 2:
        record = create_random_record()
        email = record['email']
        first_name = record['first_name']
        last_name = record['last_name']
        hubspot_id = create_or_update_contact(first_name=first_name, last_name=last_name,email=email,access_token=access_token)
        update_hubspot_id_in_database(hubspot_id, email)
        print("Record added in DB and Hubspot successfully with id" + hubspot_id)
        print("===== Ending Task gracefully =====")