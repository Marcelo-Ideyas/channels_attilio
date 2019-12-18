import asyncio
import json
from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async

from .models import Thread, ChatMessage

class ChatConsumer(AsyncConsumer):

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.keepalive = False

    async def websocket_connect(self, event):
        print("connected", event)
        # Após min 23
        # função que fará o servidor enviar um response para o websocket
        # enviando um dicionario com o type e utilizando o await para executar o codigo
        # até ser finalizado

        ### A função comentada foi para baixo criar todo o Data antes de conectar o socket
        # await self.send({
        #     "type":"websocket.accept"
        # })
        other_user = self.scope['url_route']['kwargs']['username']
        me = self.scope['user']
        print(other_user, me)
        # é necessário utilizar await aqui, pois get_thread é uma função de sync que vira async
        thread_obj = await self.get_thread(me, other_user)
        print(me, thread_obj.id)
        self.thread_obj = thread_obj ## Criação da thread_obj para ser utilizado no create
        chat_room = f"thread_{thread_obj.id}" # Chat room name
        self.chat_room = chat_room
        await self.channel_layer.group_add(
            chat_room,
            self.channel_name, # basic atribute for channel_layer
        )
        await self.send({
            "type":"websocket.accept"
        })

        # await asyncio.sleep(10)
        
        # await self.send({
        #     # "type":"websocket.close"
        #     "type":"websocket.send",
        #     "text":"ekidumiki"
        # })
        

    async def websocket_receive(self, event):
        print("receive", event)
        # {'type': 'websocket.receive', 'text': '{"message":"Dic"}'}
        front_text = event.get('text', None)
        if front_text is not None:
            loaded_dict_data = json.loads(front_text)
            msg = loaded_dict_data.get('message')
            print(msg)
            user = self.scope['user']
            username = 'default'
            if user.is_authenticated:
                username = user.username
            myResponse = {
                # 'message': "This is a instance message",
                'message': msg,
                'username': username
            }
            await self.create_chat_message(user, msg)

            ### Comentado, pois a partir de 1:03 não é mais necessário um new_event
            # new_event = {
            #     "type": "websocket.send",
            #     "text": json.dumps(myResponse)
            # }

            ### Por conta da mensagem nao ter chegado para o outro usuario, sera necessario utilizar um metodo diferente 1:00
            
            ## broadcasts the message event to be sent
            await self.channel_layer.group_send(
                self.chat_room,
                # dict_key(dict_key[key])
                {
                    'type': 'chat_message',
                    'message': json.dumps(myResponse)
                }
                # new_event
            )
            # enviando a mensagem de volta pro front
            # await self.send({ # Comentado após inserir o Redis para o chat
            #     # "type":"websocket.close"
            #     "type":"websocket.send",
            #     # "text":msg # Para enviar uma msg comum
            #     "text": json.dumps(myResponse) # Envia o dicionario myResponse
            # })

    async def chat_message(self, event):
        print('BEFORE')
        print("message", event)
        # send the actual message
        await self.send({
            "type": "websocket.send",
            "text": event['message']
        })

    async def websocket_disconnect(self, event):
        print("disconnect", event)
        

    # Sync method
    # importante utilizar, verificar melhor o motivo
    @database_sync_to_async
    def get_thread(self, user, other_username):
        return Thread.objects.get_or_new(user, other_username)[0]

    # me is the sender, msg is the msg
    @database_sync_to_async
    def create_chat_message(self, me, msg):
        thread_obj = self.thread_obj
        print('Salvando')
        return ChatMessage.objects.create(
                                    ### Para utilizar a thread_obj foi necessário acrescentar ao self thread.obj na linha 18
                                    thread=thread_obj,
                                    user=me,
                                    message=msg
                                )
        print('Salvou')
