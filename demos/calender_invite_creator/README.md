# Agentic AI Calendar Invite Creator

This project is an interactive, agentic AI application that helps users create and send calendar invites using natural language prompts. It leverages Hugging Face's NLP models, Streamlit for the chat UI, and Python libraries for calendar and email integration.

## Features

- *Conversational Chat UI:* Built with Streamlit, the app guides users through the process of creating a calendar invite, asking for missing details as needed.
- *Natural Language Understanding:* Uses a Hugging Face question-answering model to extract event details (title, description, recipient email, date, and time) from user prompts.
- *Flexible Date & Time Parsing:* Supports a wide range of human-friendly date and time expressions (e.g., "tomorrow at 3pm", "Oct 5th 14:00") using the dateparser library.
- *Calendar Invite Generation:* Creates a standards-compliant .ics file with all required fields (organizer, attendee, summary, description, start/end time).
- *Email Integration:* Sends the invite as an email attachment using SMTP and a Google App Password for authentication.
- *Stateful Conversation:* Remembers chat history and the current state of the invite creation process within the session.

## How It Works

1. *User Interaction:*
   - The user enters a prompt (e.g., "Create a calendar invite for a team meeting about the Q3 roadmap for user@example.com tomorrow at 4pm").
   - The AI attempts to extract all necessary details from the prompt.
   - If any details are missing (email, title, description, date/time), the AI asks for them one by one.

2. *Detail Extraction:*
   - The app uses a Hugging Face QA model to extract title, description, and email.
   - The dateparser library is used to extract and interpret date and time information.

3. *Invite Creation:*
   - Once all details are collected, the app generates an .ics calendar invite file with the correct fields and time zone.
   - The invite is sent as an email attachment to the specified recipient.

4. *Session State:*
   - The chat history and invite details are retained for the duration of the browser session.

## Setup & Usage

1. *Clone the repository and install dependencies:*
   bash
   pip install -r requirements.txt
   

2. *Set up your environment variables:*
   - Create a .env file with your Hugging Face API token and Gmail App Password:
     
     HUGGINGFACE_API_TOKEN="your_huggingface_token"
     GMAIL_APP_PASSWORD="your_gmail_app_password"
     
   - Update the sender email in app.py (FROM_EMAIL).

3. *Run the app:*
   bash
   streamlit run app.py
   
   - Open your browser to [http://localhost:8501](http://localhost:8501)

4. *Interact with the AI:*
   - Type your event request in natural language.
   - Answer any follow-up questions for missing details.
   - The app will send a calendar invite to the specified recipient.

## Example Prompts

- Create a calendar invite for a project demo for alice@example.com tomorrow at 2pm
- Schedule a meeting with bob@example.com on Oct 5th at 10:00 about Q4 planning

## Security Notes
- Use a Google App Password (not your main Gmail password) for email sending.
- Do not share your .env file or credentials.

## Dependencies
- streamlit
- transformers
- torch
- python-dotenv
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib
- ics
- pytz
- dateparser

## License
MIT
