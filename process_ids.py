import unidecode
import pandas as pd
pd.set_option('display.max_columns', None)  
import json, codecs
import datetime as dt
import mapbox
from mapbox import Directions
import os
from geojson import Point
import requests
import math
import time

mbkey = 'pk.eyJ1IjoiYXJpYW5lc2NoYW5nIiwiYSI6ImNqaGIwM3VidzB0M2UzMHFwZWRtbGR6bzIifQ.PnGzkOpLBIJJEeOwWVOhLg'


def load_station_data():

	json_data=open('data/stations.json').read()
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
	trip_df = trip_df.drop(['is_member'], axis = 1)
	trip_df['start_date'] = pd.to_datetime(trip_df['start_date'] )
	trip_df['end_date'] = pd.to_datetime(trip_df['end_date'] )

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
	#service = Directions(access_token=key)

	directions_file = open('data/directions.txt', 'a')

	#trips = trips[0:5]
	#print trips

	dict_obj = {'items': []}

	for ix, row in trips.iterrows():
		print ix
		print row['start_date'].time()
		coords = get_coords(row)
		if coords == None:
			continue
		json_row = {'time': str(row['start_date'].time()), 'coords': coords}
		dict_obj['items'].append(json_row)
		if int(ix) % 10 == 0:
			with open('../arianeschang.github.io/data/coord_data.json', 'wb') as f:
				json.dump(dict_obj, codecs.getwriter('utf-8')(f), ensure_ascii=False)

	print dict_obj
	#json_obj = json.dumps(dict_obj)
	with open('../arianeschang.github.io/data/coord_data.json', 'wb') as f:
		json.dump(dict_obj, codecs.getwriter('utf-8')(f), ensure_ascii=False)


def get_coords(row):

	origin = [row['start_long'], row['start_lat']]
	destination = [row['end_long'], row['end_lat']]

	coordinate_list = []
	time.sleep(0.1)
	response = get_response(origin, destination)
	if 'routes' in response:
		steps = response['routes'][0]['legs'][0]['steps']
	else:
		time.sleep(20)
		response = get_response(origin, destination)
		if 'routes' in response:
			steps = response['routes'][0]['legs'][0]['steps']
		else:
			print 'skipping'
			print response
			return None


	eachStep = row['duration_sec']/20

	currentFirst = origin

	for i in range(len(steps)):
		if i == len(steps) - 1:
			break
		currentFirst = steps[i]['maneuver']['location']
		currentSecond = steps[i+1]['maneuver']['location']
		numSteps = int(math.ceil(steps[i]['distance']/eachStep))

		all_points = get_points(currentFirst, currentSecond, numSteps)
		coordinate_list += all_points

	coordinate_list.append(destination)
	print len(coordinate_list)
	return coordinate_list

	
def get_points(p1, p2, numPoints):
	if numPoints == 0:
		numPoints = 1
	points_to_return = []
	percentOfLine = 1/numPoints
	otherPercent = 1 - (1/numPoints)

	if numPoints == 1:
		return [p1, p2]

	for i in range(numPoints):
		i = float(i) + 1
		point_x = ((numPoints - i)/numPoints) * p1[0] + ((i/numPoints)*p2[0])
		point_y = ((numPoints - i)/numPoints) * p1[1] + ((i/numPoints)*p2[1])
		points_to_return.append([point_x, point_y])

	return points_to_return

def get_response(origin, destination):
    '''
    inputs: origin - coordinate tuple
            destination - coordinate tuple
    '''
    
    base_url = 'https://api.mapbox.com/directions/v5/mapbox/cycling/'
        
    # Constructs the url to query and returns the json response
    http_endpoint = base_url + str(origin[0]) + ',' + str(origin[1]) + ';' + \
    			 str(destination[0]) + ',' + str(destination[1]) + '?' + 'access_token=' + \
    			 str(mbkey) + '&steps=true' 
    response = requests.get(http_endpoint)
    response_json = response.json()
    return response_json


def main():

	station_df = load_station_data()
	trips = load_trip_data('data/bike_data_apr_28.csv', station_df)
	get_directions(trips)

	





if __name__ == "__main__":
    main()