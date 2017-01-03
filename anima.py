'''
Anima-Chan ver. 0.2
/u/Pedrowski
used solutions: 
http://www.yilmazhuseyin.com/blog/dev/advanced_json_manipulation_with_python/

'''
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

AGENDA = "agenda.json"

#creates file if doesn't exist
if not os.path.isfile(AGENDA):
	f = open(AGENDA,"x")
	f.close()
	
#Discord TKN here
discord_tkn = 'MjE0NTY1Mzc3NzgxMzk5NTUz.CpK1GQ.mUYCXTPrwegPPoytQq7pR5yjnuw'
	
	
#Anilist user credentials here
client_id = 'tsukalos-atojm'
client_secret = '3mc1o2QdJstxKnWvg7aCyZbDR'
	
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
	if c['airing'] == None:
		if c['airing_status'] == 'finished airing':
			return "finished"
	else:
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
		
def object_hook_handler(dct):
    """ parsed_dict argument will get 
        json object as a dictionary
        for above example it would have
        following dictionary as value
    """
    return AnimeSlot(id=dct['id'], name=dct['name'], airtime=dct['airtime'], nextep=dct['nextep'])

def save_agenda():
	f = open(AGENDA,"w")
	f.write(json.dumps([a.__dict__ for a in agendalist], sort_keys=True , indent=4))
	f.close()



async def agendaloop():
	await bot.wait_until_ready()
	channel = discord.Object(id='265313634521972736')
	
	while not bot.is_closed: #things to be looped go here
		if not agendalist == []:
			for x in agendalist:
				if int(time.time()) > (x.airtime-(60*10)) and int(time.time()) < x.airtime:
					await bot.send_message(channel, "Anime "+str(x.name)+" around "+str(datetime.fromtimestamp(x.airtime)))
					#agendalist.remove(x)
					#bot.send_message(channel, "")
					

		

					
		await asyncio.sleep(60*10) # task runs every 10 min




async def update_list():
	await bot.wait_until_ready()
	global agendalist
	while not bot.is_closed:
		if not agendalist == []:
			for x in agendalist:
				if int(time.time()) > (x.airtime):
					a = create_slot_fromid(x.id)
					if type(a) == AnimeSlot:
						x = a
						logging.info("updating "+x.name)
					else:
						if a == "finished":
							logging.info(x.name+" has finished airing!")
			save_agenda()
		await asyncio.sleep(60*60) # task runs every 60 min	
		
@bot.event
async def on_ready():
	global agendalist
	if not os.stat(AGENDA).st_size == 0:
		f = open(AGENDA,"r")
		agendalist = json.load(f, object_hook=object_hook_handler)
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
	if  type(aslot) == AnimeSlot:
		agendalist.append(aslot)
		save_agenda()
		await bot.say(aslot.name+" set to the agenda!")
	else:
		if aslot == "finished":
			await bot.say("This show has already finished airing :cry:")
	
	
@bot.command()
async def seeagenda():
	await bot.say("Animes in the agenda:")
	text = ""
	for a in agendalist:
		text = text + "https://anilist.co/anime/"+str(a.id)+"	**"+a.name+"** \n"
	await bot.say(text)

	
@bot.command()
async def killbot():
	exit()

bot.loop.create_task(agendaloop())
bot.run(discord_tkn)