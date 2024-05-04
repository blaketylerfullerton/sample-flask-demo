from flask import Flask, request, jsonify, current_app, render_template
import os
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
import json
from datasets import Dataset
from pinecone import ServerlessSpec, Pinecone
import time
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse, Start, Gather, VoiceResponse, Say
import random
import mysql.connector
from datetime import datetime
from fetchassignments import fetchassignments
from flask_cors import CORS
import requests

res_content = None  # Global variable to store response content


from langchain.schema import SystemMessage, HumanMessage, AIMessage

messages = []
# Initialize variables or objects that will be used across requests
openai_api_key = os.environ["OPENAI_API_KEY"]
chat = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-3.5-turbo")

# Load JSON data from a local file
with open("data/assignments.json", "r") as f:
    json_data = json.load(f)
dataset = Dataset.from_dict({"Assignment": json_data})

# Initialize Pinecone index and other necessary variables
pine_cone_api_key = os.environ["PINECONE_API_KEY"]
pc = Pinecone(api_key=pine_cone_api_key)
spec = ServerlessSpec(cloud="aws", region="us-east-1")

index = pc.Index(index_name)

# Initialize embedding model
embed_model = OpenAIEmbeddings(model="text-embedding-ada-002")
text_field = "name"  # the metadata field that contains our text

from langchain.vectorstores import Pinecone

# initialize the vector store objecta
vectorstore = Pinecone(index, embed_model.embed_query, text_field)


def augment_prompt(query: str):
    # get top 3 results from knowledge base
    results = vectorstore.similarity_search(query, k=3)
    # get the text from the results
    source_knowledge = "\n".join([x.page_content for x in results])
    # feed into an augmented prompt
    augmented_prompt = f"""Using the contexts below, answer the query, be short and consice.

    
    {source_knowledge}

    Query: {query}"""
    return augmented_prompt


app = Flask(__name__)
CORS(app)


# Define routes
@app.route("/query", methods=["POST"])
def query():
    # Get request headers
    headers = request.headers

    # Get request data
    data = request.get_json()

    # Print headers and data
    print("Request Headers:")
    print(headers)
    print("Request Data:")
    print(data)

    # Check if data is None (indicating request body is not JSON)
    if data is None:
        return jsonify({"error": "Request body is not in JSON format"}), 400

    # Get query parameter from request
    query_text = str(data.get("query"))
    print("QUERY TEXT TYPE: ", type(query_text))
    print("QUERY TEXT: ", query_text, "\n")

    # Use the query text to search through your vector database
    similar_items = vectorstore.similarity_search(query_text, k=3)

    print(similar_items)
    similar_items = [
        {
            "page_content": document.page_content,
            "metadata": {
                "description": document.metadata.get("description", ""),
                "due_at": document.metadata.get("due_at", ""),
                "points_possible": document.metadata.get("points_possible", 0),
            },
        }
        for document in similar_items
    ]
    # create a new user prompt
    prompt = HumanMessage(content=augment_prompt(f"{query_text}"))

    res = chat(messages + [prompt])
    res_content = res.content  # Storing response content in the global variable
    print(res.content)

    # Return the response
    return jsonify({"response_data": res.content})


@app.route("/querysimple", methods=["POST"])
def query_simple():
    # Get request headers
    headers = request.headers

    # Get request data
    data = request.get_json()

    # Print headers and data
    print("Request Headers:")
    print(headers)
    print("Request Data:")
    print(data)

    # Check if data is None (indicating request body is not JSON)
    if data is None:
        return jsonify({"error": "Request body is not in JSON format"}), 400

    # Get query parameter from request
    phoneNumber = str(data.get("phoneNumber"))

    next_assignments = fetchassignments(phoneNumber)

    # Return the response
    return jsonify({"upcoming_assignments": next_assignments})


@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/testforbland", methods = ["POST"])
def testforbland():
    # Get request data
    data = request.get_json()
    print(data)
    # Extract records from the request
    records = data.get('records', [])
    index = pc.Index("sample-index")

    # Insert each record into the Pinecone index
    for record in records:
        record_id = record.get('id')
        values = record.get('values')
        index.upsert(ids=[record_id], vectors=[values])
    
    return jsonify({"Status": "Records inserted successfully"})
    


def waitingList(email, name):
    try:
        # Connect to MySQL server
        db_connection = mysql.connector.connect(
            host="athena-do-user-16198044-0.c.db.ondigitalocean.com",
            user="doadmin",
            password=os.environ["DB_API_KEY"],
            database="defaultdb",
            port=25060,
        )
        cursor = db_connection.cursor()

        # Insert scheduling information into the database
        insert_query = "INSERT INTO users (email,name) VALUES (%s, %s)"
        cursor.execute(insert_query, (email, name))
        db_connection.commit()

        # Close database connection
        cursor.close()
        db_connection.close()
        return render_template("index.html")
    except mysql.connector.Error as error:
        # Handle any MySQL errors
        print("Error occurred:", error)
        return "An error occurred while processing your request."


@app.route("/append", methods=["POST"])
def append():
    # Get JSON data from the request
    data = request.get_json()

    # Print the received data
    print("Received data:", data)

    # Extract email and name from the received data
    email = data.get("email")
    name = data.get("name")

    # Call the waitingList function
    waitingList(email, name)

    # Return a JSON response indicating success
    return jsonify({"status": "List Joined"})


def call_prospect(phone_number, name, course):
    # Headers
    headers = {
        "Authorization": "sk-rpdial4c4b4x2k6gxbfq6uk3kvpi4q6ca2tb7ce2g9oldpwoc51tf0z8i92542uc69"
    }

    # Data
    data = {
        "phone_number": f"+1{phone_number}",
        "task": f'You are Athena, a casually speaking, slightly sarcastic, quick-witted, curious, and very smart A I Phone agent that\'s the face of Athena AI. You are speaking to {name}. \n\nSay "AI" like "A I" in separate characters so it\'s pronounced correctly\n\nYour primary goal is to talk to the student and convince them to join the waiting list. Tell them about how you are an AI cloud agent built to guide them through their education, especially in their {course} class. \n\n\nSpeech style examples (mix it up and never use placeholders, but you get the idea. These would be full responses from you):\n- "Hey! Who\'s this?"\n- "What Educational Tools are you using right now?"\n- "You know what? That sounds awesome - you should tell me more about (thing)."\n- "Well, I\'ve got some news you\'ll love to hear (their name)"\n- "Bet. Dolphins, racecars, the world\'s largest tree, anything at all - tell me what you want to talk about and let\'s get to it!"\n\nGood things to find out from potential platform adopters:\n- Their Education\n- How many missed assignments they get\n- How important having educational assistance is\n- The single most important pain point they want to cure with having an A I assistant\n\nFacts to bring up:\n- Most students need help with their education, and cant do it alone\n- Athena\'s owners are constantly adding more features to streamline education. We are able to  trigger things like text messages, call reminders, getting real-time calendar information. \n- If they think that it\'s so cool, the site to sign up for an account is "go dot athena-chat dot com" there they can sign up for the waiting list.\n-Upcoming tools, every day striving to be more of a Jarvis, but for students. Built By students, for students.',
        "model": "enhanced",
        "language": "eng",
        "voice": "maya",
        "voice_settings": {},
        "local_dialing": True,
        "max_duration": "5",
        "wait_for_greeting": True,
        "record": True,
        "interruption_threshold": 50,
    }

    # Making the API request
    response = requests.post("https://api.bland.ai/v1/calls", json=data, headers=headers)
    
    # Checking if the request was successful (status code 200)
    if response.status_code == 200:
        # Parsing the response content as JSON
        response_data = response.json()
        print("Response:", response_data)
    else:
        print("Failed to make the API request. Status code:", response.status_code)

@app.route("/call_customer", methods=["POST"])
def call_customer():
    # Get JSON data from the request
    data = request.get_json()
    # Print the received data
    print("Received Customer Data:", data)

    # Extract email and name from the received data
    phone_number = data.get("phoneNumber")
    name = data.get("name")
    course = data.get("exampleCourse")

    # Call the waitingList function
    call_prospect(phone_number, name, course)

    # Return a JSON response indicating success
    return jsonify({"status": "Call Qued"})


# Endpoint to send SMS with verification code
@app.route("/message", methods=["POST"])
def send_verification_code():
    data = request.get_json()
    headers = request.headers
    print("Request Headers:")
    print(headers)
    print("Request Data:")
    print(data)
    # Twilio credentials
    account_sid = os.getenv("account_sid")
    auth_token = os.getenv("auth_token")
    twilio_phone_number = "+12255353633"

    client = Client(account_sid, auth_token)
    data = request.get_json()
    phone_number = data.get("phoneNumber")
    information = res_content  # Using the response content from the /query endpoint
    hard_info = data.get("information")

    # Send SMS
    message = client.messages.create(
        body=f"{hard_info}", from_=twilio_phone_number, to=phone_number
    )

    print(f"SMS sent to {phone_number}. SID: {message.sid}. {information}")

    return jsonify({"status": "Message Sent"})


@app.route("/test")
def backup():
    return render_template("index1.html")


@app.route("/endpoint", methods=["POST", "GET"])
def your_endpoint():
    fake_data = {
        "assignments": "homework 3",
        "description": "write a 69 page essay",
        "points_possible": "120",
    }
    return jsonify(fake_data)


# Function to insert scheduled call into the database
def insert_scheduled_call(caller_name, caller_number, scheduled_time, notes):
    # Connect to MySQL server
    db_connection = mysql.connector.connect(
        host="athena-do-user-16198044-0.c.db.ondigitalocean.com",
        user="doadmin",
        password=os.environ["DB_API_KEY"],
        database="defaultdb",
        port=25060,
    )
    cursor = db_connection.cursor()

    # Parse the datetime string to a datetime object
    dt_object = datetime.fromisoformat(scheduled_time.replace("Z", "+00:00"))

    # Format the datetime object to match MySQL's format
    formatted_datetime_str = dt_object.strftime("%Y-%m-%d %H:%M:%S")

    # Insert scheduling information into the database
    insert_query = "INSERT INTO scheduled_calls (caller_name, caller_number, scheduled_time, notes) VALUES (%s, %s, %s, %s)"
    cursor.execute(
        insert_query, (caller_name, caller_number, formatted_datetime_str, notes)
    )
    db_connection.commit()

    # Close database connection
    cursor.close()
    db_connection.close()


# Route to schedule a call
@app.route("/schedule_call", methods=["POST"])
def schedule_call():
    data = request.json
    print("Request Data:")
    print(data)

    # Extract necessary information from the request data
    caller_name = data.get("caller_name")
    caller_number = data.get("caller_number")
    scheduled_time = data.get("scheduled_time")
    notes = data.get("notes")

    # Insert scheduling information into the database
    insert_scheduled_call(caller_name, caller_number, scheduled_time, notes)

    return jsonify({"message": "Call scheduled successfully"})


if __name__ == "__main__":
    app.run(debug=True)
