from flask import Flask, request, Response, jsonify;
from configuration import Configuration;
from models import database, User;
from email.utils import parseaddr;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity;
from sqlalchemy import and_, or_
import re
from adminDecorator import roleCheck

application = Flask(__name__)
application.config.from_object(Configuration)

@application.route("/", methods=["GET"])
def index():
    return "Hello world"


@application.route("/register", methods = ["POST"])
def register():
    email = request.json.get("email", "");
    password = request.json.get("password", "");
    forename = request.json.get("forename", "");
    surname = request.json.get("surname", "");
    jmbg = request.json.get("jmbg","");
    emailEmpty = len(email) == 0;
    passwordEmpty = len(password) == 0;
    forenameEmpty = len(forename) == 0;
    surnameEmpty = len(surname) == 0;
    jmbgEmpty = len(jmbg) == 0;

    if (jmbgEmpty):
        return jsonify(message="Field jmbg is missing."), 400
    if (forenameEmpty):
        return jsonify(message="Field forename is missing."), 400
    if (surnameEmpty):
        return jsonify(message="Field surname is missing."), 400
    if (emailEmpty):
        return jsonify(message="Field email is missing."), 400
    if (passwordEmpty):
        return jsonify(message="Field password is missing."), 400


    pattern = re.compile("(\d\d)(\d\d)(\d\d\d)(\d\d)(\d\d\d)(\d)");
    groups = pattern.match(jmbg);
    if (groups == None):
        return jsonify(message="Invalid jmbg."), 400
    groups = groups.groups();
    if (int(groups[0]) > 31 or int(groups[0]) < 1 or int(groups[1]) > 12 or int(groups[1]) < 1 or int(groups[3]) < 70):
        return jsonify(message="Invalid jmbg."), 400
    s = (7*int(jmbg[0]) + 6*int(jmbg[1]) + 5*int(jmbg[2]) + 4*int(jmbg[3]) + 3*int(jmbg[4]) + 2*int(jmbg[5]) + \
        7 * int(jmbg[6]) + 6 * int(jmbg[7]) + 5 * int(jmbg[8]) + 4 * int(jmbg[9]) + 3 * int(jmbg[10]) + 2 * int(jmbg[11])) % 11;
    k = s;
    if (s == 1):
        return jsonify(message="Invalid jmbg."), 400
    if (s > 1):
        k = 11 - s
    if (k != int(jmbg[12])):
        return jsonify(message="Invalid jmbg."), 400

    regexEmail = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
    if (not re.match(regexEmail, email)):
        return jsonify(message="Invalid email."), 400

    if (len(password) < 8 or not re.search(r'[A-Z]+', password) or not re.search(r'[a-z]+', password) or not re.search(r'[0-9]+', password)):
        return jsonify(message="Invalid password."), 400

    userCheck = User.query.filter(User.email==email).first()
    if (userCheck):
        return jsonify(message="Email already exists."), 400

    user = User(email=email, password=password, forename=forename, surname=surname, jmbg=jmbg, idRole=2);
    database.session.add(user);
    database.session.commit();

    return Response(status=200)


jwt = JWTManager(application);


@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "");
    password = request.json.get("password", "");

    emailEmpty = len(email) == 0;
    passwordEmpty = len(password) == 0;

    if (emailEmpty):
        return jsonify(message="Field email is missing."), 400
    if (passwordEmpty):
        return jsonify(message="Field password is missing."), 400

    regexEmail = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
    if (not re.match(regexEmail, email)):
        return jsonify(message="Invalid email."), 400

    user = User.query.filter(and_(User.email == email, User.password == password)).first();

    if (not user):
        return jsonify(message="Invalid credentials."), 400

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "jmbg": user.jmbg,
        "role": user.role.name
    }

    accessToken = create_access_token(identity = user.email, additional_claims = additionalClaims);
    refreshToken = create_refresh_token(identity = user.email, additional_claims = additionalClaims);

    return jsonify(accessToken = accessToken, refreshToken = refreshToken), 200


@application.route("/check", methods=["POST"])
@jwt_required()
def check():
    return "Token is valid!";


@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    additionalClaims = {
            "forename": refreshClaims["forename"],
            "surname": refreshClaims["surname"],
            "jmbg": refreshClaims["jmbg"],
            "role": refreshClaims["role"]
    }

    return jsonify(accessToken=create_access_token(identity = identity, additional_claims = additionalClaims)), 200


@application.route("/delete", methods=["POST"])
@roleCheck("admin")
def delete():
    email = request.json.get("email", "")
    emailEmpty = len(email) == 0
    if (emailEmpty):
        return jsonify(message="Field email is missing."), 400
    regexEmail = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
    if (not re.match(regexEmail, email)):
        return jsonify(message="Invalid email."), 400
    user = User.query.filter(User.email == email).first()
    if (not user):
        return jsonify(message="Unknown user."), 400
    database.session.delete(user)
    database.session.commit()
    return Response(status=200)


if ( __name__ == "__main__" ):
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5000)