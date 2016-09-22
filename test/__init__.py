__author__ = 'jgevirtz'
import jfixture
import simpleorm as orm
import os
import unittest

class User(orm.Model):
    user_id = orm.Integer(primary=True)
    first_name = orm.String()
    last_name = orm.String()
    age = orm.Integer()


class Document(orm.Model):
    document_id = orm.Integer(primary=True)
    owner = orm.Integer()
    data = orm.String()


class Adapter(jfixture.ModelAdapter):
    @staticmethod
    def install_model(model):
        model.create_table()

    @staticmethod
    def install_model_instance(model, **kwargs):
        instance = model(**kwargs)
        instance.save()
        return instance

    @staticmethod
    def clear_instance(instance):
        instance.delete()

    @staticmethod
    def clear_model(model):
        model.drop_table()

    @staticmethod
    def get_attribute(instance, attribute):
        return getattr(instance, attribute)

def setUp():
    orm.connect(
        "localhost",
        "root",
        "root",
        "orm_test")

    jfixture.set_model_adapter(Adapter)
    jfixture.register_model(User)
    jfixture.register_model(Document)

def tearDown():
    jfixture.end()



