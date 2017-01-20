# Anima-Chan
Discord bot for anime airtime schedule/reminder.

## Dependencies
This bot should only work with python3.5 or higher.

`pip install -r requirements.txt`

## Setup
First make a file called `auth.json` which should be like
```
{
	"discord_token": "",
	"anilist_client_id": "",
	"anilist_client_secret": ""
}
```

Next you'll need to get these tokens from (need accounts, if you don't have one already):

`discord_token`  https://discordapp.com/developers/docs/intro

`anilist_client_id` and `anilist_client_secret`  https://anilist.co/settings/developer


Next, make other file called `config.json` which should be like
```
{
	"discord_channel_id": "",
	"command_prefix": ""
}
```
The first is the channel ID where the bot will announce the airtimes.

The second is your preferred command prefix.


##Commands


**agenda add** - Adds a anime to the agenda. Use Anilist.co url. 	`!!addanime anilist.co/anime/<..>/<..>`

**agenda see** - See which shows are in the agenda

**agenda remove** - Removes entry from the agenda




##To-do

* Need exceptions
* Better logging
