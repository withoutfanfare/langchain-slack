import os
import sys
from datetime import datetime
from dotenv import find_dotenv, load_dotenv
from flask import Flask, request, Response
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import sqlite3

from functions import draft_email, summarise_text, research_text, log_text

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Set Slack API credentials
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

# Initialize the Slack app
app = App(token=SLACK_BOT_TOKEN)

# Initialize the Flask app
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

BOT_MENTION = f"<@{os.environ['SLACK_BOT_USER_ID']}>"


def get_bot_user_id():
    """
    Get the bot user ID using the Slack API.
    Returns:
        str: The bot user ID.
    """
    try:
        # Initialize the Slack client with your bot token
        slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
        response = slack_client.auth_test()
        return response["user_id"]
    except SlackApiError as e:
        print(f"Error: {e}")


def create_database():
    try:
        conn = sqlite3.connect("logs.db")
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS log_entries (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                text TEXT,
                summary TEXT,
                tags TEXT
            )
        """)

        conn.commit()
        conn.close()
        print("Database table created successfully.")
    except Exception as e:
        print(f"Error creating database table: {e}", file=sys.stderr)


def get_summary_from_db(user_input):
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute("""
        SELECT summary FROM log_entries WHERE text = ?
    """, (user_input,))
    result = c.fetchone()
    conn.close()

    return result[0] if result else None


@app.event("app_mention")
def handle_mentions(body, say):
    """
    Event listener for mentions in Slack.
    When the bot is mentioned, this function processes the text and sends a response.

    Args:
        body (dict): The event data received from Slack.
        say (callable): A function for sending a response to the channel.
    """

    text = body["event"]["text"].replace(BOT_MENTION, "").strip()

    # mention = f"<@{SLACK_BOT_USER_ID}>"
    # text = text.replace(mention, "").strip()

    if "!draft" in text:
        say("Drafting...")
        response = draft_email(text)
    elif "!summary" in text:
        say("Summarising...")
        response = summarise_text(text)
    elif "!log" in text:
        say("Logging...")
        response = log_text(text)
    elif "!dig" in text:
        say("Digging...")
        response = research_text(text)
    else:
        response = my_function(text)

    say(response)


@flask_app.route("/", methods=['GET'])
def hello():
    return Response("Hello, World!"), 200


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


if __name__ == "__main__":
    create_database()
    flask_app.run()
