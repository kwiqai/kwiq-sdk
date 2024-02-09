from pathlib import Path

import sys

import inspect
import yaml
from abc import ABC, abstractmethod
from pydantic_core import PydanticUndefined
from typing import Union, Type, ClassVar, Any, Callable, get_args, get_origin

from pydantic import BaseModel, parse_obj_as

from kwiq.core.errors import ValidationError

InputType = Union[Type[BaseModel], None]
OutputType = Union[Type[BaseModel], type, None]


class Typed(ABC, BaseModel):
    __input_type: ClassVar[Type] = None
    __output_type: ClassVar[Type] = None
    __schema: ClassVar[dict] = None
    __compact_schema: ClassVar[str] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        class_name = cls.__name__
        if not hasattr(cls, '__abstractmethods__') and class_name != 'Flow' and class_name != 'Task':
            cls.__inspect_fn()

    @classmethod
    def __inspect_fn(cls):
        sig = inspect.signature(cls.fn)
        cls.__input_fn_params = sig.parameters
        cls.__output_type = sig.return_annotation
        cls.validate_and_build_fn_schema(cls.fn)

    @classmethod
    def get_schema(cls):
        return cls.__schema

    @classmethod
    def get_compact_schema(cls):
        return cls.__compact_schema

    def execute(self, **kwargs) -> Any:
        fn_params = self.__class__.__input_fn_params

        # Prepare and validate arguments to pass to fn based on the signature
        fn_args = {}
        for name, param in fn_params.items():
            if name == 'self':
                continue

            param_type = param.annotation
            if param_type is inspect.Parameter.empty:
                param_type = None
            else:
                origin = get_origin(param_type)
                args = get_args(param_type)
                if origin is Union and type(None) in args:
                    # This is an Optional, extract the first non-None type
                    param_type = next((arg for arg in args if arg is not type(None)), None)

            if name in kwargs:
                arg = kwargs[name]
                try:
                    if param_type is None or isinstance(arg, param_type):
                        fn_args[name] = arg
                    elif issubclass(param_type, (int, float, str, bool, list, dict, tuple, set, Path)):
                        fn_args[name] = param_type(arg)
                    elif issubclass(param_type, BaseModel):
                        # If expected type is a Pydantic model, parse it accordingly
                        fn_args[name] = param_type(**arg if isinstance(arg, dict) else arg)
                    else:
                        # Validate and convert parameter types using Pydantic's parse_obj_as
                        fn_args[name] = parse_obj_as(param_type, arg)
                except ValidationError as e:
                    raise ValidationError(f"Parameter validation failed for '{name}': {str(e)}")
            elif param_type is not None:
                # attempt to create from kwargs
                try:
                    if issubclass(param_type, (int, float, str, bool, list, dict, tuple, set, Path)):
                        if param.default is not inspect.Parameter.empty:
                            fn_args[name] = param.default
                        else:
                            raise ValueError(f"Missing required parameter: '{name}'")
                    if issubclass(param_type, BaseModel):
                        fn_args[name] = param_type(**kwargs)
                    else:
                        # Validate and convert parameter types using Pydantic's parse_obj_as
                        print("Parsing obj as...")
                        fn_args[name] = parse_obj_as(param_type, kwargs)
                except ValidationError as _:
                    if param.default is not inspect.Parameter.empty:
                        fn_args[name] = param.default
                    else:
                        raise ValueError(f"Missing required parameter: '{name}'")
            elif param.default is not inspect.Parameter.empty:
                fn_args[name] = param.default
            else:
                raise ValueError(f"Missing required parameter: '{name}'")

        result = self.fn(**fn_args)

        return self.validate_result_data(result)

    @abstractmethod
    def fn(self, *args, **kwargs) -> Any:
        """
        Execute with the given data.

        Parameters:
        - args: Positional arguments for the flow.
        - kwargs: Keyword arguments for the flow.

        Returns:
        - The output data produced, if any.
        """
        pass

    def validate_result_data(self, data) -> OutputType:
        output_type = self.__class__.__output_type

        # print(f"{self.__class__} Output type: {output_type} output type class: {output_type.__class__} data: {data}")

        if self.__output_type is None:
            result = None
        elif issubclass(output_type, (int, float, str, bool, list, dict, tuple, set, Path)):
            result = data
        elif issubclass(output_type, BaseModel):
            try:
                # Check if data is already an instance of the input model
                if isinstance(data, output_type):
                    result = data
                else:
                    result = output_type(**data)
            except ValidationError as e:
                raise ValidationError(f"Result data validation failed: {str(e)}")
        else:
            result = data
        return result

    @classmethod
    def get_pydantic_model_schema(cls, model: Type[BaseModel]):
        schema = {}
        errors = []
        for field_name, field_info in model.model_fields.items():
            default_value = None
            if field_info.default != PydanticUndefined:
                default_value = field_info.default

            field_type = field_info.annotation
            if field_type is inspect.Parameter.empty:
                field_type = None
            else:
                origin = get_origin(field_type)
                args = get_args(field_type)
                if origin is Union and type(None) in args:
                    # This is an Optional, extract the first non-None type
                    field_type = next((arg for arg in args if arg is not type(None)), None)

            if field_type is None:
                errors.append(f"ERROR: fn param '{field_name}' has no type. Not allowed")
            if issubclass(field_type, (int, float, str, bool, list, dict, tuple, set, Path)):
                schema[field_name] = {"type": field_type.__name__, "default": default_value}
            elif issubclass(field_type, BaseModel):
                child_schema, child_errors = Typed.get_pydantic_model_schema(field_type)
                if len(child_errors) > 0:
                    errors.extend(child_errors)
                schema[field_name] = {"type": 'pydantic',
                                      "schema": child_schema,
                                      "default": default_value}
            else:
                errors.append(f"ERROR: fn param '{field_name}' is unknown Python class.\n"
                              f"       Only basic types (int, float, str, bool, list, dict, tuple, set, Path)\n"
                              f"       or pydantic model or data class are allowed")

        return schema, errors

    @classmethod
    def build_fn_schema(cls, fn: Callable) -> (dict[str, Any], []):
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
            else:
                origin = get_origin(field_type)
                args = get_args(field_type)
                if origin is Union and type(None) in args:
                    # This is an Optional, extract the first non-None type
                    field_type = next((arg for arg in args if arg is not type(None)), None)

            default_value = param.default if param.default != inspect.Parameter.empty else None

            if field_type is None:
                errors.append(f"ERROR: fn param '{field_name}' has no type. Not allowed")
            elif issubclass(field_type, (int, float, str, bool, list, dict, tuple, set, Path)):
                config_structure[field_name] = {"type": field_type.__name__,
                                                "default": default_value}
            elif issubclass(field_type, BaseModel):
                child_schema, child_errors = Typed.get_pydantic_model_schema(field_type)
                if len(child_errors) > 0:
                    errors.extend(child_errors)

                config_structure[field_name] = {"type": 'pydantic',
                                                "schema": child_schema,
                                                "default": default_value}
            else:
                errors.append(f"ERROR: fn param '{field_name}' is unknown Python class.\n"
                              f"       Only basic types (int, float, str, bool, list, dict, tuple, set, Path)\n"
                              f"       or pydantic model or data class are allowed")

        return config_structure, errors

    @classmethod
    def get_schema_compact(cls, schema):
        compact_schema = {}
        for field, field_info in schema.items():
            field_type = field_info['type']
            if field_type == 'pydantic':
                compact_schema[field] = Typed.get_schema_compact(field_info['schema'])
            else:
                compact_str = f"{field_info['type']}"
                if field_info['default']:
                    compact_str += f" ({field_info['default']})"
                compact_schema[field] = compact_str

        return compact_schema

    @classmethod
    def validate_and_build_fn_schema(cls, fn: Callable):
        schema, errors = Typed.build_fn_schema(fn)
        if len(errors) > 0:
            for error in errors:
                print(error, file=sys.stderr)
            raise ValidationError("ERROR in function implementation")
        else:
            cls.__schema = schema
            cls.__compact_schema = yaml.dump(Typed.get_schema_compact(schema))
