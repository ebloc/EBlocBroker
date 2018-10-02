#!/usr/bin/env python

import owncloud, hashlib, getpass, sys, os, time, subprocess, lib
from   subprocess import call
import os.path
from colored import stylize
from colored import fg
import subprocess
import glob, errno
from contractCalls.getJobInfo import getJobInfo

jobKeyGlobal    = None
indexGlobal     = None
storageIDGlobal = None
cacheTypeGlobal = None
shareTokenGlobal = '-1'

# Paths===================================================
ipfsHashes       = lib.PROGRAM_PATH 
# =========================================================

def silentremove(filename): #{
    try:
        os.remove(filename)
    except OSError as e: # This would be "except OSError, e:" before Python 2.6
       pass
#}

def removeFiles(filename): #{
   if "*" in filename: 
       for fl in glob.glob(filename):
           print(fl)
           silentremove(fl) 
   else:
       silentremove(filename) 
#}

def log(strIn, color=''): #{
   if color != '':
       print(stylize(strIn, fg(color))) 
   else:
       print(strIn)
       
   txFile = open(lib.LOG_PATH + '/transactions/clusterOut.txt', 'a') 
   txFile.write(strIn + "\n") 
   txFile.close() 

   fname = lib.LOG_PATH + '/transactions/' + jobKeyGlobal + '_' + indexGlobal + '_driverOutput' + '.txt'
   txFile = open(fname, 'a') 
   txFile.write(strIn + "\n") 
   txFile.close() 
#}

def isRunExistInTar(tarPath): #{   
    try:
        FNULL = open(os.devnull, 'w')
        res = subprocess.check_output(['tar', 'ztf', tarPath, '--wildcards', '*/run.sh'], stderr=FNULL).decode('utf-8').strip()
        FNULL.close()
        if res.count('/') == 1: # Main folder should contain the 'run.sh' file
            log('run.sh exists under the root folder', 'green')
            return True
        else:
            log('run.sh does not exist under the root folder', 'red')
            return False            
    except:
        log('run.sh does not exist under the root folder', 'red')
        return False
#}

def cache(userID): #{
    if cacheTypeGlobal is 'local': # Download into local directory at $HOME/.eBlocBroker/cache
        globalCacheFolder = lib.PROGRAM_PATH + '/' + userID + '/cache'
        if not os.path.isdir(globalCacheFolder): # If folder does not exist
            os.makedirs(globalCacheFolder)
                   
        cachedFolder  = lib.PROGRAM_PATH + '/' + userID + '/cache' + '/' + jobKeyGlobal
        cachedTarFile = lib.PROGRAM_PATH + '/' + userID + '/cache' + '/' + jobKeyGlobal + '.tar.gz'

        if not os.path.isfile(cachedTarFile):
            eudatDownloadFolder(globalCacheFolder, cachedFolder)
            if not isRunExistInTar(cachedTarFile):
                subprocess.run(['rm', '-f', cachedTarFile])
                return False, ''            
        else:
            res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
            if res == jobKeyGlobal: #Checking is already downloaded folder's hash matches with the given hash
                log('Already cached.', 'green')
            else:
                eudatDownloadFolder(globalCacheFolder, cachedFolder)
    elif cacheTypeGlobal is 'ipfs':
        ipfsHash = subprocess.check_output(['ipfs', 'add', lib.OC + '/' + jobKeyGlobal + '/' + jobKeyGlobal + '.tar.gz']).decode('utf-8').strip()
        return True, ipfsHash.split()[1]
    return True, ''
#}

# Assume job is sent and .tar.gz file
def eudatDownloadFolder(resultsFolderPrev, resultsFolder): #{
   '''
   # cmd: unzip -l $resultsFolder/output.zip | grep $eudatFolderName/run.sh
   # Checks does zip contains run.sh file
   p1 = subprocess.Popen(['unzip', '-l', resultsFolder + '/output.zip'], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['grep', eudatFolderName + '/run.sh'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   out = p2.communicate()[0].decode('utf-8').strip()   
   if not '/run.sh' in out:
       log("Error: Folder does not contain run.sh file.")
       return  
   '''

   # Downloads shared file as .zip, much faster.
   # cmd: wget -4 -o /dev/stdout https://b2drop.eudat.eu/s/$shareToken/download --output-document=$resultsFolderPrev/output.zip
   ret = subprocess.check_output(['wget', '-4', '-o', '/dev/stdout', 'https://b2drop.eudat.eu/s/' + shareTokenGlobal +
                                  '/download', '--output-document=' + resultsFolderPrev + '/output.zip']).decode('utf-8')
   if "ERROR 404: Not Found" in ret:
       log(ret, 'red') 
       log('File not found The specified document has not been found on the server.', 'red') 
       # TODO: since folder does not exist, do complete refund to the user.
       return 0
   log(ret) 

   time.sleep(0.25)  
   if os.path.isfile(resultsFolderPrev + '/output.zip'): #{       
       subprocess.run(['unzip', '-jo', resultsFolderPrev + '/output.zip', '-d', resultsFolderPrev, '-x', '*result-*.tar.gz'])
       subprocess.run(['rm', '-f', resultsFolderPrev + '/output.zip'])              
   #}
   
   '''   
   if glob.glob(resultsFolder + '/*.tar.gz'): #{  check file ending in .tar.gz exist
      # Extracting all *.tar.gz files.
      subprocess.run(['bash', lib.EBLOCPATH + '/tar.sh', resultsFolder])      
      # Removing all tar.gz files after extraction is done.
      subprocess.run(['rm', '-f'] + glob.glob(resultsFolder + '/*.tar.gz'))
   #}
    
   if glob.glob(resultsFolder + '/*.zip'): #{  check file ending in .zip exist
      subprocess.run(['unzip', resultsFolderPrev + '/' + jobKey, '-d', resultsFolderPrev, '-x', '*result-*.tar.gz'])
      subprocess.run(['rm', '-f'] + glob.glob(resultsFolder + "/*.zip"))
   #}
   '''
#}


def eudatGetShareToken(fID): #{
   # Checks already shared or not
   # TODO: store shareToken id with jobKey in some file, later do: oc.decline_remote_share(<share_id>) to cancel shared folder
   if cacheTypeGlobal is 'ipfs' and os.path.isdir(lib.OC + '/' + jobKeyGlobal):
       log('Eudat share is already accepted...', 'green')
       return True
   
   global shareTokenGlobal
   with open(lib.EBLOCPATH + '/eudatPassword.txt', 'r') as content_file:
       password = content_file.read().strip()

   log("Login into owncloud") 
   oc = owncloud.Client('https://b2drop.eudat.eu/') 
   oc.login('5f0db7e4-3078-4988-8fa5-f066984a8a97', password)  # Unlocks EUDAT account
   password = None   
   shareList = oc.list_open_remote_share() 

   acceptFlag      = 0 
   eudatFolderName = "" 
   log("Finding share token...")
   for i in range(len(shareList)-1, -1, -1): #{ Starts iterating from last item  to first one
      inputFolderName  = shareList[i]['name']
      inputFolderName  = inputFolderName[1:] # Removes '/' on the beginning
      inputID          = shareList[i]['id']
      inputOwner       = shareList[i]['owner']

      if (inputFolderName == jobKeyGlobal) and (inputOwner == fID): #{
         shareTokenGlobal = str(shareList[i]['share_token'])
         eudatFolderName  = str(inputFolderName)
         acceptFlag = 1
         log("Found. InputId=" + inputID + " |ShareToken: " + shareTokenGlobal)
         if cacheTypeGlobal is 'ipfs': #{
             val = oc.accept_remote_share(int(inputID));
             print(val) #delete
             tryCount = 0;
             while True: #{
                 if tryCount is 5:
                     break
                 time.sleep(10)
                 try:
                     oc.list(jobKeyGlobal) # jobKey is valid folder under owncloud cloud
                     break
                 except:
                     print('Remote share did not accepted yet...')
                 tryCount += 1
             #}
         #} 
         break 
      #}
   #}
   if acceptFlag == 0:
      oc.logout() 
      log("Couldn't find the shared file", 'red')
      return False
   return True
#}

def driverEudat(jobKey, index, fID, userID, eBlocBroker, web3): #{
   global jobKeyGlobal
   global indexGlobal
   global storageIDGlobal
   global shareTokenGlobal
   global cacheTypeGlobal  
   
   jobKeyGlobal = jobKey  
   indexGlobal  = index 
   storageIDGlobal = '1'
   cacheTypeGlobal = 'ipfs'
      
   log("key: "   + jobKey) 
   log("index: " + index) 

   resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index 
   resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN' 
   
   if not eudatGetShareToken(fID):
       return

   check, ipfsHash = cache(userID)   
   if not check:
       return   
   
   if not os.path.isdir(resultsFolderPrev): # If folder does not exist
      os.makedirs(resultsFolderPrev)
      os.makedirs(resultsFolder)

    
   if cacheTypeGlobal is 'local':
       # Untar cached tar file into local directory
       subprocess.run(['tar', '-xf', lib.PROGRAM_PATH + '/' + userID + '/cache' + '/' + jobKeyGlobal + '.tar.gz', '--strip-components=1', '-C', resultsFolder])

       # Copy from cached folder into user's path that run will occur if folder is used
       # subprocess.run(['rsync', '-avq', lib.PROGRAM_PATH + '/' + userID + '/cache' + '/' + jobKeyGlobal + '/', resultsFolder])   
   elif cacheTypeGlobal is 'ipfs':
       log('Reading from IPFS hash=' + ipfsHash)
       subprocess.run(['tar', '-xf', '/ipfs/' + ipfsHash, '--strip-components=1', '-C', resultsFolder])
   
   os.chdir(resultsFolder)  # 'cd' into the working path and call sbatch from there
   lib.sbatchCall(jobKeyGlobal, indexGlobal, storageIDGlobal, shareTokenGlobal, userID, resultsFolder, eBlocBroker,  web3)
#}