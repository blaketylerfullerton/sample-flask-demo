#!/usr/bin/env python3
import requests
from datetime import datetime, timedelta
import json
import mysql.connector
from mysql.connector import Error
from twilio.rest import Client
import pytz


sun_emoji = '\u2600'
# Define the Student class
class Student:
    def __init__(self, id, name, canvas_url, canvas_api_token, personal_phone_number, is_good_morning_on, is_due_before_on, good_morning_time, due_before_time):
        self.id = id
        self.name = name
        self.canvas_url = canvas_url
        self.canvas_api_token = canvas_api_token
        self.personal_phone_number = personal_phone_number
        self.course_names = []
        self.course_ids = []
        self.final_text = []
        self.assignments = []
        self.assignment_counter = 0
        self.is_good_morning_on = is_good_morning_on
        self.is_due_before_on = is_due_before_on
        self.good_morning_time = good_morning_time
        self.due_before_time = due_before_time

    def get_courses(self):
        headers = {'Authorization': f'Bearer {self.canvas_api_token}'}
        url = f'{self.canvas_url}/api/v1/courses'

        try:
            page = 1
            while True:
                params = {
                    'page': page,
                    'per_page': 50,  # You can adjust per_page based on your needs
                }

                response = requests.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    try:
                        courses = response.json()
                        for course in courses:
                            if 'name' in course:
                                course_id = course['id']
                                course_name = course['name']
                                self.course_ids.append(course_id)
                                self.course_names.append(course_name)
                    except ValueError:
                        print("Response content is not valid JSON. The content received:\n", response.text)
                        return
                else:
                    print(f"Failed to retrieve courses. Status code: {response.status_code}")
                    print("Response content received:\n", response.text)
                    return

                # Check if there are more pages
                if 'Link' in response.headers and 'rel="next"' not in response.headers['Link']:
                    break
                else:
                    page += 1

        except Exception as e:
            print(f"An error occurred getting courses: {e}")
    def print_assignments_by_date(self, course_ids):
        result_string = ""  # Initialize an empty string to store the result
        for course_id in course_ids:
            headers = {'Authorization': f'Bearer {self.canvas_api_token}'}
            url = f"{self.canvas_url}/api/v1/courses/{course_id}/assignments"

            params = {
                "bucket": "upcoming",  # Filter for upcoming assignments
                "per_page": 15  # Set the number of assignments to retrieve
            }

            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                try:
                    assignments = response.json()
                    # Create a dictionary to organize assignments by date
                    assignments_by_date = {}
                    # Define the Pacific Time zone
                    pacific_timezone = pytz.timezone('America/Los_Angeles')

                    for assignment in assignments:
                        due_date_str = assignment.get('due_at')
                        assignment_name = assignment.get('name')  # Access the assignment name

                        if due_date_str and assignment_name:
                            due_date_utc = pytz.utc.localize(datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M:%SZ"))

                            # Convert assignment due date to Pacific Time
                            due_date_pacific = due_date_utc.replace(tzinfo=pytz.utc).astimezone(pacific_timezone)

                            # Format due date for display
                            formatted_due_date = due_date_pacific.strftime("%A, %B %d")

                            # Check if the formatted_due_date is already in the dictionary
                            if formatted_due_date not in assignments_by_date:
                                assignments_by_date[formatted_due_date] = {"count": 0, "assignments": []}

                            # Update the count and add the assignment info to the dictionary
                            assignments_by_date[formatted_due_date]["count"] += 1
                            assignments_by_date[formatted_due_date]["assignments"].append(assignment_name)  # Use assignment_name

                    # Construct the result string
                    for date, info in assignments_by_date.items():
                        result_string += f"{date}\nNumber of assignments for that day: {info['count']}\n"
                        for assignment_name in info['assignments']:
                            result_string += f"The assignment '{assignment_name}' is due on {date}\n"
                        result_string += "\n"

                except ValueError:
                    print("Response is not valid JSON.")
            else:
                print(f"Failed to retrieve assignments for Course ID {course_id}. Status code: {response.status_code}")
                print(response.text)
        print(f"RETURNING: {result_string} ")
        return result_string


# Function to connect to the MySQL database
def connect_to_database():
    try:
        # Establish a connection to the MySQL server
        connection = mysql.connector.connect(
            user="doadmin",
            password="AVNS_G_K59rLh3HLpfthyzqU",
            host="athena-do-user-16198044-0.c.db.ondigitalocean.com",
            port=25060,
            database="defaultdb",
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None

# Function to retrieve a row from the database and create a Student object
def get_student_from_database(connection, student_id):
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM studentdb WHERE student_id = {student_id}")
        row = cursor.fetchone()

        if row:
            # Create a Student instance with attributes from the row
            student = Student(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
            return student
    except Error as e:
        print(f"Error: {e}")
        return None


def process_student(student_id):
    try:
        student = get_student_from_database(connection, student_id)
        if student:
            print(f'Student ID: {student.id}')
            print(f'Student Name: {student.name}')

            if student.is_good_morning_on: # Check if good_morning is True
                student.get_courses()
                student.get_todays_assignments_for_course(student.course_ids)
                print(f'Just got {student.name}')
                print(f'{student.name} has nothing due today.')
    except Exception as e:
        print(f"An error occurred for student ID {student_id}: {e}")

def fetchassignments(phone_number):
    try:
        assignments_result = ""  # Initialize assignments_result

        # Connect to the database
        connection = connect_to_database()

        if connection:
            cursor = connection.cursor()

            # Retrieve students with the specified phone number
            cursor.execute(f"SELECT * FROM studentdb WHERE phone_number = '{phone_number}'")
            rows = cursor.fetchall()

            for row in rows:
                student = Student(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
                print(f"Retrieving data for student ID: {student.id}, Name: {student.name}")
                student.get_courses()
                assignments_result += student.print_assignments_by_date(student.course_ids)
                # Add any other logic you need for the specific student

            connection.close()
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return assignments_result



if __name__ == "__main__":
    # Example: Pass the phone number as an argument
    print("Main File")
    #fetchassignments("")


            

        
