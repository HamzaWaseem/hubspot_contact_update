import json
import psycopg2
import requests
from faker import Faker
from celery import Celery
import credentials

app = Celery("tasks", broker=credentials.CELERY_BROKER_URL)
app.config_from_object("celery_config")

faker = Faker()
mydb = psycopg2.connect(
    host=credentials.POSTGRESQL_HOST,
    user=credentials.POSTGRESQL_USER,
    password=credentials.POSTGRESQL_PASSWORD,
    database=credentials.POSTGRESQL_DATABASE,
)


class DBHandler:
    def __init__(self) -> None:
        pass

    # Create tables if they do not exist
    def create_or_check_table(self):
        cursor = mydb.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS HamzaWaseem_Contact ("
            + "id SERIAL PRIMARY KEY, first_name VARCHAR(255),"
            + "last_name VARCHAR(255), email VARCHAR(255), "
            + "hubspot_id VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        mydb.commit()
        cursor.close()
        print("Tables created/checked successfully.")

    # Create two random records in each table
    def create_random_record(self):
        cursor = mydb.cursor()
        first_name = faker.first_name()
        last_name = faker.last_name()
        email = f"{first_name}{last_name}@example.com"
        cursor.execute(
            "INSERT INTO HamzaWaseem_Contact (first_name, last_name, email) VALUES ('"
            + first_name
            + "', '"
            + last_name
            + "', '"
            + email
            + "')"
        )
        mydb.commit()
        cursor.close()
        print("Record created successfully in db")
        return {"email": email, "first_name": first_name, "last_name": last_name}

    def update_hubspot_id_in_database(self, hubspot_id, email):
        cursor = mydb.cursor()
        cursor.execute(
            "UPDATE HamzaWaseem_Contact SET hubspot_id = "
            + hubspot_id
            + " WHERE email = '"
            + email
            + "';"
        )
        mydb.commit()
        cursor.close()
        print("Row updated successfully in database")


class HubspotHandler:
    def __init__(self) -> None:
        pass

    # Get refresh token from HubSpot, I used this to get refresh token so added method here
    # def get_refresh_token(self):
    #     headers = {
    #         "charset": "utf-8",
    #         "Content-Type": "application/x-www-form-urlencoded",
    #     }
    #     url = f"{credentials.HUBSPOT_BASE_URL}/oauth/v1/token?grant_type=authorization_code&credentials.HUBSPOT_CLIENT_ID={credentials.HUBSPOT_CLIENT_ID}&credentials.HUBSPOT_CLIENT_SECRET={credentials.HUBSPOT_CLIENT_SECRET}&redirect_uri={credentials.HUBSPOT_REDIRECT_URL}&code={credentials.HUBSPOT_AUTHORIZATION_CODE}"
    #     response = requests.post(url, headers=headers)
    #     refresh_token = response.json()["refresh_token"]
    #     return refresh_token

    # Get access token using Refresh token
    def get_access_token(self):
        data = {
            "grant_type": "refresh_token",
            "client_id": {credentials.HUBSPOT_CLIENT_ID},
            "client_secret": {credentials.HUBSPOT_CLIENT_SECRET},
            "redirect_uri": {credentials.HUBSPOT_REDIRECT_URL},
            "refresh_token": {credentials.HUBSPOT_REFRESH_TOKEN},
        }
        url = f"{credentials.HUBSPOT_BASE_URL}/oauth/v1/token"
        response = requests.post(url, data=data)
        access_token = response.json()["access_token"]
        return access_token

    # Search for contact in HubSpot and create/update record
    def create_or_update_contact(self, first_name, last_name, email, access_token):
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        url = f"{credentials.HUBSPOT_BASE_URL}/contacts/v1/contact/createOrUpdate/email/{email}/"
        data = {
            "properties": [
                {"property": "firstname", "value": first_name},
                {"property": "lastname", "value": last_name},
                {"property": "email", "value": email},
            ]
        }
        response = requests.post(url, data=json.dumps(data), headers=headers)
        print("Created/Updated contact in Hubspot")
        hubspot_id = response.json()["vid"]
        return hubspot_id


@app.task
def my_task():
    print("===== Starting Task =====")
    db_handler = DBHandler()
    hubspot_handler = HubspotHandler()
    db_handler.create_or_check_table()
    access_token = hubspot_handler.get_access_token()
    number_of_records = 0
    while number_of_records < 2:
        record = db_handler.create_random_record()
        email = record["email"]
        first_name = record["first_name"]
        last_name = record["last_name"]
        hubspot_id = hubspot_handler.create_or_update_contact(
            first_name=first_name,
            last_name=last_name,
            email=email,
            access_token=access_token,
        )
        hubspot_id = str(hubspot_id)
        db_handler.update_hubspot_id_in_database(hubspot_id, email)
        print("Record added in DB and Hubspot successfully with id : " + hubspot_id)
        number_of_records += 1
    print("===== Ending Task gracefully =====")


# In case we use some other strategy instead of celery then we can use this main function
# def main():
#     print("===== Starting main =====")
#     dbHandler = DBHandler()
#     hubspotHandler = HubspotHandler()
#     dbHandler.create_or_check_table()
#     access_token = hubspotHandler.get_access_token()
#     number_of_records = 0
#     while number_of_records < 2:
#         record = dbHandler.create_random_record()
#         email = record["email"]
#         first_name = record["first_name"]
#         last_name = record["last_name"]
#         hubspot_id = hubspotHandler.create_or_update_contact(
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             access_token=access_token,
#         )
#         hubspot_id = str(hubspot_id)
#         dbHandler.update_hubspot_id_in_database(hubspot_id, email)
#         print("Record added in DB and Hubspot successfully with id : " + hubspot_id)
#         number_of_records += 1
#     print("===== Ending main gracefully =====")


# if __name__ == "__main__":
#     main()
