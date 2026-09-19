#!/usr/bin/env python3
import logging
from typing import Dict, Any, Tuple
import random
from .base_generator import BaseQueryGenerator

logger = logging.getLogger(__name__)

class InlineFragmentQueryGenerator(BaseQueryGenerator):
    def __init__(self, schema, exclude_fields=None, max_hops=2):
        super().__init__(schema, exclude_fields, max_hops)

    def generate_query(self) -> Tuple[str, Dict[str, Any]]:
        if not self.root_query_fields:
            return "", {}
        
        try:
            add_directive = self.should_add_feature(0.3)
            add_filter = False if add_directive else self.should_add_feature(0.3)
            query_sub_category = ''
            
            query_variables = {}
            
            interface_fields = []
            for field_name, field in self.root_query_fields.items():
                if field_name in self.exclude_fields:
                    continue
                
                return_type = self._get_field_type_name(field)
                type_obj = self.schema.get_type(return_type)
                
                if hasattr(type_obj, 'interfaces'):
                    interface_fields.append((field_name, field, return_type))
            
            if not interface_fields:
                return "", {}
            
            field_name, field, return_type = random.choice(interface_fields)
            
            field_args = ""
            if add_filter:
                field_name_with_filter, sub_category, filter_variables = self.add_filter_to_field(field, field_name)
                if sub_category == 'filters':
                    field_name, field_args = field_name_with_filter.split('(', 1)
                    field_args = '(' + field_args
                    query_variables.update(filter_variables)
                    query_sub_category = 'filters'
                else:
                    field_args = self._generate_non_filter_args(field)
            else:
                field_args = self._generate_non_filter_args(field)
            
            type_fields = self._select_random_fields(return_type)
            if not type_fields:
                return "", {}
            
            original_fields_string = self._build_fields_string(return_type, type_fields, max_depth=2)
            
            if add_directive:
                field_lines = original_fields_string.split('\n')
                processed_lines = []
                
                for line in field_lines:
                    line_stripped = line.strip()
                    if not line_stripped or line_stripped == '}':
                        processed_lines.append(line)
                        continue
                    
                    if self.should_add_feature(0.5):
                        if '}' in line_stripped and not any(char.isalpha() for char in line_stripped):
                            processed_lines.append(line)
                            continue
                        
                        field_with_directive, sub_category, directive_variables = self.add_directive_to_field(line)
                        processed_lines.append(field_with_directive)
                        if sub_category == 'directives' and query_sub_category != 'filters':
                            query_variables.update(directive_variables)
                            query_sub_category = 'directives'
                    else:
                        processed_lines.append(line)
                
                fields_string = '\n'.join(processed_lines)
            else:
                fields_string = original_fields_string
            
            variable_section = ""
            if query_variables:
                var_defs = []
                for var_name, var_info in query_variables.items():
                    var_type = var_info.get('type', 'String')
                    if not var_type.endswith('!'):
                        var_type += '!'
                    var_defs.append(f"${var_name}: {var_type}")
                
                if var_defs:
                    variable_section = f"({', '.join(var_defs)})"
            
            query = f"""query {field_name.capitalize()}InlineQuery{variable_section} {{
  {field_name}{field_args} {{
    ... on {return_type} {{
      {fields_string.replace('\n', '\n      ')}
    }}
  }}
}}"""
            
            final_variables = {}
            for var_name, var_info in query_variables.items():
                final_variables[var_name] = self._simplify_variable_value(var_info)
            
            return query, final_variables
        except Exception as e:
            logger.debug("Error generating inline fragments query: %s", e)
            return "", {}