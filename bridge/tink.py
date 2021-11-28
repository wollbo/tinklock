from dotenv import load_dotenv
import requests
import json
import os


def empty_to_none(field):
    value = os.getenv(field)
    if value is None or len(value) == 0:
        return None
    return value


def load_tinkenv():
    load_dotenv()
    _env = [
        'TINK_CLIENT_ID',
        'TINK_CLIENT_SECRET', 
        'ACTOR_CLIENT_ID',
        'USER_ID',
        'CREDENTIALS_ID',
        'IBAN'
        ]
    return {e: empty_to_none(e) for e in _env}


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
    url = base_url + 'api/v1/oauth/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {key: value for key, value in kwargs.items()}
    return url, headers, data


def create_tink_user(base_url, bearer_token, **kwargs):
    url = base_url + 'api/v1/user/create'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/json; charset=utf-8' 
    }
    data = {key: value for key, value in kwargs.items()}
    return url, headers, data


def create_authorization(base_url, bearer_token, **kwargs):
    url = base_url + 'api/v1/oauth/authorization-grant'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {key: value for key, value in kwargs.items()}
    return url, headers, data


def create_delegated_authorization(base_url, bearer_token, **kwargs):
    """Authorizes Tink Link to connect user account, code identifies user"""
    url = base_url + 'oauth/authorization-grant/delegate'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {key: value for key, value in kwargs.items()}
    return url, headers, data


def refresh_credentials(base_url, bearer_token, credentials_id):
    """Prepares request for automated credentials refresh"""
    url = base_url + f'api/v1/credentials/{credentials_id}/refresh'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/json; charset=utf-8'
    }
    return url, headers, {}


### TINK LINK USER INTERACTION FUNCTIONS ###

def create_credentials_link(client_id, auth_code):
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


def refresh_credentials_link(client_id, auth_code, credentials_id):
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


def update_consent_link(client_id, auth_code, credentials_id):
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


def authenticate_credentials_link(client_id, auth_code, credentials_id):
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
    url = base_url + 'api/v1/provider-consents'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/json; charset=utf-8'
    }
    return url, headers, {}


def list_accounts(base_url, bearer_token):
    url = base_url + 'data/v2/accounts'
    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Content-Type': 'application/json; charset=utf-8' 
    }
    return url, headers, {}


