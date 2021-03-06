__author__ = 'jgevirtz'

import os
import unittest
import jfixture

from test import User, Document

base = os.path.dirname(os.path.realpath(__file__))
fixture = "{}/test.json".format(base)
class TestSimple(unittest.TestCase):
    def test_get_one(self):
        with jfixture.fixture(fixture):
            ann = User.get_one(first_name="Ann")
            assert ann.last_name == "Smith"

    def test_get_many(self):
        with jfixture.fixture(fixture):
            smiths = User.get_many(last_name="Smith")
            assert len(smiths) == 2, [s.first_name for s in smiths]

    def test_fixture_data_object(self):
        with jfixture.fixture(fixture) as data:
            assert data.user1.first_name == "Ann"
            assert data.user2.first_name == "Bob"

    def test_anon(self):
        with jfixture.fixture(fixture):
            john = User.get_one(first_name="John")
            assert john.last_name == "Able"

    def test_document(self):
        with jfixture.fixture(fixture) as data:
            document = Document.get_one(owner=data.user2.user_id)
            assert document.data == "This is a document"

    def test_document_nested(self):
        with jfixture.fixture(fixture) as data:
            document = Document.get_one(owner=data.user3.user_id)
            assert document.data == "Sally's document"

    def test_documents_nested(self):
        with jfixture.fixture(fixture) as data:
            documents = Document.get_many(owner=data.user4.user_id)
            assert len(documents) == 2, len(documents)
            expected = {
                "list data 1",
                "list data 2",
            }

            data = set(d.data for d in documents)

            assert data == expected, data




