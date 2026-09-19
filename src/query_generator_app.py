#!/usr/bin/env python3
import os
from typing import List, Optional
from src.utils.schema_utils import load_schema_from_file, build_schema_with_directives
from src.utils.variable_utils import save_query_results, validate_query_uniqueness
from src.generators.generator_factory import QueryGeneratorFactory

class GraphQLQueryGeneratorApp:
    def __init__(self):
        self.generator_factory = None
        
    def generate_queries_for_schema(self, 
                                   schema_file: str, 
                                   category: str,
                                   count: int,
                                   max_hops: int = 2,
                                   output_dir: Optional[str] = None) -> None:
        """Generate queries for a specific schema file."""
        schema_name = (os.path.basename(os.path.dirname(schema_file)) 
                      if os.path.basename(schema_file) == 'index.graphql' 
                      else os.path.basename(schema_file).replace('.graphql', ''))
            
        print(f"\nProcessing schema: {schema_name}")
        
        try:
            schema_string = load_schema_from_file(schema_file)
            
            try:
                schema = build_schema_with_directives(schema_string)
                self.generator_factory = QueryGeneratorFactory(schema, None, max_hops)
                
                categories = self.generator_factory.get_all_generator_types() if category == 'all' else [category]
                
                for cat in categories:
                    mutation_count = count if cat == 'mutations' and count % 2 == 0 else count + (1 if cat == 'mutations' and count % 2 == 1 else 0)
                    print(f"  Generating {mutation_count} '{cat}' queries" + 
                          (f" (in {mutation_count // 2} insert/delete pairs)..." if cat == 'mutations' else "..."))
                    
                    generator = self.generator_factory.create_generator(cat)
                    
                    if cat == 'mutations':
                        try:
                            queries = generator.generate_queries(count)
                            original_count = len(queries)
                            queries = validate_query_uniqueness(queries)
                            if len(queries) < original_count:
                                print(f"    Removed {original_count - len(queries)} duplicate or invalid mutation queries")
                        except Exception as e:
                            print(f"    Error generating mutation queries: {e}")
                            queries = []
                    else:
                        queries = []
                        max_attempts = mutation_count * 20
                        attempts = 0
                        
                        while len(queries) < mutation_count and attempts < max_attempts:
                            attempts += 1
                            try:
                                query, variables = generator.generate_query()
                                
                                if not query or not query.strip():
                                    continue
                                
                                query_lines = [line for line in query.split('\n') if line.strip()]
                                if len(query_lines) <= 2:
                                    continue
                                    
                                queries.append((query, variables))
                            except Exception as qe:
                                print(f"    Error generating query: {qe}")
                                continue
                    
                    if queries:
                        original_count = len(queries)
                        queries = validate_query_uniqueness(queries)
                        if len(queries) < original_count:
                            print(f"  Removed {original_count - len(queries)} duplicate or invalid queries")
                    
                    if not queries:
                        print(f"  Warning: Could not generate any '{cat}' queries for this schema.")
                        continue
                    
                    if cat == 'mutations':
                        if len(queries) < mutation_count:
                            print(f"  Warning: Could only generate {len(queries)} unique '{cat}' queries (requested {mutation_count} for {mutation_count // 2} pairs).")
                        else:
                            print(f"  Successfully generated {len(queries)} mutation queries in {len(queries) // 2} insert/delete pairs.")
                    else:
                        if len(queries) < count:
                            print(f"  Warning: Could only generate {len(queries)} unique '{cat}' queries (requested {count}).")
                    
                    if output_dir is None:
                        output_dir = 'generated_queries'
                    schema_output_dir = os.path.join(output_dir, schema_name)
                    if not os.path.exists(schema_output_dir):
                        os.makedirs(schema_output_dir)
                    
                    save_query_results(queries, schema_output_dir, schema_name, cat)
                    print(f"  Saved to: {schema_output_dir}")
            
            except Exception as schema_e:
                print(f"  Schema parsing error: {schema_e}")
                print(f"  Skipping query generation for {schema_name}")
        
        except Exception as e:
            print(f"  Error processing schema: {e}")
            
    def generate_queries_from_directory(self, 
                                      schema_dir: str,
                                      category: str,
                                      count: int,
                                      max_hops: int = 2,
                                      output_dir: Optional[str] = None) -> None:
        """Generate queries from all schema files in a directory."""
        if not os.path.isdir(schema_dir):
            print(f"Error: Schema directory '{schema_dir}' does not exist.")
            return
        
        print(f"\nProcessing schemas from directory: {schema_dir}")
        
        schema_files = []
        for item in os.listdir(schema_dir):
            item_path = os.path.join(schema_dir, item)
            if os.path.isdir(item_path):
                index_file = os.path.join(item_path, 'index.graphql')
                if os.path.isfile(index_file):
                    schema_files.append(index_file)
            elif os.path.isfile(item_path) and item.endswith('.graphql'):
                schema_files.append(item_path)
        
        if not schema_files:
            print(f"Error: No GraphQL schema files found in '{schema_dir}'.")
            return
        
        print(f"Found {len(schema_files)} schema files")
        
        for schema_file in schema_files:
            self.generate_queries_for_schema(schema_file, category, count, max_hops, output_dir) 