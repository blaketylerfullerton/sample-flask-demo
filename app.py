from flask import Flask, jsonify
from flask import Flask, request, render_template
import requests
import random



app = Flask(__name__)

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


@app.route("/endpoint", methods=["POST"])
def your_endpoint():
    #fake_price = generate_fake_price()
    return jsonify({'price': 69420})

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
