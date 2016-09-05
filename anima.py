import logging
import sys
import time
import requests
import discord
import asyncio
import json
import os
import os.path
from datetime import datetime
from discord.ext import commands
from pprint import pprint
from urllib.parse import urlparse

#basic logging config,simple consele view
logging.basicConfig(level=logging.INFO)

AGENDA = "agenda"

#creates file if doesn't exist
if not os.path.isfile(AGENDA):
	f = open(AGENDA,"x")
	f.close()
	
#Discord TKN here
discord_tkn = ''
	
	
#Anilist user credentials here
client_id = ''
client_secret = ''
	
description = 'AnimeAirTime'

#header data for anilist auth
auth_data = {'grant_type': 'client_credentials', 'client_id' : client_id , 'client_secret' : client_secret }

CMDPREFIX = '!!'

bot = commands.Bot(command_prefix=CMDPREFIX, description=description)


def alist_tkn():
	''' Auth Anilist API - returns access_token str '''
	client_auth = requests.post('https://anilist.co/api/auth/access_token',data=auth_data)
	json_res = json.loads(bytes.decode(client_auth.content))
	return json_res['access_token']

token = alist_tkn()

agendalist = []

def create_slot_fromid(id):
	r = requests.get('https://anilist.co/api/anime/'+id+'?access_token='+token)
	c = json.loads(bytes.decode(r.content))
	id = c['id']
	nromaji = c['title_romaji']
	nextep = c['airing']['next_episode']
	countdown = c['airing']['countdown']
	
	t = int(time.time())+countdown
	a = AnimeSlot(id,nromaji,t,nextep)
	return a

class AnimeSlot:
	def __init__(self, id, name, airtime, nextep):
		self.id = id
		self.name = name
		self.airtime = airtime
		self.nextep = nextep


async def agendaloop():
	await bot.wait_until_ready()
	channel = discord.Object(id='169834335321587712')
	
	while not bot.is_closed: #things to be looped go here
		if not agendalist == []:
			for x in agendalist:
				if int(time.time()) > (x.airtime-(60*10)) and int(time.time()) < x.airtime:
					await bot.send_message(channel, "Anime "+str(x.name)+" around "+str(datetime.fromtimestamp(x.airtime)))
					agendalist.remove(x)	
		await asyncio.sleep(60*10) # task runs every 60 seconds 
		
'''
async def update_list():
	await bot.wait_until_ready()
	while not bot.is_closed()
		if not agendalist == []:
			for x in agendalist:
'''				
		
@bot.event
async def on_ready():
	if not os.stat(AGENDA).st_size == 0:
		f = open(AGENDA,"r")
		for line in f:
			agendalist.append(create_slot_fromid(line.rstrip()))
		f.close()
		print("AgendaList Loaded")

	print('Logged in as:	')
	print(bot.user.name)
	print('Bot ID:	') 
	print(bot.user.id)
	print('Anilist API Token: ')
	print(token)
	print('----------------')

@bot.command()
async def addanime(name : str):
	"""
		Adds a anime to the agenda
		Use Anilist.co url to add
	"""
	global agendalist
	path = os.path.split(urlparse(name).path)
	path = os.path.split(path[0])
	id = path[1]
	##need exceptions
	aslot = create_slot_fromid(id)
	agendalist.append(aslot)
	f = open(AGENDA,"a")
	f.write(id+"\n");
	f.close();
	
	await bot.say(aslot.name+" set to the agenda!")
	
	
@bot.command()
async def seeagenda():
	await bot.say("Animes in the agenda:")
	for a in agendalist:
		await bot.say(a.name)

	
@bot.command()
async def killbot():
	exit()

bot.loop.create_task(agendaloop())
bot.run(discord_tkn)