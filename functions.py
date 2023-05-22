from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from dotenv import find_dotenv, load_dotenv
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
import sqlite3
from datetime import datetime

load_dotenv(find_dotenv())


def draft_email(user_input, name="Danny"):
    chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3)

    template = """
    You are an intuitive and helpful assistant that drafts a professional email reply based on the input text.

    Your goal is to help the user quickly create a perfect email reply that is relevant and helpful.

    Keep your reply short and to the point and mimic the style of the email so you reply in a similar manner to match the tone. Overall it should be informal but professional, and use British English spelling and grammar.

    Start your reply by saying: "Hi {name}, here's a draft for your reply:". And then proceed with the reply on a new line.

    Make sure to sign of with {signature}.
    Check the spelling and convert American English words like optimize to optimise. If you are unsure how to respond, just say "I'm not sure how to respond to this email, please tell me more." and the user will post additional information for you to use in formulating your reply.
    """

    signature = f"Thanks, \n\{name}"
    system_message_prompt = SystemMessagePromptTemplate.from_template(template)

    human_template = "Here's the email to reply to and consider any other comments from the user for the reply as well: {user_input}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(
        human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    chain = LLMChain(llm=chat, prompt=chat_prompt)
    response = chain.run(user_input=user_input, signature=signature, name=name)

    return response


def summarise_text(user_input, name="Danny"):
    chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1)

    template = """
    You are an intuitive and helpful assistant that summarises and enriches input text. Your goal is analyse the text and then summarise with additional context and context to enrich the input text and make it easier for the user to recall and understand in future. Keep your summary short and to the point, and make your summary and additional context useful and insightful. Where possible add section for 'Key Terms' and 'Related Topics'.

    Start your reply by saying: "Hi {name}, here's a summary:". And then proceed with the summary on a new line. Do not include the original text in your summary. Do not include any of the instructions in your summary. Use British English spelling and grammar. If you are unsure how to summarise the text, just say "I'm not sure how to summarise this text, please tell me more." and the user will post additional information for you to use in formulating your summary.
    """

    system_message_prompt = SystemMessagePromptTemplate.from_template(template)

    human_template = "Here's the text to analyse, summarise and enrich with additional context, key terms and related topics: {user_input}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(
        human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    chain = LLMChain(llm=chat, prompt=chat_prompt)
    response = chain.run(user_input=user_input, name=name)

    return response


def log_text(text):
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()

    summary = 'summary'
    tags = 'tags'

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
        INSERT INTO log_entries (timestamp, text, summary, tags)
        VALUES (?, ?, ?, ?)
    """, (timestamp, text, summary, tags))

    conn.commit()
    conn.close()


def research_text(user_input, name="Danny"):
    chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1)

    return user_input
