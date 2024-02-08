class Config:
    MYSQL_HOST = 'marinehub.mysql.database.azure.com'
    MYSQL_USER = 'marinehub'
    MYSQL_PASSWORD = 'Admin123'
    MYSQL_DB = 'marine'
    MYSQL_PORT = 3306
    STATIC_TABLE = "t_static_mmsi"
    REALTIME_TABLE = "t_realtime"

    HOST = '0.0.0.0'
    PORT = '443'

    BACK_END_URL = "https://eco.marinehub.online"
    MARINE_TRAFFIC_SEARCH_URL = "https://www.marinetraffic.com/en/search/"
    MARINE_TRAFFIC_PHOTO_URL = "https://photos.marinetraffic.com/ais/"

    MODEL_PATH = 'models'
    FUEL_MODEL = 'New_LinearRegression_Fuel.joblib'
    CO2_MODEL = 'New_LinearRegression_Co2.joblib'

class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    DEBUG = False
    SSH_NAME_PATH = '/etc/letsencrypt/live/flask.marinehub.online/fullchain.pem'
    SSH_KEY_PATH = '/etc/letsencrypt/live/flask.marinehub.online/privkey.pem'
