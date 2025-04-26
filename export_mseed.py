import sys, os
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import logging
from logging.handlers import RotatingFileHandler

# სკრიპტის სამუშაო დირექტორია
SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

# მიწისძვრის დრო, რომელიც გადაეცემა როგორც არგუმენტი
# ORIGIN_TIME = UTCDateTime(sys.argv[1])
ORIGIN_TIME = UTCDateTime("2025-03-08T11:28:25.120")

START_TIME = ORIGIN_TIME - 300  # 300 წამით ადრე
END_TIME = ORIGIN_TIME + 300    # 300 წამით გვიან

# დროებითი ფაილების დირექტორია
TEMP_DIR = os.path.join(SCRIPT_PATH, "export")
os.makedirs(TEMP_DIR, exist_ok=True)

# ლოგ ფაილების მისამართი
LOGS_DIR_PATH = os.path.join(SCRIPT_PATH, "logs")
os.makedirs(LOGS_DIR_PATH, exist_ok=True)

# ლოგირების კონფიგურაცია
LOG_FILENAME = os.path.join(LOGS_DIR_PATH, "export_mseed.log")
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

rotating_handler = RotatingFileHandler(LOG_FILENAME, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
rotating_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(rotating_handler)

# სეისმური სადგურის მონაცემების მისაღები სერვერი
FDSN_CLIENT = Client("IRIS")

# მონაცემების პარამეტრები
NETWORK = 'GO'
STATIONS = '*'
LOCATION = '*'
CHANNEL = 'HN*'

def export_mseed():
    try:
        logger.info(f"მონაცემების მოთხოვნა დაიწყო: {START_TIME} - {END_TIME}")
        st = FDSN_CLIENT.get_waveforms(NETWORK, STATIONS, LOCATION, CHANNEL, START_TIME, END_TIME)
        logger.info(f"მონაცემები მიღებულია — {len(st)} ჩანაწერი.")

        for tr in st:
            try:
                station = tr.stats.station
                channel = tr.stats.channel
                location = tr.stats.location or "00"
                network = tr.stats.network
                year_str = tr.stats.starttime.strftime('%Y')
                doy_str = tr.stats.starttime.strftime('%j')  # DOY (Day of Year)

                # დირექტორიების სტრუქტურა: export/GO/STATION/HN1.D/
                network_dir = os.path.join(TEMP_DIR, network)
                station_dir = os.path.join(network_dir, station)
                channel_dir = os.path.join(station_dir, f"{channel}.D")
                os.makedirs(channel_dir, exist_ok=True)

                # ფაილის სახელი: GO.STAT.LOC.CHAN.D.YYYY.DDD
                filename = f"{network}.{station}.{location}.{channel}.D.{year_str}.{doy_str}"
                st_file_path = os.path.join(channel_dir, filename)

                logger.info(f"ინახება ჩანაწერი: {st_file_path}")
                tr.write(st_file_path, format='MSEED')
            except Exception as err:
                logger.exception(f"შეცდომა ჩანაწერის ({tr.id}) შენახვისას: {err}")

        logger.info("ყველა ჩანაწერი წარმატებით შენახულია.")
    except Exception as err:
        logger.exception("შეცდომა ტალღური მონაცემების მიღებისას: " + str(err))


if __name__ == "__main__":
    try:
        export_mseed()
    except Exception as err:
        logger.exception("მოულოდნელი შეცდომა სკრიპტის შესრულებისას: " + str(err))
