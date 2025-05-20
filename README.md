# Discord Bot for WoW Community

![Bot Status](https://img.shields.io/badge/status-active-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Discord.py Version](https://img.shields.io/badge/discord.py-2.3.0%2B-orange)

A feature-rich Discord bot designed for World of Warcraft communities with moderation, utility, and fun commands.

## Features

### WoW-Related Commands
- `/solemnity` - Show guild progression and raid rankings
- `/logs [character]` - Check Warcraft Logs statistics
- `/weekly [character]` - Show Mythic+ runs completed this week

### Moderation Tools
- `/muteall` - Mute all users in voice channel
- `/unmuteall` - Unmute all users in voice channel

### Fun Commands
- `fortune` - Displays a random fortune prediction
- `/compliment [user]` - Sends a random compliment to the specified user
- `/hype [level]` - Shows your excitement level with a visual meter
- `/8ball [question]` - Classic magic 8-ball that answers your yes/no questions

### Server Analytics
- `/yapping` - Show server message activity level
- `/yapping_user [user]` - Check user's message count

### Automation
- Random reactions to messages
- MP4 file forwarding to specific channel
- Telegram notifications from designated channel
- Automated responses when mentioned

## Install dependencies
`pip install -r requirements.txt`

## Set up configuration
- `TOKEN = "your_discord_bot_token"`
- `TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"`
- `TELEGRAM_CHAT_ID = "your_telegram_chat_id"`
- `WCL_API_KEY = "your_warcraft_logs_api_key"`

Create responses.txt with bot response phrases (one per line)

## Run the bot
`python main.py`

## Requirements
- Python 3.8+
- discord.py 2.3.0+
- requests library
- Warcraft Logs API key (for logs feature)

## File Structure
discord-bot/  
├── cogs/  
│   ├── fun.py  
│   ├── moderation.py  
│   ├── wow.py  
│   └── yapping.py  
├── config.py  
├── main.py  
├── responses.txt  
└── requirements.txt
