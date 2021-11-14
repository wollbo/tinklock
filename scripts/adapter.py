from bridge import Bridge
import tink

class Adapter:
    base_url = 'https://api.tink.com/'
    #NOTE: 'access' is not needed in adapter, this should be created beforehand
    #and the 'credentialsId' should be passed to the bridge operators .env
    to_params = ['ping', 'balance'] # valid calls
    re_params = ['']

    def __init__(self, input):
        self.id = input.get('id', '1')
        self.request_data = input.get('data')
        self.unpack_env() # sets environment variables
        if self.validate_request_data():
            self.bridge = Bridge()
            self.set_params()
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


    def create_request(self, method='get'): # atomic unit, use several times per job
        try: # if method is post, params should be a json
            params = self.params
            headers = self.headers
            response = self.bridge.request(self.url, method, params, headers)
            data = response.json()
            self.result = data[self.re_param]
            data['result'] = self.result
            self.result_success(data)
        except Exception as e:
            self.result_error(e)
        finally:
            self.bridge.close()


    def wrap_request(self, func, _re_param, *args, **kwargs):
        """
        Wrapper function for containing logic in the process of creating url,
        headers and parameters of a request, sending the request to the bridge,
        interpreting the response and returning the result for the next step.
        """
        self.url, self.params, self.headers = func(*args, **kwargs)
        self.re_param = _re_param
        self.create_request()
        return self.result["result"]


    def ping_request(self):
        """Simple ping request for verifying tink server and bridge function"""
        self.url = self.base_url + '/api/v1/monitoring/ping'
        self.provided_param = {}
        self.headers = {'Content-Type': 'application/x-www-form-urlencoded'}  
        self.create_request()


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
                                user_id=self.USER_ID,
                                scope='authorization:grant,authorization:read,credentials:read,credentials:refresh,credentials:write,providers:read,user:read,provider-consents:read'
                            )
        
        user_access_token = self.wrap_request(
                                tink.create_bearer_token,
                                "code",
                                self.base_url,
                                code=authorization_code,
                                client_id=self.TINK_CLIENT_ID,
                                client_secret=self.TINK_CLIENT_SECRET,
                                grant_type='authorization_code'
                            )
        #refresh_credentials
        #while status != UPDATED, repeat...
        #see tink_test
        return None

    
    def balance_request():
        return None


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
