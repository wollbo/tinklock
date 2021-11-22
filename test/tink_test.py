from dotenv import load_dotenv
import requests
import json
import os
import sys
import time


## TEST SCRIPT FOR VERIFYING TINK BEHAVIOUR WITHOUT BRIDGE ##

ping = False
user = True
access = False
refresh = True
account = True


load_dotenv()


def load_tinkenv():
    load_dotenv()
    _env = [
        'TINK_CLIENT_ID',
        'TINK_CLIENT_SECRET', 
        'ACTOR_CLIENT_ID',
        'USER_ID',
        'CREDENTIALS_ID'
        ]
    return {e: empty_to_none(e) for e in _env}


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


def json_parse(json_object, path):
    """Basic parser, assumes path is reachable in json_object"""
    for item in path:
        json_object = json_object[item]
    return json_object


# Required .env variables obtained from Tink
TINK_CLIENT_ID = empty_to_none('TINK_CLIENT_ID')
TINK_CLIENT_SECRET = empty_to_none('TINK_CLIENT_SECRET')
ACTOR_CLIENT_ID = empty_to_none('ACTOR_CLIENT_ID') # Tink open banking identifier

# Generated variables using Tink client credentials
BEARER_TOKEN = empty_to_none('BEARER_TOKEN')
USER_ID = empty_to_none('USER_ID')
CREDENTIALS_ID =  empty_to_none('CREDENTIALS_ID') # denotes a specific consent
USER_AUTH_CODE = empty_to_none('USER_AUTH_CODE') # one-time code

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
    print(url)
    print(headers)
    print(data)
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
    """Authorizes Tink Link to connect user account, code identifies user"""
    url = base_url + 'oauth/authorization-grant/delegate'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {key: value for key, value in kwargs.items()}
    r = requests.post(url, headers=headers, data=data)
    assert(str(r.status_code).startswith('2'), r.text)
    return r.json()["code"]


### TINK LINK USER INTERACTION FUNCTIONS ###

def create_credentials(client_id, auth_code):
    base_url = 'https://link.tink.com/1.0/credentials/add'
    data = {
        "client_id": client_id,
        "redirect_uri": 'https://console.tink.com/callback',
        "authorization_code": auth_code,
        "market": 'SE'
    }
    url = construct_url(
        url=base_url,
        ending='add',
        **data
    )
    return url


def refresh_credentials(client_id, auth_code, credentials_id):
    base_url = 'https://link.tink.com/1.0/credentials/refresh'
    data = {
        "client_id": client_id,
        "redirect_uri": 'https://console.tink.com/callback',
        "authorization_code": auth_code,
        "market": 'SE',
        "credentials_id": credentials_id
    }
    url = construct_url(
        url=base_url,
        ending='refresh',
        **data
    )
    return url


def refresh_credentials_auto(base_url, bearer, credentials_id):
    url = base_url + f'credentials/{credentials_id}/refresh'
    headers = {
        'Authorization': 'Bearer ' + bearer,
        'Content-Type': 'application/json; charset=utf-8'
    }
    return url, headers


def update_consent(client_id, auth_code, credentials_id):
    base_url = 'https://link.tink.com/1.0/transactions/update-consent'
    data = {
        "client_id": client_id,
        "redirect_uri": 'https://console.tink.com/callback',
        "authorization_code": auth_code,
        "market": 'SE',
        "credentials_id": credentials_id
    }
    url = construct_url(
        url=base_url,
        ending='update-consent',
        **data
    )
    return url


def authenticate_credentials(client_id, auth_code, credentials_id):
    base_url = 'https://link.tink.com/1.0/credentials/authenticate'
    data = {
        "client_id": client_id,
        "redirect_uri": 'https://console.tink.com/callback',
        "authorization_code": auth_code,
        "market": 'SE',
        "credentials_id": credentials_id
    }
    url = construct_url(
        url=base_url,
        ending='authenticate',
        **data
    )
    return url


### GET REQUESTS ###


def get_consents(base_url, bearer_token):
    url = base_url + 'provider-consents'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/json; charset=utf-8'
    }
    return url, headers

def get_user(base_url, bearer_token):
    url = base_url + 'user'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/json; charset=utf-8' 
    }
    r = requests.get(url, headers=headers)
    return r


def list_accounts(base_url, bearer_token):
    url = base_url + 'accounts'
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

if user: # move this part to adapter 
    if not BEARER_TOKEN: # used for creating both user and authorization code
        bearer = create_bearer_token(
            BASE_URL, 
            client_id=TINK_CLIENT_ID,
            client_secret=TINK_CLIENT_SECRET,
            grant_type='client_credentials',
            scope='authorization:grant,user:create' # best practices: should be separated into two
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
            scope='authorization:grant,authorization:read,credentials:read,credentials:refresh,credentials:write,providers:read,user:read,provider-consents:read'
        )

        url = update_consent( # can expire
            TINK_CLIENT_ID, 
            USER_AUTH_CODE, 
            CREDENTIALS_ID
        )

        sys.exit(url)


if access:
    url = create_credentials(
        client_id=TINK_CLIENT_ID, 
        auth_code=USER_AUTH_CODE
    )
    print(url) # consider having the user register the credentials_id through SC

# NOTE: Difference between client access token and user access token!!!

if refresh: # credentials need to be refreshed after each transaction, onlyBuyer EA?
    
    client_access_token = create_bearer_token(
        BASE_URL, 
        client_id=TINK_CLIENT_ID,
        client_secret=TINK_CLIENT_SECRET,
        grant_type='client_credentials',
        scope='authorization:grant'
    )

    authorization_code = create_authorization(
        BASE_URL,
        client_access_token,
        user_id=USER_ID,
        id_hint='hackathon_user',
        scope='authorization:grant,authorization:read,credentials:read,credentials:refresh,credentials:write,providers:read,user:read,provider-consents:read'
    ) # cant simply use the delegated one!!
    user_access_token = create_bearer_token( # this should ideally return the whole json object
        BASE_URL,
        code=authorization_code,
        client_id=TINK_CLIENT_ID,
        client_secret=TINK_CLIENT_SECRET,
        grant_type='authorization_code'
    )

    # FOR LISTING EXISTING CONSENTS
    #url, headers = get_consents(BASE_URL, user_access_token)
    #r = requests.get(url, headers=headers)
    #print(r.json())
    #sys.exit(0)

    url, headers = refresh_credentials_auto(
        BASE_URL,
        user_access_token,
        CREDENTIALS_ID
    )
    r = requests.post(url, headers=headers)
    print(r)
    print(r.status_code)
    assert(r.status_code == 204, 'Wrong status code!')
    status=''
    while status != 'UPDATED': # consider creating an outer function for this 
        client_access_token = create_bearer_token(
            BASE_URL, 
            client_id=TINK_CLIENT_ID,
            client_secret=TINK_CLIENT_SECRET,
            grant_type='client_credentials',
            scope='authorization:grant' # best practices: should be separated into two
        )

        authorization_code = create_authorization(
            BASE_URL,
            client_access_token,
            user_id=USER_ID,
            id_hint='hackathon_user',
            scope='authorization:grant,authorization:read,credentials:read,credentials:refresh,credentials:write,providers:read,user:read,provider-consents:read'
        ) # cant simply use the delegated one!!
        user_access_token = create_bearer_token( # this should ideally return the whole json object
            BASE_URL,
            code=authorization_code,
            client_id=TINK_CLIENT_ID,
            client_secret=TINK_CLIENT_SECRET,
            grant_type='authorization_code'
        )
        url, headers = get_consents(BASE_URL, user_access_token)
        r = requests.get(url, headers=headers)
        consents = r.json()["providerConsents"]
        status = [cons["status"] for cons in consents if cons["credentialsId"] == CREDENTIALS_ID][0]
        print(status)
        time.sleep(2) # this takes 2-3 seconds to update!
        if status == 'AWAITING_MOBILE_BANKID_AUTHENTICATION':
            client_access_token = create_bearer_token(
                BASE_URL, 
                client_id=TINK_CLIENT_ID,
                client_secret=TINK_CLIENT_SECRET,
                grant_type='client_credentials',
                scope='authorization:grant' # best practices: should be separated into two
            )

            authorization_code = create_delegated_authorization(
                BASE_URL,
                client_access_token,
                user_id=USER_ID,
                id_hint='hackathon_user',
                scope='authorization:grant,authorization:read,credentials:read,credentials:refresh,credentials:write,providers:read,user:read,provider-consents:read'
            )
            print(url)
            sys.exit('NEEDS REAUTHENTICATION')
    print('UPDATED!')

if account: # only this part is strictly necessary for external adapter 

    access_token = create_bearer_token(
        BASE_URL, 
        client_id=TINK_CLIENT_ID,
        client_secret=TINK_CLIENT_SECRET,
        grant_type='client_credentials',
        scope='authorization:grant'
    )

    authorization_code = create_authorization(
        BASE_URL,
        access_token,
        user_id=USER_ID,
        scope='accounts:read,balances:read,transactions:read,provider-consents:read'
    )

    user_access_token = create_bearer_token( # this should ideally return the whole json object
        BASE_URL,
        code=authorization_code,
        client_id=TINK_CLIENT_ID,
        client_secret=TINK_CLIENT_SECRET,
        grant_type='authorization_code'
    )

def return_balance(url='https://api.tink.com/data/v2/', req='list'):
    if req == 'list':
        account = list_accounts(url, user_access_token).json()["accounts"] # last account
        account = account[-1]
        value = json_parse(account, path=['balances', 'booked', 'amount', 'value'])
        scaled_value = int(value["unscaledValue"]) / (10 ** int(value["scale"]))
    else:
        scaled_value = None
    return scaled_value

value = return_balance()
print(value)