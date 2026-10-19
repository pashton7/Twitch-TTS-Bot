import asyncio
import time
import twitchio
from twitchio.ext import commands
import obswebsocket
from obswebsocket import obsws, requests


import os
import threading
import random

from dotenv import load_dotenv
from TTS import AzureTTSManager

from AudioPlayer import AudioManager

load_dotenv("bot.env")

BOT_TOKEN = os.getenv("TWITCH_TOKEN")
OBS_WEBHOOK = os.getenv("OBS_WEBHOOK")
CHANNEL_NAME = os.getenv("CHANNEL_NAME")


images = [
    "Cortex.png",
    "Crash.png"
]

client = obsws("localhost", 4455, OBS_WEBHOOK)

client.connect()
print("Connected to OBS")

chatMsgsGroup = requests.GetSceneItemId(
    sceneName = "Game", sourceName = "ChatMsgs"
)
chatMsgs_id = client.call(chatMsgsGroup).getSceneItemId()

ttsQueue = {}

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=BOT_TOKEN,
            prefix="?",
            initial_channels=[CHANNEL_NAME]
        )
        self.azureTTS = AzureTTSManager()
        self.audioSystem = AudioManager()
        self.processingTTS = False

    async def event_ready(self):
        print(f"Logged in as | {self.nick}")

    async def close(self):
        print("Disconnecting Bot")
        return await super().close()

    def random_img(self):
        '''Chooses a random image in the /Images file to represent the TTS character'''
        image = random.choice(images)
        print(os.path.dirname(os.path.abspath(__file__)) + "\\Images\\" + image)
        client.call(requests.SetInputSettings(
                    inputName="Image",
                    inputSettings={
                        "file": os.path.dirname(os.path.abspath(__file__)) + "\\Images\\" + image
                    },
                ))

    def ttsSpeak(self, author, message):
        
        msg = message[:200] # Cap the message length to 200 characters

        ## Following lines are for the OBS webhook
        client.call(requests.SetSourceFilterEnabled(
            sourceName="BotVoices",
            filterName="TTS_move",
            filterEnabled=True
        ))

        self.random_img()

        client.call(requests.SetSceneItemEnabled(
            sceneName = "Game",
            sceneItemId = chatMsgs_id,
            sceneItemEnabled = True
        ))

        client.call(requests.SetInputSettings(
            inputName="chatMessage",
            inputSettings={
                "text": msg
            },
            overlay=True
        ))

        print(f"Speak message: {msg}")

        client.call(requests.SetInputSettings(
                    inputName="chatAuthor",
                    inputSettings={
                        "text": author
                    },
                    overlay=True
                ))

        self.audioSystem.play_audio(self.azureTTS.text_to_audio(msg, "random"),True,True,True) # Plays the TTS message
        
        time.sleep(5) ## Waits to hide the OBS items
        
        client.call(requests.SetSceneItemEnabled(
                    sceneName = "Game",
                    sceneItemId = chatMsgs_id,
                    sceneItemEnabled = False
                ))

        client.call(requests.SetSourceFilterEnabled(
                    sourceName="BotVoices",
                    filterName="TTS_move",
                    filterEnabled=False
                ))

        self.processingTTS = False # Next TTS message can now be played
       
    async def event_message(self, message):

        if message.echo:
            return

        if message.content.startswith("!tts") : 
                print("Added tts message to queue")
                
                ttsQueue[message.author.name] = {"message": message.content.removeprefix("!tts").strip()}
       
        
        print(f"{message.author.name}: {message.content}")

        await self.handle_commands(message)

        


def startTwitchBot():
    global twitchbot
    asyncio.set_event_loop(asyncio.new_event_loop()) # Create and set the event loop for this thread
    twitchbot = Bot()
    twitchbot.run() # Kicks off the Twitchio connection

if __name__ == '__main__':

    chat_bot_thread = threading.Thread(target=startTwitchBot)
    chat_bot_thread.start()

    while True:
        time.sleep(0.5)
        #twitchbot.random_img()
        if twitchbot.processingTTS == False: # Check for queued messages and play them
            try:
                queue_key = next(iter(ttsQueue))
                twitchbot.processingTTS = True
                print(ttsQueue.get(queue_key).get('message'))
                twitchbot.ttsSpeak(queue_key, ttsQueue.get(queue_key).get('message'))
                ttsQueue.pop(queue_key)
            except:
                print("Queue empty")