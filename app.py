from flask import Flask, request, jsonify, current_app, render_template
import os
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
import json
from datasets import Dataset
from pinecone import ServerlessSpec, Pinecone
import time

from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)
messages = [
    
]
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
text_field = "name"  # the metadata field that contains our text

from langchain.vectorstores import Pinecone 
# initialize the vector store object
vectorstore = Pinecone(
    index, embed_model.embed_query, text_field
)
def augment_prompt(query: str):
    # get top 3 results from knowledge base
    results = vectorstore.similarity_search(query, k=3)
    # get the text from the results
    source_knowledge = "\n".join([x.page_content for x in results])
    # feed into an augmented prompt
    augmented_prompt = f"""Using the contexts below, answer the query. be short and consice.

    
    {source_knowledge}

    Query: {query}"""
    return augmented_prompt

app = Flask(__name__)
# Define routes
@app.route("/query", methods=['POST'])
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
        return jsonify({'error': 'Request body is not in JSON format'}), 400
    

    # Get query parameter from request
    query_text = str(data.get('query'))
    print('QUERY TEXT TYPE: ', type(query_text))
    print('QUERY TEXT: ', query_text,'\n\n\n')

    # Use the query text to search through your vector database
    similar_items = vectorstore.similarity_search(query_text, k=3)


    # Use the query text to search through your vector database
    similar_items = vectorstore.similarity_search(query_text, k=5)
    
    #print(similar_items)
    similar_items = [
    {
        "page_content": document.page_content,
        "metadata": {
            "description": document.metadata.get("description", ""),
            "due_at": document.metadata.get("due_at", ""),
            "points_possible": document.metadata.get("points_possible", 0)
        }
    }
        for document in similar_items
    ]
    # create a new user prompt
    prompt = HumanMessage(
    content=augment_prompt(
        f"{query_text}"
        )
    )

    res = chat(messages + [prompt])
    print(res.content)
    
    # Return the response
    return jsonify({"response_data": res.content})

@app.route("/")
def hello_world():
    return render_template("index.html")



@app.route("/test")
def backup():
    return render_template("index1.html")

@app.route("/endpoint", methods=["POST", "GET"])
def your_endpoint():
    fake_data = {
        'assignments': 'homework 3',
        'description': 'write a 69 page essay',
        'points_possible': '120'
    }
    return jsonify(fake_data)
    

if __name__ == "__main__":
    app.run(debug=True)
