#!/usr/bin/env python3
import logging
from typing import Dict, Any, Tuple
import random
from .base_generator import BaseQueryGenerator

logger = logging.getLogger(__name__)

class BasicQueryGenerator(BaseQueryGenerator):
    """Generator for basic GraphQL queries with simple field selection."""
    
    def __init__(self, schema, exclude_fields=None, max_hops=2):
        super().__init__(schema, exclude_fields, max_hops)
    
    def generate_query(self) -> Tuple[str, Dict[str, Any]]:
        """Generate a basic GraphQL query."""
        if not self.root_query_fields:
            return "", {}

        field_name, field = random.choice(list(self.root_query_fields.items()))
        if field_name in self.exclude_fields:
            return "", {}
        
        field_args, _ = self._get_field_args(field, use_variables=False)
        return_type = self._get_field_type_name(field)
        fields = self._build_fields_string(return_type, max_depth=2)
        
        query = f"""query Basic{field_name.capitalize()}Query {{
  {field_name}{field_args} {{
    {fields.replace('\n', '\n    ')}
  }}
}}"""
        
        return query, {} 