#!/usr/bin/env python3
import logging
from typing import Dict, Any, Tuple
import random
from .base_generator import BaseQueryGenerator
from graphql import is_non_null_type

logger = logging.getLogger(__name__)

class DirectiveQueryGenerator(BaseQueryGenerator):
    def __init__(self, schema, exclude_fields=None, max_hops=2):
        super().__init__(schema, exclude_fields, max_hops)

    def generate_query(self) -> Tuple[str, Dict[str, Any]]:
        """Generate a GraphQL query with @include and @skip directives."""
        if not self.root_query_fields:
            return "", {}
        
        try:
            available_fields = [f for f in (self.query_fields or self.root_query_fields.keys()) 
                              if f in self.root_query_fields and f not in self.exclude_fields]
                
            if not available_fields:
                return "", {}
            
            valid_fields = []
            
            for field_name in available_fields:
                field = self.root_query_fields.get(field_name)
                if field:
                    try:
                        required_args = {}
                        
                        for arg_name, arg in field.args.items():
                            if is_non_null_type(arg.type):
                                arg_value = self._get_input_value(arg.type)
                                type_str = self._get_type_string(arg.type)
                                arg_value = self._ensure_correct_value_for_type(arg_value, type_str)
                                
                                if arg_value is not None:
                                    required_args[arg_name] = {
                                        'value': arg_value,
                                        'type': type_str
                                    }
                        
                        if required_args and len(required_args) != sum(1 for arg in field.args.values() if is_non_null_type(arg.type)):
                            continue
                                
                        return_type = self._get_field_type_name(field)
                        if self._is_object_or_interface(return_type):
                            type_fields = self._get_type_fields(return_type)
                            if type_fields and len(type_fields) > 0:
                                if required_args:
                                    valid_fields.append((field_name, field, return_type, required_args))
                                else:
                                    valid_fields.append((field_name, field, return_type))
                    except Exception:
                        continue
            
            if not valid_fields:
                return "", {}
                
            if len(valid_fields) > 0 and len(valid_fields[0]) > 3:
                field_name, field, return_type, required_args = random.choice(
                    [f for f in valid_fields if len(f) > 3]
                )
                
                field_args_list = []
                field_vars = {}
                
                for arg_name, arg_info in required_args.items():
                    var_name = f"{arg_name}Var"
                    field_args_list.append(f"{arg_name}: ${var_name}")
                    field_vars[var_name] = {
                        'value': arg_info['value'],
                        'type': arg_info['type']
                    }
                
                field_args = f"({', '.join(field_args_list)})" if field_args_list else ""
            else:
                field_tuple = random.choice(valid_fields)
                if len(field_tuple) <= 3:
                    field_name, field, return_type = field_tuple
                    field_args, field_vars = self._get_field_args(field)
                else:
                    field_name, field, return_type, required_args = field_tuple
                    field_args_list = []
                    field_vars = {}
                    
                    for arg_name, arg_info in required_args.items():
                        var_name = f"{arg_name}Var"
                        field_args_list.append(f"{arg_name}: ${var_name}")
                        field_vars[var_name] = {
                            'value': arg_info['value'],
                            'type': arg_info['type']
                        }
                    
                    field_args = f"({', '.join(field_args_list)})" if field_args_list else ""
            
            directive_variables = {
                'includeDetails': {'value': True, 'type': 'Boolean!'},
                'skipOptionalFields': {'value': False, 'type': 'Boolean!'},
            }
            
            selected_fields = self._select_random_fields(return_type)
            if not selected_fields:
                return "", {}
                
            num_fields = min(len(selected_fields), 5)
            if num_fields == 0:
                return "", {}
            
            selected_fields = selected_fields[:num_fields]
            
            field_strings = []
            used_directives = set()
            
            for selected_field_name in selected_fields:
                if selected_field_name == field_name:
                    continue
                    
                field = self._get_type_fields(return_type).get(selected_field_name)
                if not field:
                    continue
                
                field_type = self._get_field_type_name(field)
                apply_directive = random.random() < 0.4
                directive = ""
                
                if apply_directive:
                    if random.choice([True, False]):
                        directive = '@include(if: $includeDetails)'
                        used_directives.add('includeDetails')
                    else:
                        directive = '@skip(if: $skipOptionalFields)'
                        used_directives.add('skipOptionalFields')
                
                field_strings.append(self._format_field_with_directive(
                    selected_field_name, field_type, directive, apply_directive
                ))

            if not used_directives and field_strings:
                max_attempts = min(5, len(field_strings))
                
                for _ in range(max_attempts):
                    field_idx = random.randint(0, len(field_strings) - 1)
                    field_info = field_strings[field_idx]
                    
                    if field_info.strip() == '}' or not any(char.isalpha() for char in field_info.strip()):
                        continue
                        
                    field_name_parts = field_info.split(' ')
                    sub_field_name = field_name_parts[0] if field_name_parts else field_info
                    
                    directive_choice = random.choice(['include', 'skip'])
                    if directive_choice == 'include':
                        directive = '@include(if: $includeDetails)'
                        used_directives.add('includeDetails')
                    else:
                        directive = '@skip(if: $skipOptionalFields)'
                        used_directives.add('skipOptionalFields')
                    
                    if '{' in field_info:
                        opening_brace = field_info.find('{')
                        content_after_brace = field_info[opening_brace+1:].lstrip()
                        field_strings[field_idx] = f"{sub_field_name} {directive} {{\n      {content_after_brace}"
                    else:
                        field_strings[field_idx] = f"{sub_field_name} {directive}"
                    
                    break

            variable_defs = []
            filtered_directive_variables = {}
            for var_name, var_info in directive_variables.items():
                if var_name in used_directives:
                    var_type = var_info.get('type', 'String')
                    variable_defs.append(f"${var_name}: {var_type}")
                    filtered_directive_variables[var_name] = var_info
            
            for var_name, var_info in field_vars.items():
                if isinstance(var_info, dict) and 'type' in var_info:
                    var_type = var_info['type']
                    variable_defs.append(f"${var_name}: {var_type}")
                    filtered_directive_variables[var_name] = var_info
                else:
                    if isinstance(var_info, int):
                        var_type = "Int!"
                    elif isinstance(var_info, float):
                        var_type = "Float!"
                    elif isinstance(var_info, bool):
                        var_type = "Boolean!"
                    else:
                        var_type = "String!"
                    
                    variable_defs.append(f"${var_name}: {var_type}")
                    filtered_directive_variables[var_name] = {'value': var_info, 'type': var_type}
            
            formatted_vars = [f"  {var_def}" for var_def in variable_defs]
            variable_string = "\n".join(formatted_vars)
            
            formatted_field_strings = "\n    ".join(field_strings)
            
            query = f"""query {field_name.capitalize()}DirectiveQuery(
{variable_string}
) {{
  {field_name}{field_args} {{
    {formatted_field_strings}
  }}
}}"""
            
            result_variables = {}
            for var_name, var_info in filtered_directive_variables.items():
                result_variables[var_name] = self._simplify_variable_value(var_info)
                
            return query, result_variables
        except Exception as e:
            logger.debug("Error generating directive query: %s", e)
            return "", {}
    
    def _format_field_with_directive(self, field_name: str, field_type: str, 
                                      directive: str, has_directive: bool) -> str:
        """Format a field with optional directive and nested content."""
        if not self._is_object_or_interface(field_type):
            return f"{field_name} {directive}".strip() if directive else field_name
        
        nested_fields = self._select_random_fields(field_type)
        nested_str = ""
        if nested_fields:
            nested_str = self._build_fields_string(field_type, nested_fields, max_depth=2)
        
        if not nested_str:
            nested_str = self._get_default_field(field_type)
        
        if has_directive:
            indented_str = nested_str.replace('\n', '\n        ')
            return f"{field_name} {directive} {{\n        {indented_str}\n      }}"
        else:
            indented_str = nested_str.replace('\n', '\n      ')
            return f"{field_name} {{\n      {indented_str}\n    }}" 