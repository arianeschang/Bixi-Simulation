import unidecode
import pandas as pd
pd.set_option('display.max_columns', None)  
import json
import datetime as dt
import mapbox
from mapbox import Directions
import os
from geojson import Point

def load_station_data():

	json_data=open('stations.json').read()
	station_data = json.loads(json_data)['data']['stations']

	data_tuples = []

	for station in station_data:
		station_cross_street = unidecode.unidecode(station['name'])
		data_tuples.append((int(station['short_name']), station['lon'], 
			station['lat'], station_cross_street))

	station_df = pd.DataFrame.from_records(data_tuples, columns = ('station_id', 'station_long',
		'station_lat', 'station_cross_street'))
	return station_df

def load_trip_data(trip_file, station_df):
	trip_df = pd.read_csv(trip_file)
	trip_df = trip_df.drop(['is_member', 'duration_sec'], axis = 1)
	trip_df['start_date'] = pd.to_datetime(trip_df['start_date'] )
	trip_df['end_date'] = pd.to_datetime(trip_df['start_date'] )

	# Merge coordinates on start trip, delte unnecessary columns
	merged_data = pd.merge(left=trip_df,right=station_df, how='left', 
		left_on=['start_station_code'] , right_on=['station_id'])
	merged_data = merged_data.drop(['station_id'], 1)
	merged_data = merged_data.rename(index=str, columns={'station_long': 'start_long', 'station_lat': 'start_lat', 
		'station_cross_street': 'start_x_street'})

	# Merge coordinates on end station
	merged_data = pd.merge(left=merged_data,right=station_df, how='left', 
		left_on=['end_station_code'] , right_on=['station_id'])
	merged_data = merged_data.drop(['station_id'], 1)
	merged_data = merged_data.rename(index=str, columns={'station_long': 'end_long', 'station_lat': 'end_lat',
		'station_cross_street': 'end_x_street'})

	return merged_data


def get_directions(trips):
	key = 'pk.eyJ1IjoiYXJpYW5lc2NoYW5nIiwiYSI6ImNqaGIwM3VidzB0M2UzMHFwZWRtbGR6bzIifQ.PnGzkOpLBIJJEeOwWVOhLg'
	service = Directions(access_token=key)

	directions_file = open('directions.txt', 'a')

	print trips.iloc[[0]]

	for ix, row in trips.iterrows():
		origin = Point((row['start_long'], row['start_lat']))
		destination = Point((row['end_long'], row['end_lat']))

		print origin
		print type(origin)
		print destination

		
		response = service.directions([origin, destination], 'mapbox.cycling')
		print response
		print response.status_code
		print response.headers
		break

  	#json.dump(data, f, ensure_ascii=False)

	



def main():

	station_df = load_station_data()
	trips = load_trip_data('bike_data_apr_28.csv', station_df)
	get_directions(trips)

	





if __name__ == "__main__":
    main()