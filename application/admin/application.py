from flask import Flask, request, jsonify
from configuration import Configuration
from models import Participant, database, Election, ParticipantElection, Vote
from datetime import datetime
import dateutil.parser
from flask_jwt_extended import JWTManager
from roleCheck import roleCheck
from sqlalchemy import and_;

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route("/", methods=["GET"])
def index():
    return "Hello world"


@application.route("/createParticipant", methods=["POST"])
@roleCheck("admin")
def createParticipant():
    name = request.json.get("name", "")
    individual = request.json.get("individual", "")

    nameEmpty = len(name) == 0
    individualEmpty = individual==""

    if (nameEmpty):
        return jsonify(message="Field name is missing."), 400
    if (individualEmpty):
        return jsonify(message="Field individual is missing."), 400

    p = Participant(name=name, individual=individual)
    database.session.add(p)
    database.session.commit()
    return jsonify(id=p.id), 200


@application.route("/getParticipants", methods=["GET"])
@roleCheck("admin")
def getParticipants():
    #provera da li je admin
    participants = Participant.query.all()
    return jsonify(participants=[i.serialize for i in participants]), 200


@application.route("/createElection", methods=["POST"])
@roleCheck("admin")
def createElection():
    start = request.json.get("start", "")
    end = request.json.get("end", "")
    individual = request.json.get("individual", "")
    participants = request.json.get("participants", "")

    startEmpty = len(start) == 0
    endEmpty = len(end) == 0
    individualEmpty = individual == ""
    participantsEmpty = participants == ""

    if (startEmpty):
        return jsonify(message="Field start is missing."), 400
    if (endEmpty):
        return jsonify(message="Field end is missing."), 400
    if (individualEmpty):
        return jsonify(message="Field individual is missing."), 400
    if (participantsEmpty):
        return jsonify(message="Field participants is missing."), 400

    try:
        startDate = dateutil.parser.isoparse(start)
    except:
        return jsonify(message="Invalid date and time."), 400
    try:
        endDate = dateutil.parser.isoparse(end)
    except:
        return jsonify(message="Invalid date and time."), 400

    if (not startDate or not endDate):
        return jsonify(message="Invalid date and time."), 400

    election = Election.query.filter(and_(Election.start <= endDate, Election.end >= startDate)).first()
    if (election):
        return jsonify(message="Invalid date and time."), 400


    if (startDate >= endDate):
        return jsonify(message="Invalid date and time."), 400

    if (len(participants) < 2):
        return jsonify(message="Invalid participants."), 400

    okParticipants = []
    for p in participants:
        if (not isInt(p)):
            return jsonify(message="Invalid participants."), 400
        participant = Participant.query.get(p)
        if (participant==None or participant.individual != individual):
            return jsonify(message="Invalid participants."), 400
        okParticipants.append(participant)

    election = Election(start=start, end=end, individual=individual, participants=okParticipants)

    database.session.add(election)
    database.session.commit()

    i = 1
    pollNumbers = []
    for p in participants:
        if (not isInt(p)):
            return jsonify(message="Invalid participants."), 400
        pe = ParticipantElection.query.filter(and_(ParticipantElection.electionsId==election.id, ParticipantElection.participantId==p)).first()
        pe.pollNumber = i
        pollNumbers.append(i)
        i = i+1
    database.session.commit()

    return jsonify(pollNumbers=pollNumbers), 200


@application.route("/getElections", methods=["GET"])
@roleCheck("admin")
def getElections():
    elections = Election.query.all()
    return jsonify(elections=[i.serialize for i in elections]), 200


@application.route("/getResults", methods=["GET"])
@roleCheck("admin")
def getResults():
    id = request.args.get("id")
    if (not id):
        return jsonify(message="Field id is missing."), 400

    election = Election.query.filter(Election.id==int(id)).first()
    if (not election):
        return jsonify(message="Election does not exist."), 400

    today = datetime.now()
    if (election.end > today):
        return jsonify(message="Election is ongoing."), 400

    results = []


    ep = ParticipantElection.query.filter(ParticipantElection.electionsId==id).all()
    allVotes = len(Vote.query.filter(Vote.electionId == id).all())  # ukupan broj glasova
    invalidVotes = Vote.query.filter(and_(Vote.electionId == id, Vote.ok==False)).all()
    if (election.individual==True):
        for p in ep:
            votes = Vote.query.filter(and_(Vote.electionId==id, Vote.pollNumber==p.pollNumber, Vote.ok==True)).all()
            participant = Participant.query.filter(Participant.id==p.participantId).first()
            number = len(votes)
            res = "{:.2f}".format(number/allVotes)
            results.append({"pollNumber":p.pollNumber, "name": participant.name, "result": float(res)})

        return jsonify(participants=results, invalidVotes=[i.serialize for i in invalidVotes]), 200
    else:
        mandates = 250
        seats = [0]*len(ep)
        participants = []
        numVotes = []
        for p in ep:
            participants.append(Participant.query.filter(Participant.id==p.participantId).first())
            votes = Vote.query.filter(and_(Vote.electionId == id, Vote.pollNumber == p.pollNumber, Vote.ok == True)).all()
            numVotes.append(len(votes))

        while mandates > 0:
            maxResult = -1
            index = -1
            for i, p in enumerate(participants):
                if (numVotes[i] > allVotes*0.05):
                    current = numVotes[i] / (seats[i]+1)
                    if (maxResult<current):
                        maxResult = current
                        index = i
            mandates = mandates - 1
            seats[index] = seats[index]+1
        results = []
        for i, p in enumerate(participants):
            pollNumber = ParticipantElection.query.filter(ParticipantElection.electionsId==id, ParticipantElection.participantId==p.id).first().pollNumber
            results.append({"pollNumber": pollNumber, "name": p.name, "result":seats[i]})

        return jsonify(participants=results, invalidVotes=[i.serialize for i in invalidVotes]), 200


def isInt(number):
    try:
        int(number)
    except:
        return False
    return True


if ( __name__ == "__main__" ):
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5001)