# AWS Lambda Function with API Gateway and Slack Integration

This README provides an overview and setup instructions for an AWS Lambda function that integrates with Slack to retrieve PDF documents, summarize their content using OpenAI, and send the summary back to Slack.

## Overview

This Lambda function is triggered by a Slack event. It retrieves a PDF document from Slack, extracts the text from the PDF, uses OpenAI to summarize the text, and posts the summary back to the Slack channel where the document was shared.

## Prerequisites

1. **AWS Account**: You need an AWS account to create and deploy the Lambda function.
2. **Slack App**: Create a Slack app with the necessary permissions and obtain the bot token.
3. **OpenAI API Key**: Obtain an API key from OpenAI.
4. **Python Packages**: Ensure the required Python packages are installed. This includes `requests`, `PyMuPDF`, `slack_sdk`, and `slack_bolt`.

## Environment Variables

The following environment variables need to be set in the Lambda function configuration:

- `BOT_TOKEN`: The bot token from your Slack app.
- `OPENAI_API_KEY`: Your OpenAI API key.

## Likely Failiures

--**Failure to retrieve PDF:** Faliure to retrieve the document the get_pdf_text function will return "Failed to retrieve the document." This will be sent to OpenAI, summarised and sent to the channel. This will likely show up in the message.
--**Failure to Extract Text:** If the text cannot be extracted using the PYMuPDF module either an empty string will be returned this will be reflected in the request to OpenAI and the slack message. If an error is thrown the  funtion will stop and an error message will be returned to the CloudWatch Logs.

--**OpenAI Down:** If OpenAI may respond with an error code which will be posted to Slack.

--**Send_text_response:** If there is a problem sending the message to slack an error may be shown in the CloudWatch Logs. Howver, the message to slack may just fail to post and this may not show a log and onyl be noticed from the lack of response in the channel.

--**AWS problem:** If there is a problem with AWS this shown in the AWS consol for the Lambda function.

--**Slack changes:** We should be notified of any changes to the Slack API by email as a registered APP creator.
