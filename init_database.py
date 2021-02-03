from app import db, User, guard
import os

if __name__ == '__main__':
	db.create_all()
	email = os.environ['ADMINEMAIL']
	password = os.environ['ADMINPASSWORD']
	if db.session.query(User).filter_by(email=email).count() < 1:
		db.session.add(User(
			email=email,
			password=guard.hash_password(password),
			roles='admin'
			))
		db.session.commit()