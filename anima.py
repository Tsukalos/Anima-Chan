'''
Anima-Chan ver. 0.5
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


#json files
AGENDA = "agenda.json"
AUTH = "auth.json"
CONFIG = "config.json"

#creates file if doesn't exist
if not os.path.isfile(AGENDA):
	f = open(AGENDA,"x")
	f.close()
if not os.path.isfile(AUTH):
	f = open(AUTH,"x")
	f.close()
if not os.path.isfile(CONFIG):
	f = open(CONFIG, "x")
	f.close()

	
## tokens needed to be inputed in auth.json file
discord_tkn = ''
client_id = ''
client_secret = ''

## used after anilist auth
token = ''

#bot description 
description = 'AnimeAirTime'

#default announce channel, defined in config.json
channel = discord.Object(id='')

#default command prefix
CMDPREFIX = '!!'

#Discord.Client define, from ext.commands
bot = commands.Bot(command_prefix=CMDPREFIX, description=description)

#retrieves information from config.json
def get_pref_config():
	global channel
	global CMDPREFIX
	f = open(CONFIG, "r")
	c = json.load(f)
	channel = discord.Object(id=str(c['discord_channel_id']))
	CMDPREFIX = str(c['command_prefix'])
	logging.info('Loaded config.json')
	f.close()
	
get_pref_config()
	
#retrieves authentication from auth file
def get_credentials_from_file():
	global discord_tkn
	global client_id
	global client_secret
	f = open(AUTH,"r")
	c = json.load(f)
	discord_tkn = str(c['discord_token'])
	client_id = str(c['anilist_client_id'])
	client_secret = str(c['anilist_client_secret'])
	logging.info('Loaded auth.json')
	f.close()
	
get_credentials_from_file()

#header data for anilist auth
auth_data = {'grant_type': 'client_credentials', 'client_id' : client_id , 'client_secret' : client_secret }
	
#gets access_token for anilist api use.
def alist_tkn():
	''' Auth Anilist API - returns access_token str '''
	client_auth = requests.post('https://anilist.co/api/auth/access_token',data=auth_data)
	json_res = json.loads(bytes.decode(client_auth.content))
	return json_res['access_token']

#global agenda
agendalist = []

#checks if url is a valid anilist.co url
def validate_url(url):
	try:
		r = requests.get(url)
	except:
		return False
	path = urlparse(url).path
	if path.startswith('/anime/'):
		return True
	else:
		return False

# using id parameter from anilist, creates a AnimeSlot object,
# if show is not airing, or id is invalid, returns a str.
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

#gets a dict object and transforms into AnimeSlot object.		
def object_hook_handler(dct):
    """ parsed_dict argument will get 
        json object as a dictionary
    """
    return AnimeSlot(id=dct['id'], name=dct['name'], airtime=dct['airtime'], nextep=dct['nextep'])

#writes agendalist into a json file.
def save_agenda():
	f = open(AGENDA,"w")
	f.write(json.dumps([a.__dict__ for a in agendalist], sort_keys=True , indent=4))
	f.close()


#async loop that checks if AnimeSlot anime is airing in X minutes.
async def agendaloop():
	await bot.wait_until_ready()
	while not bot.is_closed: #things to be looped go here
		if agendalist:
			for x in agendalist:
				if int(time.time()) > (x.airtime-(60*15)) and int(time.time()) < x.airtime:
					dt = datetime.fromtimestamp(x.airtime)
					await bot.send_message(channel, "Anime **"+str(x.name)+"** around **"+dt.strftime('%d/%m/%y  %H:%M')+"**")
					
				

		

					
		await asyncio.sleep(60*10) # task runs every 10 min

#checks if AnimeSlot anime in agendalist is outdated.
def update_list():
	global agendalist
	if agendalist:
		auxagenda = agendalist
		for x in agendalist:
			if int(time.time()) > (x.airtime):
				a = create_slot_fromid(str(x.id))
				if type(a) == AnimeSlot:
					i = agendalist.index(x)
					auxagenda.pop(i)
					auxagenda.insert(i, a)
					logging.info("Updating "+x.name)
				else:
					if a == "finished":
						logging.info(x.name+" has finished airing!")
						auxagenda.remove(x)
		agendalist = auxagenda
		save_agenda()
	

async def auto_update_list():
	await bot.wait_until_ready()
	global agendalist
	while not bot.is_closed:
		update_list()
		await asyncio.sleep(60*20) # task runs every 60 min	
		
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

#agenda group of commands.
@bot.group(pass_context=True)
async def agenda(ctx):
	if ctx.invoked_subcommand is None:
		await bot.say('Invalid agenda command!')

	
@agenda.command()
async def add(name : str):
	"""
		Adds a anime to the agenda
		Use Anilist.co url to add
		
		Use: !!agenda add anilist.co/anime/<..>/<..>
	"""
	global agendalist
	
	scheme = urlparse(name).scheme
	if scheme == '':
		name = 'https://'+name
		
	netloc = urlparse(name).netloc
	if not netloc == 'anilist.co':
		await bot.say("Please use a anilist.co valid anime url!")
	else:
		if validate_url(name):
			logging.info(name)
			path = urlparse(name).path
			logging.info(path)
			id = path[7:11]+path[11]
			
			flag = True
			for a in agendalist:
				if a.id == int(id):
					await bot.say("The show **"+a.name+"** already in the agenda!")
					flag = False
					break
			if flag:
				aslot = create_slot_fromid(id)
				if  type(aslot) == AnimeSlot:
					agendalist.append(aslot)
					save_agenda()
					await bot.say("**"+aslot.name+"** set to the agenda!")
				else:
					if aslot == "finished":
						await bot.say("This show has already finished airing :cry:")
		else:
			await bot.say("This is not a valid url! :cry:")
	
	
@agenda.command()
async def see():
	'''
		Displays Animes in the agenda
	'''
	update_list()
	if not agendalist == []:
		await bot.say("Animes in the agenda:")
		text = ""
		for a in agendalist:
			fstrtime = datetime.fromtimestamp(a.airtime).strftime('%d/%m/%y  %H:%M')
			text = text + "https://anilist.co/anime/"+str(a.id)+"/	 EP"+str(a.nextep)+"  (__"+fstrtime+"__)	**"+a.name+"** \n"
		await bot.say(text)
	else:
		await bot.say("The agenda is empty :confounded:")

	
def check_number(msg):
		return msg.content.isdigit()

@agenda.command(pass_context = True)
async def remove(ctx, member: discord.Member = None):
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
		if num == None:
			break
	
	if not num == None:
		x = agendalist[int(num.content)-1]
		agendalist.remove(x)
		save_agenda()
		await bot.say(x.name+" removed from the agenda!")

#logs to console commands inputs
@bot.event
async def on_message(m):
	if m.content.startswith("!!"):
		msub = m.content[2:]
		t = "[COMMAND]"+m.author.name+"("+m.author.id+") - "+msub
		logging.info(t)
	await bot.process_commands(m)
	
@bot.command()
async def killbot():
	exit()

bot.loop.create_task(auto_update_list())
	
bot.loop.create_task(agendaloop())

bot.run(discord_tkn)