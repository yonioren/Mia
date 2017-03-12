#! /usr/bin/python
from MiaLBUpdater import mialb_update_farm
from threading import Thread

update = Thread(target=mialb_update_farm.conf_file_order, kwargs={})

from api_router import api_router as application
update.start()
#from . import *
