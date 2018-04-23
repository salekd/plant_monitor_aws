from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from flask_restful_swagger_2 import Api
from flask_restful_swagger_2 import swagger, Resource, Schema
from collections import OrderedDict
from configparser import ConfigParser
from werkzeug import secure_filename
import os


# Read config file
config = ConfigParser()
config.read('flask_app.cfg')
database_uri = config.get('SQLAlchemy', 'database_uri')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
db = SQLAlchemy(app)
ALLOWED_EXTENSIONS = ['jpg']

# Use the swagger Api class as you would use the flask restful class.
# It supports several (optional) parameters, these are the defaults:
api = Api(app, api_version='0.0', api_spec_url='/api/swagger')


class MifloraModel(Schema):
    type = 'object'
    properties = {
        'device': {
            'type': 'string'
        },
        'timestamp': {
            'type': 'string'
        },
        'moisture': {
            'type': 'number'
        },
        'temperature': {
            'type': 'number'
        },
        'conductivity': {
            'type': 'number'
        },
        'light': {
            'type': 'number'
        }
    }


class BME280Model(Schema):
    type = 'object'
    properties = {
        'device': {
            'type': 'string'
        },
        'timestamp': {
            'type': 'string'
        },
        'temperature': {
            'type': 'number'
        },
        'pressure': {
            'type': 'number'
        },
        'humidity': {
            'type': 'number'
        }
    }


class SI1145Model(Schema):
    type = 'object'
    properties = {
        'device': {
            'type': 'string'
        },
        'timestamp': {
            'type': 'string'
        },
        'visible': {
            'type': 'number'
        },
        'IR': {
            'type': 'number'
        },
        'UV': {
            'type': 'number'
        }
    }


class PumpModel(Schema):
    type = 'object'
    properties = {
        'device': {
            'type': 'string'
        },
        'timestamp': {
            'type': 'string'
        },
        'duration': {
            'type': 'number'
        }
    }


class ErrorModel(Schema):
    type = 'object'
    properties = {
        'message': {
            'type': 'string'
        }
    }


class MifloraResource(Resource):
    @swagger.doc({
        'tags': ['measurement'],
        'description': 'Adds a measurement from the plant sensor',
        'parameters': [
            {
                'name': 'measurement',
                'description': 'Measurement that needs to be added to a csv file and to the database',
                'in': 'body',
                'schema': MifloraModel,
                'required': True,
            }
        ],
        'responses': {
            '201': {
                'description': 'Added measurement',
                'schema': MifloraModel
            }
        }
    })
    def post(self):
        # curl -H "Content-Type: application/json" -X POST -d '{"device":"C4:7C:8D:65:BD:76", "timestamp": "2018-01-23 22:00:41.062114", "moisture": 0, "temperature": 19.7, "conductivity": 0, "light": 39}' http://ec2-34-243-27-176.eu-west-1.compute.amazonaws.com:5000/measurement

        # Validate request body with schema model
        try:
            measurement = MifloraModel(**request.get_json())
        except ValueError as e:
            return ErrorModel(**{'message': e.args[0]}), 400
        print(measurement)

        # Make sure the entries are in the correct order
        keys = ['timestamp', 'moisture', 'temperature', 'conductivity', 'light']
        ordered = OrderedDict([(key, measurement[key]) for key in keys])

        # Append to a csv file for the device
        csvfile = "/data/measurements/{}.csv".format(measurement['device'].replace(':', ''))
        with open(csvfile, "a") as f:
            f.write(", ".join([str(x) for x in ordered.values()]) + '\n')

        # Insert into PostgreSQL database
        query = """INSERT INTO measurements (device, time, moisture, temperature, conductivity, light)
    VALUES ('%(device)s', '%(timestamp)s', %(moisture)s, %(temperature)s, %(conductivity)s, %(light)s);""" % measurement
        db.engine.execute(query)

        return measurement, 201

api.add_resource(MifloraResource, '/measurement')


class BME280Resource(Resource):
    @swagger.doc({
        'tags': ['measurement'],
        'description': 'Adds a measurement from the BME280 sensor',
        'parameters': [
            {
                'name': 'measurement',
                'description': 'Measurement that needs to be added to a csv file and to the database',
                'in': 'body',
                'schema': BME280Model,
                'required': True,
            }
        ],
        'responses': {
            '201': {
                'description': 'Added measurement',
                'schema': BME280Model
            }
        }
    })
    def post(self):
        # Validate request body with schema model
        try:
            measurement = BME280Model(**request.get_json())
        except ValueError as e:
            return ErrorModel(**{'message': e.args[0]}), 400
        print(measurement)

        # Make sure the entries are in the correct order
        keys = ['timestamp', 'temperature', 'pressure', 'humidity']
        ordered = OrderedDict([(key, measurement[key]) for key in keys])

        # Append to a csv file for the device
        csvfile = "/data/measurements/BME280_{}.csv".format(measurement['device'])
        with open(csvfile, "a") as f:
            f.write(", ".join([str(x) for x in ordered.values()]) + '\n')

        # Insert into PostgreSQL database
        query = """INSERT INTO bme280 (device, time, temperature, pressure, humidity)
    VALUES ('%(device)s', '%(timestamp)s', %(temperature)s, %(pressure)s, %(humidity)s);""" % measurement
        db.engine.execute(query)

        return measurement, 201

api.add_resource(BME280Resource, '/bme280')


class SI1145Resource(Resource):
    @swagger.doc({
        'tags': ['measurement'],
        'description': 'Adds a measurement from the SI1145 sensor',
        'parameters': [
            {
                'name': 'measurement',
                'description': 'Measurement that needs to be added to a csv file and to the database',
                'in': 'body',
                'schema': SI1145Model,
                'required': True,
            }
        ],
        'responses': {
            '201': {
                'description': 'Added measurement',
                'schema': SI1145Model
            }
        }
    })
    def post(self):
        # Validate request body with schema model
        try:
            measurement = SI1145Model(**request.get_json())
        except ValueError as e:
            return ErrorModel(**{'message': e.args[0]}), 400
        print(measurement)

        # Make sure the entries are in the correct order
        keys = ['timestamp', 'visible', 'IR', 'UV']
        ordered = OrderedDict([(key, measurement[key]) for key in keys])

        # Append to a csv file for the device
        csvfile = "/data/measurements/SI1145_{}.csv".format(measurement['device'])
        with open(csvfile, "a") as f:
            f.write(", ".join([str(x) for x in ordered.values()]) + '\n')

        # Insert into PostgreSQL database
        query = """INSERT INTO si1145 (device, time, visible, IR, UV)
    VALUES ('%(device)s', '%(timestamp)s', %(visible)s, %(IR)s, %(UV)s);""" % measurement
        db.engine.execute(query)

        return measurement, 201

api.add_resource(SI1145Resource, '/si1145')


class PumpResource(Resource):
    @swagger.doc({
        'tags': ['pump'],
        'description': 'Adds a pump watering duration',
        'parameters': [
            {
                'name': 'pump',
                'description': 'Pump watering duration that needs to be added to a csv file and to the database',
                'in': 'body',
                'schema': PumpModel,
                'required': True,
            }
        ],
        'responses': {
            '201': {
                'description': 'Added pump watering duration',
                'schema': PumpModel
            }
        }
    })
    def post(self):
        # Validate request body with schema model
        try:
            pump_log = PumpModel(**request.get_json())
        except ValueError as e:
            return ErrorModel(**{'message': e.args[0]}), 400
        print(pump_log)

        # Make sure the entries are in the correct order
        keys = ['timestamp', 'duration']
        ordered = OrderedDict([(key, pump_log[key]) for key in keys])

        # Append to a csv file for the device
        csvfile = "/data/measurements/pump_{}.csv".format(pump_log['device'].replace(':', ''))
        with open(csvfile, "a") as f:
            f.write(", ".join([str(x) for x in ordered.values()]) + '\n')

        # Insert into PostgreSQL database
        query = """INSERT INTO pump (device, time, duration)
    VALUES ('%(device)s', '%(timestamp)s', %(duration)s);""" % pump_log
        db.engine.execute(query)

        return pump_log, 201

api.add_resource(PumpResource, '/pump')


class ImageResource(Resource):
    @swagger.doc({
        'tags': ['image'],
        'description': 'Adds an image',
        'parameters': [
            {
                'name': 'image',
                'description': 'Snapshot that needs to be saved as a file',
                'in': 'formData',
                'type': 'file',
                'required': True,
            }
        ],
        'responses': {
            '201': {
                'description': 'Added image',
            }
        }
    })
    def post(self):
        f = request.files['file']
        filename = secure_filename(f.filename)
        if '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            print(filename)
            f.save(os.path.join('/data/images', filename))
        else:
            return None, 400
        return None, 201

api.add_resource(ImageResource, '/image')


if __name__ == '__main__':
    # Specify host 0.0.0.0 to make the service visible to the outside world.
    app.run(host='0.0.0.0', port=5000)

