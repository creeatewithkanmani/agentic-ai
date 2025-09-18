import streamlit as st
from transformers import pipeline
import os
from dotenv import load_dotenv
from ics import Calendar, Event
from datetime import datetime, timedelta
import smtplib
import pytz # Import the pytz library
import dateparser # Import dateparser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Load environment variables
load_dotenv()

# --- Model Loading ---
# Cache the model loading to avoid reloading on every interaction
@st.cache_resource
def load_classifier():
    """Loads the Hugging Face pipeline and caches it."""
    # Using a Question-Answering model now for detail extraction
    return pipeline("question-answering", model="deepset/roberta-base-squad2")

# --- Detail Extraction ---
def extract_details(context):
    """Uses the QA model and dateparser to extract event details from a user's prompt."""
    qa_pipeline = load_classifier()
    details = {"title": None, "description": None, "to_email": None, "event_datetime": None}

    # Ask questions to find details in the context
    title_question = "What is the title of the event?"
    description_question = "What is the description of the event?"
    email_question = "What is the email address to send the invite to?"

    # Extract Title
    title_result = qa_pipeline(question=title_question, context=context)
    if title_result['score'] > 0.1: # Confidence threshold
        details['title'] = title_result['answer']

    # Extract Description (can often be the same as title in short prompts)
    description_result = qa_pipeline(question=description_question, context=context)
    if description_result['score'] > 0.1:
        details['description'] = description_result['answer']
        # If title wasn't found but description was, use it as title
        if not details['title']:
            details['title'] = details['description']


    # Simple regex for email as it's more reliable
    import re
    email_match = re.search(r'[\w\.-]+@[\w\.-]+', context)
    if email_match:
        details['to_email'] = email_match.group(0)

    # Use dateparser to find date and time information
    # 'PREFER_DATES_FROM': 'future' helps interpret ambiguous dates like "tomorrow" correctly
    parsed_datetime = dateparser.parse(context, settings={'PREFER_DATES_FROM': 'future', 'RETURN_AS_TIMEZONE_AWARE': True})
    if parsed_datetime:
        details['event_datetime'] = parsed_datetime

    return details


def create_calendar_invite(title, description, to_email, from_email, event_datetime):
    """Creates a more robust calendar invite with a specific start time."""
    c = Calendar()
    e = Event()
    e.name = title
    e.description = description
    
    # The datetime object is now passed in directly
    if event_datetime:
        e.begin = event_datetime
    else:
        # Fallback if something goes wrong, though the logic should prevent this
        e.begin = datetime.now(pytz.utc)

    e.end = e.begin + timedelta(hours=1) # Add a default 1-hour duration

    # --- Crucial fields for a proper invitation ---
    # The ics library adds 'mailto:' automatically.
    e.organizer = from_email
    e.attendees.add(to_email)
    
    c.events.add(e)
    
    # This tells the mail client that this is an invitation to be processed
    c.method = "REQUEST"

    # The ics library automatically handles writing the file correctly
    # Using .serialize() as recommended by the library to avoid FutureWarning
    with open("invite.ics", "w") as f:
        f.write(c.serialize())

    # Pass the from_email to the send function
    send_email(to_email, title, description, from_email)
    return True

def send_email(to_email, subject, body, from_email):
    from_password = os.getenv("GMAIL_APP_PASSWORD")

    if not from_password:
        st.error("Gmail App Password not found. Please set the GMAIL_APP_PASSWORD environment variable.")
        return

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    attachment = open("invite.ics", "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % "invite.ics")
    msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
    except Exception as e:
        st.error(f"Failed to send email: {e}")


st.title("Agentic AI Calendar Invite Creator")

# --- App Constants ---
FROM_EMAIL = "kanmani.abi@gmail.com"  # Your email address as the sender/organizer

if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'details' not in st.session_state:
    st.session_state['details'] = {"title": None, "description": None, "to_email": None, "event_datetime": None}
# Add a state to track what the AI is waiting for
if 'state' not in st.session_state:
    st.session_state['state'] = "awaiting_prompt"


st.info("e.g., 'Create a calendar invite for a team meeting about the Q3 roadmap for user@example.com'")

# --- Chat History Display ---
# Moved from the bottom to display before the input box
for message in st.session_state.history:
    st.write(message)


# --- Input and Logic ---
# Use a form to manage the input and submission
with st.form(key='chat_form', clear_on_submit=True):
    user_input = st.text_input("You: ", key="user_input")
    submit_button = st.form_submit_button(label='Send')

if submit_button and user_input:
    # Append user message to history immediately
    st.session_state.history.append(f"You: {user_input}")
    
    details = st.session_state.details
    response = ""
    current_state = st.session_state.state

    # --- New, more robust logic ---

    # Check for simple greetings first
    is_greeting = user_input.lower() in ["hi", "hello", "hey", "yo"]
    if is_greeting and current_state == "awaiting_prompt":
        response = "Hello! How can I help you create a calendar invite today?"
        st.session_state.history.append(f"AI: {response}")
        st.rerun()

    # If we are waiting for a specific piece of info, try to fill it
    elif current_state == "awaiting_email":
        import re
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', user_input)
        if email_match:
            details['to_email'] = email_match.group(0)
            st.session_state.details['to_email'] = details['to_email']
            st.session_state.state = "awaiting_prompt" # Reset state
        else:
            response = "That doesn't look like a valid email. Could you please provide a correct email address?"

    elif current_state == "awaiting_title":
        details['title'] = user_input
        st.session_state.details['title'] = user_input
        st.session_state.state = "awaiting_prompt" # Reset state

    elif current_state == "awaiting_description":
        details['description'] = user_input
        st.session_state.details['description'] = user_input
        st.session_state.state = "awaiting_prompt" # Reset state

    elif current_state == "awaiting_datetime":
        # Use dateparser to understand the user's input for date/time
        parsed_datetime = dateparser.parse(user_input, settings={'PREFER_DATES_FROM': 'future', 'RETURN_AS_TIMEZONE_AWARE': True})
        if parsed_datetime:
            details['event_datetime'] = parsed_datetime
            st.session_state.details['event_datetime'] = parsed_datetime
            st.session_state.state = "awaiting_prompt" # Reset state
        else:
            response = "I'm sorry, I didn't understand that date and time. Could you try again? (e.g., 'tomorrow at 3pm' or 'Oct 5th at 10:00')"


    # If we are in the initial state, try to extract everything
    elif current_state == "awaiting_prompt":
        extracted_details = extract_details(user_input)
        # Only update if something was actually found
        if any(v is not None for v in extracted_details.values()):
            st.session_state.details.update({k: v for k, v in extracted_details.items() if v is not None})
            details = st.session_state.details # Refresh details

    # --- After processing input, check the status and decide what to do next ---
    
    # 1. Check if we have everything to send the invite
    if all(details.get(key) for key in ["title", "description", "to_email", "event_datetime"]):
        st.write("All details collected. Creating and sending invite...")
        success = create_calendar_invite(
            title=details['title'], 
            description=details['description'], 
            to_email=details['to_email'], 
            from_email=FROM_EMAIL,
            event_datetime=details['event_datetime']
        )
        if success:
            response = "Calendar invite sent successfully!"
            # Reset for the next request
            st.session_state.details = {"title": None, "description": None, "to_email": None, "event_datetime": None}
            st.session_state.state = "awaiting_prompt"
        else:
            response = "There was an issue sending the calendar invite."

    # 2. If not, ask for the first missing piece of information
    elif not details.get('to_email'):
        response = "I see you want to create an event. Who should I send the invite to? Please provide an email address."
        st.session_state.state = "awaiting_email"
    
    elif not details.get('title'):
        response = "I have the email. What should be the title of the event?"
        st.session_state.state = "awaiting_title"

    elif not details.get('description'):
        response = "Great, I have the title. What should be the description for the event?"
        st.session_state.state = "awaiting_description"

    elif not details.get('event_datetime'):
        response = "Got it. When should the event be scheduled? (e.g., tomorrow at 5pm, Oct 5th 14:00)"
        st.session_state.state = "awaiting_datetime"


    # Add the final response to history and rerun
    if response:
        st.session_state.history.append(f"AI: {response}")

    st.rerun()
