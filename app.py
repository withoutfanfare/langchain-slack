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
    text = body["event"]["text"].replace(BOT_MENTION, "").strip()

    command, *args = text.split()
    response = None

    # Filter out any None values from args
    args = [arg for arg in args if arg is not None]

    summary_from_db = get_summary_from_db(" ".join(args)) if args else None

    if summary_from_db:
        response = summary_from_db
    else:
        if command == "!draft":
            say("Drafting...")
            response = draft_email(" ".join(args))
        elif command == "!summary":
            say("Summarising...")
            response = summarise_text(" ".join(args))
        elif command == "!log":
            skip_summary = "!skip" in args
            print(skip_summary)
            args = [arg for arg in args if arg != "!skip"]
            say("Logging...")
            response = log_text(" ".join(args), skip_summary)
        elif command == "!dig":
            say("Digging...")
            response = research_text(" ".join(args))
        elif command == "!help":
            help_message = (
                "Available commands:\n"
                "!draft <text> - Draft an email based on the input text.\n"
                "!summary <text> - Summarise and enrich the input text.\n"
                "!log <text> - Log the input text. Add !skip to skip summary.\n"
                "!dig <text> - Research the input text."
            )
            response = help_message

    if response:
        say(response)


@flask_app.route("/", methods=['GET'])
def hello():
    return Response("Hello, World!"), 200


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


create_database()

if __name__ == "__main__":
    flask_app.run()
