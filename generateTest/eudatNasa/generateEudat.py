#!/usr/bin/python3

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from os.path import expanduser
from random import randint

path = os.getcwd()
home = expanduser("~")
sys.path.insert(0, home + '/eBlocBroker')

from lib_owncloud import singleFolderShare
from lib_owncloud import eudatInitializeFolder

os.environ['path'] = path

# Login to EUDAT account----------------------------------------
f = open(home + '/TESTS/password.txt', 'r') # Password read from the file.
password = f.read().replace("\n", "").replace(" ", "")
f.close()
oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('059ab6ba-4030-48bb-b81b-12115f531296', password)
#---------------------------------------------------------------
flag        = 0
counter     = 0
itemsToScan = 151
hashesFile = open(path + '/hashOutput.txt', 'w+')

with open(path + "/nasa.txt") as test:
    for line in test:
        f = open('ipfs/run.sh', 'w+')
        lineIn = line.split(" ")

        if (int(lineIn[1]) - int(lineIn[0])) > 60 and int(lineIn[2]) != 0:
           print("Time to take in seconds: "  + str(int(lineIn[1]) - int(lineIn[0])))
           print("CoreNum: "  + str(int(lineIn[2])))
           print(line)

           with open("ipfs/run_temp.sh") as ff:
              for line in ff:
                 f.write(line)

           randomHash = str(random.getrandbits(128)) + str(random.getrandbits(128))
           f.write("sleep " + str(int(lineIn[1]) - int(lineIn[0])) + "\n")
           f.write("#" + randomHash + "\n") # Add random line to create different hash
           f.write("echo completed " + str(int(lineIn[1]) - int(lineIn[0])) + " > completed.txt\n" ) #add random line to create different hash.
           f.close()

           tarHash = eudatInitializeFolder('ipfs', oc) # Should give folder name
           time.sleep(1)
           # After run.sh is update share the ipfs through eudat
           print(singleFolderShare(tarHash, oc))

           if flag == 1:
               hashesFile.write(" " + str(int(lineIn[0])-startTimeTemp) + '\n')

           startTimeTemp=int(lineIn[0])
           flag = 1
           print(counter)
           counter += 1
           if (counter == itemsToScan):
              break
           hashesFile.write(tarHash + " " + str(int(lineIn[1]) - int(lineIn[0])) + " " + str(int(lineIn[2])) + " " + str(int(lineIn[0])) + " " + str(int(lineIn[1])))

hashesFile.close()

print('\nFolders are created. Sharing files now...')
print(os.popen('python $path/shareOwnCloud.py').read())

# -------------------------------------
#ipfsHash = os.popen( 'IPFS_PATH="/home/prc/.ipfs" export IPFS_PATH ipfs add -r /home/prc/testIpfs/ipfs' ).read()
#ipfsHash = ipfsHash.split("\n")
#tarHash = ipfsHash[len(ipfsHash) - 2].split(" ")[1]
#print( "HASH: " + tarHash ) # lineNumber -> hash olarak kaydet.
