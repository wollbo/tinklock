from dotenv import load_dotenv
import requests
import json
import os

ping = False
user = True
access = False
account = True

load_dotenv()

def empty_to_none(field):
    value = os.getenv(field)
    if value is None or len(value) == 0:
        return None
    return value

def append_to_env(**kwargs): # extend to read .env first
    with open(".env", "a") as f:
        for key, value in kwargs.items():
            f.write(f'\n{key}={value}')
    f.close()

# Required .env variables obtained from Tink
TINK_CLIENT_ID = empty_to_none('TINK_CLIENT_ID')
TINK_CLIENT_SECRET = empty_to_none('TINK_CLIENT_SECRET')
ACTOR_CLIENT_ID = empty_to_none('ACTOR_CLIENT_ID')

# Generated variables using Tink client credentials
BEARER_TOKEN = empty_to_none('BEARER_TOKEN')
USER_ID = empty_to_none('USER_ID')
USER_AUTH_CODE = empty_to_none('USER_AUTH_CODE')

BASE_URL = 'https://api.tink.com/api/v1/'

def construct_url(
    url='https://api.tink.com/api/v1/oauth/token', 
    ending='token', 
    **kwargs
    ):
    """Used for generating user interactive Tink Link URL"""
    if url.endswith(ending) and kwargs:
        url += '?'
        for key, value in kwargs.items():
            url += f'{key}={value}&'
    return url.rstrip('&')


def create_bearer_token(base_url, **kwargs):
    url = base_url + 'oauth/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {key: value for key, value in kwargs.items()}
    r = requests.post(url, headers=headers, data=data)
    assert(str(r.status_code).startswith('2'), r.text)
    return r.json()["access_token"]


def create_tink_user(base_url, bearer_token, **kwargs):
    url = base_url + 'user/create'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/json; charset=utf-8' 
    }
    data = {key: value for key, value in kwargs.items()}
    r = requests.post(url, headers=headers, json=data) # must be passed as json
    assert(str(r.status_code).startswith('2'), r.text)
    return r.json()["user_id"]


def create_authorization(base_url, bearer_token, **kwargs):
    url = base_url + 'oauth/authorization-grant'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {key: value for key, value in kwargs.items()}
    r = requests.post(url, headers=headers, data=data)
    assert(str(r.status_code).startswith('2'), r.text)
    return r.json()["code"]


def create_delegated_authorization(base_url, bearer_token, **kwargs):
    url = base_url + 'oauth/authorization-grant/delegate'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {key: value for key, value in kwargs.items()}
    r = requests.post(url, headers=headers, data=data)
    assert(str(r.status_code).startswith('2'), r.text)
    return r.json()["code"]


### GET REQUESTS ###

def get_user(base_url, bearer_token):
    url = base_url + '/user'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/json; charset=utf-8' 
    }
    r = requests.get(url, headers=headers)
    return r

def list_accounts(base_url, bearer_token):
    url = base_url + '/accounts/list'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/json; charset=utf-8' 
    }
    r = requests.get(url, headers=headers)
    return r


def get_balance(base_url, bearer_token, id):
    url = base_url + f'accounts/{id}/balances'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/json; charset=utf-8' 
    }
    r = requests.get(url, headers=headers)
    return r


if ping:
    url = 'https://api.tink.com/api/v1/monitoring/ping'
    r = requests.get(url)

if user:
    if not BEARER_TOKEN:
        bearer = create_bearer_token(
            BASE_URL, 
            client_id=TINK_CLIENT_ID,
            client_secret=TINK_CLIENT_SECRET,
            grant_type='client_credentials',
            scope='authorization:grant,user:create' # best practice: should be separated into two
        )
        #append_to_env('BEARER_TOKEN') = bearer expires every 30 min

    if not USER_ID:
        USER_ID = create_tink_user(
            BASE_URL,
            bearer,
            locale='en_US',
            market='SE'
        )
        append_to_env(USER_ID=USER_ID)

    if not USER_AUTH_CODE:
        USER_AUTH_CODE = create_delegated_authorization(
            BASE_URL,
            bearer,
            user_id=USER_ID,
            id_hint='hackathon_user',
            actor_client_id=ACTOR_CLIENT_ID,
            scope='credentials:read,credentials:refresh,credentials:write,providers:read,user:read,authorization:read'
        )
        append_to_env(USER_AUTH_CODE=USER_AUTH_CODE) #consider generating this every time
    
if access:
    url = 'https://link.tink.com/1.0/credentials/add'
    data = {
        "client_id": TINK_CLIENT_ID,
        "redirect_uri": 'https://console.tink.com/callback',
        "authorization_code": USER_AUTH_CODE,
        "market": 'SE'
    }
    url = construct_url(
        url='https://link.tink.com/1.0/credentials/add',
        ending='add',
        **data
    )
    print(url)

if account:
    code = create_authorization(
            BASE_URL,
            bearer,
            user_id=USER_ID,
            scope='accounts:read,balances:read,transactions:read'
    )
    access_token = create_bearer_token( # this should return the whole json object, not just token
        BASE_URL,
        code=code,
        client_id=TINK_CLIENT_ID,
        client_secret=TINK_CLIENT_SECRET,
        grant_type='authorization_code'
    )
    
    print(list_accounts(BASE_URL, access_token)) # who is the authenticated user?
    # use this to gain account_id and run get balance
    # see below for implementation, might be different with continuous access
    # https://docs.tink.com/resources/aggregation/balances
    # https://docs.tink.com/api#data-v1/account/list-accounts
