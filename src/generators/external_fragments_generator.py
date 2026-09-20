#!/usr/bin/env python3
import logging
from typing import Dict, Any, Tuple
import random
from .base_generator import BaseQueryGenerator

logger = logging.getLogger(__name__)

class ExternalFragmentQueryGenerator(BaseQueryGenerator):
    def __init__(self, schema, exclude_fields=None, max_hops=2):
        super().__init__(schema, exclude_fields, max_hops)
        self.used_fragment_names = set()
        
    def _get_unique_fragment_name(self, type_name: str) -> str:
        base_name = f"Fragment{type_name}"
        if base_name not in self.used_fragment_names:
            self.used_fragment_names.add(base_name)
            return base_name
        
        for i in range(1, 1000):
            name = f"{base_name}{i}"
            if name not in self.used_fragment_names:
                self.used_fragment_names.add(name)
                return name
        
        return f"{base_name}{random.randint(1000, 9999)}"
        
    def generate_query(self) -> Tuple[str, Dict[str, Any]]:
        if not self.root_query_fields:
            return "", {}
        
        available_fields = [f for f in self.root_query_fields.keys() if f not in self.exclude_fields]
        if not available_fields:
            return "", {}
            
        try:
            add_directive = self.should_add_feature(0.3)
            add_filter = False if add_directive else self.should_add_feature(0.3)
            query_sub_category = ''
            
            query_variables = {}
            
            query_field_name = random.choice(available_fields)
            query_field = self.root_query_fields[query_field_name]
            
            return_type = self._get_field_type_name(query_field)
            if not self._is_object_or_interface(return_type):
                return "", {}
            
            field_args = ""
            if add_filter:
                field_name_with_filter, sub_category, filter_variables = self.add_filter_to_field(query_field, query_field_name)
                if sub_category == 'filters':
                    query_field_name, field_args = field_name_with_filter.split('(', 1)
                    field_args = '(' + field_args
                    query_variables.update(filter_variables)
                    query_sub_category = 'filters'
                else:
                    field_args = self._generate_non_filter_args(query_field)
            else:
                field_args = self._generate_non_filter_args(query_field)
            
            fragment_fields = self._select_random_fields(return_type)
            if not fragment_fields:
                return "", {}
            
            fragment_name = self._get_unique_fragment_name(return_type)
            
            original_fields_string = self._build_fields_string(return_type, fragment_fields, max_depth=2)
            
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
            indented_fields = fields_string.replace("\n", "\n    ")
            fragment_def = f"""fragment {fragment_name} on {return_type} {{
  {indented_fields}
}}"""
            
            query = f"""query {query_field_name.capitalize()}Query{variable_section} {{
  {query_field_name}{field_args} {{
    ...{fragment_name}
  }}
}}

{fragment_def}"""
            
            final_variables = {}
            for var_name, var_info in query_variables.items():
                final_variables[var_name] = self._simplify_variable_value(var_info)
            
            return query, final_variables
        except Exception as e:
            logger.debug("Error generating external fragments query: %s", e)
            return "", {}