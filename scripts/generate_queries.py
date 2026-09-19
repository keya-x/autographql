#!/usr/bin/env python3
import os
import sys
import argparse

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.query_generator_app import GraphQLQueryGeneratorApp

def main():
    parser = argparse.ArgumentParser(description='Generate GraphQL queries from multiple schemas')
    parser.add_argument('--schema', type=str, help='Path to a specific GraphQL schema file')
    parser.add_argument('--category', type=str, required=True, 
                        choices=['external_fragments', 'inline_fragments', 'directives', 'filters', 'aliases', 'mutations', 'pagination', 'all'],
                        help='Category of queries to generate')
    parser.add_argument('--count', type=int, required=True, help='Number of unique queries to generate per category')
    parser.add_argument('--max-hops', type=int, default=2, help='Maximum number of hops (query depth) allowed in generated queries')
    
    args = parser.parse_args()
    
    schema_dir = 'schemas'
    output_dir = 'generated_queries'
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if not os.path.exists(schema_dir):
        os.makedirs(schema_dir)
    
    app = GraphQLQueryGeneratorApp()
    
    if args.schema:
        schema_path = args.schema
        
        if os.path.isdir(schema_path):
            index_file = os.path.join(schema_path, 'index.graphql')
            if os.path.isfile(index_file):
                schema_path = index_file
        elif not os.path.exists(schema_path):
            schema_dir_path = os.path.join(schema_dir, schema_path)
            index_file = os.path.join(schema_dir_path, 'index.graphql')
            
            if os.path.isdir(schema_dir_path) and os.path.isfile(index_file):
                schema_path = index_file
            else:
                schema_file = schema_path
                if not schema_file.endswith('.graphql'):
                    schema_file += '.graphql'
                
                schema_path = os.path.join(schema_dir, schema_file)        

        if not os.path.exists(schema_path):
            print(f"Error: Schema '{args.schema}' does not exist at any of the possible locations.")
            return 1
        
        app.generate_queries_for_schema(schema_path, args.category, args.count, args.max_hops, output_dir)
    else:
        app.generate_queries_from_directory(schema_dir, args.category, args.count, args.max_hops, output_dir)
    
    print("\nQuery generation complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 