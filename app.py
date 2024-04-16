from flask import Flask, request, jsonify, current_app
import os
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
import json
from datasets import Dataset
from pinecone import Pinecone
from pinecone import ServerlessSpec
from langchain.vectorstores import Pinecone
import time

# Initialize variables or objects that will be used across requests
openai_api_key = os.environ["OPENAI_API_KEY"]
chat = ChatOpenAI(
    openai_api_key=openai_api_key,
    model='gpt-3.5-turbo'
)

# Load JSON data from a local file
with open("data/assignments.json", "r") as f:
    json_data = json.load(f)
dataset = Dataset.from_dict({"Assignment": json_data})

# Initialize Pinecone index and other necessary variables
pine_cone_api_key = os.environ["PINECONE_API_KEY"]
pc = Pinecone(api_key=pine_cone_api_key)
index_name = 'athena-testing'
spec = ServerlessSpec(
    cloud="aws", region="us-east-1"
)

index = pc.Index(index_name)

# Initialize embedding model
embed_model = OpenAIEmbeddings(model="text-embedding-ada-002")


app = Flask(__name__)
# Define routes
@app.route("/query", methods=["POST"])
def query():
    # Get request headers
    headers = request.headers

    # Get request data
    data = request.data

    # Print headers and data
    print("Request Headers:")
    print(headers)
    print("Request Data:")
    print(data)
    
    # Get query parameter from request
    query_text = request.json.get("query")
    
    # Use the query text to search through your vector database
    similar_items = vectorstore.similarity_search(query_text, k=5)
    
    # Extract relevant information from the search results
    response_data = []
    for item in similar_items:
        response_data.append({
            "name": item.name,
            "data": item.data
        })
    
    # Return the response
    return jsonify({"response_data": response_data})

ngrok_url = "https://5975-2600-8801-be18-a000-74b8-2bdc-2b64-c7f0.ngrok-free.app"
@app.route("/")
def hello_world():
    return render_template("index.html")



@app.route("/test")
def backup():
    return render_template("index1.html")

# Fake price generator function
def generate_fake_price():
    return round(random.uniform(10, 100), 2)


@app.route("/endpoint", methods=["POST", "GET"])
def your_endpoint():
    fake_data = {
        'assignments': 'homework 3',
        'description': 'write a 69 page essay',
        'points_possible': '120'
    }
    return jsonify(fake_data)
    
@app.route("/submit-form", methods=["POST"])
def submit_form_simple():
    phone = request.form.get("phone")
    # Create a dictionary with the form data
    data = {
    'To': phone  
    }  
    url = ngrok_url + '/make-call'
    response = requests.post(url, data=data)
    print(response)
    
    if response.status_code == 200:
        return render_template("index.html")
    else:
        return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
