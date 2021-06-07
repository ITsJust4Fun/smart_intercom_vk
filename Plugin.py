import requests


class Plugin:
    def __init__(self, name, address):
        self.address = address
        response = requests.get(address + 'auth',
                                json={'name': name, 'request_type': 'message'})

        if response.status_code != 200:
            return

        response_json = response.json()

        if 'jwt' in response_json:
            self.jwt = 'Bearer ' + response_json['jwt']

    def getEvent(self):
        response = requests.get(self.address + 'get_event',
                                headers={'Authorization': self.jwt})

        if response.status_code != 200:
            return "error " + str(response.status_code)

        response_json = response.json()

        if 'message' in response_json:
            print(response_json['message'])
            return response_json['message']

        return ""
