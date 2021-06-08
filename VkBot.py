from vk_api import VkApi
from vk_api import upload
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

import time
from pymongo import MongoClient

API_VERSION = '5.131'


class VkBot:
    def __init__(self, group_id, group_token, client_token, mongo, mongo_port):
        self.group_id = group_id
        self.group_token = group_token
        self.client_token = client_token

        self.vk_session = VkApi(token=group_token, api_version=API_VERSION)
        self.vk_session_client = VkApi(token=client_token, api_version=API_VERSION)
        self.vk = self.vk_session.get_api()
        self.longPoll = VkBotLongPoll(self.vk_session, group_id=group_id, wait=10)

        settings = dict(one_time=False, inline=True)

        keyboard_call = VkKeyboard(**settings)
        keyboard_call.add_callback_button(label='Ответить',
                                          color=VkKeyboardColor.POSITIVE,
                                          payload={'type': 'answer'})

        keyboard_call.add_callback_button(label='Отклонить',
                                          color=VkKeyboardColor.NEGATIVE,
                                          payload={'type': 'reject'})

        keyboard_answer = VkKeyboard(**settings)
        keyboard_answer.add_callback_button('Открыть',
                                            color=VkKeyboardColor.POSITIVE,
                                            payload={"type": "open"})

        keyboard_answer.add_callback_button('Отклонить',
                                            color=VkKeyboardColor.NEGATIVE,
                                            payload={"type": "close"})

        self.keyboard_call = keyboard_call
        self.keyboard_answer = keyboard_answer

        client = MongoClient(mongo, mongo_port)
        db = client['smart_intercom_vk']
        self.collection_users = db['users']

    def getAllUsers(self):
        results = self.collection_users.find()
        result = [r for r in results]

        if not result:
            return []
        return result

    def findUser(self, peer_id):
        return self.collection_users.find_one({'peer_id': peer_id})

    def insertUser(self, peer_id):
        return self.collection_users.insert_one({'peer_id': peer_id}).inserted_id

    def listen(self, duration):
        start_time = time.time()

        while time.time() - start_time < duration:
            event_array = self.longPoll.check()

            for event in event_array:
                yield event

            if not len(event_array):
                yield []

        return []

    def editMessageWithVideoText(self, peer_id, conversation_message_id, text):
        messages = self.vk.messages.getByConversationMessageId(
            peer_id=peer_id,
            conversation_message_ids=conversation_message_id
        )

        if messages['count'] == 1:
            message = messages['items'][0]

            video = message['attachments'][0]['video']

            video_string = 'video' + str(video['owner_id']) + '_' \
                           + str(video['id']) + '_' \
                           + video['access_key']

            self.vk.messages.edit(
                peer_id=message['peer_id'],
                message=text,
                conversation_message_id=conversation_message_id,
                attachment=video_string
            )
        else:
            self.vk.messages.edit(
                peer_id=peer_id,
                message='Открыто!',
                conversation_message_id=conversation_message_id,
            )

    def sendMessage(self, peer_id, text):
        self.vk.messages.send(
            user_id=peer_id,
            random_id=get_random_id(),
            peer_id=peer_id,
            message=text
        )

    def registerUser(self, event):
        if 'callback' not in event.obj.client_info['button_actions']:
            print(f'Клиент {event.obj.message["from_id"]} не поддерж. callback')

        result = self.findUser(event.obj.message['from_id'])

        if not result:
            self.insertUser(event.obj.message['from_id'])
            self.sendMessage(event.obj.message['from_id'], 'Зарегистрирован!')
        else:
            self.sendMessage(event.obj.message['from_id'], 'Уже зарегистрирован!')

    def incomingCall(self):
        users = self.getAllUsers()

        for user in users:
            self.vk.messages.send(
                user_id=user['peer_id'],
                random_id=get_random_id(),
                peer_id=user['peer_id'],
                keyboard=self.keyboard_call.get_keyboard(),
                message='Входящий вызов'
            )

    def sendVideo(self, peer_id, conversation_message_id, video_path):
        vk_upload = upload.VkUpload(self.vk_session_client)
        video = vk_upload.video(video_file=video_path,
                                name='output',
                                description='description',
                                is_private=True,
                                group_id=int(self.group_id),
                                no_comments=True)

        video_string = 'video' + str(video['owner_id']) + '_' \
                       + str(video['video_id']) + '_' \
                       + video['access_key']

        self.vk.messages.edit(
            peer_id=peer_id,
            conversation_message_id=conversation_message_id,
            keyboard=self.keyboard_answer.get_keyboard(),
            attachment=video_string
        )

    def processRegistration(self, duration):
        for event in self.listen(duration):
            if isinstance(event, list):
                continue
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.obj.message['text'] != '' and event.from_user:
                    self.registerUser(event)
                    break

    def processAnswer(self, duration, video):
        for event in self.listen(duration):
            if isinstance(event, list):
                continue
            elif event.type == VkBotEventType.MESSAGE_EVENT:
                if event.object.payload.get('type') == 'answer':
                    self.sendVideo(event.obj.peer_id,
                                   event.obj.conversation_message_id,
                                   video)
                    return event.obj.peer_id
                elif event.object.payload.get('type') == 'reject':
                    self.vk.messages.edit(
                        peer_id=event.obj.peer_id,
                        message='Отклонено',
                        conversation_message_id=event.obj.conversation_message_id,
                    )
                    return 0
        return 0

    def processOpen(self, duration, peer_id):
        for event in self.listen(duration):
            if isinstance(event, list):
                continue
            elif event.type == VkBotEventType.MESSAGE_EVENT and event.obj.peer_id == peer_id:
                if event.object.payload.get('type') == 'open':
                    self.editMessageWithVideoText(event.obj.peer_id,
                                                  event.obj.conversation_message_id,
                                                  'Открыто!')
                    return True

                elif event.object.payload.get('type') == 'close':
                    self.editMessageWithVideoText(event.obj.peer_id,
                                                  event.obj.conversation_message_id,
                                                  'Отклонено!')
                    return False
        return False
