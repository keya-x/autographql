#!/usr/bin/env python3
import logging
from typing import Dict, Any, Tuple, Set
import random
from .base_generator import BaseQueryGenerator

logger = logging.getLogger(__name__)

class AliasQueryGenerator(BaseQueryGenerator):
    def __init__(self, schema, exclude_fields: Set[str] = None, max_hops: int = 2):
        super().__init__(schema, exclude_fields, max_hops)

    def generate_query(self) -> Tuple[str, Dict[str, Any]]:
        if not self.root_query_fields:
            return "", {}
        
        add_directive = self.should_add_feature(0.3)
        add_filter = False if add_directive else self.should_add_feature(0.3)
        query_sub_category = ''
        query_variables = {}
        
        available_fields = []
        for field_name in self.root_query_fields.keys():
            if field_name in self.exclude_fields:
                continue
            
            field = self.root_query_fields.get(field_name)
            if field:
                return_type = self._get_field_type_name(field)
                if return_type:
                    available_fields.append(field_name)
        
        if not available_fields:
            return "", {}
        
        object_fields = []
        for field_name in available_fields:
            field = self.root_query_fields.get(field_name)
            if not field:
                continue
                
            return_type_name = self._get_field_type_name(field)
            if self._is_object_or_interface(return_type_name):
                sub_fields = self._get_type_fields(return_type_name)
                if sub_fields and len(sub_fields) > 0:
                    object_fields.append((field_name, field, return_type_name))
        
        if object_fields:
            field_name, field, return_type_name = random.choice(object_fields)
            
            field_args, field_vars = self._get_field_args(field, use_variables=True)
            query_variables.update(field_vars)
            
            if add_filter and not field_args:
                field_name_with_filter, sub_category, filter_variables = self.add_filter_to_field(field, field_name)
                if sub_category == 'filters':
                    field_name, field_args = field_name_with_filter.split('(', 1)
                    field_args = '(' + field_args
                    query_variables.update(filter_variables)
                    query_sub_category = 'filters'
            
            sub_fields = self._get_type_fields(return_type_name)
            sub_field_names = list(sub_fields.keys())
            
            if sub_field_names:
                num_subfields = min(random.randint(2, 5), len(sub_field_names))
                selected_subfields = random.sample(sub_field_names, num_subfields)
                
                aliased_fields = []
                for subfield in selected_subfields:
                    alias = f"aliased{subfield.capitalize()}"
                    subfield_type = self._get_field_type_name(sub_fields[subfield])
                    subfield_name = subfield
                    apply_directive = add_directive and self.should_add_feature(0.5) and query_sub_category != 'filters'
                    
                    if self._is_object_or_interface(subfield_type):
                        nested_fields_str = self._build_fields_string(subfield_type, max_depth=2)
                        
                        if apply_directive:
                            subfield_with_directive, sub_category, directive_variables = self.add_directive_to_field(
                                subfield_name + " {"
                            )
                            if sub_category == 'directives':
                                query_variables.update(directive_variables)
                                query_sub_category = 'directives'
                                subfield_opening = subfield_with_directive
                            else:
                                subfield_opening = f"{subfield_name} {{"
                        else:
                            subfield_opening = f"{subfield_name} {{"
                        
                        if nested_fields_str:
                            indented_nested_str = nested_fields_str.replace('\n', '\n      ')
                            aliased_fields.append(f"{alias}: {subfield_opening}\n      {indented_nested_str}\n    }}")
                        else:
                            default_field = self._get_default_field(subfield_type)
                            aliased_fields.append(f"{alias}: {subfield_opening}\n      {default_field}\n    }}")
                    else:
                        if apply_directive:
                            subfield_with_directive, sub_category, directive_variables = self.add_directive_to_field(subfield_name)
                            if sub_category == 'directives':
                                query_variables.update(directive_variables)
                                query_sub_category = 'directives'
                                aliased_fields.append(f"{alias}: {subfield_with_directive}")
                            else:
                                aliased_fields.append(f"{alias}: {subfield_name}")
                        else:
                            aliased_fields.append(f"{alias}: {subfield_name}")
                
                variable_section = self._format_variable_section(query_variables)
                
                query = f"""query {field_name.capitalize()}AliasQuery{variable_section} {{
  {field_name}{field_args} {{
    {"\n    ".join(aliased_fields)}
  }}
}}"""
              
                final_variables = self._simplify_variables(query_variables)
                return query, final_variables
        
        return "", {}

    def _format_variable_section(self, query_variables: Dict[str, Any]) -> str:
        """Format the variable section for the query."""
        if not query_variables:
            return ""
        
        var_defs = []
        for var_name, var_info in query_variables.items():
            var_type = var_info.get('type', 'String')
            if not var_type.endswith('!'):
                var_type += '!'
            var_defs.append(f"${var_name}: {var_type}")
        
        return f"({', '.join(var_defs)})" if var_defs else ""

    def _simplify_variables(self, query_variables: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify variable values for the query."""
        final_variables = {}
        for var_name, var_info in query_variables.items():
            final_variables[var_name] = self._simplify_variable_value(var_info)
        return final_variables 