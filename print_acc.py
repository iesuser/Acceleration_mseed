#/home/sysop/Desktop/work/attenuation_plotting/virt_env/convert_sesmic_data/bin/python3
# -*- coding: utf-8 -*-
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import os, glob

from print_and_log import print_and_log

client = Client("http://192.168.11.250:8080") 				# Static 
script_path = os.path.dirname(os.path.realpath(__file__))	# Static

network = "GO" 		# Static
location = "20"		# Static
channel = "HN*"		# Static
unit = "ACC"		# static

# ფუნქცია რომელიც იწერს მიწისძვრებს მითითებული სადგურის მიხედვით ხსნის რესფონს და ინახავს ფაილს Mseed ფორმატში თუ გადააჭარბებს მაქსიმალურ აჩქარებას
def print_wave_and_acc(stations: dict, event_data: dict) -> None:
	st_file_path = script_path + f"/temp/"
	public_event_id = event_data["Event_id"]
	magnitude = event_data["Mag"]
	starttime = UTCDateTime(event_data["Time"])
	year = starttime.strftime('%Y')
	endtime = starttime + 5
	otd = starttime

	# glob გვეხმარება შევამოწმოთ მითითებულ ადგილას გვაქვს თუ არა სახელის გამეორება.
	pattern = f'{st_file_path}/{year}/{network}/{public_event_id}*'
	if glob.glob(pattern):
		print("Subdirectory already exists.")
		exit(0)
  
	try:
		inventory = client.get_stations(network='GO',station='*',location='20',channel=channel,starttime=starttime,endtime=endtime, level="response")
	except Exception as err:
		print_and_log("შეცდომა ფუნქცია client.get_stations გამოძახების დროს: " + str(err))
		
	for station , value in stations.items():

		try:
			st = client.get_waveforms(network,station,location,channel,UTCDateTime(value["Time"]),UTCDateTime(value["Time"]) + 10)
			station_inv = inventory.select(network=network,station=station,channel=channel)
			st.remove_response(inventory=station_inv, output=unit.upper(), zero_mean=True)
		except Exception as err:
			print_and_log("შეცდომა მითითებული სადგურის მონაცემების მიხედვით არ არსებობს ჩანაწერი:   " + str(err))
			continue

		if not os.path.exists(f'{st_file_path}/{year}/{network}/{public_event_id}_{otd}_{magnitude}/{station}'):
			os.makedirs(f'{st_file_path}/{year}/{network}/{public_event_id}_{otd}_{magnitude}/{station}')
			print_and_log("Subdirectory created successfully.")
		else:
			print_and_log("Subdirectory already exists.")
			exit(0)

		for trace in st:
			try:
				print(UTCDateTime(value["Time"]))
				st_file_path = f'{st_file_path}{year}/{network}/{public_event_id}_{otd}_{magnitude}/{trace.stats.station}/'
				filename = f'{UTCDateTime(value["Time"])}_{magnitude}_{trace.stats.network}_{trace.stats.station}_{trace.stats.channel}'
				st_file_path = f'{st_file_path}{filename}'
				trace.write(st_file_path + ".MSEED", format='MSEED')
				st_file_path = script_path + "/temp/"
			except Exception as err:
				print_and_log("შეცდომა: " + str(err))
