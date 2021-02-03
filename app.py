import os
import sys
from flask import Flask, request
import flask_sqlalchemy
import flask_praetorian
import flask_cors
from flask_marshmallow import Marshmallow




# Initialize flask app for the example
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'top secret'
app.config['JWT_ACCESS_LIFESPAN'] = {'hours': 24}
app.config['JWT_REFRESH_LIFESPAN'] = {'days': 30}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.getcwd(), 'database.db')}"

db = flask_sqlalchemy.SQLAlchemy(app)
ma = Marshmallow(app)
guard = flask_praetorian.Praetorian()
cors = flask_cors.CORS(app)


class User(db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.Text, unique=True)
	password = db.Column(db.Text)
	roles = db.Column(db.Text)
	is_active = db.Column(db.Boolean, default=True, server_default='true')
	events = db.relationship("Event")

	@property
	def rolenames(self):
		try:
			return self.roles.split(',')
		except Exception:
			return []

	@classmethod
	def lookup(cls, email):
		return cls.query.filter_by(email=email).one_or_none()

	@classmethod
	def identify(cls, id):
		return cls.query.get(id)

	@property
	def identity(self):
		return self.id

	def is_valid(self):
		return self.is_active


class Category(db.Model):
	__tablename__ = 'category'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.Text, unique=True)


class Category_Schema(ma.Schema):
	class Meta:
		fields = ("id", "name")

category_schema = Category_Schema()
categories_schema = Category_Schema(many=True)


class Event(db.Model):
	__tablename__ = 'event'
	id = db.Column(db.Integer, primary_key=True)
	category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	place = db.Column(db.Text)
	address = db.Column(db.Text)
	start_date = db.Column(db.BigInteger)
	end_date = db.Column(db.BigInteger)


class Event_Schema(ma.Schema):
	class Meta:
		fields = ("id", "category_id","user_id","place","address","start_date","end_date")

event_schema = Event_Schema()
events_schema = Event_Schema(many=True)

# Initialize the flask-praetorian instance for the app
guard.init_app(app, User)


# Views
@app.route('/')
def home():
	return {"Hello": "World"}, 200

  
@app.route('/login', methods=['POST'])
def login():
	"""
	.. example::
	   $ curl http://localhost:5000/login -X POST \
		 -d '{"email":"Sergio","password":"password123"}'
	"""
	req = request.get_json()
	email = req.get('email', None)
	password = req.get('password', None)
	user = guard.authenticate(email, password)
	return {'access_token': guard.encode_jwt_token(user)}, 200


@app.route('/register', methods=['POST'])
def register():
	req = request.get_json()
	email = req.get('email', None)
	password = req.get('password', None)
	app.logger.info('recupera')
	if db.session.query(User).filter_by(email=email).count() < 1:
		db.session.add(User(
			email=email,
			password=guard.hash_password(password),
			))
		db.session.commit()
		return {'msg': 'usuario creado'}, 200

	else:
		return {'msg': 'Email already in use'}, 400

  
@app.route('/refresh', methods=['POST'])
def refresh():
	"""
	.. example::
	   $ curl http://localhost:5000/refresh -X GET \
		 -H "Authorization: Bearer <token>"
	"""
	old_token = request.get_data()
	new_token = guard.refresh_jwt_token(old_token)
	return {'access_token': new_token}, 200


@app.route('/events')
@flask_praetorian.auth_required
def list_events():
	user = flask_praetorian.current_user()
	return {"events":events_schema.dump(user.events)}


@app.route('/categories')
def list_categories():
	categories = Category.query.all()
	return {"categories":categories_schema.dump(categories)}


@app.route('/categories', methods=['POST'])
def create_category():
	req = request.get_json()
	name = req['name']
	category = Category(name=name)
	db.session.add(category)
	db.session.commit()
	return category_schema.dump(category)


@app.route('/events', methods=['POST'])
@flask_praetorian.auth_required
def create_event():
	user = flask_praetorian.current_user()
	req = request.get_json()
	category_id = req['category_id']
	user_id = user.id
	place = req['place']
	address = req['address']
	start_date = req['start_date']
	end_date = req['end_date']
	event = Event(
		category_id=category_id,
		user_id=user_id,
		place=place,
		address=address,
		start_date=start_date,
		end_date=end_date,
		)
	db.session.add(event)
	db.session.commit()
	return event_schema.dump(event)


@app.route('/events/<int:event_id>', methods=['GET','PUT','DELETE'])
@flask_praetorian.auth_required
def get_event(event_id):
	user = flask_praetorian.current_user()
	event = Event.query.get_or_404(event_id)
	if user.id != event.user_id:
		return {"msg":"you can only access events you created"},403
	if request.method == 'GET':
		return event_schema.dump(event)
	elif request.method == 'PUT':
		req = request.get_json()
		if 'category_id' in req:
			event.category_id = req['category_id']
		if 'place' in req:
			event.place = req['place']
		if 'address' in req:
			event.address = req['address']
		if 'start_date' in req:
			event.start_date = req['start_date']
		if 'end_date' in req:
			event.end_date = req['end_date']

		db.session.commit()
		return event_schema.dump(event)
	else:
		db.session.delete(event)
		db.session.commit()
		return '',204


# Run the app
if __name__ == '__main__':
	if len(sys.argv) > 1 and sys.argv[1] == 'init':
		db.drop_all()
		db.create_all()
		if db.session.query(User).filter_by(email='secardenas@cardenas.com').count() < 1:
			db.session.add(User(
				email='secardenas@cardenas.com',
				password=guard.hash_password('password123'),
				roles='admin'
				))
	app.run(host='0.0.0.0', port=8080)