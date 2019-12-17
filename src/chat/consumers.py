import asyncio
import json
from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async

from .models import Thread, ChatMessage

class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print("connected", event)
        # Após min 23
        # função que fará o servidor enviar um response para o websocket
        # enviando um dicionario com o type e utilizando o await para executar o codigo
        # até ser finalizado
        await self.send({
            "type":"websocket.accept"
        })
        other_user = self.scope['url_route']['kwargs']['username']
        me = self.scope['user']
        print(other_user, me)
        # é necessário utilizar await aqui, pois get_thread é uma função de sync que vira async
        thread_obj = await self.get_thread(me, other_user)
        print(thread_obj)
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
                'message': msg,
                'username': username
            }
            # enviando a mensagem de volta pro front
            await self.send({
                # "type":"websocket.close"
                "type":"websocket.send",
                # "text":msg # Para enviar uma msg comum
                "text": json.dumps(myResponse) # Envia o dicionario myResponse
            })
    async def websocket_disconnect(self, event):
        print("disconnect", event)

    # Sync method
    # importante utilizar, verificar melhor o motivo
    @database_sync_to_async
    def get_thread(self, user, other_username):
        return Thread.objects.get_or_new(user, other_username)[0]