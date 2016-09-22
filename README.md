# jfixture
jfixture is a simple framework I wrote to help me do some unit testing on an database-driven application.  

After a few different attempts at writing similar tools, 
it occurred to me that all I really needed was a simple language to represent the fixture data I was dealing with.  

Based on my needs at the time, I identified two features I really wanted:

* Simple, meaninfgul syntax
* Database independent representation of data
* The ability to reference objects within the fixture language

What I can up with is by no means a comprehensive solution to the question of testing with fixtures, but it was 
sufficient for my needs.  

For simlicity, I embeded the "language" in JSON syntax.  This was because I am a lazy person and neither didn't want to 
write my own parser nor did I want to require additional dependencies. This means I get to use Python's json package
to do my parsing for me, at the cost of unnecessary quotes.  

Here is what the heart of the system looks like.  We assume that fixture data has  been specified in "/path/to/fixture.json".
To do testing with this fixture, we wouuld do the following

```python
import jfixture as jf
# ...do some setting up stuff
with jf.fixture('/path/to/fixture.json'):
 # Do some tests

# Outside the context, the database is cleared and we can do some other, completely unrelated test:

with jf.fixture('/path/to/other_fixture.json'):
 # Do some other tests

```

# Tutorial

Let's go over a brief tutorial of how this system is used.  We first have to cover the ModelAdapter, the mechanics
of which allow jfixture to work with any database one might choose to use.  

## ModelAdapter

The point of a fixture is to install temporary database data to test against.  As such, a fixture framework must either
be written to work for with a particular database or set of databases, or it must provide the necessary abstraction
to allow use with any database system (or, I suppose, both of these options).

The jfixture approach is to provide the necessary abstraction layer; this is done through the ModelAdapter class.

ModelAdapter tells jfixture how to perform the minimal set of operations it needs to in order to set up schema, install 
data in the database, and then undo these things when testing is done.  There are 5 methods that can be implemented, 
but only 3 must be implemented.  Let's look at the interface definition:

```python
class ModelAdapter(object):
    @staticmethod
    def install_model(model):
        pass
        
    @staticmethod
    def clear_model(model):
        pass

    @staticmethod
    def install_model_instance(model, **kwargs):
        raise NotImplemented()

    @staticmethod
    def clear_instance(instance):
        raise NotImplemented()

    @staticmethod
    def get_attribute(instance, attribute):
        raise NotImplemented()
```

The terminology of "Model" is meant to remind us of traditional ORMs.  So, to digest the ModelAdapter, think in terms of
something like SQLAlchemy, where you have models which provide an abstract description of objects in a database. Model
instances correspond objects persisted in the database.  

The first and second methods of the ModelAdapter tell how to create and destroy the schema of a given model.  In the SQLAlchemy
example, this would mean creating and dropping SQL tables.  It is possible that you might have a static test database
that whose schema doesn't change, in which case creating and destroying tables for each batch of tests doesn't make sense.
For this reason, these two methods do not have to be implemented, in which case nothing will happen when jfixture calls them.

The third method, install_model_instance, instantiates a model using the data stored in kwargs and saves it, using 
whatever mechanism is supplied by the underlying database or ORM.  Something has to be returned by this method that will
uniquley identify an object in the database to be removed by the next method, clear_instance.

The clear_instance method takes an object returned by install_model_instance and undoes the latter methods action.  An
example is probably good.  Pretend we have a very simple ORM where we can create and delete model instances like this:

```python
user = User(name="Lauren", age=25)  # instantiates model, doesn't save to DB
user.save()  # save to DB
user.delete() # delete from DB
print("The user's name is {}".format(user.name))
```

As an aside: this is actually [simpleorm](https://github.com/joshgev/simpleorm), which is a toy ORM that I wrote for testing and demonstration of jfixture.  Outside of its utility for this project, it might be a educational to look it 
over to get an idea of how things like SQLAlchemy or Django ORM do some of the things which to me seemed so magical
when I first used them.  Specifically, it is a solid example of why one might use metaprogramming :).

Using this ORM, our methods of install_model_instance and clear_instance will look like this:

```python
@staticmethod
def install_model_instance(model, **kwargs):
  instance = model(**kwargs)
  instance.save()
  return instance
  
@staticmethod
def clear_instance(instance):
  instance.delete()
```

The final method, get_attribute, gets an attribute with the given name from the instance provided as an argument.  
Using our simple ORM as an example, the method would look like this:

```python
@staticmethod
def get_attribute(instance, attribute):
  return getattr(instance, attribute):
```

The test directory contains a working example of a full implementation of ModelAdapter using 
[simpleorm](https://github.com/joshgev/simpleorm) to demonstrate the system and to test it.

## jfixture language

The jfixture language is straight forward.  Let's write a JSON file ("/path/to/simple_fixture.json") to demonstrate the basic usage 
of the language.  We will assume that we have a simple ORM (like the one described above) that is used to describe 
users and documents:

```python
from simpleorm import *

class User(Model):
  user_id = Integer(primary=True)
  name = String()
  age = Integer()
  
  
class Document(Model):
  document_id = Integer(primary=True)
  owner_id = Integer()  # Should be a valid User.user_id
  data = String()
```
Our most basic fixture json file is this:

```json
{
  "@User": {
    "name": "Sally Mae",
    "age": 25
  }
}
```
## jfixture usage
We now have an example of the language.  Let's use it.  First, we'll assume that the models we defined in the previous 
section, User and Document, are defined in a module named "models.py."  Further, we assume that we have implemented a 
ModelAdapter in a module named "adapter.py"

To define the fixture, we have to specify the ModelAdapter and then register our models.  Then,
we use the jfixture.fixture context manager to do our testing.

```python
import jfixture as jf
from models import User, Document
from adapter import MyAdapter

jfixture.set_model_adapter(MyAdapter)
jfixture.register_model(User)
jfixture.register_model(Document)

# At this point, the schema is installed, but the database should be empty.

with jf.fixture('/path/to/simple_fixture.json'):  # This installs the data in simple_fixture.json
  # Within this context, the database should contain our one user object (Sally Mae)
  # and we can do some test using this object
  user = User.get_one(name="Sally Mae")
  assert user.age == 25
  
# Outside of the context manager, the database is cleared of data, but the schema is in tact.  
# We can destroy the schema with a call to jfixture.end():
jf.end()
```

That's all there is to it.  Of course, this is pretty trivial so far, so let's make it a bit more interesting.

## More jfixture features

### References in the Fixture Specification

Remember that one of the key points I wanted was the ability to reference database objects within the fixture language.
The reason for this is made evident by the Document mode: in order to have a valid Document, you need a foreign 
key into some User object that will be installed in the database.  Of course, since the fixture specifies data 
that is **going to be installed** in a database and does not yet exist there, we don't know in general what the
IDs are going to be.  The solution is the feature I want: references in the fixture language.  Here is how we do it 
in jfixture:

```json
{
  "@User, $sally": {
    "name": "Sally Mae",
    "age": 25
  },
  "@Document": {
    "owner_id": "$sally.user_id",
    "data": "stuff"
  }
}
```

Notice, we did two things here: first, we added a name to our one User object: "sally" (the $ is part of the syntax, don't 
omit it :)).  Secondly, the owner_id field of our one document references $sally.  That's all there is to it.

### References in python

In the previous subsection, we introduced the concept of named objects: we named our user object "sally."  When 
we use our fixtures in python, it might be useful to refer to the objects that were described by the fixture.  This
is easily done with jfixture.  Using the json file we wrote in the previous subsection, we can refer to Sally easily:

```python
import jfixture as jf
# ..setup
with jf.fixture('/path/to/fixture.json') as data:
 assert data.sally.age == 25
```

### Multiple Objects
Say Sally owns three documents.  We have two ways of specifying this fixture.  The first method requires us
to name each document object:

```json
{
  "@User, $sally": {
    "name": "Sally Mae",
    "age": 25
  },
  "@Document, $d1": {
    "owner_id": "$sally.user_id",
    "data": "document1"
  },
  "@Document, $d2": {
    "owner_id": "$sally.user_id",
    "data": "document2"
  },
  "@Document, $d3": {
    "owner_id": "$sally.user_id",
    "data": "document3"
  }
}
```

We can write this more concisely, though, if we don't need documents to be named:

```json
{
  "@User, $sally": {
    "name": "Sally Mae",
    "age": 25
  },
  "@Document": [
    {
      "owner_id": "$sally.user_id",
      "data": "document1"
    },
    {
      "owner_id": "$sally.user_id",
      "data": "document2"
    },
    {
      "owner_id": "$sally.user_id",
      "data": "document3"
    }
  ]
}
```

### Nested Objects

Pretend we have two users, Sally and Bob, who each have three documents.  Using the lessons of the previous subsection,
we might write a fixture file like this (note, we will write the json is a slightly more compressed way, since our fixture
file is getting a bit long):

```json
{
  "@User, $sally": { "name": "Sally Mae", "age": 25 },
  "@User, $bob": { "name": "Bob Be","age": 52 },
  "@Document": [
    { "owner_id": "$sally.user_id", "data": "document1" },
    { "owner_id": "$sally.user_id", "data": "document2" },
    { "owner_id": "$sally.user_id", "data": "document3" },
    { "owner_id": "$bob.user_id", "data": "document4" },
    { "owner_id": "$bob.user_id", "data": "document5" },
    { "owner_id": "$bob.user_id", "data": "document6" }
  ]
}
```

This works just fine, but one might imagine that, as fixture files get large, using one long list to specify all 
documents might get a bit disorganized.  To address this problem, jfixture allows objects to be nested within one 
another.  Using this mechanism, we can rewrite the above file as:

```json
{
  "@User, $sally": {
    "name": "Sally Mae",
    "age": 25,
    "@Document": [
     {"owner_id": "$sally.user_id", "data": "document1"},
     {"owner_id": "$sally.user_id", "data": "document2"},
     {"owner_id": "$sally.user_id", "data": "document3"},
    ]
  },
  "@User, $bob": {
    "name": "Bob Be",
    "age": 52,
    "@Document": [
     {"owner_id": "$bob.user_id", "data": "document4"},
     {"owner_id": "$bob.user_id", "data": "document5"},
     {"owner_id": "$bob.user_id", "data": "document6"},
    ]
  }
}
```

Note that writing the fixture file in this way doesn't change anything about the way it is processed; this is simply
a tool to make the fixture file easier to understand, which is useful when writing and debugging large fixture files.

# Insecurity

There are many issues with this system, a small fraction of which I am aware of.  A prominent example is exception handling
which is currently exceptionally poor.  One day I might fix this and other issues (pull requests are welcome).  My primary
motivation for publishing this is simply to share some ideas I had for implementing a simple framework that is actually
useful.
