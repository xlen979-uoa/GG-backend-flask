import requests
import joblib
import json
from haversine import haversine
from datetime import datetime
import math
import numpy as np

# model_co2 = joblib.load('LinearRegression_Co2.joblib')
# model_fuel = joblib.load('RandomForest_Fuel.joblib')
model_co2 = joblib.load('New_LinearRegression_Co2.joblib')
model_fuel = joblib.load('New_LinearRegression_Fuel.joblib')
def get_past_track(mmsi,interval=60):
    url = f"http://13.236.117.100:8888/rest/v1/ship/history/{mmsi}/{interval}"
    res = requests.get(url)
    data = json.loads(res.content.decode('utf-8'))
    past_track = data["data"]
    return past_track


def get_distance(past_track):
    if len(past_track) > 1:
        start_point = (float(past_track[0]["latitude"]), float(past_track[0]["longitude"]))
        end_point = (float(past_track[-1]["latitude"]), float(past_track[-1]["longitude"]))
        distance = haversine(start_point, end_point)
    else:
        distance = 0
    return distance


def get_time_length(past_track):
    fmt = '%Y-%m-%d %H:%M:%S'
    if len(past_track) > 1:
        start_time = datetime.strptime(past_track[0]["dtPosUtc"], fmt)
        end_time = datetime.strptime(past_track[-1]["dtPosUtc"], fmt)
        time_length = end_time - start_time
        time_length = time_length.total_seconds() / 3600  # hour
    else:
        time_length = 0
    return time_length


def get_type_array(ship_type):
    """
    :param ship_type:
    :return:  one hot vector for prediction
    """
    type_dict = {
        "Cargo":[1, 0, 0, 0, 0],
        "Other": [0, 1, 0, 0, 0],
        "Passenger": [0, 0, 1, 0, 0],
        "Ships Not Party to Armed Conflict": [0, 0, 0, 1, 0],
        "Tanker": [0, 0, 0, 0, 1]
    }
    if ship_type in type_dict:
        type_array = type_dict[ship_type]
    else:
        type_array = type_dict["Other"]
    return type_array


def get_total_fuel(distance, time_length, length, width, type_array):
    if distance and distance >= 3:
        log10_Total_Distance_Km = math.log10(distance * 100)
        log10_Total_Hours_Spent_At_Sea = math.log10(time_length * 100)
        log10_length = math.log10(length)
        log10_width = math.log10(width)
        input_data = [
                         log10_Total_Distance_Km,
                         log10_Total_Hours_Spent_At_Sea,
                         log10_length,
                         log10_width
                     ] + type_array
        predict_input = np.array(input_data).reshape(1, -1)

        pollution_fuel = model_fuel.predict(predict_input)[0]
        total_fuel = 10 ** pollution_fuel / 100
        print(input_data, 10 ** pollution_fuel / 100)
    else:
        total_fuel =0
    return total_fuel

def get_total_CO2(fuel_consumption, distance, type_array):
    if fuel_consumption:
        log10_Total_Fuel = math.log10(fuel_consumption * 100)
        log10_Total_Distance_Km = math.log10(distance * 100)
        # input_data = [
        #                  log10_Total_Fuel,
        #                  log10_Total_Distance_Km,
        #              ] + type_array

        input_data = [
                         log10_Total_Fuel,
                     ]
        predict_input = np.array(input_data).reshape(1, -1)
        pollution_co2 = model_co2.predict(predict_input)[0]
        total_co2 = 10 ** pollution_co2 / 100
        print(input_data, 10 ** pollution_co2 / 100)
    else:
        total_co2 = 0
    return total_co2



