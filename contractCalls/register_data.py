#!/usr/bin/env python3

import traceback

from lib import PROVIDER_ID
from imports import connect


def register_data(sourceCodeHash, price, commitmentBlockDuration, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return

    try:
        tx = eBlocBroker.functions.registerData(sourceCodeHash, price, commitmentBlockDuration).transact({"from": w3.toChecksumAddress(PROVIDER_ID), "gas": 100000})
        
    except Exception:
        return False, traceback.format_exc()

    return True, tx.hex()


if __name__ == '__main__':
    sourceCodeHash = "0x68b8d8218e730fc2957bcb12119cb204"
    status, result = register_data(sourceCodeHash, 20, 240)
    
    if status:
        print('tx_hash=' + result)        
    else:
        print(result)       
