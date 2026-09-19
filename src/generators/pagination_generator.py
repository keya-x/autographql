#!/usr/bin/env python3
import logging
from typing import Dict, List, Any, Tuple
import random
import base64
import json
from graphql import GraphQLSchema, GraphQLField
from .base_generator import BaseQueryGenerator

logger = logging.getLogger(__name__)

class PaginationGenerator(BaseQueryGenerator):
    """Generator for GraphQL pagination queries using first, last, before, after, limit, offset, skip, take parameters."""
    
    def __init__(self, schema: GraphQLSchema, exclude_fields=None, max_hops=2):
        super().__init__(schema, exclude_fields, max_hops)
        self.pagination_params = ['first', 'last', 'before', 'after', 'limit', 'offset', 'skip', 'take']
        
    def generate_query(self) -> Tuple[str, Dict[str, Any]]:
        """Generate a GraphQL query with pagination parameters."""
        try:
            paginated_fields = self._find_paginated_fields()
            
            if not paginated_fields:
                return "", {}
            
            field_name, field_info = random.choice(list(paginated_fields.items()))
            
            if field_name in self.exclude_fields:
                return "", {}
            
            args_string, variables = self._generate_pagination_args(field_info['field'])
            
            response_fields = self._build_pagination_response_fields(field_info)
            if not response_fields:
                return "", {}
            
            var_declarations = self._generate_variable_declarations(variables) if args_string else ""
            
            if args_string:
                query = f"""query {field_name.capitalize()}PaginationQuery{var_declarations} {{
  {field_name}{args_string} {{
    {response_fields}
  }}
}}"""
            else:
                query = f"""query {field_name.capitalize()}PaginationQuery {{
  {field_name} {{
    {response_fields}
  }}
}}"""
            
            return query, variables
            
        except Exception as e:
            logger.debug("Error generating pagination query: %s", e)
            return "", {}
    
    def _find_paginated_fields(self) -> Dict[str, Dict[str, Any]]:
        """Find fields that support pagination parameters."""
        paginated_fields = {}
        
        if self.schema.query_type:
            for field_name, field in self._get_fields(self.schema.query_type).items():
                if self._field_supports_pagination(field):
                    return_type = self._get_field_type_name(field)
                    
                    paginated_fields[field_name] = {
                        'field': field,
                        'return_type': return_type,
                        'pagination_args': self._get_pagination_args(field)
                    }
        
        return paginated_fields
    
    def _field_supports_pagination(self, field: GraphQLField) -> bool:
        """Check if a field supports pagination parameters."""
        if not field.args:
            return False
        
        arg_names = set(field.args.keys())
        return bool(arg_names & set(self.pagination_params))
    
    def _get_pagination_args(self, field: GraphQLField) -> List[str]:
        """Get the pagination arguments available for a field."""
        if not field.args:
            return []
        
        return [arg_name for arg_name in field.args.keys() 
                if arg_name in self.pagination_params]
    
    def _generate_pagination_args(self, field: GraphQLField) -> Tuple[str, Dict[str, Any]]:
        """Generate pagination arguments and variables for a field."""
        if not field.args:
            return "", {}
        
        available_pagination_args = self._get_pagination_args(field)
        if not available_pagination_args:
            return "", {}
        
        args_list = []
        variables = {}
        
        if 'first' in available_pagination_args:
            args_list.append("first: $firstVar")
            first_arg = field.args['first']
            first_type = self._get_type_string(first_arg.type)
            variables['firstVar'] = {
                'value': random.choice([5, 10, 15, 20]),
                'type': first_type
            }
            
            if 'after' in available_pagination_args and random.choice([True, False]):
                args_list.append("after: $afterVar")
                after_arg = field.args['after']
                after_type = self._get_type_string(after_arg.type)
                
                if after_type in ['String', 'String!']:
                    cursor_value = self._generate_cursor_value()
                elif after_type in ['Int', 'Int!']:
                    cursor_value = random.choice([1, 5, 10, 20, 50])
                elif after_type in ['ID', 'ID!']:
                    cursor_value = str(random.randint(1, 100))
                else:
                    cursor_value = self._generate_cursor_value()
                
                variables['afterVar'] = {
                    'value': cursor_value,
                    'type': after_type
                }
        
        elif 'last' in available_pagination_args:
            args_list.append("last: $lastVar")
            last_arg = field.args['last']
            last_type = self._get_type_string(last_arg.type)
            variables['lastVar'] = {
                'value': random.choice([5, 10, 15, 20]),
                'type': last_type
            }
            
            if 'before' in available_pagination_args and random.choice([True, False]):
                args_list.append("before: $beforeVar")
                before_arg = field.args['before']
                before_type = self._get_type_string(before_arg.type)
                
                if before_type in ['String', 'String!']:
                    cursor_value = self._generate_cursor_value()
                elif before_type in ['Int', 'Int!']:
                    cursor_value = random.choice([1, 5, 10, 20, 50])
                elif before_type in ['ID', 'ID!']:
                    cursor_value = str(random.randint(1, 100))
                else:
                    cursor_value = self._generate_cursor_value()
                
                variables['beforeVar'] = {
                    'value': cursor_value,
                    'type': before_type
                }
        
        elif 'limit' in available_pagination_args:
            args_list.append("limit: $limitVar")
            limit_arg = field.args['limit']
            limit_type = self._get_type_string(limit_arg.type)
            variables['limitVar'] = {
                'value': random.choice([5, 10, 15, 20, 25]),
                'type': limit_type
            }
            
            if 'offset' in available_pagination_args and random.choice([True, False]):
                args_list.append("offset: $offsetVar")
                offset_arg = field.args['offset']
                offset_type = self._get_type_string(offset_arg.type)
                variables['offsetVar'] = {
                    'value': random.choice([0, 5, 10, 20, 50]),
                    'type': offset_type
                }
        
        elif 'take' in available_pagination_args:
            args_list.append("take: $takeVar")
            take_arg = field.args['take']
            take_type = self._get_type_string(take_arg.type)
            variables['takeVar'] = {
                'value': random.choice([5, 10, 15, 20]),
                'type': take_type
            }
            
            if 'skip' in available_pagination_args and random.choice([True, False]):
                args_list.append("skip: $skipVar")
                skip_arg = field.args['skip']
                skip_type = self._get_type_string(skip_arg.type)
                variables['skipVar'] = {
                    'value': random.choice([0, 5, 10, 20]),
                    'type': skip_type
                }
        
        other_args = [arg_name for arg_name in field.args.keys() 
                     if arg_name not in self.pagination_params]
        
        if other_args and random.choice([True, False]):
            arg_name = random.choice(other_args)
            arg = field.args[arg_name]
            
            var_name = f"{arg_name}Var"
            arg_value = self._get_input_value(arg.type)
            type_str = self._get_type_string(arg.type)
            
            args_list.append(f"{arg_name}: ${var_name}")
            variables[var_name] = {
                'value': arg_value,
                'type': type_str
            }
        
        args_string = f"({', '.join(args_list)})" if args_list else ""
        return args_string, variables
    
    def _generate_cursor_value(self) -> str:
        """Generate a realistic cursor value (base64 encoded)."""
        cursor_data = {
            'id': str(random.randint(1, 1000)),
            'timestamp': random.randint(1600000000, 1700000000)
        }
        
        cursor_json = json.dumps(cursor_data)
        cursor_bytes = cursor_json.encode('utf-8')
        cursor_base64 = base64.b64encode(cursor_bytes).decode('utf-8')
        
        return cursor_base64
    
    def _build_pagination_response_fields(self, field_info: Dict[str, Any]) -> str:
        """Build response fields for pagination queries."""
        return_type = field_info['return_type']
        
        if not return_type:
            return ""
        
        return self._build_list_response_fields(return_type)
    
    def _build_list_response_fields(self, list_type: str) -> str:
        """Build response fields for simple list pagination."""
        if list_type.startswith('[') and list_type.endswith(']'):
            item_type = list_type[1:-1]
        else:
            item_type = list_type
        
        item_fields = self._get_type_fields(item_type)
        if not item_fields:
            return ""
        
        selected_fields = self._select_node_fields(item_fields)
        return self._build_fields_string(item_type, selected_fields, depth=0, max_depth=self.max_hops)
    
    def _select_node_fields(self, type_fields: Dict[str, GraphQLField]) -> List[str]:
        """Select appropriate fields for nodes/list items."""
        if not type_fields:
            return []
        
        available_fields = {name: field for name, field in type_fields.items() 
                          if name not in self.exclude_fields}
        
        if not available_fields:
            return []
        
        priority_fields = []
        regular_fields = []
        
        for field_name, field in available_fields.items():
            field_type = self._get_field_type_name(field)
            
            if field_type in ['String', 'Int', 'Float', 'Boolean', 'ID'] or \
               field_name.lower() in ['id', 'name', 'title', 'email', 'status', 'created_at', 'updated_at']:
                priority_fields.append(field_name)
            else:
                regular_fields.append(field_name)
        
        selected = []
        
        selected.extend(priority_fields[:6])
        
        remaining_slots = max(0, 4 - len(selected))
        if remaining_slots > 0 and regular_fields:
            selected.extend(random.sample(regular_fields, min(remaining_slots, len(regular_fields))))
        
        if not selected and available_fields:
            selected = [random.choice(list(available_fields.keys()))]
        
        return selected
    
    def _generate_variable_declarations(self, variables: Dict[str, Any]) -> str:
        """Generate variable declarations for the pagination query."""
        if not variables:
            return ""
        
        declarations = []
        for var_name, var_info in variables.items():
            type_str = var_info.get('type', 'String')
            declarations.append(f"${var_name}: {type_str}")
        
        return f"({', '.join(declarations)})" 