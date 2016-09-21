__author__ = 'jgevirtz'
import json
import re
import random
from contextlib import contextmanager
from collections import namedtuple



class ModelAdapter(object):
    @staticmethod
    def install_model(model):
        """
        Install model in database.  A ModelAdapter for MySQL, for example, would create a table.
        :return: None
        """
        raise NotImplemented()

    @staticmethod
    def install_model_instance(model, **kwargs):
        """
        Install an instance of a database model. A ModelAdapter for MySQL, for example, would insert a row.
        :return: Instance of model created
        """
        raise NotImplemented()

    @staticmethod
    def clear_instance(instance):
        """
        Remove an instance of a database model. A ModelAdapter for MySQL, for example, would remove a row.
        :return: None
        """
        raise NotImplemented()

    @staticmethod
    def clear_model(model):
        """
        Remove model from the database. A ModelAdapter for Mysql, for example, would drop a table.
        :return: None
        """

    @staticmethod
    def get_attribute(instance, attribute):
        raise NotImplemented()


_adapter = None
_models = {}
_dependencies = {}
_installed = {}

_MODEL_KEY_PATTERN = r'@(?P<model>\w+)(,\s*\$(?P<name>\w+))?'
_DEPENDENCY_PATTERN = r'\s*\$(?P<instance_name>\w+)\.(?P<attribute>\w+)'

ModelInstance = namedtuple('ModelInstance', 'model name attributes')
ModelDependency = namedtuple('ModelDependency', 'instance_name attribute target')



def set_model_adapter(adapter):
    global _adapter
    _adapter = adapter

def register_model(model, name=None):
    if not name:
        name = model.__name__
    _models[name] = model
    _adapter.install_model(model)

def end():
    for m in _models.values():
        _adapter.clear_model(m)

def _scan_model_attributes(raw_model):
    attributes = {}
    for k, v in raw_model.items():
        if not re.match(_MODEL_KEY_PATTERN, k):
            attributes[k] = v
    return attributes

def _scan_instance_dependencies(instance):
    dependencies = []
    for k, v in instance.attributes.items():
        if isinstance(v, str):
            match = re.match(_DEPENDENCY_PATTERN, v)
            if match:
                groups = match.groupdict()
                dependency = ModelDependency(
                    groups['instance_name'],
                    groups['attribute'],
                    k)
                dependencies.append(dependency)
    return dependencies

def _get_model_instances(raw):
    models = []
    for key, value in raw.items():
        match = re.match(_MODEL_KEY_PATTERN, key)
        if not match:
            continue

        groupdict = match.groupdict()
        model = groupdict['model']
        name = groupdict['name']

        if not name:
            if isinstance(value, list):
                for i in value:
                    name = ''.join([str(random.randint(0, 9)) for i in range(50)])
                    attributes = _scan_model_attributes(i)
                    print ("LIST: {}".format(attributes))
                    print ("MODEL: {}".format(model))
                    models.append(ModelInstance(model, name, attributes))
                    models += _get_model_instances(i)
            else:
                name = ''.join([str(random.randint(0, 9)) for i in range(50)])
                attributes = _scan_model_attributes(value)
                models.append(ModelInstance(model, name, attributes))
                models += _get_model_instances(value)
        else:
            attributes = _scan_model_attributes(value)
            models.append(ModelInstance(model, name, attributes))
            models += _get_model_instances(value)

    return models

def _dependencies_met(instance):
    for d in _dependencies[instance.name]:
        if d.instance_name not in _installed:
            return False
    return True

def _get_next(instances):
    passing = [i for i in filter(_dependencies_met, instances)]
    failing = [i for i in filter(lambda x: not _dependencies_met(x), instances)]
    return passing, failing

def _resolve_dependencies(instance):
    dependencies = _dependencies[instance.name]
    new_instance = ModelInstance(
        instance.model,
        instance.name,
        instance.attributes)
    for d in dependencies:
        try:
            new_instance.attributes[d.target] = _adapter.get_attribute(_installed[d.instance_name], d.attribute)
        except:
            raise Exception("Error getting attribute '{}' from ${}".format(d.attribute, d.instance_name))
    return new_instance

def _install_instance(instance):
    if instance.model not in _models.keys():
        raise Exception("Model '{}' is not registered".format(instance.model))
    model = _models[instance.model]
    instance = _resolve_dependencies(instance)
    return _adapter.install_model_instance(model, **instance.attributes)

def _install_fixture(fixture):
    with open(fixture) as fin:
        contents = fin.read()
    raw = json.loads(contents)
    instances = _get_model_instances(raw)

    debug = __name__ == '__main__'

    if debug:
        for instance in instances:
            print("Found instance of model {} with name {}".format(instance.model, instance.name))
            dependencies = _scan_instance_dependencies(instance)
            for d in dependencies:
                print("\t dependency: {}.{}".format(d.instance_name, d.attribute))

    for i in instances:
        _dependencies[i.name] = _scan_instance_dependencies(i)

    while len(instances) > 0:
        batch, instances = _get_next(instances)
        if len(batch) == 0:
            raise Exception("Dependency error!  The following instances have dependencies that "
                            "are impossible to satisfy: {}".format([i.attributes for i in instances]))
        for i in batch:
            print('\t{} {}'.format(i.model, i.name))
            _installed[i.name] = _install_instance(i)

class FixtureInstance(object):
    def __init__(self, installed):
        self.__dict__.update(installed)


@contextmanager
def fixture(fixture):
    global _dependencies, _installed
    _install_fixture(fixture)
    yield FixtureInstance(_installed)

    for m in _installed.values():
        _adapter.clear_instance(m)

    _dependencies = {}
    _installed = {}

if __name__ == '__main__':
    _install_fixture('test/nose/fixture2/test.json')




