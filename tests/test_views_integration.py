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

		# Create an example user
		self.user = models.User(name = "Alice"
						      , email = "alice@example.com"
						      , password = generate_password_hash("test")
						       )

		session.add(self.user)
		session.commit()

	def tearDown(self):
		""" Test teardown """
		# Remove the tables and their data from the database
		Base.metadata.drop_all(engine)

	def simulate_login(self):
		with self.client.session_transaction() as http_session:
			http_session["user_id"] = str(self.user.id)
			http_session["_fresh"] = True

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
		self.simulate_login()

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
		self.assertEqual(post.author, self.user)

	def testEditPost(self):
		# Create an example post by Alice
		self.post = models.Post(title = "Test Post"
								, content = mistune.markdown("Test content") 
								, author = self.user
								)
		session.add(self.post)
		session.commit()

		# Does not work before logged in
		response = self.client.get("/post/<post_id>/edit", data = {
			"post_id": self.post.id
			})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(urlparse(response.location).path, "/")
		
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 1)

		posts = session.query(models.Post).all()
		post = posts[0]
		self.assertEqual(post.title, "Test Post")
		self.assertEqual(post.content, "<p>Test content</p>\n")
		self.assertEqual(post.author, self.user)
		
		# Does not work if user is not author of post

		# Works is user is logged in and author of post

if __name__ == "__main__":
	unittest.main()