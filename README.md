# Anima-Chan
Discord bot for anime airtime schedule/remainder.

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

##Commands

Command prefix is '!!' (you can change this)

**addanime** - Adds a anime to the agenda. Use Anilist.co url 	`!!addanime anilist.co/anime/<..>/<..>`

**seeagenda** - See which shows are in the agenda

**removeanime** - Removes entry from the agenda




##To-do

* Need exceptions, lot's of 'em
* ?
