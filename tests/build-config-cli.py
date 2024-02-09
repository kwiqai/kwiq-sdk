import inspect
import yaml
from pydantic import BaseModel
from pydantic_core import PydanticUndefined
from typing import Callable, Dict, Any, Type


class ChildModel(BaseModel):
    childParam1: str
    childParam2: int = 42
    childParam3: bool = True


class ExampleModel(BaseModel):
    param1: str
    param2: int = 42
    param3: bool = True
    child: ChildModel


class ExampleClass:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age


def get_pydantic_model_schema(model: Type[BaseModel]):
    schema = {}
    errors = []
    for field_name, field_info in model.model_fields.items():
        default_value = None
        if field_info.default != PydanticUndefined:
            default_value = field_info.default

        field_type = field_info.annotation
        if field_type is inspect.Parameter.empty:
            field_type = None

        if field_type is None:
            # config_structure[param_name] = {'type': None}
            errors.append(f"ERROR: fn param '{field_name}' has no type. Not allowed")
        if issubclass(field_type, (int, float, str, bool, list, dict, tuple, set)):
            schema[field_name] = {"type": field_type.__name__, "default": default_value}
        elif issubclass(field_type, BaseModel):
            child_schema, child_errors = get_pydantic_model_schema(field_type)
            if len(child_errors) > 0:
                errors.extend(child_errors)
            schema[field_name] = {"type": 'pydantic',
                                  "schema": child_schema,
                                  "default": default_value}
        else:
            errors.append(f"ERROR: fn param '{field_name}' is unknown Python class.\n"
                          f"       Only basic types (int, float, str, bool, list, dict, tuple, set)\n"
                          f"       or pydantic model or data class are allowed")

    return schema, errors


def get_flow_config_structure(fn: Callable) -> (Dict[str, Any], []):
    sig = inspect.signature(fn)
    parameters = sig.parameters

    errors = []
    config_structure = {}
    for field_name, param in parameters.items():
        if field_name == 'self':
            continue

        field_type = param.annotation
        if field_type is inspect.Parameter.empty:
            field_type = None

        default_value = None
        if param.default != inspect.Parameter.empty:
            default_value = param.default

        if field_type is None:
            errors.append(f"ERROR: fn param '{field_name}' has no type. Not allowed")
        elif issubclass(field_type, (int, float, str, bool, list, dict, tuple, set)):
            config_structure[field_name] = {"type": field_type.__name__,
                                            "default": default_value}
        elif issubclass(field_type, BaseModel):
            child_schema, child_errors = get_pydantic_model_schema(field_type)
            if len(child_errors) > 0:
                errors.extend(child_errors)

            config_structure[field_name] = {"type": 'pydantic',
                                            "schema": child_schema,
                                            "default": default_value}
        else:
            errors.append(f"ERROR: fn param '{field_name}' is unknown Python class.\n"
                          f"       Only basic types (int, float, str, bool, list, dict, tuple, set)\n"
                          f"       or pydantic model or data class are allowed")

    return config_structure, errors


def get_schema_compact(schema):
    compact_schema = {}
    for field, field_info in schema.items():
        field_type = field_info['type']
        if field_type == 'pydantic':
            compact_schema[field] = get_schema_compact(field_info['schema'])
        else:
            compact_str = f"{field_info['type']}"
            if field_info['default']:
                compact_str += f" ({field_info['default']})"
            compact_schema[field] = compact_str

    return compact_schema


def print_schema(fn: Callable):
    schema, errors = get_flow_config_structure(fn)
    if len(errors) > 0:
        for error in errors:
            print(error)
    else:
        print(yaml.dump(get_schema_compact(schema), default_flow_style=False))
        # print(config_structure)


# Example function with parameters
def example_function(param1: str, ex_model: ExampleModel, param2: int = 42,
                     param3: bool = True):
    pass


# Print YAML structure for the expected config
print_schema(example_function)
