from flask import render_template, request
import json
import requests
from app import app
from app.databaseOperations import avg_type_size
from app.backendApi import get_past_track
from app.dataPreprocess import *
from app.calculatePollution import *

BASE_URL = '/'


@app.route(BASE_URL)
def index():
    return render_template('index.html')


@app.route(BASE_URL + 'get/shipID', methods=['GET'])
def ship_id():
    param = request.args.to_dict()
    mmsi = param['mmsi']
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    url = app.config['MARINE_TRAFFIC_SEARCH_URL'] + f"searchAsset?what=vessel&term={mmsi}"
    res = requests.get(url, headers=headers)
    id_data = json.loads(res.content.decode('utf-8'))
    if id_data:
        return {'vessel_id': id_data[0]['id']}
    else:
        return {'vessel_id': None}


@app.route(BASE_URL + 'get/shipPicture', methods=['GET'])
def ship_pic():
    param = request.args.to_dict()
    ship_id = param['ship_id']
    url = app.config['MARINE_TRAFFIC_PHOTO_URL'] + f"showphoto.aspx?shipid={ship_id}&size=thumb"
    res = requests.get(url)
    if res.status_code == 200:
        return {'ship_image': url}
    else:
        return {'ship_image': None}


@app.route(BASE_URL + 'get/pollution', methods=['GET'])
def ship_pollution():
    param = request.args.to_dict()
    mmsi = param['mmsi']

    past_track = get_past_track(mmsi)
    if len(past_track) > 1:
        processed_track = get_past_track_24(past_track)
        vessel_type = past_track[0]["vesselType"]
        avg_length, avg_width, avg_sog = avg_type_size(vessel_type)
        length, width = get_width_length(past_track[0], avg_length, avg_width)

        input_data_list = prepare_predict_data(processed_track, length, width,vessel_type)
        input_data_list_avg = prepare_predict_data(processed_track, avg_length, avg_width,vessel_type)

        # predict
        pollution_fuel = fuel_24(input_data_list)
        pollution_fuel_avg = fuel_24(input_data_list_avg)
        pollution_co2 = co2_24(pollution_fuel)
        pollution_co2_avg = co2_24(pollution_fuel_avg)

        result = {
            "mmsi": mmsi,
            "status": "successful",
            "pollution_fuel": pollution_fuel,
            "pollution_fuel_avg": pollution_fuel_avg,
            "pollution_co2": pollution_co2,
            "pollution_co2_avg": pollution_co2_avg
        }
    else:
        result = {
            "mmsi": mmsi,
            "status": "error",
        }
    return (result)


@app.route(BASE_URL + 'get/total_pollution', methods=['GET'])
def total_pollution():
    param = request.args.to_dict()
    mmsi = param['mmsi']
    past_track = get_past_track(mmsi)

    if len(past_track) > 1:

        # preprocess
        distance = get_distance(past_track)
        time_length = get_time_length(past_track)
        vessel_type = past_track[0]["vesselType"]
        type_array = get_type_array(vessel_type)
        avg_length, avg_width, avg_sog = avg_type_size(vessel_type)
        length, width = get_width_length(past_track[0], avg_length, avg_width)

        # prediction
        fuel = total_fuel(distance, time_length, length, width, type_array)
        fuel_avg = total_fuel(distance, time_length, avg_length, avg_width, type_array)
        co2 = total_CO2(fuel, distance, type_array)
        co2_avg = total_CO2(fuel_avg, distance, type_array)

        # return result
        result = {
            "mmsi": mmsi,
            "status": "successful",
            "sog": round(float(past_track[-1]["sog"]), 2),
            "sog_avg": round(avg_sog, 2),
            "width": round(width, 2),
            "width_avg": round(avg_width, 2),
            "length": round(length, 2),
            "length_avg": round(avg_length, 2),
            "total_fuel": round(fuel, 2),
            "total_fuel_avg": round(fuel_avg, 2),
            "total_co2": round(co2, 2),
            "total_co2_avg": round(co2_avg, 2),
        }
    else:
        result = {
            "mmsi": mmsi,
            "status": "error",
        }
    return result
