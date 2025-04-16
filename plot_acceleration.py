from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import numpy as np

# სეისმური სადგურის მონაცემების მისაღები სერვერი
FDSN_CLIENT = Client("http://192.168.11.250:8080")
# მიწისძვრის დრო, რომელიც გადაეცემა როგორც არგუმენტი
ORIGIN_TIME = UTCDateTime("2025-03-08T11:28:25.120000")
START_TIME = ORIGIN_TIME - 120  # 120 წამით ადრე
END_TIME = ORIGIN_TIME + 180  # 180 წამით გვიან

station_code = 'DDFN'


st_inventory = FDSN_CLIENT.get_stations(network='GO', station=station_code, location='*', channel='HN*', starttime=START_TIME, endtime=END_TIME, level="response")

# ვიღებთ ტალღის ფორმებს
stream = FDSN_CLIENT.get_waveforms('GO', station_code, '*', 'HN*', START_TIME, END_TIME)
# ვშლით ინსტრუმენტულ პასუხს (response) და ვცვლით ერთეულს
stream.remove_response(inventory=st_inventory, output="ACC", plot=True)

plot_path = f"{station_code}_plot.png"
stream.plot(outfile=plot_path, format="png")  # გრაფიკის შენახვა

for tr in stream:
    g_acc = tr.data / 9.81  # აჩქარების გადაყვანა g ერთეულში
    max_g = np.max(np.abs(g_acc))

print(max_g)