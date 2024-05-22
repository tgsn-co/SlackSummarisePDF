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

SLACK_URL = "https://slack.com/api/chat.postMessage"
OpenAI_Model = "gpt-4o-2024-05-13"

def get_pdf_text(url):
    """Queries Slack API at the url provided, looking for a PDF file. It then opens the file, and returns all the text contained within as a string."""
    headers = {"Authorization": f"Bearer {BOT_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200: # Check if the request returned status OK. Access the file if yes, otherwise return an error message
        with fitz.open(stream=response.content, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text
    else:
        return "Failed to retrieve the document."
    
def SlackApp(document: str) -> str:
    """Sends an API request to OpenAI asking for a summary of some input document. OpenAI returns the completed message generated by Chat-GPT 4o. 
    The function returns a string of this message."""
    completion = OpenAI_client.chat.completions.create(
    model=OpenAI_Model,
    messages=[
        {"role": "system", "content": "You are part of a helpful assistant used to support project design and bid writing for a company called TGSN that works in the development, humanitarian and defense sectors. You are a tool used to provide a summary of a document. You will be given a document in the form of text, provide a detailed summary of the document. Only output the document summary."},
        {"role": "user", "content": document}
    ]
    )
    return completion.choices[0].message.content

def send_text_response(event_body, response_text):
    """
    Posts a response message to the Slack channel where the original trigger event occurred.

    This function takes the event body from the Slack event and the generated response text.
    It constructs and sends a message back to the appropriate Slack channel where the original file was shared.
    """
    
    print("Messaging Slack...")
    channel_id = event_body['event']['channel_id']
    data = urllib.parse.urlencode(
        (
            ("token", os.environ["BOT_TOKEN"]),
            ("channel", channel_id),
            ("text", response_text),
        )
    )
    data = data.encode("ascii")
    
    request = urllib.request.Request(SLACK_URL, data=data, method="POST")
    request.add_header( "Content-Type", "application/x-www-form-urlencoded" )
    
    x = urllib.request.urlopen(request).read()
    
def handler(event, context):
    """
    The main Lambda handler that processes Slack events and coordinates the workflow.

    This function is triggered by an event from the API Gateway, which in turn is triggered by a Slack event. 
    It handles the event by performing the following steps:
    1. Parses the event and context information.
    2. Checks for retry headers to avoid duplicate processing.
    3. Retrieves the file ID from the event body and fetches file information from Slack.
    4. If the file is a PDF, retrieves the text from the PDF.
    5. Sends the text to OpenAI for summarization.
    6. Posts the summary back to the Slack channel.
    """
    print(f"Received event:\n{event}\nWith context:\n{context}")
    
    body = json.loads(event['body'])
    headers = event.get('headers', {})
    if headers.get('X-Slack-Retry-Num') is None:
        file_id = body['event']['file']['id']
        response = client.files_info(file=file_id)
        file_info = response['file']
        
        if file_info['mimetype'] == 'application/pdf':
            private_url = file_info['url_private']
            
            text = get_pdf_text(private_url)
            summary = SlackApp(text)
        send_text_response(body, summary)
    
    return {
        'statusCode': 200,
        'body': 'OK'
    }
