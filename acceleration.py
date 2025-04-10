import sys, subprocess, glob, os
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
LOG_FILENAME = f'{LOGS_DIR_PATH}/print_acc.log'
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
FDSN_CLIENT = Client("http://192.168.11.250:8080")

# მონაცემების პარამეტრები
NETWORK = 'GO'
STATIONS = '*'
LOCATION = '*'
CHANNEL = 'HN*'
UNIT = "ACC"
G_TRASHOLD = 0.001  # g ერთეულში

def collect_acceleration():
    try:
        # სადგურების ინფრომაციის წამოღება
        inventory = FDSN_CLIENT.get_stations(network=NETWORK, station=STATIONS, location=LOCATION, channel=CHANNEL, starttime=START_TIME, endtime=END_TIME, level="response")
        acceleration_data = []  # სიის შექმნა აჩქარების შესანახად

        for network in inventory:
            for station in network:
                try:
                    # თუ სადგურის კოდი არ არის, ვტოვებთ გამოტოვებით
                    if not station.code:
                        logger.warning("გამოტოვებულია სადგური, რომელსაც არ აქვს კოდი")
                        continue

                    # ვიღებთ ტალღის ფორმებს
                    st = FDSN_CLIENT.get_waveforms(NETWORK, station.code, LOCATION, CHANNEL, START_TIME, END_TIME)

                    if len(st) == 0:
                        logger.debug(f"არ არსებობს ჩანაწერი სადგურისთვის: {station.code}")
                        continue

                    # ვიღებთ სადგურის შესაბამის დეტალებს
                    station_inv = inventory.select(network=NETWORK, station=station.code, channel=CHANNEL)

                    if not station_inv or len(station_inv) == 0:
                        logger.warning(f"არ არის შესაბამისი response მონაცემები სადგურისთვის {station.code}. ვტოვებთ...")
                        continue

                    # ვშლით ინსტრუმენტულ პასუხს (response) და ვცვლით ერთეულს
                    st.remove_response(inventory=station_inv, output=UNIT.upper())

                    export_station_data = False  # მონაცემების შენახვის საჭიროება
                    max_g = 0.0  # მაქსიმალური აჩქარების მნიშვნელობა

                    for tr in st:
                        g_acc = tr.data / 9.81  # აჩქარების გადაყვანა g ერთეულში
                        max_g = np.max(np.abs(g_acc))
                        logger.debug(f"სადგურზე {station.code} დაფიქსირდა აჩქარება G: {max_g}")
                        # ვამატებთ მონაცემს საბოლოო სიაში
                        acceleration_data.append(f"{tr.stats.network}_{tr.stats.station}_{tr.stats.channel}, {max_g}")

                        if max_g > G_TRASHOLD and export_station_data == False:
                            export_station_data = True

                    if export_station_data:
                        WORK_DIR = f'{TEMP_DIR}/{str(ORIGIN_TIME)[:4]}/{NETWORK}/{ORIGIN_TIME}/{station.code}'
                        os.makedirs(WORK_DIR, exist_ok=True)
                        logger.debug(f"ქვედირექტორია შექმნილია ან უკვე არსებობს: {WORK_DIR}")

                        # **შენახვა XML ფაილში**
                        # station_inv_file = f"{WORK_DIR}/{station.code}_station_inv.xml"
                        # try:
                        #     station_inv.write(station_inv_file, format="STATIONXML")
                        #     logger.info(f"შენახულია სადგურის ინფო: {station_inv_file}")
                        # except Exception as err:
                        #     logger.exception(f"შეცდომა სადგურის ({station.code}) ინფოს შენახვისას: {err}")

                        for tr in st:
                            try:
                                filename = f'{ORIGIN_TIME}_{round(max_g, 5)}_{tr.stats.network}_{tr.stats.station}_{tr.stats.channel}'
                                st_file_path = f'{WORK_DIR}/{filename}.ascii'
                                logger.debug(f"ინახება: {st_file_path}")

                                tr.write(st_file_path, format='TSPAIR')

                            except Exception as err:
                                logger.exception(f"შეცდომა ჩანაწერის ({tr.stats.station}) შენახვისას: {err}")

                except Exception as err:
                    logger.warning(f"შეცდომა სადგურის ({station.code}) მონაცემების დამუშავებისას: {err}")
                    continue

        # **შენახვა Acceleration.txt ფაილში**
        final_txt_path = f'{TEMP_DIR}/{str(ORIGIN_TIME)[:4]}/{NETWORK}/{ORIGIN_TIME}/Acceleration.txt'
        with open(final_txt_path, "w") as file:
            file.write("Station, Max G\n")
            file.write("\n".join(acceleration_data))

        logger.info(f"Acceleration.txt ფაილი შეინახა: {final_txt_path}")
    
    except Exception as err:
        logger.exception("მოულოდნელი შეცდომა collect_acceleration ფუნქციაში: " + str(err))

# სკრიპტის შესრულების ძირითადი ნაწილი
if __name__ == "__main__":
    try:
        collect_acceleration()
    except Exception as err:
        logger.exception("მოულოდნელი შეცდომა სკრიპტის შესრულებისას: " + str(err))