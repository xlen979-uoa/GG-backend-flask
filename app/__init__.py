from flask import Flask
from flask_cors import CORS
import joblib
import os
import argparse
from config import DevConfig, ProdConfig

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# these code are for dev
#parser = argparse.ArgumentParser(description='Run the Flask app')
#parser.add_argument('--env', default='dev', choices=['prod', 'dev'],
#    help='Specify the environment to run the app (prod or dev)')

#args = parser.parse_args()

#if args.env == 'prod':
#    app.config.from_object(ProdConfig)
#    print(" * Running in production mode")
#else:
#    app.config.from_object(DevConfig)
#    print(" * Running in development mode")

app.config.from_object(ProdConfig)

# Load model when service starts
model_path_fuel = os.path.join(
            os.path.dirname(__file__),
            app.config['MODEL_PATH'],
            app.config['FUEL_MODEL'])
model_path_co2 = os.path.join(
            os.path.dirname(__file__),
            app.config['MODEL_PATH'],
            app.config['CO2_MODEL'])

model_fuel = joblib.load(model_path_fuel)
model_co2 = joblib.load(model_path_co2)
print(" * Models successfully Loaded")

from app import routes
