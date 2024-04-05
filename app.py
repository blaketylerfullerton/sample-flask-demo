from flask import Flask
from flask import Flask, request, render_template
import requests

app = Flask(__name__)

ngrok_url = "https://b460-144-37-98-25.ngrok-free.app"
@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/test")
def backup():
    return render_template("index1.html")

'''
@app.route("/submit-form", methods=["POST"])
def submit_form():
    name = request.form.get("name")
    phone = request.form.get("phone")
    work = request.form.get("work")
    print(name)
    print(phone)
    print(work)
    # Create a dictionary with the form data
    request_data = {
        "To": phone,
        "name": name,
        "phone": phone,
        "work": work
    }
    
    # Send a POST request to a fake URL with the form data
    fake_url = ngrok_url + '/make-call'
    
    response = requests.post(fake_url, json=request_data)
    print(request_data)
    
    # Check if the request was successful
    if response.status_code == 200:
        return "Form submitted successfully!"
    else:
        return "Failed to submit form. Please try again later."
    '''
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
