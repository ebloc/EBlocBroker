#!/usr/bin/env

from subprocess import call
import sys, os, time, subprocess, string, driverFunc, lib, _thread
from colored import stylize
from colored import fg
import hashlib
import sys, signal
from imports import connectEblocBroker
from imports import getWeb3

sys.path.insert(0, './contractCalls')
from contractCalls.getDeployedBlockNumber   import getDeployedBlockNumber
from contractCalls.isContractExist          import isContractExist
from contractCalls.isClusterExist           import isClusterExist
from contractCalls.getClusterReceivedAmount import getClusterReceivedAmount
from contractCalls.blockNumber              import blockNumber
from contractCalls.getJobInfo               import getJobInfo
from contractCalls.isUserExist              import isUserExist
from contractCalls.getUserInfo              import getUserInfo
from contractCalls.isWeb3Connected          import isWeb3Connected

import LogJob

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)

# cmd: ps aux | grep \'[d]riverCancel\' | grep \'python3\' | wc -l 
p1 = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
#-----------
p2 = subprocess.Popen(['grep', '[d]riverCancel'], stdin=p1.stdout, stdout=subprocess.PIPE)
p1.stdout.close()
#-----------
p3 = subprocess.Popen(['grep', 'python3'], stdin=p2.stdout,stdout=subprocess.PIPE)
p2.stdout.close()
#-----------
p4 = subprocess.Popen(['wc', '-l'], stdin=p3.stdout,stdout=subprocess.PIPE)
p3.stdout.close()
#-----------
out = p4.communicate()[0].decode('utf-8').strip()
# ----------------------------------------------------------------

if int(out) == 0: #{   
   # Running driverCancel.py on the background
   pro = subprocess.Popen(['python3','driverCancel.py']) 
#}

# Paths =================================================================
jobsReadFromPath               = lib.JOBS_READ_FROM_FILE
# =======================================================================

# res = subprocess.check_output(["stty", "size"]).strip().decode('utf-8').split()
# rows = res[0] columns = res[1]
columns = 100

def log(strIn, color=''): #{
   if color != '':
      print(stylize(strIn, fg(color)))
   else:
      print(strIn)
      
   txFile = open(lib.LOG_PATH + '/transactions/clusterOut.txt', 'a')
   txFile.write(strIn + "\n")
   txFile.close()   
#}

def terminate(): #{
   log('Terminated')
   subprocess.run(['sudo', 'bash', 'killall.sh']) # Kill all dependent processes and exit.   

   # Following lines are added in ./killall.sh does not work due to sudo:
   os.killpg(os.getpgid(pro.pid), signal.SIGTERM)  # Send the kill signal to all the process groups
   sys.exit()
#}


def shellCommand(args): #{
   return subprocess.check_output(args).decode('utf-8').strip() 
#}

def idleCoreNumber(printFlag=1): #{
    coreInfo = shellCommand(['sinfo', '-h', '-o%C']).split("/")
    if len(coreInfo) != 0:
       idleCore = coreInfo[1]
       if printFlag == 1:
          log('AllocatedCores: ' + coreInfo[0] + '| IdleCores: ' + coreInfo[1] + '| OtherCores: ' + coreInfo[2] + '| TotalNumberOfCores: ' + coreInfo[3], 'blue')               
    else:
       log("sinfo return emptry string.", 'red')
       idleCore = 0
    return idleCore
#}   

def slurmPendingJobCheck(): #{
    idleCore  = idleCoreNumber()       
    printFlag = 0    
    while idleCore == '0':  #{
       if printFlag == 0:
          log('Waiting running jobs to be completed...', 'blue')
          printFlag = 1
       time.sleep(10)
       idleCore = idleCoreNumber(0)
    #}
#}

# checks whether geth runs on the background
def isGethOn(): #{  
   # cmd: ps aux | grep [g]eth | grep '8545' | wc -l
   p1 = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['grep', '[g]eth'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   p3 = subprocess.Popen(['grep', str(lib.RPC_PORT)], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   #-----------
   p4 = subprocess.Popen(['wc', '-l'], stdin=p3.stdout,stdout=subprocess.PIPE)
   p3.stdout.close()
   #-----------
   out = p4.communicate()[0].decode('utf-8').strip()
   
   if int(out) == 0:
      log("Geth is not running on the background.", 'red')
      lib.terminate()      
#}

# checks: does Driver.py runs on the background
def isDriverOn(): #{
   # cmd: ps aux | grep \'[D]river.py\' | grep \'python\' | wc -l
   p1 = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['grep', '[D]river.py'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   p3 = subprocess.Popen(['grep', 'python'], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   #-----------
   p4 = subprocess.Popen(['wc', '-l'], stdin=p3.stdout,stdout=subprocess.PIPE)
   p3.stdout.close()
   #-----------
   out = p4.communicate()[0].decode('utf-8').strip()
   
   if int(out) > 1:
      log("Driver is already running.", 'green')
#}

yes = set(['yes', 'y', 'ye'])
no  = set(['no' , 'n'])
if lib.WHOAMI == '' or lib.EBLOCPATH == '' or lib.CLUSTER_ID == '': #{
   print(stylize('Once please run:  ./initialize.sh \n', fg('red')))
   terminate()
#}

isDriverOn()
lib.isSlurmOn()
isGethOn()
   
isContractExist = isContractExist(web3)
if 'False' in isContractExist:
   log('Please check that you are using eBloc blockchain.', 'red')
   terminate()

log('=' * int(int(columns) / 2  - 12)   + ' cluster session starts ' + '=' * int(int(columns) / 2 - 12), "green")
log('isWeb3Connected: ' + str(isWeb3Connected(web3)))
log('rootdir: ' + os.getcwd())
with open('contractCalls/address.json', 'r') as content_file:
   log('{0: <20}'.format('contractAddress:') + "\"" + content_file.read().strip() + "\"", "yellow")
   
if lib.IPFS_USE == 1:
   lib.isIpfsOn()
   
clusterAddress = lib.CLUSTER_ID
isClusterExist = isClusterExist(clusterAddress, eBlocBroker, web3)

if "false" in isClusterExist.lower(): #{
   print(stylize("Error: Your Ethereum address '" + clusterAddress + "' \n"
                 "does not match with any cluster in eBlocBroker. Please register your \n" 
                 "cluster using your Ethereum Address in to the eBlocBroker. You can \n"   
                 "use 'contractCalls/registerCluster.py' script to register your cluster.", fg('red')))
   terminate()
#}

deployedBlockNumber = getDeployedBlockNumber(eBlocBroker)
blockReadFromContract = str(0)

log('{0: <20}'.format('clusterAddress:') + "\"" + clusterAddress + "\"", "yellow")
if not os.path.isfile(lib.BLOCK_READ_FROM_FILE): #{
   f = open(lib.BLOCK_READ_FROM_FILE, 'w')
   f.write(deployedBlockNumber + "\n")
   f.close()
#}

f = open(lib.BLOCK_READ_FROM_FILE, 'r')
blockReadFromLocal = f.read().rstrip('\n')
f.close()

if not blockReadFromLocal.isdigit(): #{
   log("Error: lib.BLOCK_READ_FROM_FILE is empty or contains and invalid value")
   log("#> Would you like to read from contract's deployed block number? y/n")   
   while True: #{
      choice = input().lower()
      if choice in yes:
         blockReadFromLocal = deployedBlockNumber
         f = open(lib.BLOCK_READ_FROM_FILE, 'w')
         f.write( deployedBlockNumber + "\n")
         f.close()
         log("\n")
         break
      elif choice in no:
         terminate()
      else:
         sys.stdout.write("Please respond with 'yes' or 'no'")
   #}
#}

blockReadFrom = 0
if int(blockReadFromLocal) < int(blockReadFromContract):
   blockReadFrom = blockReadFromContract
else:
   blockReadFrom = blockReadFromLocal

clusterGainedAmountInit = getClusterReceivedAmount(clusterAddress, eBlocBroker, web3)
log('{0: <21}'.format('deployedBlockNumber:') +  str(deployedBlockNumber) + "| Cluster's initial money: " + clusterGainedAmountInit)

# Remove queuedJobs from previous test.
subprocess.run(['rm', '-rf', lib.LOG_PATH + 'queuedJobs.txt']) 
subprocess.run(['rm', '-f',  lib.JOBS_READ_FROM_FILE])

while True: #{    
    if "Error" in blockReadFrom:
       log(blockReadFrom)
       terminate()

    clusterGainedAmount = getClusterReceivedAmount(clusterAddress, eBlocBroker, web3) 
    squeueStatus        = shellCommand(['squeue'])    

    if "squeue: error:" in str(squeueStatus): #{
       log("SLURM is not running on the background, please run \'sudo ./runSlurm.sh\'. \n")
       log(squeueStatus)
       terminate()
    #}
    idleCoreNumber()
    
    log("Current Slurm Running jobs status: \n" + squeueStatus)
    log('-' * int(columns), "green")
    if 'notconnected' != clusterGainedAmount:
       log("Current Time: " + time.ctime() + '| ClusterGainedAmount: ' + str(int(clusterGainedAmount) - int(clusterGainedAmountInit)))
    log("Waiting new job to come since block number: " + blockReadFrom)
    
    currentBlockNumber = blockNumber() 
    log("Waiting new block to increment by one.")
    log("Current BlockNumber: " + currentBlockNumber  + "| sync from block number: " + blockReadFrom)

    while int(currentBlockNumber) < int(blockReadFrom): #{          
       time.sleep(2)
       currentBlockNumber = blockNumber(web3)
    #}

    log("Passed incremented block number... Continue to wait from block number: " + blockReadFrom)   
    blockReadFrom = str(blockReadFrom) # Starting reading event's location has been updated
    # blockReadFrom = 1094262 # used for test purposes.
    slurmPendingJobCheck()    
    loggedJobs = LogJob.run(blockReadFrom, clusterAddress, eBlocBroker)       
    
    print('isWeb3Connected: ' + str(isWeb3Connected(web3)))
    maxVal               = 0
    isClusterReceivedJob = 0
    counter              = 0
        
    for i in range(0, len(loggedJobs)):
       runFlag = 0
       isClusterReceivedJob = 1
       log(str(counter) + ' ' + '-' * (int(columns) - 2), "green")
       counter += 1

       log("BlockNum: " + str(loggedJobs[i]['blockNumber']) + " " + loggedJobs[i].args['clusterAddress'] + " " + loggedJobs[i].args['jobKey'] + " " +
           str(loggedJobs[i].args['index']) + " " + str(loggedJobs[i].args['storageID']) + " " + loggedJobs[i].args['desc'])

       if loggedJobs[i]['blockNumber'] > int(maxVal):
          maxVal = loggedJobs[i]['blockNumber']

       jobKey = loggedJobs[i].args['jobKey']
       index  = int(loggedJobs[i].args['index'])

       strCheck = shellCommand(["bash", lib.EBLOCPATH + "/strCheck.sh", jobKey])

       jobInfo  = getJobInfo(clusterAddress, jobKey, index, eBlocBroker, web3)
       userID   = ""
       if not jobInfo: #if not ',' in jobInfo or jobInfo == '': 
          log("jobInfo is returned as empty list. Geth might be closed", 'red')
          runFlag = 1
       else: #{
          log('jobOwner/userID: ' + jobInfo[6])
          userID    = jobInfo[6]          
          userExist = isUserExist(userID, eBlocBroker, web3)          

          if jobInfo[0] == str(lib.job_state_code['COMPLETED']):
             log("Job is already completed.", 'red')
             runFlag = 1
          if jobInfo[0] == str(lib.job_state_code['REFUNDED']):
             log("Job is refunded.", 'red')
             runFlag = 1
          if runFlag == 0 and not jobInfo[0] == lib.job_state_code['PENDING']:
             log("Job is already captured and in process or completed.", 'red')
             runFlag = 1
          if 'False' in strCheck:
             log('Filename contains invalid character', 'red')
             runFlag = 1
          if "false" in userExist.lower(): 
             log('jobOwner is not registered', 'red')
             runFlag = 1
          else:
             userInfo = getUserInfo(userID, '1', eBlocBroker, web3)
                         
          slurmPendingJobCheck()
          print(shellCommand(['sudo', 'bash', lib.EBLOCPATH + '/user.sh', userID, lib.PROGRAM_PATH]))          
       #}

       if runFlag == 1:
          pass
       elif str(loggedJobs[i].args['storageID']) == '0':
          log("New job has been received. IPFS call |" + time.ctime(), "green")
          driverFunc.driverIpfsCall(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']),
                                    str(loggedJobs[i].args['storageID'], eBlocBroker, web3), hashlib.md5(userID.encode('utf-8')).hexdigest()) 
       elif str(loggedJobs[i].args['storageID']) == '1':
          log("New job has been received. EUDAT call |" + time.ctime(), "green")          
          driverFunc.driverEudatCall(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']), userInfo[4],
                                     hashlib.md5(userID.encode('utf-8')).hexdigest(), eBlocBroker, web3)
          #thread.start_new_thread(driverFunc.driverEudatCall, (loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']))) 
       elif str(loggedJobs[i].args['storageID']) == '2':
          log("New job has been received. IPFS with miniLock call |" + time.ctime(), "green")
          driverFunc.driverIpfsCall(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']),
                                    str(loggedJobs[i].args['storageID'], eBlocBroker, web3), hashlib.md5(userID.encode('utf-8')).hexdigest())
          #thread.start_new_thread(driverFunc.driverIpfsCall, (loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']), str(loggedJobs[i].args['storageID']), submittedJob[5]))
       elif str(loggedJobs[i].args['storageID']) == '3': 
          log("New job has been received. GitHub call |" + time.ctime(), "green")
          driverFunc.driverGithubCall(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']),
                                      str(loggedJobs[i].args['storageID'], eBlocBroker, web3), hashlib.md5(userID.encode('utf-8')).hexdigest())
       elif str(loggedJobs[i].args['storageID']) == '4': 
          log("New job has been received. Googe Drive call |" + time.ctime(), "green")
          driverFunc.driverGdriveCall(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']), str(loggedJobs[i].args['storageID']),
                                      hashlib.md5(userID.encode('utf-8')).hexdigest(), eBlocBroker, web3)
    #}    

    if len(loggedJobs) > 0 and int(maxVal) != 0: #{ 
       f_blockReadFrom = open(lib.BLOCK_READ_FROM_FILE, 'w') # Updates the latest read block number      
       f_blockReadFrom.write(str(int(maxVal) + 1) + '\n') 
       f_blockReadFrom.close()
       blockReadFrom = str(int(maxVal) + 1)
    #}

    if isClusterReceivedJob == 0: #{ If there is no submitted job for the cluster, block start to read from current block number
       f_blockReadFrom = open(lib.BLOCK_READ_FROM_FILE, 'w') # Updates the latest read block number
       f_blockReadFrom.write(str(currentBlockNumber) + '\n')
       f_blockReadFrom.close()
       blockReadFrom = str(currentBlockNumber)
    #}
#}
