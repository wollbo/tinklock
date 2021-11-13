from bridge import Bridge
from tink import *

class Adapter:
    base_url = 'https://api.tink.com/'
    params = ['ping', 'user', 'access', 'refresh', 'account'] # valid calls
    return_params = ['']

    def __init__(self, input):
        self.id = input.get('id', '1')
        self.request_data = input.get('data')
        if self.validate_request_data():
            self.bridge = Bridge()
            self.set_params()
            self.make_tink_request()
            #self.set_headers()
            #self.create_request()
        else:
            self.result_error('No data provided')

    def validate_request_data(self):
        if self.request_data is None:
            return False
        if self.request_data == {}:
            return False
        return True

    def set_param(self):
        for param in self.params:
            self.provided_param = self.request_data.get(param)
            if self.provided_param is not None:
                break

    def set_headers(bearer_token, ):
        return None 

    def create_request(self, method='get'): # atomic unit, use several times per job
        try:
            params = self.provided_param
            headers = self.headers
            response = self.bridge.request(self.url, method, params, headers)
            data = response.json()
            self.result = data[self.to_param]
            data['result'] = self.result
            self.result_success(data)
        except Exception as e:
            self.result_error(e)
        finally:
            self.bridge.close()

    def make_tink_request(self):
        """Master function for all tink requests"""
        # consider using text/functionality directly from param string
        if self.provided_param == 'ping':
            self.ping_request()  
        elif self.provided_param == 'user':
            pass
        elif self.provided_param == 'access':
            pass
        elif self.provided_param == 'refresh':
            pass
        elif self.provided_param == 'account':
            pass
        else:
            raise(Exception)
    

    def ping_request(self):
        self.url = self.base_url + '/api/v1/monitoring/ping'
        self.provided_param = {}
        self.headers = {'Content-Type': 'application/x-www-form-urlencoded'}  
        self.create_request()

    
    def user_request(self):
        return None
        

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
