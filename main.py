import os
import urllib.request, urllib.parse

import requests
import fitz  # PyMuPDF
import os
import urllib
from openai import OpenAI

from slack_sdk import WebClient
from slack_bolt import App
import json


BOT_TOKEN = os.environ.get('BOT_TOKEN')
OPENAI_API_KEY  = os.environ.get('OPENAI_API_KEY')

OpenAI_client = OpenAI()
app = App(token=BOT_TOKEN)
client = WebClient(token=BOT_TOKEN)


def get_pdf_text(url):
    "Retrieves a PDF from a private URL from Slack then returns all of the text."
    headers = {"Authorization": f"Bearer {BOT_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with fitz.open(stream=response.content, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text
    else:
        return "Failed to retrieve the document."
    
def SlackApp(document: str) -> str:
    "Sends some text to OpenAI asking for it to be summarised"
    completion = OpenAI_client.chat.completions.create(
    model="gpt-4o-2024-05-13",
    messages=[
        {"role": "system", "content": "You are part of a helpful assistant used to support project design and bid writing for a company called TGSN that works in the development, humanitarian and defense sectors. You are a tool used to provide a summary of a document. You will be given a document in the form of text, provide a detailed summary of the document. Only output the document summary."},
        {"role": "user", "content": document}
    ]
    )
    return completion.choices[0].message.content

def send_text_response(event_body, response_text, file_info):
    "Responds the Slack trigger by posting a response into the chat where the trigger comes from. "
    print("Messaging Slack...")
    SLACK_URL = "https://slack.com/api/chat.postMessage"
    channel_id = event_body['event']['channel_id']
    thread_ts = file_info['shares']['public'][channel_id][0]['thread_ts']
    data = urllib.parse.urlencode(
        (
            ("token", os.environ["BOT_TOKEN"]),
            ("channel", channel_id),
            ("text", response_text),
            (thread_ts, thread_ts)
        )
    )
    data = data.encode("ascii")
    
    request = urllib.request.Request(SLACK_URL, data=data, method="POST")
    request.add_header( "Content-Type", "application/x-www-form-urlencoded" )
    
    x = urllib.request.urlopen(request).read()
    
def handler(event, context):
    "The main Lambda handler which orchestrates the Lambda Function and sends an acknowledgement back to slack."
    print(f"Received event:\n{event}\nWith context:\n{context}")
    body = json.loads(event['body'])
    headers = event.get('headers', {})
    if headers.get('X-Slack-Retry-Num') is None:
        # print(f"body = {body}")
        file_id = body['event']['file']['id']
        # print(file_id)
        response = client.files_info(file=file_id)
        # print(f"response = {response}")
        file_info = response['file']
        
        if file_info['mimetype'] == 'application/pdf':
            private_url = file_info['url_private']
            
            text = get_pdf_text(private_url)
            # print(f"text: {text}")
            summary = SlackApp(text)
            # print(f"summary: {summary}")
        send_text_response(body, summary, file_info)
    
    return {
        'statusCode': 200,
        'body': 'OK'
    }
