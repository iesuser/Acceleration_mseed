import sys, os
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import numpy as np
import logging
from logging.handlers import RotatingFileHandler

# სკრიპტის სამუშაო დირექტორია
SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

# მიწისძვრის დრო, რომელიც გადაეცემა როგორც არგუმენტი
ORIGIN_TIME = UTCDateTime(sys.argv[1])
START_TIME = ORIGIN_TIME - 120  # 120 წამით ადრე
END_TIME = ORIGIN_TIME + 180  # 180 წამით გვიან

# დროებითი ფაილების დირექტორია
TEMP_DIR = f"{SCRIPT_PATH}/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# ლოგ ფაილების მისამართი
LOGS_DIR_PATH = f"{SCRIPT_PATH}/logs"
os.makedirs(LOGS_DIR_PATH, exist_ok=True)

# ლოგირების კონფიგურაცია
LOG_FILENAME = f'{LOGS_DIR_PATH}/vel2_acc.log'
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3  # მაქსიმუმ 3 სარეზერვო ლოგ ფაილი

# ლოგ ფაილის როტაციის კონფიგურაცია
rotating_handler = RotatingFileHandler(LOG_FILENAME, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
rotating_handler.setFormatter(formatter)

# ლოგერის კონფიგურაცია
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(rotating_handler)

# სეისმური სადგურის მონაცემების მისაღები სერვერი
FDSN_CLIENT = Client("http://10.0.0.249:8080")

station_code = 'TBLG'
station_channel = 'HH*'
CHANNEL_VEL = 'HH*'
UNIT_VEL = "VEL"

# მონაცემების პარამეტრები
NETWORK = 'GO'
STATIONS = '*'
LOCATION = '*'
CHANNEL_ACC = 'HN*'
UNIT_ACC = "ACC"
G_THRESHOLD = 0.001  # G ერთეულში

inventory_vel = FDSN_CLIENT.get_stations(network=NETWORK, station=STATIONS, location=LOCATION, channel=CHANNEL_VEL, starttime=START_TIME, endtime=END_TIME, level="response")

