from sqlalchemy import DateTime
from sqlalchemy_utils import PasswordType, JSONType

from .model_serializer import ModelSerializer
from .field import Field, NestedModelField, NestedAttributesField, PrimaryKeyField

SWAGGER_BASIC_TYPES = {
    str: dict(type='string'),
    bool: dict(type='boolean'),
    int: dict(type='integer', format='int64'),
    float: dict(type='number', format='double'),
    bytes: dict(type='string', format='byte'),
}


def gen_spec(model_serializer: ModelSerializer, http_method: str, is_child=False):
    '''
    Generates a Swagger spec dict for the given `model_serializer` and `http_method`.

    By setting this dict to the `specs_dict` attribute of the respective Resource class method, a full Swagger spec
    can be generated automatic for the API:

        StuffResource.get.specs_dict = gen_spec(stuff_serializer, "GET")

    :param class model_serializer: Resource serializer instance

    :param str http_method: http method used

    :param bool is_child: Tels if the model is a child resource in the route, meaning that parent
        id must be part of the route

    :rtype: dict
    '''
    resource_name = model_serializer.get_model_name()
    parameters = []
    if is_child:
        parameters.append(
            {
                'name': 'parent_id',
                'in': 'path',
                'required': True,
                'type': 'integer',
                'format': 'int64',
            }
        )
    if http_method in ['GET', 'PUT', 'DELETE']:
        parameters.append(
            {'name': 'id', 'in': 'path', 'required': True, 'type': 'integer', 'format': 'int64'}
        )
    if http_method in ['POST', 'PUT']:
        parameters.append(
            {
                'name': 'body',
                'in': 'body',
                'required': True,
                'schema': {'$ref': '#/definitions/%s' % resource_name},
            }
        )

    produces = ["application/json"]
    receives = ["application/json"]

    specs_dict = {
        "tags": [resource_name],
        "parameters": parameters,
        "produces": produces,
        "receives": receives,
        "schemes": ["http", "https"],
        "deprecated": False,
        "security": [{"Bearer": []}],
        "responses": _gen_path_responses(http_method, resource_name),
        "definitions": _gen_object_definition(model_serializer),
    }

    return specs_dict


def _gen_path_responses(http_method, resource_name):
    '''
    This function receives a HTTP method and a resource name and generates the standard responses of the method

    :param str http_method:
        http method used

    :param str resource_name:
        name of the resource being served

    :rtype dict:
    :return: dict containing the standard responses of the method
    '''
    if http_method == 'GET_Collection':
        return {
            '200': {
                'description': 'successful operation',
                'schema': {'type': 'array', 'items': {'$ref': '#/definitions/%s' % resource_name}},
            }
        }
    elif http_method == 'PUT':
        return {
            '204': {'description': 'successfully updated'},
            '400': {'description': 'invalid %s supplied' % resource_name},
            '404': {'description': '%s not found' % resource_name},
        }
    elif http_method == 'GET':
        return {
            '200': {
                'description': 'successful operation',
                'schema': {'$ref': '#/definitions/%s' % resource_name},
            },
            '400': {'description': 'invalid ID supplied'},
            '404': {'description': '%s not found' % resource_name},
        }
    elif http_method == 'POST':
        return {
            '201': {'description': 'the %s was created successfully' % resource_name},
            '405': {'description': 'invalid input'},
        }
    elif http_method == 'DELETE':
        return {
            '204': {'description': 'successfully deleted'},
            '400': {'description': 'invalid ID supplied'},
            '404': {'description': '%s not found' % resource_name},
        }

    return None


def _gen_object_definition(model_serializer: ModelSerializer):
    definitions = {}
    properties = {}
    for field_name, field in model_serializer._fields.items():
        if field_name == 'id':
            continue
        elif isinstance(field, NestedModelField):
            nested_resource_name = field.serializer.get_model_name()
            properties[field_name] = {"$ref": "#/definitions/{}".format(nested_resource_name)}
            definitions.update(_gen_object_definition(field.serializer))
        elif isinstance(field, NestedAttributesField):
            properties[field_name] = {'type': 'object', 'readOnly': True, 'properties': {}}
            for nested_attribute in field.serializer.attributes:
                attr_type = field.serializer.attributes[nested_attribute]
                nested_properties = _gen_object_parameters_from_column(attr_type)
                properties[field_name]['properties'][nested_attribute] = nested_properties
        elif isinstance(field, PrimaryKeyField):
            properties[field_name] = {'type': 'array', 'items': {"type": "integer"}}
        elif isinstance(field, Field):
            col = model_serializer.model_columns.get(field_name)
            if col is None:
                continue
            properties[field_name] = _gen_object_parameters_from_column(col.type)
            if field.load_only:
                properties[field_name]['writeOnly'] = True
            if field.dump_only:
                properties[field_name]['readOnly'] = True
    resource_name = model_serializer.get_model_name()
    definitions[resource_name] = {"type": "object", "properties": properties}
    return definitions


def _gen_object_parameters_from_column(sql_type):
    if isinstance(sql_type, DateTime) or (
        hasattr(sql_type, "impl") and isinstance(sql_type.impl, DateTime)
    ):
        return {'type': 'string', 'format': 'date-time'}
    elif isinstance(sql_type, PasswordType):
        return {'type': 'string', 'format': 'password'}
    elif isinstance(sql_type, JSONType):
        return {
            'type': 'string',
        }
    elif isinstance(sql_type, type):
        return dict(SWAGGER_BASIC_TYPES[sql_type])
    elif hasattr(sql_type, 'python_type'):
        return dict(SWAGGER_BASIC_TYPES[sql_type.python_type])
    else:
        return {}
