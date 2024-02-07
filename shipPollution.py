import pymysql  # or use another database adapter as per your DB
# from flask import Flask, jsonify
#
# app = Flask(__name__)
import warnings
warnings.filterwarnings("ignore")
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from haversine import haversine
import math
import numpy as np
import joblib
# import tables

# db_connection = pymysql.connect(host='database-mysql-1.cllmsnxsu4hy.ap-southeast-2.rds.amazonaws.com',
#                                  user='admin',
#                                  password='admin123',
#                                  db='db_maritime',
#                                  charset='utf8mb4',
#                                  cursorclass=pymysql.cursors.DictCursor)


# @app.route('/maritime_data/<int:mmsi>', methods=['GET'])

# model_co2 = joblib.load('LinearRegression_Co2.joblib')
# model_fuel = joblib.load('RandomForest_Fuel.joblib')

model_co2 = joblib.load('New_LinearRegression_Co2.joblib')
model_fuel = joblib.load('New_LinearRegression_Fuel.joblib')

def query_table(table_name, mmsi):
    db_connection = pymysql.connect(host='database-mysql-1.cllmsnxsu4hy.ap-southeast-2.rds.amazonaws.com',
                                    user='admin',
                                    password='eco.marinehub.online.2024',
                                    db='db_maritime',
                                    charset='utf8mb4',
                                    cursorclass=pymysql.cursors.DictCursor)
    with db_connection.cursor() as cursor:
        sql = f"""
            SELECT mmsi, longitude, latitude, dt_pos_utc, length, width,vessel_type
            FROM `{table_name}` 
            WHERE mmsi = %s limit 1
        """
        cursor.execute(sql, (mmsi,))
        return cursor.fetchall()


def get_past_track(mmsi,interval=60):
    url = f"http://13.236.117.100:8888/rest/v1/ship/history/{mmsi}/{interval}"
    res = requests.get(url)
    data = json.loads(res.content.decode('utf-8'))
    past_track = data["data"]
    return past_track


def query_avg_size(table_name,vessel_type):
    db_connection = pymysql.connect(host='database-mysql-1.cllmsnxsu4hy.ap-southeast-2.rds.amazonaws.com',
                                    user='admin',
                                    password='eco.marinehub.online.2024',
                                    db='db_maritime',
                                    charset='utf8mb4',
                                    cursorclass=pymysql.cursors.DictCursor)
    with db_connection.cursor() as cursor:
        sql = f"""
            SELECT avg(length) as length,avg(width) as width, avg(sog) as sog
            FROM `{table_name}` 
            WHERE vessel_type = %s and length!=0 and width!=0
        """
        cursor.execute(sql, (vessel_type,))
        return cursor.fetchone()


def query_size(table_name, mmsi):
    db_connection = pymysql.connect(host='database-mysql-1.cllmsnxsu4hy.ap-southeast-2.rds.amazonaws.com',
                                    user='admin',
                                    password='eco.marinehub.online.2024',
                                    db='db_maritime',
                                    charset='utf8mb4',
                                    cursorclass=pymysql.cursors.DictCursor)
    with db_connection.cursor() as cursor:
        sql = f"""
            SELECT length, width,vessel_type
            FROM `{table_name}` 
            WHERE mmsi = %s limit 1
        """
        cursor.execute(sql, (mmsi,))
        return cursor.fetchone()


def get_size_type(mmsi):
    with ThreadPoolExecutor(max_workers=len(tables.table_names)) as executor:
        future = executor.submit(query_size, "t_realtime", mmsi)
        results = future.result()
        if results and results["length"] and results["width"]:
            length, width = int(results["length"]), int(results["width"])
        else:
            length, width = (0,0)
        vessel_type = results["vessel_type"]
    return length, width, vessel_type


def get_avg_size(mmsi):
    avg_length, avg_width = (79,14)
    with ThreadPoolExecutor(max_workers=len(tables.table_names)) as executor:
        future = executor.submit(query_table, "t_realtime", mmsi)
        results = future.result()
        if results:
            vessel_type = results[0]["vessel_type"]
            # print(vessel_type)

    with ThreadPoolExecutor(max_workers=len(tables.table_names)) as executor:
        futures_avg = executor.submit(query_avg_size, "t_realtime", vessel_type)
        results_avg = futures_avg.result()
        if results_avg :
            avg_length, avg_width,avg_sog = results_avg["length"],results_avg["width"],results_avg["sog"]
    return avg_length, avg_width, avg_sog


def get_maritime_data(mmsi):
    ship_tracker = []
    with ThreadPoolExecutor(max_workers=len(tables.table_names)) as executor:
        futures = [executor.submit(query_table, table_name, mmsi) for table_name in tables.table_names]
        results = [future.result() for future in futures]
    for result in results:
        if result:
            ship_tracker = ship_tracker + result
        # else:
        #     if len(ship_tracker)>0:
        #         ship_tracker.append(ship_tracker[-1])   # 某个时间没收到 则默认仍然为前一时刻的位置
        #     else:
        #         ship_tracker.append({})
        else:
            ship_tracker.append({})
    return ship_tracker


def get_past_track_24(past_track):
    """
    change pasttrack into 24 hour format
    :param past_track:
    :return:
    """                            
    hourly_data = [{} for _ in range(13)]
    for item in past_track:                                            
        dt = datetime.strptime(item["dtPosUtc"], "%Y-%m-%d %H:%M:%S")
        hour_index = dt.hour//2+1
        hourly_data[hour_index]=item
    print(hourly_data)
    return hourly_data


def get_distance_list(ship_tracker):
    distance_list = []
    for i in range(0, len(ship_tracker)-1):
        if not ship_tracker[i] or not ship_tracker[i+1]:
            if distance_list:
                distance = distance_list[-1]  # 如果distance为0 设置distance等于之前
            else:
                distance = 0
        else:
            start_point = (float(ship_tracker[i]["latitude"]), float(ship_tracker[i]["longitude"]))   # first point; tuple of (latitude, longitude) in decimal degrees
            end_point= (float(ship_tracker[i+1]["latitude"]), float(ship_tracker[i+1]["longitude"]))   # econd point; tuple of (latitude, longitude) in decimal degrees
            distance = haversine(start_point, end_point)
        # print(f"distance{i+1}: {distance} km")
        distance_list.append(distance)
    return distance_list

def calculate_distances_and_times(ship_tracker):
    distances = [0] * len(ship_tracker)
    times = [0] * len(ship_tracker)  # Initialize times with zeros
    non_empty_indices = [i for i, coord in enumerate(ship_tracker) if coord]

    for i in range(len(non_empty_indices) - 1):
        current_index = non_empty_indices[i]
        next_index = non_empty_indices[i + 1]
        current_coord = ship_tracker[current_index]
        next_coord = ship_tracker[next_index]
        start_point = (float(current_coord["latitude"]), float(current_coord["longitude"]))
        end_point = (float(next_coord["latitude"]), float(next_coord["longitude"]))
        distance = haversine(start_point, end_point)
        time_diff = (datetime.strptime((next_coord['dtPosUtc']), "%Y-%m-%d %H:%M:%S")
                     - datetime.strptime((current_coord['dtPosUtc']),"%Y-%m-%d %H:%M:%S")).total_seconds()
        if time_diff > 0:
            avg_speed = distance / time_diff
            avg_time_diff = time_diff / (next_index - current_index)
            for j in range(current_index, next_index + 1):
                distances[j] = avg_speed * avg_time_diff
                times[j] = avg_time_diff / 3600  # Convert seconds to hours
        else:
            for j in range(current_index, next_index + 1):
                distances[j] = distance
                times[j] = 0
    if len(distances)>0 and len(times)>0:
        distances = distances[:-1]
        times = times[:-1]
    return distances, times




def get_time_length_list(ship_tracker):
    time_list = []
    fmt = '%Y-%m-%d %H:%M:%S'
    for i in range(0, len(ship_tracker) - 1):
        if not ship_tracker[i] or not ship_tracker[i + 1]:
            if time_list:
                hours_difference = time_list[-1]
            else:
                hours_difference = 0
        else:
            start_time = datetime.strptime(ship_tracker[i]["dtPosUtc"], fmt)
            end_time = datetime.strptime(ship_tracker[i+1]["dtPosUtc"], fmt)
            time_difference = end_time - start_time
            hours_difference = time_difference.total_seconds() / 3600   # hour
        # print(f"时间{i + 1}: {hours_difference} 小时")
        time_list.append(hours_difference)
    return time_list


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


def prepare_predict_data(mmsi,ship_points,avg_length,avg_width, calculate_avg=False):
    # model parameters
    # log10_Total_Distance_Km
    # log10_Total_Hours_Spent_At_Sea
    # log10_length
    # log10_width
    # vessel_type_onehot_array
    input_data_list = []
    #
    # distance_list = get_distance_list(ship_points)
    # time_list = get_time_length_list(ship_points)

    distance_list,time_list = calculate_distances_and_times(ship_points)
    # print("distance_list",len(distance_list),distance_list)
    # print("distance_list2",len(distance_list2),distance_list2)
    #
    # print("time_list",len(time_list),time_list)
    # print("time_list2",len(time_list2),time_list2)

    # print("calculate_avg:",calculate_avg)
    length, width, vessel_type = get_size_type(mmsi)

    if not length or calculate_avg:
        length = avg_length  # average
    if not width or calculate_avg:
        width = avg_width  # average
    # print("length "+str(length)+"width"+str(width))

    log10_length = math.log10(length)
    # print("width:"+str(width))

    log10_width = math.log10(width)
    type_array = get_type_array(vessel_type)

    assert len(distance_list) == len(time_list)

    for i in range(0, len(distance_list)):
        if distance_list[i]:
            log10_Total_Distance_Km = math.log10(distance_list[i]*2000)
        else:
            log10_Total_Distance_Km = math.log10(1)  # when distance is 0 set it to 1 for calculation

        if time_list[i]:
            log10_Total_Hours_Spent_At_Sea = math.log10(time_list[i]*2000)
        else:
            log10_Total_Hours_Spent_At_Sea = math.log10(1)
        input_data = [
            log10_Total_Distance_Km,
            log10_Total_Hours_Spent_At_Sea,
            log10_length,
            log10_width
        ] + type_array
        input_data_list.append(input_data)
    return input_data_list


def get_pollution_fuel(mmsi,calculate_avg = False):
    # ship_points = get_maritime_data(mmsi)
    past_track = get_past_track(mmsi)
    ship_points = get_past_track_24(past_track)
    print(ship_points)
    # print(ship_points)
    if len(ship_points)<=1:
        pollution_list =[]
    else:
        avg_length, avg_width, avg_sog = get_avg_size(mmsi)
        pollution_list = []
        input_data_list = prepare_predict_data(mmsi,ship_points,avg_length,avg_width,calculate_avg= calculate_avg)
        for input_data in input_data_list:
            # print("input",input_data)
            predict_input = np.array(input_data).reshape(1, -1)
            pollution_fuel = model_fuel.predict(predict_input)[0]
            distance = 10**input_data[0]/2000
            print(mmsi, distance,input_data, 10**pollution_fuel/2000)
            if distance < 0.2:
                pollution_list.append(round(0,2))         # small diatance with pollution
            else:
                pollution_list.append(round(10 ** pollution_fuel / 2000,2))
        
        # print(pollution_list)
        for i in range(0,len(pollution_list)):
            if pollution_list[i]!=0:
                break
        for j in range(0, i):
            pollution_list[j] = pollution_list[i]
        # if pollution_list[0]==0:
        #     pollution_list[0]=pollution_list[1]
        return pollution_list


def get_co2(fuel_list):
    print("fuel_list",fuel_list)
    co2_list = []
    for fuel_consumption in fuel_list:
        if not fuel_consumption:
            fuel_consumption = 1
        log10_Total_Fuel = math.log10(fuel_consumption * 100)
        input_data = [log10_Total_Fuel]
        predict_input = np.array(input_data).reshape(1, -1)
        prediction = model_co2.predict(predict_input)[0]
        pollution_co2 = 10 ** prediction / 100
        co2_list.append(pollution_co2)
        print(input_data, 10 ** prediction / 100)
    else:
        co2_list.append(0)
    return co2_list



if __name__ == '__main__':
    get_avg_size("338185704")

