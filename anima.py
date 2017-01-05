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
AUTH = "auth.json"

#creates file if doesn't exist
if not os.path.isfile(AGENDA):
	f = open(AGENDA,"x")
	f.close()
if not os.path.isfile(AUTH):
	f = open(AUTH,"x")
	f.close()

	
## tokens needed to be inputed in auth.json file
discord_tkn = ''
client_id = ''
client_secret = ''

## used after anilist auth
token = ''

description = 'AnimeAirTime'


CMDPREFIX = '!!'

bot = commands.Bot(command_prefix=CMDPREFIX, description=description)

def get_credentials_from_file():
	global discord_tkn
	global client_id
	global client_secret
	f = open(AUTH,"r")
	c = json.load(f)
	discord_tkn = str(c['discord_token'])
	client_id = str(c['anilist_client_id'])
	client_secret = str(c['anilist_client_secret'])
	
get_credentials_from_file()

#header data for anilist auth
auth_data = {'grant_type': 'client_credentials', 'client_id' : client_id , 'client_secret' : client_secret }
	
def alist_tkn():
	''' Auth Anilist API - returns access_token str '''
	client_auth = requests.post('https://anilist.co/api/auth/access_token',data=auth_data)
	json_res = json.loads(bytes.decode(client_auth.content))
	return json_res['access_token']


agendalist = []



def create_slot_fromid(id):
	r = requests.get('https://anilist.co/api/anime/'+id+'?access_token='+token)
	c = json.loads(bytes.decode(r.content))
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
		logging.info(agendalist)
		if not agendalist == []:
			for x in agendalist:
				if int(time.time()) > (x.airtime-(60*10)) and int(time.time()) < x.airtime:
					await bot.send_message(channel, "Anime "+str(x.name)+" around "+str(datetime.fromtimestamp(x.airtime)))
					
				

		

					
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
							agendalist.remove(x)
			save_agenda()
		await asyncio.sleep(60*60) # task runs every 60 min	
		
@bot.event
async def on_ready():
	global agendalist
	global token
	token = alist_tkn()
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
		
		Use: !!addanime anilist.co/anime/<..>/<..>
	"""
	global agendalist
	scheme = urlparse(name).scheme
	if scheme == '':
		name = 'https://'+name
	logging.info(name)
	path = urlparse(name).path
	logging.info(path)
	id = path[7:11]+path[11]
	
	flag = True
	for a in agendalist:
		if a.id == int(id):
			await bot.say("The show "+a.name+" already in the agenda!")
			flag = False
			break
	if flag:
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
	if not agendalist == []:
		await bot.say("Animes in the agenda:")
		text = ""
		for a in agendalist:
			text = text + "https://anilist.co/anime/"+str(a.id)+"/	**"+a.name+"** \n"
		await bot.say(text)
	else:
		await bot.say("The agenda is empty :confounded:")

	
def check_number(msg):
		return msg.content.isdigit()

@bot.command(pass_context = True)
async def removeanime(ctx, member: discord.Member = None):
	'''
		Removes anime from the list
	'''
	if member is None:
		author = ctx.message.author
	await bot.say("Animes in the agenda:")
	text = ""
	i = 0
	for a in agendalist:
		i = i + 1
		text = text + "[  "+str(i)+"  ]		**"+a.name+"** \n"
	text = text + "\n Type the number of the anime you wish to remove."
	await bot.say(text)
	num = await bot.wait_for_message(timeout=10.0, author=author, check=check_number)
	while int(num.content) <= 0 or int(num.content) > i:
		await bot.say("Please choose one of the numbers above.")
		num = await bot.wait_for_message(timeout=10.0, author=author, check=check_number)
	
	x = agendalist[int(num.content)-1]
	agendalist.remove(x)
	save_agenda()
	await bot.say(x.name+" removed from the agenda!")
	
	

@bot.command()
async def killbot():
	exit()

bot.loop.create_task(agendaloop())
bot.run(discord_tkn)