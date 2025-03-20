import os
import argparse
from twilio.rest import Client
from dotenv import load_dotenv


def make_call(to_number: str):
    load_dotenv(override=True)

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    client = Client(account_sid, auth_token)

    # Initiate an outbound call
    call = client.calls.create(
        to=to_number,  # Recipient's phone number
        from_="+18317132074",  # Your Twilio phone number
        url="https://splendid-working-stallion.ngrok-free.app",  # URL for TwiML instructions
    )

    print(f"Call initiated with SID: {call.sid}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make a phone call using Twilio")
    parser.add_argument(
        "phone_number",
        help="Phone number to call (in format +1XXXXXXXXXX)",
    )

    args = parser.parse_args()
    make_call(args.phone_number)
