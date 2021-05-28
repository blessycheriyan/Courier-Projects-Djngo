import os
from twilio.rest import Client
from django.conf import settings


# Your Account Sid and Auth Token from twilio.com/console
# and set the environment variables. See http://twil.io/secure

def send_sms(body, from_, to):
    """

    """
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    client = Client(account_sid, auth_token)
    message = client.messages \
        .create(
        body=body,
        from_=from_,
        to=to
    )

    print(message.sid)
    return message.sid
