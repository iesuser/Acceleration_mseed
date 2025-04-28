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
FDSN_CLIENT = Client("http://10.0.0.249:8080")

STATION_DICT = {'AKHA':'AKHN', 'ALIA':'ALIG', 'KHMA':'KHMG', 'LGDA':'LGDN', 'LPNA':'LPNG', 'MUGA':'MUGD', 'SHTA':'SHTL', 'VSHA':'VSHL'}
EXPORT_ST_VELOCITY = set()
CHANNEL_VEL = 'HH*'
UNIT_VEL = "VEL"

# მონაცემების პარამეტრები
NETWORK = 'GO'
STATIONS = '*'
LOCATION = '*'
CHANNEL_ACC = 'HN*'
UNIT_ACC = "ACC"
G_THRESHOLD = 0.001  # G ერთეულში

def export_velocity():
    if EXPORT_ST_VELOCITY:
        inventory_vel = FDSN_CLIENT.get_stations(network=NETWORK, station=STATIONS, location=LOCATION, channel=CHANNEL_VEL, starttime=START_TIME, endtime=END_TIME, level="response")
        for station in EXPORT_ST_VELOCITY:
            try:
                # ვიღებთ ტალღის ფორმებს
                st_vel = FDSN_CLIENT.get_waveforms(NETWORK, station, LOCATION, CHANNEL_VEL, START_TIME, END_TIME)
                if len(st_vel) == 0:
                    logger.debug(f"არ არსებობს ჩანაწერი სადგურისთვის: {station}")
                    continue

                # ვიღებთ სადგურის შესაბამის დეტალებს
                st_vel_inv = inventory_vel.select(network=NETWORK, station=station, channel=CHANNEL_VEL)

                if not st_vel_inv or len(st_vel_inv) == 0:
                    logger.warning(f"არ არის შესაბამისი response მონაცემები სადგურისთვის {station}. ვტოვებთ...")
                    continue

                # ვშლით ინსტრუმენტულ პასუხს (response) და ვცვლით ერთეულს
                st_vel.remove_response(inventory=st_vel_inv, output=UNIT_VEL.upper(), water_level=0.0)
                
                WORK_DIR = f'{TEMP_DIR}/{str(ORIGIN_TIME)[:4]}/{NETWORK}/{ORIGIN_TIME}/{station}'
                os.makedirs(WORK_DIR, exist_ok=True)
                logger.debug(f"ქვედირექტორია შექმნილია ან უკვე არსებობს: {WORK_DIR}")

                for tr in st_vel:
                    try:
                        filename = f'{ORIGIN_TIME}_{tr.stats.network}_{tr.stats.station}_{tr.stats.channel}'
                        st_file_path = os.path.join(WORK_DIR, f'{filename}.ascii')
                        logger.debug(f"ინახება: {st_file_path}")
                        tr.write(st_file_path, format='TSPAIR')
                    except Exception as err:
                        logger.exception(f"შეცდომა ჩანაწერის ({tr.stats.station}) შენახვისას: {err}")

            except Exception as err:
                logger.warning(f"შეცდომა სადგურის ({station}) მონაცემების დამუშავებისას: {err}")
                continue
    else:
        logger.warning("არცერთი სადგურიდან არ ვიწერთ სიჩქარის მონაცემებს")

def collect_acceleration():
    try:
        # სადგურების ინფრომაციის წამოღება
        inventory = FDSN_CLIENT.get_stations(network=NETWORK, station=STATIONS, location=LOCATION, channel=CHANNEL_ACC, starttime=START_TIME, endtime=END_TIME, level="response")
        more_g_threshold = {}  # initialize dictionary
        acceleration_data = []  # სიის შექმნა აჩქარების შესანახად

        for network in inventory:
            for station in network:
                try:
                    # თუ სადგურის კოდი არ არის, ვტოვებთ გამოტოვებით
                    if not station.code:
                        logger.warning("გამოტოვებულია სადგური, რომელსაც არ აქვს კოდი")
                        continue

                    # ვიღებთ ტალღის ფორმებს
                    st = FDSN_CLIENT.get_waveforms(NETWORK, station.code, LOCATION, CHANNEL_ACC, START_TIME, END_TIME)

                    if len(st) == 0:
                        logger.debug(f"არ არსებობს ჩანაწერი სადგურისთვის: {station.code}")
                        continue

                    # ვიღებთ სადგურის შესაბამის დეტალებს
                    station_inv = inventory.select(network=NETWORK, station=station.code, channel=CHANNEL_ACC)

                    if not station_inv or len(station_inv) == 0:
                        logger.warning(f"არ არის შესაბამისი response მონაცემები სადგურისთვის {station.code}. ვტოვებთ...")
                        continue

                    # ვშლით ინსტრუმენტულ პასუხს (response) და ვცვლით ერთეულს
                    st.remove_response(inventory=station_inv, output=UNIT_ACC.upper(), water_level=0.0)

                    export_station_data = False  # მონაცემების შენახვის საჭიროება
                    max_g = 0.0  # მაქსიმალური აჩქარების მნიშვნელობა

                    for tr in st:
                        g_acc = tr.data / 9.81  # აჩქარების გადაყვანა g ერთეულში
                        max_g = np.max(np.abs(g_acc))
                        logger.debug(f"სადგურზე {station.code} დაფიქსირდა აჩქარება G: {max_g}")

                        # ვამატებთ მონაცემს საბოლოო სიაში
                        acceleration_data.append(f"{tr.stats.network}_{tr.stats.station}_{tr.stats.channel}, {max_g}")
                        key = f"{tr.stats.network}_{tr.stats.station}_{tr.stats.channel}"
                        value = (max_g)

                        # If key doesn't exist, create a new dict
                        if key not in more_g_threshold:
                            more_g_threshold[key] = {
                                "values": [],
                                "exported": False
                            }

                        more_g_threshold[key]["values"].append(value)

                        if max_g > G_THRESHOLD and not export_station_data:
                            export_station_data = True
                            if tr.stats.station in STATION_DICT:
                                EXPORT_ST_VELOCITY.add(STATION_DICT[tr.stats.station])
                            else:
                                EXPORT_ST_VELOCITY.add(tr.stats.station)

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

                        for i, stream in enumerate(st[:3]):
                            plot_path = f'{WORK_DIR}/{station.code}_{stream.stats.channel}_plot.png'
                            stream.plot(outfile=plot_path, format="png")

                        for tr in st:
                            exported_key = f"{tr.stats.network}_{tr.stats.station}_{tr.stats.channel}"
                            more_g_threshold[exported_key]["exported"] = True

                            try:
                                filename = f'{ORIGIN_TIME}_{tr.stats.network}_{tr.stats.station}_{tr.stats.channel}'
                                st_file_path = os.path.join(WORK_DIR, f'{filename}.ascii')
                                logger.debug(f"ინახება: {st_file_path}")
                                tr.write(st_file_path, format='TSPAIR')
                            except Exception as err:
                                logger.exception(f"შეცდომა ჩანაწერის ({tr.stats.station}) შენახვისას: {err}")
                                
                except Exception as err:
                    logger.warning(f"შეცდომა სადგურის ({station.code}) მონაცემების დამუშავებისას: {err}")
                    continue

        # **შენახვა Accelerations.txt ფაილში**
        WORK_DIR = f'{TEMP_DIR}/{str(ORIGIN_TIME)[:4]}/{NETWORK}/{ORIGIN_TIME}'
        os.makedirs(WORK_DIR, exist_ok=True)
        acceleration_data_txt_path = f'{TEMP_DIR}/{str(ORIGIN_TIME)[:4]}/{NETWORK}/{ORIGIN_TIME}/Accelerations.txt'
        with open(acceleration_data_txt_path, "w") as file:
            file.write(f"{ORIGIN_TIME}\n")
            file.write("Station, Max G\n")
            file.write("\n".join(acceleration_data))

        logger.info(f"Accelerations.txt ფაილი შეინახა: {acceleration_data_txt_path}")

        # **შენახვა More_G_Threshold.txt ფაილში**
        logger.debug(f"ქვედირექტორია შექმნილია ან უკვე არსებობს: {WORK_DIR}")
        more_g_threshold_txt_path = f'{TEMP_DIR}/{str(ORIGIN_TIME)[:4]}/{NETWORK}/{ORIGIN_TIME}/More_G_Threshold.txt'
        with open(more_g_threshold_txt_path, "w") as file:
            file.write(f"{ORIGIN_TIME}\n")
            file.write("Stations, Max G\n")
            for station_key, data in more_g_threshold.items():
                if data["exported"]:
                    for value in data["values"]:
                        file.write(f"{station_key}, {value:.6f}\n")
                else:
                    logger.info(f"სადგური {station_key} არ გადაცდა ზღვარს, არ შეინახა.")

        logger.info(f"More_G_Threshold.txt ფაილი შეინახა: {more_g_threshold_txt_path}")
    
    except Exception as err:
        logger.exception("მოულოდნელი შეცდომა collect_acceleration ფუნქციაში: " + str(err))

# სკრიპტის შესრულების ძირითადი ნაწილი
if __name__ == "__main__":
    try:
        collect_acceleration()
        export_velocity()
    except Exception as err:
        logger.exception("მოულოდნელი შეცდომა სკრიპტის შესრულებისას: " + str(err))