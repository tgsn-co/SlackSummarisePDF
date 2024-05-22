# AWS Lambda Function with API Gateway and Slack Integration

This code creates a Slack app that automatically summarise PDFs in Slack channel using OpenAI ChatGPT and AWS Lambda functions.

Specifically, it allows you to setup a Slack bot that takes in a pdf file, calls an AWS Lambda Function with API Gateway. This Lambda function is triggered by a Slack event. It retrieves a PDF document from Slack, extracts the text from the PDF, uses OpenAI to summarize the text, and posts the summary back to the Slack channel where the document was shared.

This README provides an overview and setup instructions for an AWS Lambda function that integrates with Slack to retrieve PDF documents, summarize their content using OpenAI, and send the summary back to Slack.

## Prerequisites

1. **AWS Account**: You need an AWS account to create and deploy the Lambda function.
2. **Slack App**: Create a Slack app with the necessary permissions and obtain the bot token.
3. **OpenAI API Key**: Obtain an API key from OpenAI.
4. **Python Packages**: Ensure the required Python packages are installed. This includes `requests`, `PyMuPDF`, `slack_sdk`, and `slack_bolt`.

## Environment Variables

The following environment variables need to be set in the Lambda function configuration:

- `BOT_TOKEN`: The bot token from your Slack app.
- `OPENAI_API_KEY`: Your OpenAI API key.

## Installation and Setup
**Clone the Repository:**
```
git clone https://github.com/tgsn-co/SlackSummarisePDF.git
cd SlackSummarisePDF
```
**Install Dependencies:**
```
pip install -r requirements.txt
```
**Set Up Docker (if relevant):**

If using Docker for deployment, ensure Docker is installed and running on your machine. Build and run the Docker container:
```
docker build -t SlackSummarisePDF .
docker run -p 9000:8080 SlackSummarisePDF
```
**Deploy the Lambda Function:**

Deploy the function to AWS Lambda using the AWS CLI or the AWS Management Console. Ensure the environment variables BOT_TOKEN and OPENAI_API_KEY are set in the Lambda configuration.

**Create the Slack App**

Go to https://api.slack.com/ and select the “Your Apps” tab on the site. Once on the page choose “Create New App”. You will be presented with a page to name your app and assign it to a workspace.
Once Created you should be directed to the “Basic Information” page of your Slack App.
On the sidebar, under the “Features” heading, select “Bot Users” and complete the fields and “Save Changes”.

**Configure API Gateway:**

1. Return to the Lambda function and create an API Gateway and configure it to trigger the Lambda function. In order to verify the gateway with Slack change the code in main.py to:

```
import json
def handler(event, context):
    print(f"Received event:\n{event}\nWith context:\n{context}")
    
    slack_body = event.get("body")
    slack_event = json.loads(slack_body)
    challenge_answer = slack_event.get("challenge")
    
    return {
        'statusCode': 200,
        'body': challenge_answer
    }
```

    Update the Docker image with the new code and push it the AWS Lambda function.

2. Copy the link provided in the API Gateway. Return to the Slack App page and enable Event Subscriptions and insert the link. The Slack API will then test the API Gateway and Lambda function.
    Our Gateway will now return the “challenge” value in our lambda function.

3. Configure your Slack app to subscribe to the file-uploaded event and set the request URL to the API Gateway endpoint.

4. Revert the Lambda function back to the orgional image with the working Slack App.

5. On the Slack App page Go to OAuth and Permissions --> Scopes --> Add chat:write scope.

6. Finally, back to “Basic Information” --> “Install your app to your workspace” --> “Allow”
   Once that is successful. Restart your slack app and install the app.

**Usage**

After completing the setup, add the bot to any Slack channel and share a PDF document in the channel. The Lambda function will be triggered, process the PDF, summarise its content using OpenAI, and post the summary back to the Slack channel.

## Potential Source of Errors

--**Failure to retrieve PDF:** Faliure to retrieve the document the get_pdf_text function will return "Failed to retrieve the document." This will be sent to OpenAI, summarised and sent to the channel. This will likely show up in the message.

--**Failure to Extract Text:** If the text cannot be extracted using the PYMuPDF module either an empty string or an error will be returned. An empty string will be reflected in the request to OpenAI and the slack message. If an error is thrown the funtion will stop and an error message will be returned to the CloudWatch Logs.

--**OpenAI Down:** If OpenAI may respond with an error code which will be posted to Slack.

--**Send_text_response:** If there is a problem sending the message to slack an error may be shown in the CloudWatch Logs. Howver, the message to slack may just fail to post and this may not show a log and onyl be noticed from the lack of response in the channel.

--**AWS problem:** If there is a problem with AWS this shown in the AWS consol for the Lambda function.

--**Slack changes:** You should should be notified of any changes to the Slack API by email as a registered APP creator.
