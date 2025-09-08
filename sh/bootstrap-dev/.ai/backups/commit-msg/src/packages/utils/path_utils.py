"""Path utility functions for consistent path processing across the system."""

from pathlib import Path
from typing import Dict


def apply_target_prefix_stripping(component: str, rel_file: str, manifest: Dict) -> str:
    """Apply target_prefix stripping if configured for component.
    
    Args:
        component: Component name
        rel_file: Relative file path
        manifest: Installation manifest
        
    Returns:
        Relative file path with target_prefix stripped if configured
    """
    if component not in manifest['components']:
        return rel_file

    component_config = manifest['components'][component]
    target_prefix = component_config.get('target_prefix', '')

    if target_prefix and rel_file.startswith(target_prefix):
        return rel_file[len(target_prefix):]

    return rel_file


def apply_destination_mappings(rel_path: Path, destination_mappings: Dict[str, str]) -> Path:
    """Apply destination mappings to transform file paths.
    
    Args:
        rel_path: Relative path to transform
        destination_mappings: Dictionary of source pattern -> destination pattern
        
    Returns:
        Transformed path
    """
    mapped_path = rel_path
    path_str = str(rel_path)
    
    for src_pattern, dst_pattern in destination_mappings.items():
        # Handle exact matches
        if path_str == src_pattern:
            mapped_path = Path(dst_pattern)
            break
        # Handle prefix matches  
        elif path_str.startswith(src_pattern):
            mapped_path = Path(path_str.replace(src_pattern, dst_pattern, 1))
            break
        # Handle suffix matches (e.g., .template -> "")
        elif src_pattern.startswith('.') and path_str.endswith(src_pattern):
            mapped_path = Path(path_str[:-len(src_pattern)] + dst_pattern)
            break
            
    return mapped_path
