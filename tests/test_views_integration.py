import os
import unittest
from urlparse import urlparse
import mistune

from werkzeug.security import generate_password_hash

# Configure our app to use the testing database
os.environ["CONFIG_PATH"] = "blog.config.TestingConfig"

from blog import app
from blog import models
from blog.database import Base, engine, session

class TestViews(unittest.TestCase):
	def setUp(self):
		""" Test setup """
		self.client = app.test_client()

		# Set up the tables in the database
		Base.metadata.create_all(engine)

		# Create two example users
		self.alice = models.User(name = "Alice"
						      , email = "alice@example.com"
						      , password = generate_password_hash("test")
						       )
		self.bob = models.User(name = "Bob"
						      , email = "bob@example.com"
						      , password = generate_password_hash("test")
						       )

		session.add(self.alice)
		session.add(self.bob)
		session.commit()

	def tearDown(self):
		""" Test teardown """
		# Remove the tables and their data from the database
		Base.metadata.drop_all(engine)

	def simulate_login(self, user):
		with self.client.session_transaction() as http_session:
			http_session["user_id"] = str(user.id)
			http_session["_fresh"] = True
		
	def simulate_logout(self):
		with self.client.session_transaction() as http_session:
				http_session["user_id"] = None

	def testAddPost(self):
		# Does not work before logged in
		response = self.client.post("/post/add", data = {
			"title": "Test Post",
			"content": "Test content"
			})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(urlparse(response.location).path, "/login")
		
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 0)
		
		# Works after logging in
		self.simulate_login(self.alice)

		response = self.client.post("/post/add", data = {
			"title": "Test Post",
			"content": "Test content"
			})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(urlparse(response.location).path, "/")
		
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 1)

		post = posts[0]
		self.assertEqual(post.title, "Test Post")
		self.assertEqual(post.content, "<p>Test content</p>\n")
		self.assertEqual(post.author, self.alice)
	
	def testEditPost_Get(self):
		self.simulate_login(self.alice)

		# Create an example post by Alice
		response = self.client.post("/post/add", data = {
			"title": "Test Post",
			"content": "Test content"
			})
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 1)
		post = posts[0]
		self.assertEqual(post.title, "Test Post")
		self.assertEqual(post.content, "<p>Test content</p>\n")
		self.assertEqual(post.author, self.alice)

		# Redirect if not logged in
		self.simulate_logout()
		response = self.client.get("/post/%i/edit" % post.id)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(urlparse(response.location).path, "/")
		
		# Redirect if user is not author of post
		self.simulate_login(self.bob)
		
		response = self.client.get("/post/%i/edit" % post.id)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(urlparse(response.location).path, "/")

		# Works is user is logged in and author of post
		self.simulate_login(self.alice)

		response = self.client.get("/post/%i/edit" % post.id)
		self.assertEqual(response.status_code, 200)
		
	def testEditPost_Post(self):	
		self.simulate_login(self.alice)

		# Create an example post by Alice
		response = self.client.post("/post/add", data = {
			"title": "Test Post",
			"content": "Test content"
			})
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 1)
		post = posts[0]
		self.assertEqual(post.title, "Test Post")
		self.assertEqual(post.content, "<p>Test content</p>\n")
		self.assertEqual(post.author, self.alice)

		# Redirect if not logged in
		self.simulate_logout()

		response = self.client.post("/post/%i/edit" % post.id, data = {
			"title": "Edited Post Title",
			"content": "Edited content"
			})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(urlparse(response.location).path, "/")
		
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 1)
		post = posts[0]
		self.assertEqual(post.title, "Test Post")
		self.assertEqual(post.content, "<p>Test content</p>\n")
		self.assertEqual(post.author, self.alice)

		# Redirect if user is not author of post
		self.simulate_login(self.bob)

		response = self.client.post("/post/%i/edit" % post.id, data = {
			"title": "Edited Post Title",
			"content": "Edited content"
			})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(urlparse(response.location).path, "/")
		
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 1)
		post = posts[0]
		self.assertEqual(post.title, "Test Post")
		self.assertEqual(post.content, "<p>Test content</p>\n")
		self.assertEqual(post.author, self.alice)

		# Works is user is logged in and author of post
		self.simulate_login(self.alice)

		response = self.client.post("/post/%i/edit" % post.id, data = {
			"title": "Edited Post Title",
			"content": "Edited content"
			})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(urlparse(response.location).path, "/post/%i" % post.id)
		
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 1)
		post = posts[0]
		self.assertEqual(post.title, "Edited Post Title")
		self.assertEqual(post.content, "<p>Edited content</p>\n")
		self.assertEqual(post.author, self.alice)

	def testDeletePost(self):
		self.simulate_login(self.alice)

		# Create an example post by Alice
		response = self.client.post("/post/add", data = {
			"title": "Test Post",
			"content": "Test content"
			})
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 1)
		post = posts[0]
		self.assertEqual(post.title, "Test Post")
		self.assertEqual(post.content, "<p>Test content</p>\n")
		self.assertEqual(post.author, self.alice)

		# Redirect if not logged in
		self.simulate_logout()

		response = self.client.post("/post/%i/delete" % post.id)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(urlparse(response.location).path, "/")
		
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 1)
		post = posts[0]
		self.assertEqual(post.title, "Test Post")
		self.assertEqual(post.content, "<p>Test content</p>\n")
		self.assertEqual(post.author, self.alice)

		# Redirect if user is not author of post
		self.simulate_login(self.bob)

		response = self.client.post("/post/%i/delete" % post.id)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(urlparse(response.location).path, "/")
		
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 1)
		post = posts[0]
		self.assertEqual(post.title, "Test Post")
		self.assertEqual(post.content, "<p>Test content</p>\n")
		self.assertEqual(post.author, self.alice)

		# Works is user is logged in and author of post
		self.simulate_login(self.alice)

		response = self.client.post("/post/%i/delete" % post.id)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(urlparse(response.location).path, "/")
		
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 0)

if __name__ == "__main__":
	unittest.main()