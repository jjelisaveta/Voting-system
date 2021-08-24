import threading
import datetime
import os
import threading
import time
from flask import Flask
from configuration import Configuration
from models import database, Election, ParticipantElection, Vote
from datetime import datetime
from sqlalchemy import and_
from redis import Redis


application = Flask(__name__)
application.config.from_object(Configuration)


@application.route("/", methods=["GET"])
def index():
    return "Hello world"


def daemonThread():
    with application.app_context():
        with Redis(host=Configuration.REDIS_HOST) as redis:
            count = 0
            print("krenuo")
            pubsub = redis.pubsub()
            pubsub.subscribe(Configuration.REDIS_CHANNEL)
            for item in pubsub.listen():
                count = count + 1
                data = item["data"]
                if (type(data)!=int):
                    data = data.decode("utf-8").split("#")
                    guid = data[0];
                    pollNumber = data[1]
                    jmbg = data[2]

                    today = datetime.now().isoformat()
                    election = Election.query.filter(and_(Election.start < today, Election.end > today)).first()  # izbori u toku

                    if election == None:
                        print("Election does not exist " + str(today))
                        continue
                    ballot = Vote.query.filter(Vote.ballotGuid == guid).first()
                    ok = ParticipantElection.query.filter(and_(ParticipantElection.electionsId == election.id,
                                                               ParticipantElection.pollNumber == pollNumber)).first()
                    poruka = "ok"
                    if (ballot):
                         poruka = "duplikat"
                         vote = Vote(electionId=election.id, ballotGuid=guid, electionOfficialJmbg=jmbg, pollNumber=pollNumber,
                                     ok=False, reason="Duplicate ballot.")
                    elif (not ok):
                         poruka = "nema broj"
                         vote = Vote(electionId=election.id, ballotGuid=guid, electionOfficialJmbg=jmbg, pollNumber=pollNumber,
                                    ok=False, reason="Invalid poll number.")
                    else:
                         vote = Vote(electionId=election.id, ballotGuid=guid, electionOfficialJmbg=jmbg, pollNumber=pollNumber,
                                     ok=True, reason="")

                    database.session.add(vote)
                    database.session.commit()

                    #print(poruka)
                    #print(count)


if ( __name__ == "__main__" ):
    os.environ['TZ'] = 'Europe/Belgrade'
    time.tzset()
    database.init_app(application)
    threading.Thread(target=daemonThread, args=()).start()


