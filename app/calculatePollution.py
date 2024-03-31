import math
import numpy as np
from app import model_fuel,model_co2


def total_fuel(distance, time_length, length, width, type_array):
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
        # print(input_data, 10 ** pollution_fuel / 100)
    else:
        total_fuel =0
    return total_fuel


def total_CO2(fuel_consumption, distance, type_array):
    if fuel_consumption:
        log10_Total_Fuel = math.log10(fuel_consumption * 100)
        input_data = [
                         log10_Total_Fuel,
                     ]
        predict_input = np.array(input_data).reshape(1, -1)
        pollution_co2 = model_co2.predict(predict_input)[0]
        total_co2 = 10 ** pollution_co2 / 100
        # print(input_data, 10 ** pollution_co2 / 100)
    else:
        total_co2 = 0
    return total_co2


def fuel_24(input_data_list):
    pollution_list = []
    for input_data in input_data_list:
        predict_input = np.array(input_data).reshape(1, -1)
        pollution_fuel = model_fuel.predict(predict_input)[0]
        distance = 10 ** input_data[0] / 2000
        if distance < 0.2:
            pollution_list.append(round(0, 2))  # small diatance with pollution
        else:
            pollution_list.append(round(10 ** pollution_fuel / 2000, 2))
    for i in range(0, len(pollution_list)):
        if pollution_list[i] != 0:
            break
    for j in range(0, i):
        pollution_list[j] = pollution_list[i]
    return pollution_list


def co2_24(fuel_list):
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
        # print(input_data, 10 ** prediction / 100)
    else:
        co2_list.append(0)
    return co2_list

