# coding:utf-8
from flask import Flask, request
from flask_cors import CORS  # Import CORS from flask_cors
import shipPollution
from totalPollution import *
from shipPollution import *

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

BASE_URL = '/'




@app.route(BASE_URL + 'get/test', methods=['GET'])
def test_get():
    # 解析请求参数
    param = request.args.to_dict()
    name = param['name']
    password = param['password']
    result = {
        'msg': "Welcome! " + name
    }
    # 返回json
    result_json = json.dumps(result)
    return result_json


# 接收post请求
@app.route(BASE_URL + 'post/test', methods=['POST'])
def test_post():
    data = request.get_data()
    # print(type(data))
    json_data = json.loads(data.decode("utf-8"))
    name = json_data['name']
    password = json_data['password']
    result = {
        'msg': "welcome! " + name
    }
    result_json = json.dumps(result)
    return result_json
#
def get_ship_id(mmsi):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    url = f"https://www.marinetraffic.com/en/search/searchAsset?what=vessel&term={mmsi}"
    res = requests.get(url, headers=headers)
    data = json.loads(res.content.decode('utf-8'))
    return data

@app.route(BASE_URL + 'get/shipID', methods=['GET'])
def ship_id():
    param = request.args.to_dict()
    mmsi = param['mmsi']
    result = get_ship_id(mmsi)
    if result:
        return {'vessel_id': result[0]['id']}
    else:
        return {'vessel_id': None}

@app.route(BASE_URL + 'get/shipPicture', methods=['GET'])
def ship_pic():
    param = request.args.to_dict()
    ship_id = param['ship_id']
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    url = f"https://photos.marinetraffic.com/ais/showphoto.aspx?shipid={ship_id}&size=thumb"
    res = requests.get(url, headers=headers)
    if res.status_code ==200:
        return {'ship_image':url}
    else:
        return {'ship_image':None}


@app.route(BASE_URL + 'get/pollution', methods=['GET'])
def ship_pollution():
    param = request.args.to_dict()
    mmsi = param['mmsi']
    pollution_list = shipPollution.get_pollution_fuel(mmsi)
    fuel_list_avg = shipPollution.get_pollution_fuel(mmsi, calculate_avg=True)
    if pollution_list:
        result = {
            "mmsi": mmsi,
            "status": "successful",
            "pollution_fuel": pollution_list,
            "pollution_fuel_avg": fuel_list_avg,
            "pollution_co2": shipPollution.get_co2(pollution_list),
            "pollution_co2_avg": shipPollution.get_co2(fuel_list_avg),

        }
    else:
        result = {
            "mmsi": mmsi,
            "status": "error",
        }
    return(result)



@app.route(BASE_URL + 'get/total_pollution', methods=['GET'])
def total_pollution():
    param = request.args.to_dict()
    mmsi = param['mmsi']
    past_track = get_past_track(mmsi)
    distance = get_distance(past_track)
    time_length = get_time_length(past_track)
    resault = {}
    if len(past_track) > 1:
        avg_length, avg_width,avg_sog = get_avg_size(mmsi)
        if "length" in past_track[0] and int(past_track[0]["length"]):
            length = int(past_track[0]["length"])                       
        else:                                            
            length = avg_length
        if "width" in past_track[0] and int(past_track[0]["width"]):
            width = int(past_track[0]["width"])                         
        else:                                   
            width = avg_width
        vessel_type = past_track[0]["vesselType"]
        type_array = get_type_array(vessel_type)
        total_fuel = get_total_fuel(distance, time_length, length, width, type_array)
        total_fuel_avg = get_total_fuel(distance, time_length, avg_length, avg_width, type_array)
        total_co2 = get_total_CO2(total_fuel, distance, type_array)
        total_co2_avg = get_total_CO2(total_fuel_avg, distance, type_array)

        result = {
            "mmsi": mmsi,
            "status": "successful",
            "sog":round(float(past_track[-1]["sog"]),2),
            "sog_avg": round(avg_sog,2),
            "width": round(width,2),
            "width_avg": round(avg_width,2),
            "length": round(length,2),
            "length_avg": round(avg_length,2),
            "total_fuel": round(total_fuel,2),
            "total_fuel_avg": round(total_fuel_avg,2),
            "total_co2": round(total_co2,2),
            "total_co2_avg": round(total_co2_avg,2),
        }
    else:
        result = {
            "mmsi": mmsi,
            "status": "error",
        }
    return  result



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
    ship_pollution(227277040)
