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
            return response_json['message']

        return ""

    def answer(self):
        response = requests.get(self.address + 'answer',
                                headers={'Authorization': self.jwt})

        if response.status_code != 200:
            return "error " + str(response.status_code)

        response_json = response.json()

        if 'message' in response_json and 'link' in response_json:
            return response_json

        return {}

    def cancel(self):
        response = requests.get(self.address + 'cancel',
                                headers={'Authorization': self.jwt})

        if response.status_code != 200:
            return {}

        response_json = response.json()

        if 'message' in response_json:
            return response_json['message']

        return ""

    def open(self):
        response = requests.get(self.address + 'open',
                                headers={'Authorization': self.jwt})

        if response.status_code != 200:
            return "error " + str(response.status_code)

        response_json = response.json()

        if 'message' in response_json:
            return response_json['message']

        return ""

    def reject(self):
        response = requests.get(self.address + 'reject',
                                headers={'Authorization': self.jwt})

        if response.status_code != 200:
            return "error " + str(response.status_code)

        response_json = response.json()

        if 'message' in response_json:
            return response_json['message']

        return ""

    def listenEvents(self):
        while True:
            yield self.getEvent()