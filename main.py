from VkBot import VkBot
from Plugin import Plugin
from pymongo import MongoClient

MONGO_URL = '192.168.3.14'
MONGO_PORT = 27017

client = MongoClient(MONGO_URL, MONGO_PORT)
db = client['smart_intercom_vk']
collection_settings = db['settings']


def insert_document(collection, data):
    return collection.insert_one(data).inserted_id


def find_document(collection, elements):
    return collection.find_one(elements)


if __name__ == '__main__':
    results = collection_settings.find()
    result = [r for r in results]

    settings = {}

    if not len(result):
        collection_settings.insert_one({'group_id': '',
                                        'group_token': '',
                                        'client_token': '',
                                        'is_registration_mode': False})
    else:
        settings = result[0]

    if (not len(settings)
            or settings['group_id'] == ''
            or settings['group_token'] == ''
            or settings['client_token'] == ''):
        print('Specify settings!')
    else:
        bot = VkBot(settings['group_id'], settings['group_token'], settings['client_token'], MONGO_URL, MONGO_PORT)

        if settings['is_registration_mode']:
            bot.processRegistration(50)
        else:
            plugin = Plugin('vk_bot', 'http://localhost:8080/plugin/')
            for event in plugin.listenEvents():
                if 'message' in event:
                    if event['message'] == 'incoming':
                        bot.incomingCall()
                        peer_id = bot.processAnswer(60, 'C:/Users/Artyom/Downloads/output.mp4')
                        if peer_id != 0:
                            plugin.answer()
                            isOpen = bot.processOpen(60, peer_id)
                            if isOpen:
                                plugin.open()
                            else:
                                plugin.reject()
                        else:
                            plugin.cancel()
