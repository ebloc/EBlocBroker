#!/usr/bin/env python

# from web3.auto import w3
import asyncio
from web3 import Web3, HTTPProvider
web3 = Web3(HTTPProvider('http://localhost:8545'))
from web3.shh import Shh
Shh.attach(web3, "shh")

import json,sys,os.path

from os.path import expanduser
home = expanduser("~")

topic = '0x07678231'
testFlag    = True

def log(strIn):
	if testFlag:
		print(strIn)

def post(message):
	try:
		web3.shh.post({
			'powTarget': 2, # 2.5
			'powTime': 5,   # 2
			'ttl': 60,
			'payload': web3.toHex(text='I am on.'),
			'topic': topic,
			'pubKey': message,
		})
	except:
		post(message)


def handle_event(event):
    #print(event)
	message = event['payload'].decode("utf-8")
	log(message)
	post(message)

async def log_loop(event_filter, poll_interval):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event) # TODO: add try catch
        await asyncio.sleep(poll_interval)


def receiver(kId, publicKey, filterID, myFilter):
	retreived_messages = web3.shh.getMessages(filterID)

	log('whisperPublicKey: ' + publicKey);
	'''
	log('FilterID: ' + filterID)
	log('receiverPrivateK: ' + web3.shh.getPrivateKey(kId));
	log(web3.shh.hasKeyPair(kId))
	log('PubKey: ' + web3.shh.getPublicKey(kId))
	'''
	# retreived_messages = web3.shh.getMessages('13723641127bc212ab379100a5d9e05e09b8c34fe1357f51e54cf17b568918cc')
	log('Received Messages:')
	for i in range(0, len(retreived_messages)):
		log(retreived_messages[i]['payload'].decode("utf-8"))
		log('---------------------------------')
		# print(retreived_messages[i])
	loop = asyncio.get_event_loop()
	try:
		loop.run_until_complete(
			asyncio.gather(
				log_loop(myFilter, 2)))
	finally:
		loop.close()

def main():
	# print(web3.shh.info)
	if not os.path.isfile(home + '/.eBlocBroker/whisperInfo.txt'):
		# First time running:
		log('Please first run: python whisperInitialize.py')
		sys.exit()
	else:
		with open(home + '/.eBlocBroker/whisperInfo.txt') as json_file:
			data = json.load(json_file)
		kId = data['kId']
		publicKey = data['publicKey']
		if not web3.shh.hasKeyPair(kId):
			log("Whisper node's private key of a key pair did not match with the given ID")
			sys.exit()
		myFilter = web3.shh.newMessageFilter({'topic': topic, 'privateKeyID': kId, 'recipientPublicKey': publicKey})
		myFilter.poll_interval = 600; # Make it equal with the live-time of the message
		filterID = data['filterID']
		# privateKey = "0xc0995bb51a0a74fcedf972662569849de4b4d0e8ceca8e4e6e8846a5d00f0b0c"
		# kId = web3.shh.addPrivateKey(privateKey)

	receiver(kId, publicKey, filterID, myFilter)

if __name__ == '__main__':
    main()
