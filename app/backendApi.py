import requests
import json
from flask import current_app


def get_past_track(mmsi,interval=60):
    url = current_app.config["BACK_END_URL"] + f"/back/rest/v1/ship/history/{mmsi}/{interval}"
    res = requests.get(url)
    data = json.loads(res.content.decode('utf-8'))
    past_track = data["data"]
    return past_track
