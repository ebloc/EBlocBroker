import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from shutil import copyfile
from typing import Dict, List

import eblocbroker.Contract as Contract
import libs.mongodb as mongodb
import libs.slurm as slurm
import utils
from config import ThreadFilter, env, logging
from lib import log, run
from libs.slurm import remove_user
from libs.sudo import _run_as_sudo
from libs.user_setup import add_user_to_slurm, give_RWE_access
from utils import (
    CacheType,
    Link,
    _colorize_traceback,
    bytes32_to_ipfs,
    cd,
    generate_md5sum,
    mkdir,
    read_json,
    write_to_file,
)


class BaseClass:
    def whoami(self):
        return type(self).__name__


class Storage(BaseClass):
    def __init__(self, logged_job, job_info, requester_id, is_already_cached) -> None:
        self.thread_name = uuid.uuid4().hex  # https://stackoverflow.com/a/44992275/2402577
        self.requester_id = requester_id
        self.job_info = job_info
        self.logged_job = logged_job
        self.job_key = self.logged_job.args["jobKey"]
        self.index = self.logged_job.args["index"]
        self.cores = self.logged_job.args["core"]
        self.run_time = self.logged_job.args["runTime"]
        self.job_id = 0
        self.cache_type = logged_job.args["cacheType"]
        self.data_transfer_in_requested = job_info[0]["dataTransferIn"]
        self.data_transfer_in_to_download = 0  # size_to_download
        self.is_already_cached = is_already_cached
        self.source_code_hashes: List[bytes] = logged_job.args["sourceCodeHash"]
        self.source_code_hashes_str: List[str] = [bytes32_to_ipfs(_hash) for _hash in self.source_code_hashes]
        self.job_key_list: List[str] = []
        self.md5sum_dict = {}
        self.folder_path_to_download: Dict[str, str] = {}
        self.cloudStorageID = logged_job.args["cloudStorageID"]
        self.requester_home = f"{env.PROGRAM_PATH}/{self.requester_id}"
        self.results_folder_prev = f"{self.requester_home}/{self.job_key}_{self.index}"
        self.results_folder = f"{self.results_folder_prev}/JOB_TO_RUN"
        self.run_path = f"{self.results_folder}/run.sh"
        self.results_data_folder = f"{self.results_folder_prev}/data"
        self.results_data_link = f"{self.results_folder_prev}/data_link"
        self.private_dir = f"{self.requester_home}/cache"
        self.public_dir = f"{env.PROGRAM_PATH}/cache"
        self.patch_folder = f"{self.results_folder_prev}/patch"
        self.folder_type_dict: Dict[str, str] = {}
        self.Ebb = Contract.eblocbroker
        self.drivers_log_path = f"{env.LOG_PATH}/drivers_output/{self.job_key}_{self.index}.log"
        self.start_time = None
        self.mc = None
        self.coll = None
        utils.log_files[self.thread_name] = self.drivers_log_path

        try:
            mkdir(self.private_dir)
        except PermissionError:
            give_RWE_access(env.SLURMUSER, self.requester_home)
            mkdir(self.private_dir)

        mkdir(self.public_dir)
        mkdir(self.results_folder)
        mkdir(self.results_data_folder)
        mkdir(self.results_data_link)
        mkdir(self.patch_folder)

    def thread_log_setup(self):
        import threading
        import config

        _log = logging.getLogger()  # root logger
        for hdlr in _log.handlers[:]:  # remove all old handlers
            _log.removeHandler(hdlr)

        # A dedicated per-thread handler
        thread_handler = logging.FileHandler(self.drivers_log_path, "a")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        thread_handler.setFormatter(formatter)
        # The ThreadFilter makes sure this handler only accepts logrecords that originate
        # in *this* thread, only. It needs the current thread id for this:
        thread_handler.addFilter(ThreadFilter(thread_id=threading.get_ident()))
        config.logging.addHandler(thread_handler)
        time.sleep(0.25)
        # config.logging = logging
        # _log = logging.getLogger()
        # _log.addHandler(thread_handler)
        # config.logging = _log

    def check_already_cached(self, source_code_hash):
        if os.path.isfile(f"{self.private_dir}/{source_code_hash}.tar.gz"):
            log(f"==> {source_code_hash} is already cached in {self.private_dir}", color="blue")
            self.is_already_cached[source_code_hash] = True
        elif os.path.isfile(f"{self.public_dir}/{source_code_hash}.tar.gz"):
            log(f"==> {source_code_hash} is already cached in {self.public_dir}", color="blue")
            self.is_already_cached[source_code_hash] = True

    def complete_refund(self) -> str:
        """Complete refund back to the requester."""
        try:
            tx_hash = self.Ebb.refund(
                self.logged_job.args["provider"],
                env.PROVIDER_ID,
                self.job_key,
                self.index,
                self.job_id,
                self.cores,
                self.run_time,
            )
            log(f"==> refund() tx_hash={tx_hash}")
            return tx_hash
        except:
            _colorize_traceback()
            raise

    def is_md5sum_matches(self, path, name, _id, folder_type, cache_type) -> bool:
        output = generate_md5sum(path)
        if output == name:
            # checking is already downloaded folder's hash matches with the given hash
            if self.whoami() == "EudatClass" and folder_type != "":
                self.folder_type_dict[name] = folder_type

            self.cache_type[_id] = cache_type
            if cache_type == CacheType.PUBLIC:
                self.folder_path_to_download[name] = self.public_dir
                log(f"==> {name} is already cached under the public directory...", "blue")
            elif cache_type == CacheType.PRIVATE:
                self.folder_path_to_download[name] = self.private_dir
                log(f"==> {name} is already cached under the private directory")
            return True
        return False

    def is_cached(self, name, _id) -> bool:
        if self.cache_type[_id] == CacheType.PRIVATE:
            # Checks whether it is already exist under public cache directory
            cached_folder = f"{self.public_dir}/{name}"
            cached_tar_file = f"{cached_folder}.tar.gz"

            if not os.path.isfile(cached_tar_file):
                if os.path.isfile(f"{cached_folder}/run.sh"):
                    return self.is_md5sum_matches(cached_folder, name, _id, "folder", CacheType.PUBLIC)
            else:
                if self.whoami() == "EudatClass":
                    self.folder_type_dict[name] = "tar.gz"

                return self.is_md5sum_matches(cached_tar_file, name, _id, "", CacheType.PUBLIC)
        else:
            # Checks whether it is already exist under the requesting user's private cache directory
            cached_folder = self.private_dir
            cached_folder = f"{self.private_dir}/{name}"
            cached_tar_file = f"{cached_folder}.tar.gz"
            if not os.path.isfile(cached_tar_file):
                if os.path.isfile(f"{cached_folder}/run.sh"):
                    return self.is_md5sum_matches(cached_folder, name, _id, "folder", CacheType.PRIVATE)
            else:
                if self.whoami() == "EudatClass":
                    self.folder_type_dict[name] = "tar.gz"

                return self.is_md5sum_matches(cached_tar_file, name, _id, "", CacheType.PRIVATE)

        return False

    def is_run_exists_in_tar(self, tar_path) -> bool:
        try:
            output = (
                subprocess.check_output(["tar", "ztf", tar_path, "--wildcards", "*/run.sh"], stderr=subprocess.DEVNULL,)
                .decode("utf-8")
                .strip()
            )
            if output.count("/") == 1:
                # main folder should contain the 'run.sh' file
                logging.info("./run.sh exists under the parent folder")
                return True
            else:
                logging.error("E: run.sh does not exist under the parent folder")
                return False
        except:
            logging.error("E: run.sh does not exist under the parent folder")
            return False

    def check_run_sh(self) -> bool:
        if not os.path.isfile(self.run_path):
            logging.error(f"E: {self.run_path} file does not exist")
            return False
        return True

    def sbatch_call(self):
        try:
            link = Link(self.results_data_folder, self.results_data_link)
            link.link_folders()
            # file permission for the requester's foders should be reset
            give_RWE_access(self.requester_id, self.requester_home)
            give_RWE_access(env.WHOAMI, self.requester_home)
            self._sbatch_call()
        except Exception:
            logging.error("E: Failed to call _sbatch_call() function")
            _colorize_traceback()
            raise

    def _sbatch_call(self):
        job_key = self.logged_job.args["jobKey"]
        index = self.logged_job.args["index"]
        source_code_idx = 0  # 0 indicated maps to source_sode
        main_cloud_storage_id = self.logged_job.args["cloudStorageID"][source_code_idx]
        job_info = self.job_info[0]
        job_id = 0  # base job_id for them workflow
        job_block_number = self.logged_job.blockNumber
        date = (
            subprocess.check_output(  # cmd: date --date=1 seconds +%b %d %k:%M:%S %Y
                ["date", "--date=" + "1 seconds", "+%b %d %k:%M:%S %Y"], env={"LANG": "en_us_88591"},
            )
            .decode("utf-8")
            .strip()
        )
        logging.info(f"Date={date}")
        write_to_file(f"{self.results_folder_prev}/modified_date.txt", date)

        # cmd: echo date | date +%s
        p1 = subprocess.Popen(["echo", date], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["date", "+%s"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        timestamp = p2.communicate()[0].decode("utf-8").strip()
        log(f"==> timestamp={timestamp}")
        write_to_file(f"{self.results_folder_prev}/timestamp.txt", timestamp)

        log(f"==> job_received_block_number={job_block_number}")
        logging.info("Adding recevied job into the mongodb database.")
        # write_to_file(f"{results_folder_prev}/blockNumber.txt", job_block_number)

        # adding job_key info along with its cache_duration into mongodb
        mongodb.add_item(
            job_key,
            self.index,
            self.source_code_hashes_str,
            self.requester_id,
            timestamp,
            main_cloud_storage_id,
            job_info,
        )

        # TODO: update as used_data_transfer_in value
        data_transfer_in_json = f"{self.results_folder_prev}/data_transfer_in.json"
        try:
            data = read_json(data_transfer_in_json)
        except:
            data = dict()
            data["data_transfer_in"] = self.data_transfer_in_to_download
            with open(data_transfer_in_json, "w") as outfile:
                json.dump(data, outfile)
            time.sleep(0.25)

        # seperator character is *
        sbatch_file_path = f"{self.results_folder}/{job_key}*{index}*{job_block_number}.sh"
        copyfile(f"{self.results_folder}/run.sh", sbatch_file_path)

        job_core_num = str(job_info["core"][job_id])
        # client's requested seconds to run his/her job, 1 minute additional given
        execution_time_second = timedelta(seconds=int((job_info["run_time"][job_id] + 1) * 60))

        d = datetime(1, 1, 1) + execution_time_second
        time_limit = str(int(d.day) - 1) + "-" + str(d.hour) + ":" + str(d.minute)
        logging.info(f"time_limit={time_limit} | requested_core_num={job_core_num}")
        # give permission to user that will send jobs to Slurm.
        subprocess.check_output(["sudo", "chown", "-R", self.requester_id, self.results_folder])
        for _attempt in range(10):
            try:
                """Slurm submits job
                * Real mode -N is used. For Emulator-mode -N use 'sbatch -c'
                * cmd: sudo su - $requester_id -c "cd $results_folder &&
                       sbatch -c$job_core_num $results_folder/${job_key}*${index}.sh --mail-type=ALL
                """
                cmd = f'sbatch -N {job_core_num} "{sbatch_file_path}" --mail-type=ALL'
                with cd(self.results_folder):
                    try:
                        job_id = _run_as_sudo(env.SLURMUSER, cmd, shell=True)
                    except Exception as e:
                        if "Invalid account" in str(e):
                            remove_user(env.SLURMUSER)
                            add_user_to_slurm(env.SLURMUSER)
                            job_id = _run_as_sudo(env.SLURMUSER, cmd, shell=True)
                time.sleep(1)  # wait 1 second for slurm idle core to be updated
            except Exception:
                _colorize_traceback()
                slurm.remove_user(self.requester_id)
                slurm.add_user_to_slurm(self.requester_id)
            else:
                break
        else:
            sys.exit(1)

        slurm_job_id = job_id.split()[3]  # "Submitted batch job N"
        logging.info(f"slurm_job_id={slurm_job_id}")
        try:
            run(["scontrol", "update", f"jobid={slurm_job_id}", f"TimeLimit={time_limit}"])
            # subprocess.run(cmd, stderr=subprocess.STDOUT)
        except Exception:
            _colorize_traceback()

        if not slurm_job_id.isdigit():
            logging.error("E: Detects an error on the SLURM side. slurm_job_id is not a digit")
            return False

        return True
