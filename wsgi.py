if __name__ == '__main__':
	if len(sys.argv) > 1 and sys.argv[1] == 'init':
		db.create_all()
		email = os.environ['ADMINEMAIL']
		password = os.environ['ADMINPASSWORD']
		if db.session.query(User).filter_by(email=email).count() < 1:
			db.session.add(User(
				email=email,
				password=guard.hash_password(password),
				roles='admin'
				))
	app.run()