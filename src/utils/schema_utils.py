#!/usr/bin/env python3
import re
from graphql import build_schema, GraphQLSchema

def load_schema_from_file(file_path: str) -> str:
    """Load a GraphQL schema from a file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading schema from {file_path}: {e}")
        return ""

def build_schema_with_directives(schema_string: str) -> GraphQLSchema:
    """Build a GraphQL schema while properly handling directives and custom scalars."""
    if 'scalar Date' not in schema_string and ('Date' in schema_string or 'date' in schema_string.lower()):
        schema_string = "scalar Date\n" + schema_string
        
    if 'scalar DateTime' not in schema_string and ('DateTime' in schema_string or 'datetime' in schema_string.lower()):
        schema_string = "scalar DateTime\n" + schema_string
        
    if 'scalar Time' not in schema_string and ('Time' in schema_string or 'time' in schema_string.lower()):
        schema_string = "scalar Time\n" + schema_string
    
    if 'scalar JSON' not in schema_string and 'JSON' in schema_string:
        schema_string = "scalar JSON\n" + schema_string

    cleaned_schema = clean_schema(schema_string)
    
    try:
        return build_schema(cleaned_schema)
    except Exception as e:
        print(f"Schema parsing failed: {e}")
        raise Exception("Schema parsing failed")

def clean_schema(schema_string: str) -> str:
    """Clean schema by removing SQL blocks, directives, and problematic syntax."""
    schema_string = re.sub(r'"\w+"\s*=\s*[^,\n)]+', '""', schema_string)
    schema_string = re.sub(r'COALESCE\s*\([^)]+\)', '""', schema_string)
    
    lines = schema_string.split('\n')
    cleaned_lines = []
    in_triple_quotes = False
    
    for line in lines:
        if '"""' in line:
            quotes_count = line.count('"""')
            if quotes_count % 2 == 0:
                line = re.sub(r'""".*?"""', '""""""', line)
                cleaned_lines.append(line)
            else:
                if in_triple_quotes:
                    in_triple_quotes = False
                    cleaned_lines.append('"""')
                else:
                    in_triple_quotes = True
                    cleaned_lines.append(line.split('"""')[0] + '"""')
        elif in_triple_quotes:
            continue
        else:
            if '=' in line and ('COALESCE' in line or '"' in line):
                line = re.sub(r'"\w+"\s*=\s*[^,\n)]+', '""', line)
            cleaned_lines.append(line)
    
    schema_string = '\n'.join(cleaned_lines)
    
    schema_string = re.sub(r'directive\s+@\w+\s*(\([^)]*\))?\s*on\s+[A-Z_|]+', '', schema_string)
    
    stepzen_directives = [
        '@materializer', '@dbquery', '@rest', '@graphql', 
        '@sequence', '@jsonSchema', '@relationship', '@computed'
    ]
    
    for directive in stepzen_directives:
        schema_string = re.sub(f'{directive}\\s*\\([^)]*\\)', '', schema_string)
        schema_string = re.sub(f'{directive}', '', schema_string)
    
    schema_string = re.sub(r'"""[\s\S]*?"""', '""""""', schema_string)
    schema_string = re.sub(r'@\w+\s*\([^)]*\)', '', schema_string)
    schema_string = re.sub(r'@\w+', '', schema_string)
    
    schema_string = re.sub(r'\n\s*\n', '\n', schema_string)
    
    return schema_string