from flask import Flask, request, Response, jsonify;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity, verify_jwt_in_request;
from functools import wraps

def roleCheck(role):
    def innerRole(function):
        @wraps(function)
        def decorator( *arguments, **keywordArguments ):
            verify_jwt_in_request();
            claims = get_jwt();
            if (("role" in claims) and (role == claims["role"])):
                return function(*arguments, **keywordArguments);
            else:
                return jsonify(msg="permission denied!"), 403

        return decorator;

    return innerRole;