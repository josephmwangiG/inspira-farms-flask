from flask import Flask, json
from flask_mqtt import Mqtt
from flask_influxdb import InfluxDB
from influxdb import InfluxDBClient
from datetime import datetime 


application = Flask(__name__)

application.config['SECRET'] = 'jahsahdyfgenfcgdeyfgxwgrbyuebxrg'
application.config['TEMPLATES_AUTO_RELOAD'] = True
application.config['MQTT_BROKER_URL'] = 'test.mosquitto.org'
application.config['MQTT_BROKER_PORT'] = 1883
application.config['MQTT_USERNAME'] = ''
application.config['MQTT_PASSWORD'] = ''
application.config['MQTT_KEEPALIVE'] = 5
application.config['MQTT_TLS_ENABLED'] = False

mqtt_client = Mqtt(application)
db_client = InfluxDBClient(
    'localhost',
    '8086',
    'admin',
    '',
    'coldRoomDB'
)

db_client.create_database("coldRoomDB")

@application.route('/')
def index():     
    return "Flask and react application application"


@application.route('/data')
def data():   
    result = db_client.query("SELECT * FROM conditions ORDER BY time DESC LIMIT 15")
    results = result.get_points(measurement = "conditions")
    results = [result for result in results]
    
    fieldTemperature = [float(result['fieldTemperature']) for result in results]
    roomTemperature = [float(result['roomTemperature']) for result in results]
    roomHumidity = [float(result['roomHumidity']) for result in results]
    energyMeter = [float(result['energyMeter']) for result in results]

    # Calculate result
    latest_humidity = roomHumidity[14]
    latest_room_temp = roomTemperature[14]
    highest_field_temp = max(fieldTemperature)
    avg_room_temperature = sum(roomTemperature) / len(roomTemperature)
    energy_consumption = energyMeter[0] - energyMeter[14]

    data = {
        "latest_humidity": latest_humidity,
        "latest_room_temp": latest_room_temp,
        "highest_field_temp": highest_field_temp,
        "avg_room_temperature": avg_room_temperature,
        "energy_consumption": energy_consumption,
        "fieldTemperature": fieldTemperature,
        "roomHumidity": roomHumidity,
        "roomTemperature": roomTemperature
    }

    return data

@mqtt_client.on_connect()
def handle_connect(client, userData, flags, rc):
    mqtt_client.subscribe('/518ca9fd-7a01')

@mqtt_client.on_message()
def on_message(client, userData, message):
    data = json.loads(str(message.payload.decode('utf_8')))
    db_client.write_points([{
        'measurement':"conditions",
        'tags': {
            'room': 'coldRoom'
        },
        'time': data['timestamp'],
        'fields': {
            'sessionId': data['sessionId'],
            'roomTemperature': data['roomTemperature'],
            'roomHumidity': data['roomHumidity'],
            'fieldTemperature': data['fieldTemperature'],
            'energyMeter': data['energyMeter']
        }
    }]) 
    print(f"Message: {data}")

if __name__ == "__main__":
    application.run(debug=True)
