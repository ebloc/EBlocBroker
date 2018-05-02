/* Latest eBlocBroker Smart Contract's address and abi */
var address="0x8c22de03d3ce0b9dcb39617e7c31483ec484c720";
var abi=[{"constant":true,"inputs":[{"name":"userAddress","type":"address"}],"name":"isUserExist","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"},{"name":"jobKey","type":"string"},{"name":"index","type":"uint256"}],"name":"getJobInfo","outputs":[{"name":"","type":"uint8"},{"name":"","type":"uint32"},{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"}],"name":"getClusterReceivedAmount","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"jobKey","type":"string"},{"name":"index","type":"uint32"},{"name":"jobRunTimeMinute","type":"uint32"},{"name":"resultIpfsHash","type":"string"},{"name":"storageID","type":"uint8"},{"name":"endTime","type":"uint256"}],"name":"receiptCheck","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"}],"name":"getClusterReceiptSize","outputs":[{"name":"","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"userAddress","type":"address"}],"name":"getUserInfo","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"getClusterAddresses","outputs":[{"name":"","type":"address[]"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"userEmail","type":"string"},{"name":"fID","type":"string"},{"name":"miniLockID","type":"string"},{"name":"ipfsAddress","type":"string"}],"name":"registerUser","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"getDeployedBlockNumber","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"}],"name":"getClusterInfo","outputs":[{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"deregisterCluster","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"clusterAddress","type":"address"},{"name":"jobKey","type":"string"},{"name":"core","type":"uint32"},{"name":"jobDesc","type":"string"},{"name":"coreMinuteGas","type":"uint32"},{"name":"storageID","type":"uint8"}],"name":"submitJob","outputs":[{"name":"success","type":"bool"}],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"},{"name":"index","type":"uint32"}],"name":"getClusterReceiptNode","outputs":[{"name":"","type":"uint256"},{"name":"","type":"int32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"coreNumber","type":"uint32"},{"name":"clusterEmail","type":"string"},{"name":"fID","type":"string"},{"name":"miniLockID","type":"string"},{"name":"coreMinutePrice","type":"uint256"},{"name":"ipfsAddress","type":"string"}],"name":"updateCluster","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"}],"name":"isClusterExist","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"},{"name":"jobKey","type":"string"}],"name":"getJobSize","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"coreNumber","type":"uint32"},{"name":"clusterEmail","type":"string"},{"name":"fID","type":"string"},{"name":"miniLockID","type":"string"},{"name":"coreMinutePrice","type":"uint256"},{"name":"ipfsAddress","type":"string"}],"name":"registerCluster","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"jobKey","type":"string"},{"name":"index","type":"uint32"},{"name":"stateID","type":"uint8"},{"name":"startTime","type":"uint256"}],"name":"setJobStatus","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"clusterAddress","type":"address"},{"name":"jobKey","type":"string"},{"name":"index","type":"uint32"}],"name":"refund","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"inputs":[],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"name":"cluster","type":"address"},{"indexed":false,"name":"jobKey","type":"string"},{"indexed":false,"name":"index","type":"uint256"},{"indexed":false,"name":"storageID","type":"uint8"},{"indexed":false,"name":"desc","type":"string"}],"name":"LogJob","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"cluster","type":"address"},{"indexed":false,"name":"jobKey","type":"string"},{"indexed":false,"name":"index","type":"uint256"},{"indexed":false,"name":"recipient","type":"address"},{"indexed":false,"name":"received","type":"uint256"},{"indexed":false,"name":"returned","type":"uint256"},{"indexed":false,"name":"endTime","type":"uint256"},{"indexed":false,"name":"resultIpfsHash","type":"string"},{"indexed":false,"name":"storageID","type":"uint8"}],"name":"LogReceipt","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"cluster","type":"address"},{"indexed":false,"name":"coreNumber","type":"uint32"},{"indexed":false,"name":"clusterEmail","type":"string"},{"indexed":false,"name":"fID","type":"string"},{"indexed":false,"name":"miniLockID","type":"string"},{"indexed":false,"name":"coreMinutePrice","type":"uint256"},{"indexed":false,"name":"ipfsAddress","type":"string"}],"name":"LogCluster","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"cluster","type":"address"},{"indexed":false,"name":"userEmail","type":"string"},{"indexed":false,"name":"fID","type":"string"},{"indexed":false,"name":"miniLockID","type":"string"},{"indexed":false,"name":"ipfsAddress","type":"string"}],"name":"LogUser","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"clusterAddress","type":"address"},{"indexed":false,"name":"jobKey","type":"string"},{"indexed":false,"name":"index","type":"uint32"}],"name":"LogRefund","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"clusterAddress","type":"address"},{"indexed":false,"name":"jobKey","type":"string"},{"indexed":false,"name":"index","type":"uint32"},{"indexed":false,"name":"startTime","type":"uint256"}],"name":"LogSetJob","type":"event"}]
    
/* Exported as global variables */
exports.address = address;
exports.abi     = abi;
