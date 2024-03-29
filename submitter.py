#For google
from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# For ODPhi site
import requests
from bs4 import BeautifulSoup

# For Development
import json
from datetime import timedelta
from datetime import date
import random

# Global Variables
with open('config.json') as json_file:  
    config = json.load(json_file)["installed"]

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = config["sheets_id"]
# This is the name of the tab for the sheet
RANGE_NAME = 'Hours!A:Z'

# Converts the input string to an actual date that we can work with
# Wanted people to put the date in how they were comfortable (MM/DD/YYYY)
def getDateObject(date_string):
    month_day_year = date_string.split('-')
    return date(int(month_day_year[2]), int(month_day_year[0]), int(month_day_year[1]))

# Function that checks the format of what the user inputs to make sure it's a valid date
def checkDateFormat(date_input):
    if isinstance(date_input, int):
        return False
    month_day_year = date_input.split('-')
    if len(month_day_year) != 3:
        return False
    
    return True

# Get the starting date for the studying by asking for input from the user
while True:
    start_date = input("\nWhat was the first day you studied this quarter? Please use \"MM-DD-YYYY\" format, typing out the quotes:\n")
    if not checkDateFormat(start_date):
        print("The date you gave doesn't match the format I asked for. Please make sure it's exact : )")
        continue
    else:
        start_date = getDateObject(start_date)
        break

# Get the ending date for the studying by asking for input from the user
while True:
    end_date = input("\nWhat was the last day you studied this quarter? Please use \"MM-DD-YYYY\" format, typing out the quotes:\n")
    if not checkDateFormat(end_date):
        print("The date you gave doesn't match the format I asked for. Please make sure it's exact : )")
        continue
    else:
        end_date = getDateObject(end_date)
        break

def main():

    ##########################################
    ###### GOOGLE SHEETS AUTHENTICATION ######
    ##########################################

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'config.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # ##########################################
    # ######### CALL GOOGLE SHEETS API #########
    # ##########################################

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found was found in the google sheet. Please make sure the ID that was provided for the service sheet in config.json is correct, that you have access to the sheet, and that the sheet\'s data is in the Hours tab')
    else:
        total_hours = 0
        locations = []
        for i, row in enumerate(values):
            if (row[0] == config["name_on_study_hours_sheet"]):
                total_hours = int(row[1])
                for location in row[2:]:
                    locations.append(location)
                break
    
        # The idea is that we want to distribute the hours equally throughout the quarter, while still having it randomized
        # at least a little. SO, we start the monday of the first week (if it falls in the range) and assign a random value
        # of 0-2 hours, then do the same for the next monday and the next until we reach the last one, then we start over
        # doing the same for wednesdays, tuesdays, thursdays, sundays, saturdays, then fridays. After going through all 
        # the days, we loop back around to the first week with monday and restart the sequence. There is a max of 5 hours
        # studied in a single day so it doesn't become suspicious. There might be a better way to do this but I'm not 
        # putting in that much effort to figure this out. 

        # January 7th, March 15th

        # Define constant timedeltas
        seven_days = timedelta(days=7)
        first_monday = start_date - timedelta(days=start_date.weekday())
        first_tuesday = first_monday + timedelta(days=1)
        first_wednesday = first_monday + timedelta(days=2)
        first_thursday = first_monday + timedelta(days=3)
        first_friday = first_monday + timedelta(days=4)
        first_saturday = first_monday + timedelta(days=5)
        first_sunday = first_monday + timedelta(days=6)
        days = [first_monday, first_wednesday, first_tuesday, first_thursday, first_sunday, first_saturday, first_friday]

        # Create the list of study hours
        # Each object has a date, location, and number of hours
        study_hours = {}
        hours_left = total_hours
        current_date = first_monday
        current_day = 0
        while hours_left > 0:
            rand = random.randint(0,2)
            if rand == 0:
                current_date += seven_days
                continue
            elif rand <= hours_left:
                # the random number is less than how many hours we have left to finish
                if start_date <= current_date <= end_date:
                    study_session = {"location": locations[random.randint(0, len(locations) - 1)], "hours": rand}
                    if current_date in study_hours.keys():
                        if study_hours[current_date]["hours"] + rand > 5:
                            continue
                        else:
                            study_hours[current_date]["hours"] += rand
                    else:
                        study_hours[current_date] = study_session
                    hours_left -= rand
                    current_date += seven_days
                    continue
                elif current_date > end_date:
                    # the date is out of bounds, past the end date. Move on to the next day of the week
                    if current_day != 6:
                        current_day += 1
                    else:
                        current_day = 0
                    current_date = days[current_day]
                    continue
                else:
                    # The date is before the start date, go to the next week
                    current_date += seven_days
                    continue
            else:
                continue

        print(study_hours)







        # ##########################################
        # ############ LOGIN TO MYODPHI ############
        # ##########################################

        # login_url = 'https://myodphi.com/login/'
        # login_action = 'https://myodphi.com/wp-login.php'

        # # Start session
        # session = requests.session()

        # # Not entirely sure, but I think we need this get request for the cookies and headers
        # r = session.get(login_url)

        # # Set username and password as the form wants it
        # payload = {
        #     "log":config["odphi_username"],
        #     "pwd":config["odphi_password"]
        # }

        # # Login
        # r = session.post(login_action, data = payload)

        # #TODO Submit all the hours to the study hours form



if __name__ == '__main__':
    main()