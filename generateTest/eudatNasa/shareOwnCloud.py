#!/usr/bin/python


import os
from os.path import expanduser

import owncloud

path = os.getcwd()
home = expanduser("~")

# login to EUDAT account----------------------------------------

f = open(home + "/TESTS/password.txt", "r")  # password read from the file
password = f.read().strip()
f.close()
oc = owncloud.Client("https://b2drop.eudat.eu/")
oc.login("059ab6ba-4030-48bb-b81b-12115f531296", password)
password = None

# ---------------------------------------------------------------
folderNames = os.listdir(home + "/oc")
for i in range(0, len(folderNames) - 1):
    name = folderNames[i]
    print(name)
    if not oc.is_shared(name):
        oc.share_file_with_user(
            name, "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu", remote_user=True, perms=31,
        )
