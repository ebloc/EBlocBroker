#!/usr/bin/env python3

import sys
from typing import Union

import config
from config import logging
from lib import get_tx_status
from utils import _colorize_traceback, log


def authenticate_orc_id(self, address, orc_id, _from) -> Union[None, str]:
    address = self.w3.toChecksumAddress(address)

    if not self.w3.isAddress(_from):
        log(f"E: Account: {_from} is not a valid address")
        raise

    if not self.is_owner(_from):
        log(f"E: Account: {_from} that will call the transaction is not the owner of the contract")
        raise

    output = self.does_provider_exist(address)
    if not self.does_requester_exist(address) and not output:
        log(f"E: Address: {address} is not registered")
        raise

    if len(orc_id) != 19:
        log("E: orc_id length is not 19")
        raise

    if not orc_id.replace("-", "").isdigit():
        log("E: orc_id contains characters")
        raise

    if not self.eBlocBroker.functions.isOrcIDVerified(address).call():
        try:
            tx = self.eBlocBroker.functions.authenticateOrcID(address, str.encode(orc_id)).transact(
                {"from": _from, "gas": 4500000}
            )
            return tx.hex()
        except Exception:
            logging.error(_colorize_traceback)
            raise
    else:
        logging.warning(f"\nAddress: {address} that has orc_id: {orc_id} is already authenticated")
        return None


if __name__ == "__main__":
    import eblocbroker.Contract as Contract

    Ebb = Contract.eblocbroker
    if len(sys.argv) == 3:
        address = str(sys.argv[1])
        orc_id = str(sys.argv[2])
    else:
        log("E: Please provide the address and its orc_id as argument.\n./authenticate_orc_id.py <address> <orc_id>")
        sys.exit(1)
        """
        ./authenticate_orc_id.py 0x12ba09353d5C8aF8Cb362d6FF1D782C1E195b571 0000-0001-7642-1234  # home-1
        ./authenticate_orc_id.py 0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49 0000-0001-7642-0552  # home-2
        ./authenticate_orc_id.py 0x57b60037B82154eC7149142c606bA024fBb0f991 0000-0001-7642-0552  # netlab-cluster
        """
    try:
        tx_hash = Ebb.authenticate_orc_id(address, orc_id, _from=config.w3.eth.accounts[0])
        if tx_hash:
            receipt = get_tx_status(tx_hash)
    except:
        _colorize_traceback()
