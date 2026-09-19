#!/usr/bin/env python3
import logging
from typing import Dict, List, Any, Optional, Tuple
import random
from graphql import GraphQLSchema, GraphQLField, is_non_null_type
from .base_generator import BaseQueryGenerator

logger = logging.getLogger(__name__)

class MutationGenerator(BaseQueryGenerator):
    """Generator for GraphQL mutation queries with insert/delete pairs only."""
    
    def __init__(self, schema: GraphQLSchema, exclude_fields=None, max_hops=2):
        super().__init__(schema, exclude_fields, max_hops)
        self.mutation_type = schema.mutation_type
        self.root_mutation_fields = self._get_fields(self.mutation_type) if self.mutation_type else {}
        
        self.insert_fields = {}
        self.delete_fields = {}
        self._categorize_mutation_fields()
        
        self.current_pair_data = None
        self.is_delete_turn = False
        
        if hasattr(self, 'query_fields') and self.query_fields and self.root_mutation_fields:
            self._filter_query_fields()
    
    def _categorize_mutation_fields(self):
        """Categorize mutation fields into insert and delete operations only."""
        for field_name, field in self.root_mutation_fields.items():
            if field_name in self.exclude_fields:
                continue
                
            field_name_lower = field_name.lower()
            
            if (field_name_lower.startswith('create') or 
                field_name_lower.startswith('insert') or 
                field_name_lower.startswith('add')):
                self.insert_fields[field_name] = field
            
            elif (field_name_lower.startswith('delete') or 
                  field_name_lower.startswith('remove')):
                self.delete_fields[field_name] = field
    
    def _filter_query_fields(self):
        """Filter mutation fields based on query_fields provided."""
        if not self.query_fields:
            return
            
        valid_insert_fields = [field for field in self.query_fields if field in self.insert_fields]
        self.insert_fields = {field_name: field for field_name, field in self.insert_fields.items() 
                             if field_name in valid_insert_fields}
        
        valid_delete_fields = [field for field in self.query_fields if field in self.delete_fields]
        self.delete_fields = {field_name: field for field_name, field in self.delete_fields.items() 
                             if field_name in valid_delete_fields}
    
    def set_query_fields(self, query_fields: List[str]) -> None:
        """Set the specific mutation fields to use for generating mutations."""
        self.query_fields = query_fields
        self._filter_query_fields()
    
    def generate_query(self) -> Tuple[str, Dict[str, Any]]:
        """Generate a GraphQL mutation query - alternates between insert and delete pairs."""
        if not self.insert_fields and not self.delete_fields:
            return "", {}
        
        if not self.insert_fields:
            return "", {}
        if not self.delete_fields:
            return "", {}
        
        try:
            if not self.is_delete_turn:
                return self._generate_insert_mutation()
            else:
                return self._generate_delete_mutation()
                
        except Exception as e:
            logger.debug("Error generating mutation: %s", e)
            return "", {}
    
    def _generate_insert_mutation(self) -> Tuple[str, Dict[str, Any]]:
        """Generate an insert mutation."""
        field_name, field = random.choice(list(self.insert_fields.items()))
        
        args_string, variables = self._generate_mutation_args(field)
        
        return_type = self._get_field_type_name(field)
        response_fields = self._build_response_fields(return_type)
        
        insert_id = None
        for var_name, var_info in variables.items():
            if 'id' in var_name.lower():
                insert_id = var_info.get('value')
                break
        
        self.current_pair_data = {
            'entity_type': self._extract_entity_type(field_name),
            'return_type': return_type,
            'variables': variables,
            'insert_id': insert_id,
            'field_name': field_name
        }
        self.is_delete_turn = True
        
        clean_entity_name = self._get_clean_entity_name(field_name)
        var_declarations = self._generate_variable_declarations(variables) if args_string else ""
        
        if args_string:
            mutation = f"""mutation Create{clean_entity_name}Mutation{var_declarations} {{
  {field_name}{args_string} {{
    {response_fields}
  }}
}}"""
        else:
            mutation = f"""mutation Create{clean_entity_name}Mutation {{
  {field_name} {{
    {response_fields}
  }}
}}"""
        
        simplified_variables = {}
        for var_name, var_info in variables.items():
            simplified_variables[var_name] = self._simplify_variable_value(var_info)
        
        return mutation, simplified_variables
            
    def _generate_delete_mutation(self) -> Tuple[str, Dict[str, Any]]:
        """Generate a delete mutation that corresponds to the previous insert."""
        if not self.current_pair_data:
            field_name, field = random.choice(list(self.delete_fields.items()))
            args_string, variables = self._generate_delete_args(field)
        else:
            entity_type = self.current_pair_data['entity_type']
            matching_delete_field = self._find_matching_delete_field(entity_type)
            
            if matching_delete_field:
                field_name, field = matching_delete_field
                args_string, variables = self._generate_delete_args(field)
            else:
                field_name, field = random.choice(list(self.delete_fields.items()))
                args_string, variables = self._generate_delete_args(field)
        
        return_type = self._get_field_type_name(field)
        response_fields = self._build_response_fields(return_type)
        
        self.current_pair_data = None
        self.is_delete_turn = False
        
        clean_entity_name = self._get_clean_entity_name(field_name)
        var_declarations = self._generate_variable_declarations(variables) if args_string else ""
        
        if args_string:
            mutation = f"""mutation Delete{clean_entity_name}Mutation{var_declarations} {{
  {field_name}{args_string} {{
    {response_fields}
  }}
}}"""
        else:
            mutation = f"""mutation Delete{clean_entity_name}Mutation {{
  {field_name} {{
    {response_fields}
  }}
}}"""
        
        simplified_variables = {}
        for var_name, var_info in variables.items():
            simplified_variables[var_name] = self._simplify_variable_value(var_info)
        
        return mutation, simplified_variables
    
    def _extract_entity_type(self, field_name: str) -> str:
        """Extract the entity type from a mutation field name."""
        field_name_lower = field_name.lower()
        
        for prefix in ['create', 'insert', 'add', 'delete', 'remove']:
            if field_name_lower.startswith(prefix):
                return field_name[len(prefix):].strip('_').lower()
        
        return field_name.lower()
    
    def _get_clean_entity_name(self, field_name: str) -> str:
        """Extract the clean entity name from a mutation field name for use in mutation titles."""
        field_name_lower = field_name.lower()
        
        for prefix in ['create', 'insert', 'add', 'delete', 'remove', 'update', 'modify', 'edit']:
            if field_name_lower.startswith(prefix):
                entity_name = field_name[len(prefix):].strip('_')
                return entity_name.capitalize()
        
        return field_name.capitalize()
    
    def _find_matching_delete_field(self, entity_type: str) -> Optional[Tuple[str, GraphQLField]]:
        """Find a delete field that matches the given entity type."""
        for field_name, field in self.delete_fields.items():
            delete_entity_type = self._extract_entity_type(field_name)
            if delete_entity_type == entity_type:
                return field_name, field
        return None
    
    def _generate_mutation_args(self, field: GraphQLField) -> Tuple[str, Dict[str, Any]]:
        """Generate arguments for a mutation field."""
        if not field.args:
            return "", {}
        
        args_list = []
        variables = {}
        
        for arg_name, arg in field.args.items():
            if is_non_null_type(arg.type):
                arg_value = self._get_input_value(arg.type)
                type_str = self._get_type_string(arg.type)
                arg_value = self._ensure_correct_value_for_type(arg_value, type_str)
                
                if arg_value is not None:
                    var_name = f"{arg_name}Var"
                    args_list.append(f"{arg_name}: ${var_name}")
                    variables[var_name] = {'value': arg_value, 'type': type_str}
        
        if args_list:
            return f"({', '.join(args_list)})", variables
        return "", {}
    
    def _generate_delete_args(self, field: GraphQLField) -> Tuple[str, Dict[str, Any]]:
        """Generate arguments for a delete mutation field."""
        if not field.args:
            return "", {}
        
        args_list = []
        variables = {}
        
        for arg_name, arg in field.args.items():
            if is_non_null_type(arg.type):
                arg_value = self._get_input_value(arg.type)
                type_str = self._get_type_string(arg.type)
                arg_value = self._ensure_correct_value_for_type(arg_value, type_str)
                
                if arg_value is not None:
                    var_name = f"{arg_name}Var"
                    args_list.append(f"{arg_name}: ${var_name}")
                    variables[var_name] = {'value': arg_value, 'type': type_str}
        
        if args_list:
            return f"({', '.join(args_list)})", variables
        return "", {}
    
    def _build_response_fields(self, return_type: str) -> str:
        """Build response fields for a mutation."""
        if not self._is_object_or_interface(return_type):
            return return_type
        
        fields = self._get_type_fields(return_type)
        if not fields:
            return "id"
        
        scalar_fields = []
        for field_name, field in fields.items():
            if field_name in self.exclude_fields:
                continue
            
            field_type_name = self._get_field_type_name(field)
            if not self._is_object_or_interface(field_type_name):
                scalar_fields.append(field_name)
        
        if not scalar_fields:
            return "id"
        
        return " ".join(scalar_fields[:3])
    
    def _generate_variable_declarations(self, variables: Dict[str, Any]) -> str:
        """Generate variable declarations for the mutation."""
        if not variables:
            return ""
        
        var_defs = []
        for var_name, var_info in variables.items():
            var_type = var_info.get('type', 'String')
            if not var_type.endswith('!'):
                var_type += '!'
            var_defs.append(f"${var_name}: {var_type}")
        
        return f"({', '.join(var_defs)})" if var_defs else ""

    def generate_queries(self, count: int) -> List[Tuple[str, Dict[str, Any]]]:
        """Generate multiple mutation queries in insert/delete pairs."""
        queries = []
        for _ in range(count):
            query, variables = self.generate_query()
            queries.append((query, variables))
        return queries 