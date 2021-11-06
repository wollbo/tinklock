from dotenv import load_dotenv
import requests
import json
import os

ping = False
user = False
access = True

load_dotenv()

TINK_CLIENT_ID = os.getenv('TINK_CLIENT_ID')
TINK_CLIENT_SECRET = os.getenv('TINK_CLIENT_SECRET')
ACCOUNT_VERIFICATION_REPORT_ID = os.getenv('ACCOUNT_VERIFICATION_REPORT_ID')
TINK_CREDENTIALS_ID = os.getenv('TINK_CREDENTIALS_ID')
TINK_CODE = os.getenv('TINK_CODE')

def construct_url(
    url='https://api.tink.com/api/v1/oauth/token', 
    ending='token', 
    **kwargs
    ):
    if url.endswith(ending) and kwargs:
        url += '?'
        for key, value in kwargs.items():
            url += f'{key}={value}&'
    return url.rstrip('&')

if ping:
    url = "https://api.tink.com/api/v1/monitoring/ping"
    r = requests.get(url)

if user:
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    url = construct_url(
        url='https://link.tink.com/1.0/api/v1/oauth/token',
        ending='token',
        client_id=TINK_CLIENT_ID, 
        client_secret=TINK_CLIENT_SECRET,
        grant_type='client_credentials',
        scope='user:create',
    )
    r = requests.post(url, headers=headers)

if access:
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    url = construct_url(
        url='https://link.tink.com/1.0/api/v1/oauth/token',
        ending='token',
        code=TINK_CODE,
        client_id=TINK_CLIENT_ID, 
        client_secret=TINK_CLIENT_SECRET,
        grant_type='authorization_code',
    )
    r = requests.post(url, headers=headers)
    
print(url)
print(r)

"""
curl"https://api.tink.com/api/v1/accounts/{id}/balances"\
-H"Authorization: Bearer {YOUR TOKEN}"
"""