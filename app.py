import sys
import bcrypt
import logging
from flask import request, jsonify, Response
from flask.helpers import send_from_directory
from datetime import datetime, timedelta, timezone
from flask_cors import CORS
from flask_jwt_extended import create_access_token, set_access_cookies
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from utils import  get_list_of_dict
from database.config import  db,Reminders,Users,app
import json
from utils import jsonify_resp

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=10)
jwt = JWTManager(app)
CORS(app)

@app.route("/register_api",methods=["POST"])
def register():


    username=request.json["username"]
    password=bcrypt.hashpw(request.json["password"].encode("utf-8"),bcrypt.gensalt(14)).decode()
    try:
        user = Users(username, password)
        db.session.add(user)
        db.session.commit()
        resp=jsonify_resp( message="you are registered", statusCode=200)

        return Response(response=str(resp), status=200, mimetype='application/json')

    except SQLAlchemyError as error:
        resp=jsonify_resp(message="user already exist or there was an error", statusCode=409)
        return Response(response=str(resp), mimetype='application/json')


@app.route("/login_api",methods=["POST"])
def login():

    data=request.json
    username=data["username"]
    password= data["password"].encode("utf-8")
    user=Users.query.filter_by(username=username).first()
    if user is not None:
        if bcrypt.checkpw(password,user.password.encode("utf-8")):
            access_token = create_access_token(identity=user.id,additional_claims={"username":user.username})
            resp = jsonify_resp(acsess_token=access_token, statusCode=200)

            return Response(response=str(resp), status=200, mimetype='application/json')
        else:
            resp=jsonify_resp(statusCode=400)
            return Response(response=str(resp), mimetype='application/json')

    resp = jsonify_resp(statusCode=400)
    return Response(response=str(resp), mimetype='application/json')
@app.route("/add_api", methods=["POST"])
@jwt_required()
def add():
    # Access the identity of the current user with get_jwt_identity
    user_id = get_jwt_identity()
    data = request.json


    try:
        reminder = Reminders(user_id, int(data["case_id"]), data["reminder"], data["summery"], data["due_date"])
        db.session.add(reminder)
        db.session.commit()
    except SQLAlchemyError as error:
        print(error)
        resp=jsonify_resp(statusCode=400)
        return Response(response=str(resp), mimetype='application/json')
    finally:
        resp = jsonify_resp(statusCode=200)
        return Response(response=str(resp), mimetype='application/json')



@app.route("/cases_api", methods=["Get"])
@jwt_required()
def cases():

  result_proxy=db.session.execute("select caseid,count(*) as count from reminders where userid=:user_id group by caseid", {"user_id":get_jwt_identity()})
  result=get_list_of_dict(("caseid","count"),list(result_proxy))
  resp = jsonify_resp(statusCode=200,cases=result)
  return Response(response=str(resp), mimetype='application/json')


@app.route("/delete_cases_api", methods=["POST"])
@jwt_required()
def delete_cases():
    user_id = get_jwt_identity()

    try:
        Reminders.query.filter_by(userid=user_id,caseid=int(request.json["case"])).delete()
        db.session.commit()
    except SQLAlchemyError as error:
        print(error)
        return jsonify(status=400)
    finally:
        return jsonify(status=200)

@app.route("/reminder_api", methods=["GET"])
@jwt_required()
def reminder():
    # Access the identity of the current user with get_jwt_identity
    user_id = get_jwt_identity()

    result_proxy=Reminders.query.filter_by(userid=user_id,caseid=int(request.args["case"])).all()
    result=[]
    for row in result_proxy:
        result.append({"id":row.id,"userid":row.userid,"caseid":row.caseid, "task":row.task,"summery":row.summery,"due_date":row.due_date})
    return jsonify(reminder=result, statusCode=200)

@app.route("/update_reminder_api", methods=["POST"])
@jwt_required()
def update_reminder():
    user_id = get_jwt_identity()
    data=request.json


    try:
        reminder=Reminders.query.filter_by(userid=user_id, id=int(request.json["id"])).first()
        reminder.caseid=data["caseid"]
        reminder.task=data["task"]
        reminder.summery=data["summery"]
        reminder.due_date=data["due_date"]
        db.session.commit()
    except SQLAlchemyError as error:
        print(error)
        return jsonify(status=400)
    finally:
        return jsonify(status=200)

@app.route("/delete_reminder_api", methods=["POST"])
@jwt_required()
def delete_reminder():
    user_id = get_jwt_identity()
    try:
        Reminders.query.filter_by(userid=user_id, id=int(request.json["id"])).delete()
        db.session.commit()
    except Exception as error:
        print(error)
        return jsonify(status=400)
    finally:
        return jsonify(status=200)


@app.route("/calenderreminder_api", methods=["get"])
@jwt_required()
def calenderreminder():
    user_id = get_jwt_identity()

    result_proxy=Reminders.query.filter_by(userid=user_id,due_date=request.args["due_date"]).all()
    result=[]
    for row in result_proxy:
        result.append({"id":row.id,"userid":row.userid,"caseid":row.caseid, "task":row.task,"summery":row.summery,"due_date":row.due_date})
    return jsonify(reminder=result)

@app.route("/count_reminder",methods=["POST"])
def count_reminder():
    result = Reminders.query.filter_by(userid=request.json["user_id"],due_date=request.json["due_date"]).count()
    return jsonify(cases=result)


@app.route("/login_rem",methods=["POST"])
def login_rem():
    data = request.json
    username = data["username"]
    password = data["password"].encode("utf-8")
    user = Users.query.filter_by(username=username).first()
    if user is not None:
        if bcrypt.checkpw(password, user.password.encode("utf-8")):
            access_token = create_access_token(identity=user.id, additional_claims={"username": user.username})
            return jsonify(status=200, id=user.id)
        else:
            return jsonify(status=400)
        return jsonify(status=400)
    return jsonify(status=400)

@app.route("/test",methods=["Get"])
def test():
    return jsonify(status=400)

if __name__ == "__main__":
    app.run()