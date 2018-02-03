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


class MeasurementModel(Schema):
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


class ErrorModel(Schema):
    type = 'object'
    properties = {
        'message': {
            'type': 'string'
        }
    }


class MeasurementResource(Resource):
    @swagger.doc({
        'tags': ['measurement'],
        'description': 'Adds a measurement',
        'parameters': [
            {
                'name': 'measurement',
                'description': 'Measurement that needs to be added to a csv file and to the database',
                'in': 'body',
                'schema': MeasurementModel,
                'required': True,
            }
        ],
        'responses': {
            '201': {
                'description': 'Added measurement',
                'schema': MeasurementModel
            }
        }
    })
    def post(self):
        # curl -H "Content-Type: application/json" -X POST -d '{"device":"C4:7C:8D:65:BD:76", "timestamp": "2018-01-23 22:00:41.062114", "moisture": 0, "temperature": 19.7, "conductivity": 0, "light": 39}' http://ec2-34-243-27-176.eu-west-1.compute.amazonaws.com:5000/measurement

        # Validate request body with schema model
        try:
            measurement = MeasurementModel(**request.get_json())
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

api.add_resource(MeasurementResource, '/measurement')


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

