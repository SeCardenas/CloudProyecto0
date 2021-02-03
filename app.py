import os
import flask
import flask_sqlalchemy
import flask_praetorian
import flask_cors
from models import db


guard = flask_praetorian.Praetorian()
cors = flask_cors.CORS()

# Initialize flask app for the example
app = flask.Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'top secret'
app.config['JWT_ACCESS_LIFESPAN'] = {'hours': 24}
app.config['JWT_REFRESH_LIFESPAN'] = {'days': 30}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, server_default='true')

    @classmethod
    def lookup(cls, username):
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)

    @property
    def identity(self):
        return self.id

    def is_valid(self):
        return self.is_active

# Initialize the flask-praetorian instance for the app
guard.init_app(app, User)

# Initialize a local database for the example
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.getcwd(), 'database.db')}"
db.init_app(app)

# Initializes CORS so that the api_tool can talk to the example app
cors.init_app(app)

# Views
@app.route('/')
def home():
    return {"Hello": "World"}, 200

  
@app.route('/login', methods=['POST'])
def login():
    """
    .. example::
       $ curl http://localhost:5000/login -X POST \
         -d '{"username":"Sergio","password":"password123"}'
    """
    req = flask.request.get_json()
    username = req.get('username', None)
    password = req.get('password', None)
    user = guard.authenticate(username, password)
    return {'access_token': guard.encode_jwt_token(user)}, 200

  
@app.route('/refresh', methods=['POST'])
def refresh():
    """
    .. example::
       $ curl http://localhost:5000/refresh -X GET \
         -H "Authorization: Bearer <token>"
    """
    print("refresh request")
    old_token = request.get_data()
    new_token = guard.refresh_jwt_token(old_token)
    return {'access_token': new_token}, 200
  
  
@app.route('/protected')
@flask_praetorian.auth_required
def protected():
    """
    .. example::
       $ curl http://localhost:5000/protected -X GET \
         -H "Authorization: Bearer <token>"
    """
    return {message: 'protected endpoint'}


# Run the example
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)