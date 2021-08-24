from flask import Flask, request, jsonify
from configuration import Configuration
from models import database
from flask_jwt_extended import JWTManager, get_jwt, verify_jwt_in_request
from roleCheck import roleCheck
import io
import csv
from redis import Redis


application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route("/", methods=["GET"])
def index():
    return "Hello world"


@application.route("/vote", methods=["POST"])
@roleCheck("user")
def vote():
    with Redis(host=Configuration.REDIS_HOST) as redis:
        if (not request.files.get('file', None)):
            return jsonify(message="Field file is missing."), 400

        file = request.files["file"].stream.read().decode("utf-8 ")
        if (file==None):
            return jsonify(message="Field file is missing."), 400

        verify_jwt_in_request()
        claims = get_jwt()
        jmbg = claims["jmbg"]

        stream = io.StringIO(file)
        reader = csv.reader(stream)
        votes = []
        i = 0
        for row in reader:
            if (len(row)!=2):
                return jsonify(message="Incorrect number of values on line {}.".format(i)), 400

            guid = row[0]
            pollNumber = row[1]
            if (isInt(pollNumber)==False or int(pollNumber)<0):
                return jsonify(message="Incorrect poll number on line {}.".format(i)), 400
            #redis.publish(Configuration.REDIS_CHANNEL, guid)
            #redis.publish(Configuration.REDIS_CHANNEL, int(pollNumber))
            redis.publish(Configuration.REDIS_CHANNEL, str(guid)+"#"+str(pollNumber)+"#"+jmbg)

            #redis.rpush(Configuration.REDIS_CHANNEL, guid)
            #redis.rpush(Configuration.REDIS_CHANNEL, int(pollNumber))
            i = i + 1

        return "ok"


def isInt(number):
    try:
        int(number)
    except:
        return False
    return True


if ( __name__ == "__main__" ):
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)