from bridge import Bridge
import tink
import sys

class Adapter:
    base_url = 'https://api.tink.com/' # add api/ to all tink function urls
    #NOTE: 'access' is not needed in adapter, this should be created beforehand
    #and the 'credentialsId' should be passed to the bridge operators .env
    #TODO: investigate how passing function as parameter affects flow
    #currently we get oauth.no_auth_method_provided
    """
    To test ping request, run the following in bash: curl -v POST http://192.168.1.162:8080/ 
    -H "Content-Type: application/json" -d '{"id": 0, "data": {"request": "ping"}}'
    """
    
    to_params = ['request']  # valid calls ['ping', 'balance']
    re_params = [''] # how does this work, really? implement properly

    def __init__(self, input):
        self.id = input.get('id', '1')
        self.request_data = input.get('data')
        self.unpack_env() # sets environment variables, works
        if self.validate_request_data():
            self.bridge = Bridge()
            self.set_param()
            self.make_tink_request()
        else:
            self.result_error('No data provided')

    
    def unpack_env(self):
        _env = tink.load_tinkenv()
        for key, value in _env.items():
            setattr(self, key, value)


    def validate_request_data(self):
        if self.request_data is None:
            return False
        if self.request_data == {}:
            return False
        return True


    def set_param(self):
        for param in self.to_params:
            self.params = self.request_data.get(param)
            if self.params is not None:
                break


    def create_request(self, method='get'): # atomic unit, use several times
        try: # if method is post, params should be a json
            params = self.params
            headers = self.headers
            response = self.bridge.request(self.url, method, params, headers)
            if response.status_code == 204:
                data = response
                self.result = response.status_code
                self.result_success(data)
            else:
                data = response.json()
                self.result = data[self.re_param]
                self.result_success(data)
        except Exception as e:
            print(response.text)
            self.result_error(e)
        finally:
            self.bridge.close()


    def wrap_request(self, func, _re_param, *args, method='get', **kwargs):
        """
        Wrapper function for containing logic in the process of creating url,
        headers and parameters of a request, sending the request to the bridge,
        interpreting the response and returning the result for the next step.
        """
        self.result = {} # consider resetting here, could turn ugly otherwise
        self.url, self.headers, self.params = func(*args, **kwargs)
        self.re_param = _re_param
        self.create_request(method=method)

        try:
            return self.result["result"]
        except Exception as e:
            print(self.result["error"])
            raise e


    def ping_request(self):
        """Simple ping request for verifying tink server and bridge function"""
        self.url = self.base_url + 'api/v1/monitoring/ping'
        self.re_param = 'ping'
        try: # if method is post, params should be a json
            params = {}
            method = 'get'
            headers = {'Content-Type': 'application/x-www-form-urlencoded'} 
            response = self.bridge.request(self.url, method, params, headers)
            data = {"ping": response.text}
            self.result = data[self.re_param] # self.re_param
            self.result_success(data)
        except Exception as e:
            print(response.text)
            self.result_error(e)
        finally:
            self.bridge.close()


    def refresh_request(self):
        """
        Refreshes the credentialsId to guarantee updated account balance
        Creates client access token granting the client the authority to
        create authorization code of a specific user with a certain scope.
        This code is used to generate a user access token which grants the
        authorization to access the scopes defined within, ex. refreshing
        credentials and reading provider consents.
        """
        client_access_token = self.wrap_request(
                                tink.create_bearer_token,
                                "access_token",
                                self.base_url,
                                method='post',
                                client_id=self.TINK_CLIENT_ID,
                                client_secret=self.TINK_CLIENT_SECRET,
                                grant_type='client_credentials',
                                scope='authorization:grant'
                            )

        authorization_code = self.wrap_request(
                                tink.create_authorization,
                                "code",
                                self.base_url,
                                client_access_token,
                                method='post',
                                user_id=self.USER_ID,
                                scope='authorization:grant,authorization:read,credentials:read,credentials:refresh,credentials:write,providers:read,user:read,provider-consents:read'
                            )

        user_access_token = self.wrap_request(
                                tink.create_bearer_token,
                                "access_token",
                                self.base_url,
                                method='post',
                                code=authorization_code,
                                client_id=self.TINK_CLIENT_ID,
                                client_secret=self.TINK_CLIENT_SECRET,
                                grant_type='authorization_code'
                            )

        status_code = self.wrap_request(
                        tink.refresh_credentials,
                        "status_code",
                        self.base_url,
                        user_access_token,
                        self.CREDENTIALS_ID,
                        method='post',
                    )

        assert(status_code == 204, 'Wrong status code!')
        
        status = ''
        while status != 'UPDATED':
            client_access_token = self.wrap_request(
                                    tink.create_bearer_token,
                                    "access_token",
                                    self.base_url,
                                    method='post',
                                    client_id=self.TINK_CLIENT_ID,
                                    client_secret=self.TINK_CLIENT_SECRET,
                                    grant_type='client_credentials',
                                    scope='authorization:grant'
                                )

            authorization_code = self.wrap_request(
                                    tink.create_authorization,
                                    "code",
                                    self.base_url,
                                    client_access_token,
                                    method='post',
                                    user_id=self.USER_ID,
                                    id_hint='hackathon_user',
                                    scope='authorization:grant,authorization:read,credentials:read,credentials:refresh,credentials:write,providers:read,user:read,provider-consents:read'
                                )
        
            user_access_token = self.wrap_request(
                                    tink.create_bearer_token,
                                    "access_token",
                                    self.base_url,
                                    method='post',
                                    code=authorization_code,
                                    client_id=self.TINK_CLIENT_ID,
                                    client_secret=self.TINK_CLIENT_SECRET,
                                    grant_type='authorization_code'
                                )
            
            consents = self.wrap_request(
                            tink.get_consents,
                            "providerConsents",
                            self.base_url,
                            user_access_token,
                            method='get'
                        )
            status = [cons["status"] for cons in consents if cons["credentialsId"] == self.CREDENTIALS_ID][0]

    
    def balance_request(self):
        """
        Called to check account balance after credentials are refreshed.
        Sets the bank information data json to data, result is the scaled value
        """
        client_access_token = self.wrap_request(
                                tink.create_bearer_token,
                                "access_token",
                                self.base_url,
                                method='post',
                                client_id=self.TINK_CLIENT_ID,
                                client_secret=self.TINK_CLIENT_SECRET,
                                grant_type='client_credentials',
                                scope='authorization:grant'
                            )

        authorization_code = self.wrap_request(
                                tink.create_authorization,
                                "code",
                                self.base_url,
                                client_access_token,
                                method='post',
                                user_id=self.USER_ID,
                                scope='accounts:read,balances:read,transactions:read,provider-consents:read'
                            )
    
        user_access_token = self.wrap_request(
                                tink.create_bearer_token,
                                "access_token",
                                self.base_url,
                                method='post',
                                code=authorization_code,
                                client_id=self.TINK_CLIENT_ID,
                                client_secret=self.TINK_CLIENT_SECRET,
                                grant_type='authorization_code'
                            )
        
        account = self.wrap_request( # account is a list
                                tink.list_accounts,
                                "accounts",
                                self.base_url,
                                user_access_token,
                                method='get'
                            )
        if self.IBAN:
            data = [acc for acc in account if tink.json_parse(acc, ['identifiers', 'iban', 'iban']) == self.IBAN][0]
        else:
            data = account[-1]

        value = tink.json_parse(data, ['balances', 'booked', 'amount', 'value'])
        self.result = int(value["unscaledValue"]) / (10 ** int(value["scale"]))
        data["result"] = self.result

        try:
            self.result_success(data)
        except Exception as e:
            self.result_error(e)
        finally:
            self.bridge.close()


    def make_tink_request(self):
        """Master function for all tink requests"""
        # consider using text/functionality directly from param string
        if self.params == 'ping':
            self.ping_request()  
        elif self.params == 'balance':
            self.refresh_request() # credentials must always be updated first
            self.balance_request()
        else:
            raise(Exception)
        

    def result_success(self, data):
        self.result = {
            'jobRunID': self.id,
            'data': data,
            'result': self.result,
            'statusCode': 200,
        }


    def result_error(self, error):
        self.result = {
            'jobRunID': self.id,
            'status': 'errored',
            'error': f'There was an error: {error}',
            'statusCode': 500,
        }
