"""
Created on Tue May  7 12:23:34 2024

@author: lucas
"""

import os
import requests
import fitz  # PyMuPDF

from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_bolt import App

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


from dotenv import load_dotenv
# Use environment variables to manage sensitive information securely
load_dotenv()
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
SLACK_APP_TOKEN = os.environ.get('SLACK_APP_TOKEN')
OPENAI_API_KEY  = os.environ.get('OPENAI_API_KEY')

def SlackApp(document: str) -> str:
    SlackAppTemplate = """You are part of a helpful assistant used to support project design and bid writing for a company called TGSN that works in the development, humanitarian and defense sectors.
    You are a tool used to provide a summary of a document. 
    You will be given a document in the form of text, provide a detailed summary of the document.
    Only output the document summary.
    
    Document: {document}
    """
    prompt = ChatPromptTemplate.from_template(SlackAppTemplate)
    model = ChatOpenAI(model="gpt-4-0125-preview", temperature=0.5)
    chain = (
        {"document": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )
    return chain.invoke(document)


# Get file from URL
def get_pdf_text(url):
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with fitz.open(stream=response.content, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text
    else:
        return "Failed to retrieve the document."


# Event API & Web API
app = App(token=SLACK_BOT_TOKEN)
client = WebClient(token=SLACK_BOT_TOKEN)

@app.event("file_shared")
def handle_message_events(body, logger):
    print(str(body["event"]))
    file_id = body["event"]['file_id']
    channel_id = body["event"]["channel_id"]  
    thread_ts = body["event"]["event_ts"] #Fix this
    try:
        response = client.files_info(file=file_id)
        file_info = response['file']
        if file_info['mimetype'] == 'application/pdf':
            private_url = file_info['url_private']
            text = get_pdf_text(private_url)

            private_url = file_info['url_private']
            text = get_pdf_text(private_url)
            
            if text != "Failed to retrieve the document.":
                summary = SlackApp(text)
                client.chat_postMessage(channel=channel_id, thread_ts=thread_ts, text=f"Summary: {summary}")
            else:
                client.chat_postMessage(channel=channel_id, thread_ts=thread_ts, text="Failed to retrieve and process the document.")

    except Exception as e:
        print(f"Error retrieving file: {e}")
        client.chat_postMessage(channel=channel_id, thread_ts=thread_ts,  text=f"An error occurred: {str(e)}")


if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
