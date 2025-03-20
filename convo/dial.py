import os
from twilio.rest import Client
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv(override=True)

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    client = Client(account_sid, auth_token)

    # Initiate an outbound call
    call = client.calls.create(
        to="+18609188146",  # Recipient's phone number
        from_="+18317132074",  # Your Twilio phone number
        url="https://splendid-working-stallion.ngrok-free.app",  # URL for TwiML instructions
    )

    print(f"Call initiated with SID: {call.sid}")
