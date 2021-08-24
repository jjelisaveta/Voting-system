from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class ParticipantElection(database.Model):
    __tablename__ = "participantelection"
    id = database.Column(database.Integer, primary_key=True)
    pollNumber = database.Column(database.Integer, nullable=False, default=0)
    participantId = database.Column(database.Integer, database.ForeignKey("participants.id"), nullable=False)
    electionsId = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable=False)


class Participant(database.Model):
    __tablename__ = "participants"
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False, unique=True)
    individual = database.Column(database.Boolean, nullable=False)
    elections = database.relationship("Election", secondary=ParticipantElection.__table__, back_populates="participants")

    @property
    def serialize(self):
        return {
            'id': self.id,
            'individual': self.individual,
            'name': self.name
        }

    @property
    def serialize2(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Election(database.Model):
    __tablename__ = "elections"
    id = database.Column(database.Integer, primary_key=True)
    start = database.Column(database.DateTime, nullable=False)
    end = database.Column(database.DateTime, nullable=False)
    individual = database.Column(database.Boolean, nullable=False)
    participants = database.relationship("Participant", secondary=ParticipantElection.__table__, back_populates="elections")

    @property
    def serialize(self):
        return {
            'id': self.id,
            'start': self.start.isoformat(),
            'end': self.end.isoformat(),
            'individual': self.individual,
            'participants': [i.serialize2 for i in self.participants]
        }



class Vote(database.Model):
    __tablename__ = "votes"
    id = database.Column(database.Integer, primary_key=True)
    electionId = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable=False)
    ballotGuid = database.Column(database.String(36), nullable=False)
    electionOfficialJmbg = database.Column(database.String(256), nullable=False)
    pollNumber = database.Column(database.Integer, nullable=False)
    ok = database.Column(database.Boolean, nullable=False)
    reason = database.Column(database.String(256), nullable=True)


