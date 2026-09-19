#!/usr/bin/env python3
import logging
from abc import abstractmethod
from typing import Dict, List, Set, Any, Optional, Tuple
import json
import random
import re
from graphql import GraphQLSchema, GraphQLInputObjectType, GraphQLScalarType, GraphQLEnumType, GraphQLInputType, is_object_type, is_interface_type, is_list_type, is_non_null_type

logger = logging.getLogger(__name__)

class BaseQueryGenerator:
    def __init__(self, schema: GraphQLSchema, exclude_fields: Set[str] = None, max_hops: int = 2):
        self.schema = schema
        self.query_type = schema.query_type
        self.exclude_fields = exclude_fields or {'__schema', '__type', '__typename'}
        self.type_fields_cache = {}
        self.root_query_fields = self._get_fields(self.query_type) if self.query_type else {}
        self.query_fields = None
        self.max_hops = max_hops
        
    def set_query_fields(self, query_fields: List[str]) -> None:
        """Set the specific query fields to use for generating queries."""
        self.query_fields = query_fields
        if self.query_fields and self.root_query_fields:
            valid_fields = [field for field in self.query_fields if field in self.root_query_fields]
            self.root_query_fields = {field_name: field for field_name, field in self.root_query_fields.items() 
                                     if field_name in valid_fields}

    def _get_fields(self, type_obj):
        if not type_obj or not hasattr(type_obj, 'fields'):
            return {}
        return type_obj.fields

    def _get_type_fields(self, type_name):
        """Get fields for a type, with additional validation to ensure type exists"""
        if type_name in self.type_fields_cache:
            return self.type_fields_cache[type_name]
        
        type_obj = self.schema.get_type(type_name)
        if not type_obj:
            return {}
        
        fields = self._get_fields(type_obj)
        self.type_fields_cache[type_name] = fields
        return fields

    def _get_named_type(self, type_obj):
        """Unwrap a type from NonNull and List wrappers to get the named type."""
        if is_non_null_type(type_obj) or is_list_type(type_obj):
            return self._get_named_type(type_obj.of_type)
        return type_obj

    def _get_field_type_name(self, field):
        type_obj = field.type
        named_type = self._get_named_type(type_obj)
        return named_type.name

    def _is_object_or_interface(self, type_name):
        """Check if a type is an object or interface, with validation."""
        type_obj = self.schema.get_type(type_name)
        if not type_obj:
            return False
        return is_object_type(type_obj) or is_interface_type(type_obj)

    def _get_scalar_value(self, scalar_type: GraphQLScalarType) -> Any:
        """Generate a random value for a scalar type."""
        type_name = scalar_type.name
        
        if type_name == 'Int':
            return random.randint(1, 100)
        elif type_name == 'Float':
            return round(random.uniform(1.0, 100.0), 2)
        elif type_name == 'String':
            return random.choice(['test', 'example', 'sample', 'demo', 'query'])
        elif type_name == 'Boolean':
            return random.choice([True, False])
        elif type_name == 'ID':
            return str(random.randint(1, 100))
        elif type_name == 'Date':
            return f"{random.randint(2020, 2023):04d}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        elif type_name == 'DateTime':
            return f"{random.randint(2020, 2023):04d}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}Z"
        elif type_name == 'Time':
            return f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
        elif type_name == 'JSON':
            return {"key": "value", "number": random.randint(1, 100)}
        else:
            return f"sample_{type_name.lower()}"

    def _get_input_value(self, input_type: GraphQLInputType) -> Any:
        """Generate a random value for an input type."""
        if is_non_null_type(input_type):
            return self._get_input_value(input_type.of_type)

        if is_list_type(input_type):
            inner_value = self._get_input_value(input_type.of_type)
            return [inner_value] if inner_value is not None else []

        named_type = self._get_named_type(input_type)
        
        if isinstance(named_type, GraphQLScalarType):
            return self._get_scalar_value(named_type)
        
        elif isinstance(named_type, GraphQLEnumType):
            values = list(named_type.values.keys())
            return random.choice(values) if values else None
        
        elif isinstance(named_type, GraphQLInputObjectType):
            result = {}
            fields = named_type.fields
            
            required_fields = [name for name, field in fields.items() 
                               if is_non_null_type(field.type)]
            
            for field_name in required_fields:
                field = fields[field_name]
                value = self._get_input_value(field.type)
                if value is not None:
                    result[field_name] = value
            
            non_required_fields = [name for name in fields.keys() 
                                   if name not in required_fields]

            chosen_fields: List[str] = []
            if non_required_fields:
                min_optional = 0 if required_fields else 1
                max_optional = len(non_required_fields)
                num_optional = random.randint(min_optional, max_optional)
                if num_optional > 0:
                    chosen_fields = random.sample(non_required_fields, num_optional)
            
            for field_name in chosen_fields:
                field = fields[field_name]
                value = self._get_input_value(field.type)
                if value is not None:
                    result[field_name] = value
            
            return result
        
        return None

    def _select_random_fields(self, type_name: str, max_fields: int = 5) -> List[str]:
        """Select a random subset of fields from a type, ensuring they exist in the schema."""
        fields = self._get_type_fields(type_name)
        if not fields:
            return []
        
        if type_name == self.query_type.name and self.query_fields:
            eligible_fields = [f for f in self.query_fields if f in fields.keys() and f not in self.exclude_fields]
        else:
            eligible_fields = [f for f in fields.keys() if f not in self.exclude_fields]
        
        if not eligible_fields:
            return []
        
        num_fields = min(max_fields, len(eligible_fields))
        if num_fields == 0:
            return []
        
        selected_fields = random.sample(eligible_fields, random.randint(1, num_fields))
        return [f for f in selected_fields if f in fields]

    def _build_fields_string(self, type_name: str, field_names: Optional[List[str]] = None, 
                           depth: int = 0, max_depth: Optional[int] = None) -> str:
        """Build a string of fields for a type, with nested fields up to max_depth."""
        if max_depth is None:
            max_depth = self.max_hops
            
        if depth > max_depth or not type_name:
            return ""
        
        type_obj = self.schema.get_type(type_name)
        if not type_obj or (not is_object_type(type_obj) and not is_interface_type(type_obj)):
            return ""
        
        fields = self._get_type_fields(type_name)
        if not fields:
            return ""
        
        if field_names is None:
            field_names = self._select_random_fields(type_name)
        
        field_strings = []
        indent = '  ' * depth
        
        for field_name in field_names:
            if field_name in self.exclude_fields or field_name not in fields:
                continue
                
            field = fields[field_name]
            field_type_name = self._get_field_type_name(field)
            
            if not self._is_object_or_interface(field_type_name):
                field_strings.append(field_name)
                continue
            
            nested_content = self._build_nested_content(field_type_name, depth, max_depth)
            indented_content = nested_content.replace('\n', f'\n  {indent}')
            field_strings.append(f"{field_name} {{\n  {indent}{indented_content}\n{indent}}}")
        
        return '\n'.join(field_strings)
    
    def _build_nested_content(self, field_type_name: str, depth: int, max_depth: int) -> str:
        """Build nested field content for an object/interface type."""
        if depth >= max_depth:
            scalar_fields = self._select_leaf_scalar_fields(field_type_name)
            if scalar_fields:
                return '\n'.join(scalar_fields)
            return self._get_default_field(field_type_name)
        
        nested_field_names = self._select_random_fields(field_type_name)
        if nested_field_names:
            nested_str = self._build_fields_string(field_type_name, nested_field_names, depth + 1, max_depth)
            if nested_str:
                return nested_str
        
        scalar_fields = self._select_leaf_scalar_fields(field_type_name)
        if scalar_fields:
            return '\n'.join(scalar_fields)
        return self._get_default_field(field_type_name)

    def _select_leaf_scalar_fields(self, type_name: str) -> List[str]:
        """Select a random non-empty subset of scalar fields for leaf-level selections. """
        fields = self._get_type_fields(type_name)
        if not fields:
            return []

        required_scalars = []
        optional_scalars = []

        for field_name, field in fields.items():
            if field_name in self.exclude_fields:
                continue
            field_type_name = self._get_field_type_name(field)
            if not self._is_object_or_interface(field_type_name):
                if is_non_null_type(field.type):
                    required_scalars.append(field_name)
                else:
                    optional_scalars.append(field_name)

        selected = list(required_scalars)

        if optional_scalars:
            num_optional = random.randint(
                0 if selected else 1,
                len(optional_scalars)
            )
            if num_optional > 0:
                selected.extend(random.sample(optional_scalars, num_optional))

        if not selected:
            return [self._get_default_field(type_name)]

        return selected

    def _get_default_field(self, type_name: str) -> str:
        """Get a default field for an object type for subfield selection."""
        fields = self._get_type_fields(type_name)
        if not fields:
            return "id"
            
        for preferred in ["id", "name", "title", "key", "code"]:
            if preferred in fields:
                return preferred
                
        return next(iter(fields.keys()))

    @abstractmethod
    def generate_query(self) -> Tuple[str, Dict[str, Any]]:
        """Generate a GraphQL query. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement generate_query()")

    def generate_queries(self, count: int) -> List[Tuple[str, Dict[str, Any]]]:
        """Generate multiple queries."""
        queries = []
        for _ in range(count):
            query, variables = self.generate_query()
            queries.append((query, variables))
        return queries
        
    def should_add_feature(self, feature_prob: float = 0.3) -> bool:
        """Determine if a feature should be added based on probability."""
        return random.random() < feature_prob
        
    def add_directive_to_field(self, field_str: str) -> Tuple[str, str, Dict[str, Any]]:
        """Add a directive to a field."""
        directives = ['includeDetails', 'skipOptionalFields']
        directive_choice = random.choice(directives)
        
        directive_variables = {}
        if directive_choice == 'includeDetails':
            directive = '@include(if: $includeDetails)'
            directive_variables = {'includeDetails': {'value': True, 'type': 'Boolean'}}
        else:
            directive = '@skip(if: $skipOptionalFields)'
            directive_variables = {'skipOptionalFields': {'value': False, 'type': 'Boolean'}}
        
        if '{' in field_str:
            opening_brace_idx = field_str.find('{')
            field_name = field_str[:opening_brace_idx].strip()
            
            modified_field = f"{field_name} {directive} {{"
            
            if not field_str.strip().endswith('{'):
                content_after_brace = field_str[opening_brace_idx+1:].lstrip()
                modified_field += f"\n  {content_after_brace}"
        else:
            modified_field = field_str.strip() + f" {directive}"
        
        return modified_field, 'directives', directive_variables
        
    def add_filter_to_field(self, field, field_name: str) -> Tuple[str, str, Dict[str, Any]]:
        """Add a filter argument to a field."""
        if not hasattr(field, 'args') or not field.args:
            return field_name, '', {}
            
        pagination_args = ['first', 'last', 'limit', 'offset', 'after', 'before', 'page', 'size', 'skip', 'take']
        filter_like_terms = ['filter', 'where', 'condition', 'criteria', 'query', 'search', 'id']
        
        filter_arg = None
        for term in filter_like_terms:
            filter_arg = next((arg_name for arg_name in field.args.keys() 
                             if term in arg_name.lower() and not any(pagination_term in arg_name.lower() for pagination_term in pagination_args)), None)
            if filter_arg:
                break
        
        if not filter_arg and field.args:
            suitable_args = [arg_name for arg_name in field.args.keys() 
                           if not any(pagination_term in arg_name.lower() for pagination_term in pagination_args)]
            filter_arg = suitable_args[0] if suitable_args else None
        
        if not filter_arg:
            return field_name, '', {}
        
        filter_type = field.args[filter_arg].type
        filter_value = self._get_input_value(filter_type)
        
        if not isinstance(filter_value, dict) or not filter_value:
            filter_value = self._create_default_filter(filter_type)
        
        type_str = self._get_type_string(filter_type)
        var_name = f"{filter_arg}Var"
        field_with_filter = f"{field_name}({filter_arg}: ${var_name})"
        
        variables = {var_name: {'value': filter_value, 'type': type_str}}
        
        return field_with_filter, 'filters', variables
    
    def _create_default_filter(self, filter_type) -> Dict[str, Any]:
        """Create a default filter object based on the actual schema structure."""
        filter_type_obj = self._get_named_type(filter_type)
        if isinstance(filter_type_obj, GraphQLInputObjectType) and hasattr(filter_type_obj, 'fields'):
            return self._get_input_value(filter_type_obj)
        return {}
        
    def _generate_non_filter_args(self, field) -> str:
        """Generate field arguments as a string without including filter variables or pagination arguments."""
        if not field.args:
            return ""
        
        exclude_args = [
            'filter', 'where', 'condition', 'criteria', 'query', 'search',
            'first', 'last', 'limit', 'offset', 'after', 'before', 'page', 'size', 'skip', 'take'
        ]
        
        args_list = []
        for arg_name, arg in field.args.items():
            if any(exclude_term in arg_name.lower() for exclude_term in exclude_args):
                continue
                
            arg_value = self._get_input_value(arg.type)
            if arg_value is not None:
                args_list.append(f"{arg_name}: {json.dumps(arg_value)}")
        
        return f"({', '.join(args_list)})" if args_list else ""

    def _ensure_correct_value_for_type(self, value, type_name):
        """Ensure that the value is appropriate for the given GraphQL type."""
        if value is None:
            return None
            
        scalar_types = ['Int', 'Float', 'String', 'Boolean', 'ID']
        base_type = type_name.replace('!', '').replace('[', '').replace(']', '')
        is_scalar = base_type in scalar_types
        
        if isinstance(value, dict) and is_scalar:
            for key in ['eq', 'gt', 'lt', 'ne']:
                if key in value:
                    return value[key]
            
            if len(value) > 0:
                return next(iter(value.values()))
            
            if 'Int' in type_name:
                return random.randint(1, 100)
            elif 'Float' in type_name:
                return round(random.uniform(1.0, 100.0), 2)
            elif 'Boolean' in type_name:
                return random.choice([True, False])
            elif 'ID' in type_name:
                return str(random.randint(1, 100))
            else:
                return "default_value"
                
        if isinstance(value, dict) and not is_scalar:
            return value
            
        if isinstance(value, list):
            if not type_name.startswith('[') or not type_name.endswith(']'):
                return self._ensure_correct_value_for_type(value[0], type_name) if value else None
            else:
                inner_type = type_name[1:-1].replace('!', '')
                return [self._ensure_correct_value_for_type(item, inner_type) for item in value]
            
        if 'ID' in type_name:
            return str(value)
        
        elif 'Int' in type_name:
            if isinstance(value, str) and value.isdigit():
                return int(value)
            elif isinstance(value, float):
                return int(value)
            elif not isinstance(value, int):
                return random.randint(1, 100)
            return value
        
        elif 'Float' in type_name:
            if isinstance(value, str) and (value.isdigit() or re.match(r'^-?\d+(\.\d+)?$', value)):
                return float(value)
            elif not isinstance(value, float) and not isinstance(value, int):
                return round(random.uniform(1.0, 100.0), 2)
            return value
        
        elif 'Boolean' in type_name:
            if isinstance(value, str):
                if value.lower() in ['true', 'yes', '1']:
                    return True
                elif value.lower() in ['false', 'no', '0']:
                    return False
                else:
                    return random.choice([True, False])
            elif not isinstance(value, bool):
                return random.choice([True, False])
            return value
            
        elif 'String' in type_name:
            return str(value)
        
        return value

    def _get_type_string(self, type_obj):
        """Get a string representation of a GraphQL type for use in variable declarations."""
        if is_non_null_type(type_obj):
            return f"{self._get_type_string(type_obj.of_type)}!"
        elif is_list_type(type_obj):
            return f"[{self._get_type_string(type_obj.of_type)}]"
        else:
            return type_obj.name 

    def _get_field_args(self, field, use_variables: bool = False) -> Tuple[str, Dict[str, Any]]:
        """Generate field arguments as a string and return variables dictionary."""
        if not field.args:
            return "", {}
        
        field_args_list = []
        field_vars = {}
        
        for arg_name, arg in field.args.items():
            if arg_name in ['__typename']:
                continue
                
            arg_value = self._get_input_value(arg.type)
            if arg_value is not None:
                if use_variables:
                    var_name = f"{arg_name}Var"
                    field_args_list.append(f"{arg_name}: ${var_name}")
                    field_vars[var_name] = {
                        'value': arg_value,
                        'type': self._get_type_string(arg.type)
                    }
                else:
                    field_args_list.append(f"{arg_name}: {json.dumps(arg_value)}")
        
        field_args = f"({', '.join(field_args_list)})" if field_args_list else ""
        return field_args, field_vars

    def _simplify_variable_value(self, var_info):
        """Simplify variable values for the final output."""
        if isinstance(var_info, dict) and 'value' in var_info:
            var_type = var_info.get('type', 'String')
            value = var_info['value']
            
            scalar_types = ['Int', 'Float', 'String', 'Boolean', 'ID']
            clean_type = var_type.replace('!', '').replace('[', '').replace(']', '')
            is_scalar = clean_type in scalar_types
            
            if is_scalar and isinstance(value, dict):
                return self._ensure_correct_value_for_type(value, var_type)
            else:
                return value
        else:
            return var_info