#!/home/sysop/Desktop/work/attenuation_plotting/virt_env/obspyenv/bin/python3
import xml.etree.ElementTree as ET
import sys, subprocess, glob, os
from obspy.geodetics.base import gps2dist_azimuth
from obspy import UTCDateTime
from datetime import datetime, timedelta

from print_acc import print_wave_and_acc
from print_and_log import print_and_log

acc_limit = 0.00001  # აჩქარების მაჩვენებლის ლიმიტი.
ip_address = "192.168.11.250"
script_path = os.path.dirname(os.path.realpath(__file__))
shakemaps_path = './shakemaps'

def get_stations(public_event_id: str) -> dict:
    station_names = {}
    try:
        # დაკავშირება მიწისძვრის xml თან.
        xml_file_path = f'{shakemaps_path}/{public_event_id}/input/event_dat.xml'
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        ns = {"ns": "ch.ethz.sed.shakemap.usgs.xml"}
    except Exception as err:
        print_and_log("შეცდომა event_data.xml თან დაკავშირების დროს: " + str(err))
        return station_names, {}

    # ციკლი რომელიც გვეხმარება სათითაოდ შევამოწმოთ სადგური და ამოვიღოთ საჭირო მონაცემები.
    for station in root.findall("ns:station", ns):
        try:
            netid = station.get("netid")
            if netid == "GO":
                acc_values = []
                for comp in station.findall('ns:comp', ns):
                    acc = comp.find('ns:acc', ns)
                    acc_values.append(acc.attrib.get('value'))

                max_acc = float(max(acc_values))
                if max_acc > acc_limit:
                    station_names[station.get("name")] = {
                        "Lat": station.get("lat"),
                        "Lon": station.get("lon"),
                        "Max": max_acc
                    }
        except Exception as err:
            print_and_log("შეცდომა event_data.xml დან მონაცემების ამოღების დროს: " + str(err))

    # მიწისძვრის მონაცემების მოგროვება event.xml დან...
    try:
        # დაკავშირება მიწისძვრის თავთან(header) სადაც გვაქვს მიწისძვრის მონაცემები.
        event_data = f'{shakemaps_path}/{public_event_id}/input/event.xml'
        event = ET.parse(event_data)
        data = event.getroot()
    except Exception as err:
        print_and_log("შეცდომა event.xml თან დაკავშირების დროს: " + str(err))
        return station_names, {}

    try:
        # მიწისძვრის საჭირო მონაცემების ამოღება.
        year = int(data.attrib.get("year"))
        month = int(data.attrib.get("month"))
        day = int(data.attrib.get("day"))
        hour = int(data.attrib.get("hour"))
        minute = int(data.attrib.get("minute"))
        second = int(data.attrib.get("second"))
        event_time = UTCDateTime(year, month, day, hour, minute, second)
        event_data = {
            "Event_id": public_event_id,
            "Time": f'{event_time}',
            "Lat": data.attrib.get("lat"),
            "Lon": data.attrib.get("lon"),
            "Mag": data.attrib.get("mag")
        }
    except Exception as err:
        print_and_log("შეცდომა event.xml დან მონაცემების ამოღების დროს: " + str(err))
        return station_names, {}

    # სადგურის მონაცემების და მიწისძვრის მონაცემების დაბრუნება.
    print_and_log("ფუნქცია get_stations წარმატებით დასრულდა.")
    return station_names, event_data

# მოცემული ფუნქცია ადარებს სადგურებს dump - ით მოჭრილ xml ში მყოფ სადგურებს. 
def compare_stations(station_names: dict, public_event_id: str) -> dict:
    names_in = {}
    try:
        command = ["scxmldump", "-fPAMFJ", "-E", public_event_id, "-o", f"./dump/{public_event_id}.xml", "-d", f"{ip_address}"]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print_and_log("შეცდომა scxmlxml dump ის მოჭრისას: " + str(result.stderr))
            return station_names, {}

        xml_file_path = f'./dump/{public_event_id}.xml'
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        ns = {'ns': 'http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.13'}
    except Exception as err:
        print_and_log("შეცდომა dump xml თან დაკაშირების დროს: " + str(err))
        return station_names, {}

    try:
        for pick in root.findall('.//ns:pick', ns):
            waveform_id = pick.find('ns:waveformID', ns)
            network_code = waveform_id.attrib.get('networkCode')

            if network_code == "GO":
                name = waveform_id.attrib.get('stationCode')
                if name in station_names:
                    time_tag = pick.find('ns:time', ns)
                    time_value = time_tag.find('ns:value', ns).text

                    names_in[name] = station_names[name]
                    names_in[name]['Time'] = str(time_value)
                    del station_names[name]
    except Exception as err:
        print_and_log("შეცდომა სადგურების შედარების დროს: " + str(err))

    # ./dump ფოლდერის გასუფთავება...
    try:
        files = glob.glob(os.path.join("./dump", '*'))
        for f in files:
            os.remove(f)
    except Exception as err:
        print_and_log(f"შეცდომა ./dump ფოლდერიდან ფაილის წაშლის დროს: ფაილის სახელი: {f} :  {err}")

    print_and_log("ფუნქცია compare_stations წარმატებით დასრულდა.")
    return station_names, names_in

# ფუნქცია რომელიც თვლის მიწისძვრის ზუსტ დროს რომელიც დაფიქსირდა სადგურზე. 
def get_distance_between_station_and_earthquake(station: dict, event_data: dict) -> dict:
    try:
        origin_time = event_data["Time"]
        origin_time_dt = datetime.strptime(origin_time, '%Y-%m-%dT%H:%M:%S.%fZ')
    except Exception as err:
        print_and_log("შეცდომა დროის კონვერტაციის დროს: " + str(err))
        return station

    lat = float(event_data["Lat"])  # მიწისძვრის გრძედი 
    lon = float(event_data["Lon"])  # მიწისძვრის განედი
    p_wave_speed = 6e3  # STATIC
    try:
        for station_name, coordinates in station.items():
            distance, azimuth1, azimuth2 = gps2dist_azimuth(lat, lon, float(coordinates["Lat"]), float(coordinates["Lon"]))
            arrival_time_p = distance / p_wave_speed
            arrival_time_dt = origin_time_dt + timedelta(seconds=arrival_time_p)
            arrival_time_str = arrival_time_dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-4] + 'Z'
            station[station_name]["Time"] = str(arrival_time_str)
    except Exception as err:
        print_and_log("შეცდომა მიწისძვრის მონაცემების დამუშავების დროს: " + str(err))

    print_and_log("ფუნქცია get_distance_between_station_and_earthquake წარმატებით დასრულდა.")
    return station

# ფუნქცია main საიდანაც ხდება ყველა საჭირო ფუნქციის გამოძახება...
def main(public_event_id: str) -> str:
    station_names, event_data = get_stations(public_event_id)
    namesout, namesin = compare_stations(station_names, public_event_id)

    if namesout:
        result = get_distance_between_station_and_earthquake(namesout, event_data)
        namesin.update(result)

    print_wave_and_acc(namesin, event_data)
    return "წარმატებით დასრულდა სკრიპტის მუშაობა."

# სკრიპტის ხელით გამოსაძახებლად გამოიყენეთ ბრძანება: python3 app.py "arg1" "arg2" "public_event_id"
if __name__ == "__main__":
    try:
        public_event_id = sys.argv[3]
    except Exception as err:
        print_and_log("შეცდომა სკრიპტის გამოძახების დროს: " + str(err))
    else:
        try:
            result = main(public_event_id)
            print_and_log(result)
        except Exception as err:
            print_and_log("შეცდომა ფუნქცია main ის გამოძახების დროს: " + str(err))
