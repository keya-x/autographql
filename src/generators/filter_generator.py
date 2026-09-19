#!/usr/bin/env python3
import logging
from typing import Dict, Any, Tuple
import random
from .base_generator import BaseQueryGenerator
from graphql import GraphQLInputObjectType

logger = logging.getLogger(__name__)

class FilterQueryGenerator(BaseQueryGenerator):
    def __init__(self, schema, exclude_fields=None, max_hops=2):
        super().__init__(schema, exclude_fields, max_hops)

    def generate_query(self) -> Tuple[str, Dict[str, Any]]:
        filter_fields = []
        for field_name, field in self.root_query_fields.items():
            if field_name in self.exclude_fields:
                continue
            
            if not hasattr(field, 'args') or not field.args:
                continue
                
            has_filter = any('filter' in arg_name.lower() for arg_name in field.args.keys())
            if has_filter:
                filter_fields.append((field_name, field))
        
        if not filter_fields:
            potential_fields = []
            for field_name, field in self.root_query_fields.items():
                if field_name in self.exclude_fields:
                    continue
                
                if hasattr(field, 'args') and field.args:
                    filter_like_args = ['filter', 'where', 'condition', 'criteria', 'query', 'search']
                    has_filter_like = any(any(filter_term in arg_name.lower() for filter_term in filter_like_args) 
                                         for arg_name in field.args.keys())
                    
                    if has_filter_like:
                        potential_fields.append((field_name, field))
                    elif any('id' in arg_name.lower() for arg_name in field.args.keys()):
                        potential_fields.append((field_name, field))
            
            if potential_fields:
                filter_fields = potential_fields
            else:
                return "", {}
        
        field_name, field = random.choice(filter_fields)
        
        filter_like_terms = ['filter', 'where', 'condition', 'criteria', 'query', 'search']
        filter_arg = None
        
        filter_arg = next((arg_name for arg_name in field.args.keys() 
                          if 'filter' in arg_name.lower()), None)
        
        if not filter_arg:
            for term in filter_like_terms:
                filter_arg = next((arg_name for arg_name in field.args.keys() 
                                 if term in arg_name.lower()), None)
                if filter_arg:
                    break
        
        if not filter_arg:
            filter_arg = next((arg_name for arg_name in field.args.keys() 
                              if 'id' in arg_name.lower()), None)
        
        if not filter_arg and field.args:
            filter_arg = next(iter(field.args.keys()))
        
        if not filter_arg:
            return "", {}
        
        filter_type = field.args[filter_arg].type
        filter_type_name = self._get_named_type(filter_type).name
        
        filter_type_obj = self.schema.get_type(filter_type_name)
        if not filter_type_obj:
            return "", {}
            
        if not isinstance(filter_type_obj, GraphQLInputObjectType):
            return "", {}
        
        filter_value = self._get_input_value(filter_type)
        
        if not isinstance(filter_value, dict) or not filter_value:
            filter_value = self._create_schema_based_filter(filter_type_obj)
            
            if not filter_value:
                filter_value = self._create_default_filter(filter_type_name)
        
        return_type = self._get_field_type_name(field)
        try:
            fields_string = self._build_fields_string(return_type, max_depth=2)
        except Exception:
            basic_fields = self._get_basic_fields(return_type)
            if basic_fields:
                fields_string = " ".join(basic_fields)
            else:
                return "", {}
        
        if not fields_string:
            return "", {}
        
        type_str = self._get_type_string(filter_type)
        
        query = f"""query {field_name.capitalize()}FilterQuery($filter: {type_str}) {{
  {field_name}({filter_arg}: $filter) {{
    {fields_string.replace('\n', '\n    ')}
  }}
}}"""
        
        variables = {
            "filter": self._simplify_variable_value({'value': filter_value, 'type': type_str})
        }
        
        return query, variables
    
    def _create_schema_based_filter(self, filter_type_obj: GraphQLInputObjectType) -> Dict[str, Any]:
        """Create a filter based on the actual fields in the schema input type."""
        result = {}
        
        if hasattr(filter_type_obj, 'fields') and filter_type_obj.fields:
            fields = list(filter_type_obj.fields.items())
            num_fields = min(random.randint(1, 2), len(fields))
            selected_fields = random.sample(fields, num_fields)
            
            for field_name, field in selected_fields:
                field_type = field.type
                field_value = self._get_input_value(field_type)
                
                if field_value is not None:
                    result[field_name] = field_value
        
        return result
    
    def _get_basic_fields(self, type_name: str) -> list:
        """Get basic fields for a type when the standard approach fails."""
        fields = self._get_type_fields(type_name)
        if not fields:
            return ["id", "name", "title", "description"]
            
        result = []
        for field_name, field in fields.items():
            if field_name in self.exclude_fields:
                continue
                
            field_type_name = self._get_field_type_name(field)
            type_obj = self.schema.get_type(field_type_name)
            
            if type_obj and hasattr(type_obj, 'name') and type_obj.name in [
                'ID', 'String', 'Int', 'Float', 'Boolean', 'Date', 'DateTime'
            ]:
                result.append(field_name)
                if len(result) >= 3:
                    break
        
        if not result:
            for field in ["id", "name", "title", "code"]:
                if field in fields:
                    result.append(field)
            
        return result or ["id"]

    def _create_default_filter(self, filter_type_name: str) -> Dict[str, Any]:
        """Create a default filter object based on the actual schema structure."""
        filter_type_obj = self.schema.get_type(filter_type_name)
        if filter_type_obj and isinstance(filter_type_obj, GraphQLInputObjectType) and hasattr(filter_type_obj, 'fields'):
            return self._create_schema_based_filter(filter_type_obj)
        
        return {} 