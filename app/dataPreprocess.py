from haversine import haversine
from datetime import datetime
import math
import numpy as np
from app import model_fuel, model_co2


def get_distance(past_track):
    if len(past_track) > 1:
        start_point = (
            float(past_track[0]["latitude"]),
            float(past_track[0]["longitude"]))
        end_point = (
            float(past_track[-1]["latitude"]),
            float(past_track[-1]["longitude"]))
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
        "Cargo": [1, 0, 0, 0, 0],
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


def get_width_length(past_track_0, avg_length, avg_width):
    if "length" in past_track_0 and int(past_track_0["length"]):
        length = int(past_track_0["length"])
    else:
        length = avg_length
    if "width" in past_track_0 and int(past_track_0["width"]):
        width = int(past_track_0["width"])
    else:
        width = avg_width
    return length, width


def get_past_track_24(past_track):
    """
    change pasttrack into 24 hour format
    :param past_track:
    :return:
    """
    hourly_data = [{} for _ in range(13)]
    for item in past_track:
        dt = datetime.strptime(item["dtPosUtc"], "%Y-%m-%d %H:%M:%S")
        hour_index = dt.hour // 2 + 1
        hourly_data[hour_index] = item
    # print(hourly_data)
    return hourly_data


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
                     - datetime.strptime((current_coord['dtPosUtc']), "%Y-%m-%d %H:%M:%S")).total_seconds()
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
    if len(distances) > 0 and len(times) > 0:
        distances = distances[:-1]
        times = times[:-1]
    return distances, times


def prepare_predict_data(ship_points, length, width, vessel_type):
    # model parameters
    # log10_Total_Distance_Km
    # log10_Total_Hours_Spent_At_Sea
    # log10_length
    # log10_width
    # vessel_type_onehot_array

    input_data_list = []
    distance_list, time_list = calculate_distances_and_times(ship_points)
    log10_length = math.log10(length)
    log10_width = math.log10(width)
    type_array = get_type_array(vessel_type)

    assert len(distance_list) == len(time_list)

    for i in range(0, len(distance_list)):
        if distance_list[i]:
            log10_Total_Distance_Km = math.log10(distance_list[i] * 2000)
        else:
            log10_Total_Distance_Km = math.log10(1)  # when distance is 0 set it to 1 for calculation

        if time_list[i]:
            log10_Total_Hours_Spent_At_Sea = math.log10(time_list[i] * 2000)
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
