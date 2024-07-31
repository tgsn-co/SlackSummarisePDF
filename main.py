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
        {"role": "system", "content": """You are a tool used to provide a summary of a document. You will be given a document in the form of text, provide a detailed summary of the document. Only output the document summary and make the summary formatted for a slack message. Write "Document: document_name" at the start of the message. and use these rules: Slack Formatting Guide:

To format messages in Slack, use the following “Slack formatting” conventions. These instructions are tailored specifically for enhancing readability and organization within Slack’s desktop and mobile applications:

Bold Text: To make text bold, enclose it with asterisks (*). Example: *text* becomes bold.

Italic Text: To italicize text, enclose it with underscores (_). Example: _text_ becomes italic.

Strikethrough Text: To apply a strikethrough effect, enclose text with tildes (~). Example: ~text~ becomes strikethrough.

Inline Code: For inline code formatting, enclose text with backticks (```). Example: text becomes code.

Blockquote: To format text as a blockquote, start it with an angled bracket (>). Example: >text.

Code Block: To create a code block, enclose text with triple backticks (`````).

Ordered List: For an ordered list, start each item with a number followed by a period. Example: 1. text.

Bulleted List: For a bulleted list, start each item with an asterisk and a space. Example: * text.
"""},
        {"role": "user", "content": document}
    ]
    )
    return completion.choices[0].message.content

def send_text_response(event_body, response_text, ts):
    "Responds the Slack trigger by posting a response into the chat where the trigger comes from. "
    start_of_message = response_text[:50]
    print(f"Messaging Slack... {start_of_message}")
    SLACK_URL = "https://slack.com/api/chat.postMessage"
    channel_id = event_body['event']['channel_id']
    data = urllib.parse.urlencode(
        (
            ("token", os.environ["BOT_TOKEN"]),
            ("channel", channel_id),
            ("text", response_text),
            ("thread_ts", ts)
        )
    )
    data = data.encode("ascii")
    
    request = urllib.request.Request(SLACK_URL, data=data, method="POST")
    request.add_header( "Content-Type", "application/x-www-form-urlencoded" )
    
    x = urllib.request.urlopen(request).read()
    
def handler(event, context):
    "The main Lambda handler which orchestrates the Lambda Function."
    print(f"Received event:\n{event}\nWith context:\n{context}")
    body = json.loads(event['body'])
    headers = event.get('headers', {})
    if headers.get('X-Slack-Retry-Num') is None:
        file_id = body['event']['file']['id']
        response = client.files_info(file=file_id)
        file_info = response['file']
        if file_info['mimetype'] == 'application/pdf':
            private_url = file_info['url_private']
                        
            # Attempt to extract ts from private shares
            shares_private = file_info.get("shares", {}).get("private", {})
            ts_value = None

            if shares_private:
                channel_id, details = next(iter(shares_private.items()), (None, None))
                if details:
                    ts_value = details[0].get("ts")

            # If ts not found in private, attempt to extract from public shares
            if ts_value is None:
                shares_public = file_info.get("shares", {}).get("public", {})
                if shares_public:
                    channel_id, details = next(iter(shares_public.items()), (None, None))
                    if details:
                        ts_value = details[0].get("ts")
            text = get_pdf_text(private_url)
            summary = SlackApp(text)
        send_text_response(body, summary, ts_value)
    
    return {
        'statusCode': 200,
        'body': 'OK'
    }
