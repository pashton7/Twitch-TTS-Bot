# Twitch TTS Bot
A chat bot that turns a user message into a TTS message

# Description
A Twitch Bot that watches chat for a !tts {message} command and adds the message into a queue to be read by Azure or Google Text-To-Speech. Additionaly the bot connects to OBS Websocket to add a visual character and readable version of the message on screen.

# Requirements
- Twitch bot Auth token
- OBS websocket (only if using to show TTS messages)
- Azure API key for TTS (will use default Google TTS if there is no key)
- Channel Name (the name of the Twitch channel it will monitor)
