from flask import Flask, request, jsonify
app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello from APIAI Webhook Integration."


@app.route("/version")
def version():
    return "APIAI Webhook Integration. Version 1.0"


@app.route("/webhook", methods=['POST'])
def webhook():
    content = request.json
    # Extract out the parameters
    # Persist the record
    # Send email notification
    return jsonify({
        "speech": "Thank You for choosing python-webhook",
        "displayText": "I am in python-webhook",
        "source": "Timesheet ChatBot",
        "receivedContent": content
    })


if __name__ == "__main__":
    app.run()
