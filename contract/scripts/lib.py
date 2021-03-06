#!/usr/bin/env python3

import os
import sys
from os import path, popen
from pprint import pprint
from typing import Dict, List

from web3.logs import DISCARD

import config
import eblocbroker.Contract as Contract
import libs.git as git
from config import QuietExit
from lib import get_tx_status
from utils import (
    CacheType,
    StorageID,
    _colorize_traceback,
    bytes32_to_ipfs,
    empty_bytes32,
    is_geth_account_locked,
    log,
    silent_remove,
)

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))


class DataStorage:
    def __init__(self, ebb, w3, provider, source_code_hash, is_brownie=False) -> None:
        if is_brownie:
            output = ebb.getJobStorageTime(provider, source_code_hash)
        else:
            if not w3.isChecksumAddress(provider):
                provider = w3.toChecksumAddress(provider)

            output = ebb.functions.getJobStorageTime(provider, source_code_hash).call({"from": provider})

        self.received_block = output[0]
        self.storage_duration = output[1]
        self.is_private = output[2]
        self.is_verified_used = output[3]


class Job:
    """Object for the job that will be submitted."""

    def __init__(self, **kwargs) -> None:
        self.run_time: List[int] = []
        self.folders_to_share: List[str] = []  # path of folder to share
        self.source_code_hashes: List[bytes] = []
        self.storage_hours: List[int] = []
        self.storage_ids: List[int] = []
        self.cache_types: List[int] = []
        self.run_time = []
        self.Ebb = Contract.eblocbroker
        self.keys = {}  # type: Dict[str, str]
        self.foldername_tar_hash = {}  # type: Dict[str, str]
        self.tar_hashes = {}  # type: Dict[str, str]
        self.base_dir = ""

        for key, value in kwargs.items():
            setattr(self, key, value)

    def analyze_tx_status(self, tx_hash) -> bool:
        try:
            tx_receipt = get_tx_status(tx_hash)
            try:
                processed_logs = self.Ebb.eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
                pprint(vars(processed_logs[0].args))
                log(f"==> job_index={processed_logs[0].args['index']}")
            except IndexError:
                log("E: Transaction is reverted")
            return True
        except Exception as e:
            log(str(e), color="red")
            _colorize_traceback()
            return False

    def check(self):
        try:
            assert len(self.cores) == len(self.run_time)
            assert len(self.source_code_hashes) == len(self.storage_hours)
            assert len(self.storage_hours) == len(self.storage_ids)
            assert len(self.cache_types) == len(self.storage_ids)

            for idx, storage_id in enumerate(self.storage_ids):
                assert storage_id <= 4
                if storage_id == StorageID.IPFS:
                    assert self.cache_types[idx] == CacheType.PUBLIC
        except:
            _colorize_traceback()
            raise

    def set_cache_types(self, types) -> None:
        self.cache_types = types
        for idx, storage_id in enumerate(self.storage_ids):
            if storage_id == StorageID.IPFS_GPG:
                self.cache_types[idx] = CacheType.PRIVATE

    def generate_git_repos(self):
        git.generate_git_repo(self.folders_to_share)

    def clean_before_submit(self):
        for folder in self.folders_to_share:
            silent_remove(os.path.join(folder, ".mypy_cache"), is_warning=False)

    def check_account_status(self, account_id):
        _Ebb = Contract.eblocbroker
        try:
            _from = _Ebb.account_id_to_address(account_id)
            if is_geth_account_locked(_from):
                log(f"E: Account({_from}) is locked")
                raise QuietExit

            if not _Ebb.eBlocBroker.functions.doesRequesterExist(_from).call():
                log(f"E: Requester's Ethereum address {_from} is not registered")
                sys.exit(1)

            *_, orcid = _Ebb.eBlocBroker.functions.getRequesterInfo(_from).call()
            if not _Ebb.eBlocBroker.functions.isOrcIDVerified(_from).call():
                if orcid != empty_bytes32:
                    log(f"E: Requester({_from})'s orcid: {orcid.decode('UTF')} is not verified")
                else:
                    log(f"E: Requester({_from})'s orcid is not registered")
                raise QuietExit
        except QuietExit:
            sys.exit(1)
        except:
            _colorize_traceback()
            sys.exit(1)


class JobPrices:
    def __init__(self, job, msg_sender, is_brownie=False):
        self.ebb = config.ebb
        self.w3 = config.w3
        self.msg_sender = msg_sender
        self.is_brownie = is_brownie
        self.computational_cost = 0
        self.job_price = 0
        self.cache_cost = 0
        self.storage_cost = 0
        self.data_transfer_in_sum = 0
        self.job_price = 0
        self.cost = dict()
        self.data_transfer_cost = None

        if is_brownie:
            provider_info = self.ebb.getProviderInfo(job.provider, 0)
        else:  # real chain
            if self.ebb.functions.doesProviderExist(job.provider).call():
                provider_info = self.ebb.functions.getProviderInfo(job.provider, 0).call()
            else:
                log(f"E: {job.provider} does not exist as a provider", "red")
                raise QuietExit

        provider_price_info = provider_info[1]
        self.job = job
        self.price_core_min = provider_price_info[2]
        self.price_data_transfer = provider_price_info[3]
        self.price_storage = provider_price_info[4]
        self.price_cache = provider_price_info[5]

    def set_computational_cost(self):
        self.computational_cost = 0
        for idx, core in enumerate(self.job.cores):
            self.computational_cost += int(self.price_core_min * core * self.job.run_time[idx])

    def set_storage_cost(self):
        """Calculating the cache cost."""
        self.storage_cost = 0
        self.cache_cost = 0
        data_transfer_in_sum = 0
        for idx, source_code_hash in enumerate(self.job.source_code_hashes):
            ds = DataStorage(self.ebb, self.w3, self.job.provider, source_code_hash, self.is_brownie)
            if self.is_brownie:
                received_storage_deposit = self.ebb.getReceivedStorageDeposit(
                    self.job.provider, self.job.requester, source_code_hash
                )
            else:
                received_storage_deposit = self.ebb.functions.getReceivedStorageDeposit(
                    self.job.provider, self.job.requester, source_code_hash
                ).call({"from": self.msg_sender})

            if ds.received_block + ds.storage_duration < self.w3.eth.blockNumber:
                # storage time is completed
                received_storage_deposit = 0

            print(f"is_private:{ds.is_private}")
            # print(received_block + storage_duration >= self.w3.eth.blockNumber)
            # if received_storage_deposit > 0 or
            if (
                received_storage_deposit > 0 and ds.received_block + ds.storage_duration >= self.w3.eth.blockNumber
            ) or (
                ds.received_block + ds.storage_duration >= self.w3.eth.blockNumber
                and not ds.is_private
                and ds.is_verified_used
            ):
                print(f"For {bytes32_to_ipfs(source_code_hash)} cost of storage is not paid")
            else:
                if self.job.data_prices_set_block_numbers[idx] > 0:
                    # if true, registered data's price should be considered for storage
                    output = self.ebb.getRegisteredDataPrice(
                        self.job.provider, source_code_hash, self.job.data_prices_set_block_numbers[idx],
                    )
                    data_price = output[0]
                    self.storage_cost += data_price
                    break

                #  if not received_storage_deposit and (received_block + storage_duration < w3.eth.blockNumber):
                if not received_storage_deposit:
                    data_transfer_in_sum += self.job.data_transfer_ins[idx]
                    if self.job.storage_hours[idx] > 0:
                        self.storage_cost += (
                            self.price_storage * self.job.data_transfer_ins[idx] * self.job.storage_hours[idx]
                        )
                    else:
                        self.cache_cost += self.price_cache * self.job.data_transfer_ins[idx]
        self.data_transfer_in_cost = self.price_data_transfer * data_transfer_in_sum
        self.data_transfer_out_cost = self.price_data_transfer * self.job.dataTransferOut
        self.data_transfer_cost = self.data_transfer_in_cost + self.data_transfer_out_cost

    def set_job_price(self):
        self.job_price = self.computational_cost + self.data_transfer_cost + self.cache_cost + self.storage_cost
        log(f"job_price={self.job_price}", "blue")
        self.cost["computational"] = self.computational_cost
        self.cost["cache"] = self.cache_cost
        self.cost["storage"] = self.storage_cost
        self.cost["data_transfer_in"] = self.data_transfer_in_cost
        self.cost["data_transfer_out"] = self.data_transfer_out_cost
        self.cost["data_transfer"] = self.data_transfer_cost
        for key, value in self.cost.items():
            if key == "data_transfer":
                log(
                    f"\t=> {key}={value} <=> [in:{self.cost['data_transfer_in']} out:{self.cost['data_transfer_out']}]",
                    color="blue",
                )
            else:
                if key not in ("data_transfer_out", "data_transfer_in"):
                    log(f"\t=> {key}={value}", "blue")


def cost(provider, requester, job, is_brownie=False):
    called_filename = path.basename(sys._getframe(1).f_code.co_filename)
    if called_filename.startswith("test_"):
        is_brownie = True

    print("\nEntered into the cost calculation...")
    job.provider = provider
    job.requester = requester
    job.check()

    jp = JobPrices(job, provider, is_brownie)
    jp.set_computational_cost()
    jp.set_storage_cost()
    jp.set_job_price()
    return jp.job_price, jp.cost


def new_test():
    try:
        *_, columns = popen("stty size", "r").read().split()
    except:
        columns = 20

    line = "-" * int(columns)
    print(f"\x1b[6;30;43m{line}\x1b[0m")
