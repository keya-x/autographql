#!/usr/bin/env python3
from typing import List, Set, Optional
from graphql import GraphQLSchema
from .base_generator import BaseQueryGenerator
from .basic_query_generator import BasicQueryGenerator
from .filter_generator import FilterQueryGenerator
from .external_fragments_generator import ExternalFragmentQueryGenerator
from .inline_fragments_generator import InlineFragmentQueryGenerator
from .directive_generator import DirectiveQueryGenerator
from .alias_generator import AliasQueryGenerator
from .mutation_generator import MutationGenerator
from .pagination_generator import PaginationGenerator

class QueryGeneratorFactory:
    def __init__(self, schema: GraphQLSchema, query_fields: Optional[List[str]] = None, max_hops: int = 2):
        self.schema = schema
        self.query_fields = query_fields
        self.max_hops = max_hops
        self.generators = {
            'basic': BasicQueryGenerator,
            'external_fragments': ExternalFragmentQueryGenerator,
            'inline_fragments': InlineFragmentQueryGenerator,
            'directives': DirectiveQueryGenerator,
            'filters': FilterQueryGenerator,
            'aliases': AliasQueryGenerator,
            'mutations': MutationGenerator,
            'pagination': PaginationGenerator
        }
    
    def create_generator(self, category: str, exclude_fields: Set[str] = None) -> BaseQueryGenerator:
        """Create an appropriate generator instance for the specified category."""
        if category not in self.generators:
            raise ValueError(f"Unknown query category: {category}. Valid categories are: {', '.join(self.generators.keys())}")
        
        generator_class = self.generators[category]
        generator = generator_class(self.schema, exclude_fields, self.max_hops)
        
        if hasattr(generator, 'set_query_fields') and self.query_fields:
            generator.set_query_fields(self.query_fields)
            
        return generator
    
    def get_all_generator_types(self) -> List[str]:
        """Get a list of all available generator types."""
        return list(self.generators.keys()) 