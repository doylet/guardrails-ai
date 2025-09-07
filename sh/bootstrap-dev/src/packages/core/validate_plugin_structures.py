#!/usr/bin/env python3
"""
Plugin Structure Validation Script
Validates plugin-structure.schema.yaml files against the JSON Schema definition.

Part of Sprint 007: Plugin Schema Decoupling
Task 1.4: Plugin structure validation script
"""

import argparse
import json
import logging
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any, Tuple

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print("Error: jsonschema package not found. Install with: pip install jsonschema")
    sys.exit(1)


class PluginStructureValidator:
    """Validates plugin structure schema files against JSON Schema."""
    
    def __init__(self, schema_path: Path):
        """Initialize validator with JSON Schema."""
        self.schema_path = schema_path
        self.schema = self._load_json_schema()
        self.validator = Draft7Validator(self.schema)
        
    def _load_json_schema(self) -> Dict[str, Any]:
        """Load and parse the JSON Schema file."""
        try:
            with open(self.schema_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON Schema not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON Schema: {e}")
    
    def _load_plugin_structure(self, plugin_file: Path) -> Dict[str, Any]:
        """Load and parse a plugin structure YAML file."""
        try:
            with open(plugin_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Plugin structure file not found: {plugin_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {plugin_file}: {e}")
    
    def validate_file(self, plugin_file: Path) -> Tuple[bool, List[str]]:
        """
        Validate a single plugin structure file.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Load plugin structure
            plugin_data = self._load_plugin_structure(plugin_file)
            
            # Validate against schema
            validation_errors = list(self.validator.iter_errors(plugin_data))
            
            if validation_errors:
                for error in validation_errors:
                    path = " -> ".join(str(p) for p in error.path) if error.path else "root"
                    errors.append(f"Path '{path}': {error.message}")
                return False, errors
            
            # Additional semantic validation
            semantic_errors = self._validate_semantics(plugin_data)
            if semantic_errors:
                errors.extend(semantic_errors)
                return False, errors
                
            return True, []
            
        except (FileNotFoundError, ValueError) as e:
            return False, [str(e)]
    
    def _validate_semantics(self, plugin_data: Dict[str, Any]) -> List[str]:
        """Perform additional semantic validation beyond JSON Schema."""
        errors = []
        
        # Check for required top-level fields (plugin_version not required per JSON Schema)
        required_fields = ['schema_version', 'plugin_name', 'provides_structure']
        for field in required_fields:
            if field not in plugin_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate provides_structure is not empty
        provides = plugin_data.get('provides_structure', {})
        if not provides:
            errors.append("provides_structure cannot be empty")
        
        return errors
    
    def validate_multiple(self, plugin_files: List[Path]) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Validate multiple plugin structure files.
        
        Returns:
            Dictionary mapping file paths to (is_valid, error_messages) tuples
        """
        results = {}
        for plugin_file in plugin_files:
            results[str(plugin_file)] = self.validate_file(plugin_file)
        return results


def find_plugin_structure_files(search_path: Path) -> List[Path]:
    """Find all plugin-structure.schema.yaml files in the given path."""
    pattern = "**/plugin-structure.schema.yaml"
    return list(search_path.glob(pattern))


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def main():
    """Main validation script entry point."""
    parser = argparse.ArgumentParser(
        description="Validate plugin structure schema files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all plugin structure files in src/plugins/
  python validate_plugin_structures.py --search src/plugins/
  
  # Validate specific files
  python validate_plugin_structures.py file1.yaml file2.yaml
  
  # Validate with verbose output
  python validate_plugin_structures.py --verbose --search src/plugins/
        """
    )
    
    parser.add_argument(
        'files',
        nargs='*',
        help='Specific plugin structure files to validate'
    )
    
    parser.add_argument(
        '--search',
        type=Path,
        help='Search directory for plugin-structure.schema.yaml files'
    )
    
    parser.add_argument(
        '--schema',
        type=Path,
        default=Path('src/schemas/plugin-structure.schema.json'),
        help='Path to JSON Schema file (default: src/schemas/plugin-structure.schema.json)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Stop validation on first error'
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    # Determine files to validate
    files_to_validate = []
    
    if args.files:
        files_to_validate.extend(Path(f) for f in args.files)
    
    if args.search:
        if not args.search.exists():
            logging.error(f"Search path does not exist: {args.search}")
            sys.exit(1)
        found_files = find_plugin_structure_files(args.search)
        files_to_validate.extend(found_files)
        logging.info(f"Found {len(found_files)} plugin structure files in {args.search}")
    
    if not files_to_validate:
        logging.error("No files specified for validation. Use --search or provide file paths.")
        parser.print_help()
        sys.exit(1)
    
    # Validate JSON Schema exists
    if not args.schema.exists():
        logging.error(f"JSON Schema file not found: {args.schema}")
        sys.exit(1)
    
    # Initialize validator
    try:
        validator = PluginStructureValidator(args.schema)
        logging.info(f"Loaded JSON Schema from {args.schema}")
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Failed to load JSON Schema: {e}")
        sys.exit(1)
    
    # Validate files
    logging.info(f"Validating {len(files_to_validate)} plugin structure files...")
    
    results = validator.validate_multiple(files_to_validate)
    
    # Report results
    valid_count = 0
    invalid_count = 0
    
    for file_path, (is_valid, errors) in results.items():
        if is_valid:
            valid_count += 1
            logging.info(f"✅ {file_path}: VALID")
        else:
            invalid_count += 1
            logging.error(f"❌ {file_path}: INVALID")
            for error in errors:
                logging.error(f"   - {error}")
            
            if args.fail_fast:
                logging.error("Stopping validation due to --fail-fast")
                break
    
    # Summary
    total = len(results)
    logging.info(f"\nValidation Summary:")
    logging.info(f"  Total files: {total}")
    logging.info(f"  Valid: {valid_count}")
    logging.info(f"  Invalid: {invalid_count}")
    
    if invalid_count > 0:
        logging.error(f"Validation failed for {invalid_count} files")
        sys.exit(1)
    else:
        logging.info("All files passed validation! ✅")


if __name__ == '__main__':
    main()
