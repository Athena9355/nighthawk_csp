# flask imports
from flask import Blueprint, render_template, request, url_for, redirect, jsonify, make_response
from flask_restful import Api, Resource
import requests

from crud.model import Users, print_tester

# blueprint defaults https://flask.palletsprojects.com/en/2.0.x/api/#blueprint-objects
app_crud = Blueprint('crud', __name__,
                     url_prefix='/crud',
                     template_folder='templates/crud/',
                     static_folder='static',
                     static_url_path='assets')

# API generator https://flask-restful.readthedocs.io/en/latest/api.html#id1
api = Api(app_crud)


# ##### Routes within this blueprint broker information between HTML and Model code
# Default URL of blueprint and connecting to crud() function
@app_crud.route('/')
def crud():
    """extracts Users table from DB and returns in json format"""
    users = Users.query.all()
    return render_template("crud.html", table=[peep.read() for peep in users])


# CRUD create/add a new record to the table
@app_crud.route('/create/', methods=["POST"])
def create():
    if request.form:
        """extract data from form and call model_create"""
        po = Users(
            request.form.get("name"),
            request.form.get("email"),
            request.form.get("password"),
            request.form.get("phone")
        )
        po.create()
    return redirect(url_for('.crud'))


# CRUD read, which is filtering table based off of ID
@app_crud.route('/read/', methods=["POST"])
def read():
    table = []
    if request.form:
        userid = request.form.get("userid")
        po = Users.query.filter_by(userID=userid).first()
        if po is not None:
            table = [po.read()]  # placed in list for easier/consistent use within HTML
    return render_template("crud.html", table=table)


# CRUD update
@app_crud.route('/update/', methods=["POST"])
def update():
    if request.form:
        userid = request.form.get("userid")
        name = request.form.get("name")
        po = Users.query.filter_by(userID=userid).first()
        if po is not None:
            po.update(name)
    return redirect(url_for('crud.crud'))


# CRUD delete
@app_crud.route('/delete/', methods=["POST"])
def delete():
    if request.form:
        userid = request.form.get("userid")
        po = Users.query.filter_by(userID=userid).first()
        if po is not None:
            po.delete()
    return redirect(url_for('crud.crud'))


@app_crud.route('/search/')
def search():
    return render_template("search.html")


@app_crud.route('/search/term/', methods=["POST"])
def search_term():
    req = request.get_json()
    term = req['term']
    # term structured in anywhere form
    term = "%{}%".format(term)
    # "ilike" is case insensitive partial match
    people = Users.query.filter((Users.name.ilike(term)) | (Users.email.ilike(term)))
    # return filtered Users table into a list of dictionary rows
    query = [peep.read() for peep in people]
    response = make_response(jsonify(query), 200)

    return response


class UsersAPI:
    # class for create/post
    class _Create(Resource):
        def post(self, name, email, password, phone):
            po = Users(name, email, password, phone)
            person = po.create()
            if person:
                return person.read()
            return {'message': f'Processed {name}, either a format error or {email} is duplicate'}, 210

    # class for read/get
    class _Read(Resource):
        def get(self):
            users = Users.query.all()
            return [peep.read() for peep in users]

    # class for update/put
    class _Update(Resource):
        def put(self, email, name):
            po = Users.query.filter_by(email=email).first()
            if po is None:
                return {'message': f"{email} is not found"}, 210
            po.update(name)
            return po.read()

    class _UpdateAll(Resource):
        def put(self, email, name, password, phone):
            po = Users.query.filter_by(email=email).first()
            if po is None:
                return {'message': f"{email} is not found"}, 210
            po.update(name, password, phone)
            return po.read()

    # class for delete
    class _Delete(Resource):
        def delete(self, userid):
            po = Users.query.filter_by(userID=userid).first()
            if po is None:
                return {'message': f"{userid} is not found"}, 210
            data = po.read()
            po.delete()
            return data

    # building RESTapi resource
    api.add_resource(_Create, '/create/<string:name>/<string:email>/<string:password>/<string:phone>')
    api.add_resource(_Read, '/read/')
    api.add_resource(_Update, '/update/<string:email>/<string:name>')
    api.add_resource(_UpdateAll, '/update/<string:email>/<string:name>/<string:password>/<string:phone>')
    api.add_resource(_Delete, '/delete/<int:userid>')


# play with api on localhost, server must be running
def api_tester():
    # local host URL for model
    url = 'http://127.0.0.1:5222/crud'

    # test conditions
    API = 0
    METHOD = 1
    tests = [
        ['/create/Wilma Flintstone/wilma@bedrock.org/123wifli/0001112222', "post"],
        ['/create/Fred Flintstone/fred@bedrock.org/123wifli/0001112222', "post"],
        ['/read/', "get"],
        ['/update/wilma@bedrock.org/Wilma S Flintstone/123wsfli/0001112229', "put"],
        ['/update/wilma@bedrock.org/Wilma Slaghoople Flintstone', "put"],
        ['/delete/4', "delete"],
        ['/delete/5', "delete"],
    ]

    # loop through each test condition and provide feedback
    for test in tests:
        print()
        print(f"({test[METHOD]}, {url + test[API]})")
        if test[METHOD] == 'get':
            response = requests.get(url + test[API])
        elif test[METHOD] == 'post':
            response = requests.post(url + test[API])
        elif test[METHOD] == 'put':
            response = requests.put(url + test[API])
        elif test[METHOD] == 'delete':
            response = requests.delete(url + test[API])
        else:
            print("unknown RESTapi method")
            continue

        print(response)
        try:
            print(response.json())
        except:
            print("unknown error")


if __name__ == "__main__":
    api_tester()  # validates api's requires server to be running
    print_tester()
