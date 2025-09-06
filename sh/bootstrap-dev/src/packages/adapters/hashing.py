"""Content hashing utilities for drift detection and verification.

This module provides consistent SHA256 hashing for files and content,
supporting the receipt system's ability to detect configuration drift
and verify file integrity.
"""

import hashlib
from pathlib import Path
from typing import Union

from ..domain.constants import HASH_ALGORITHM


def sha256_file(file_path: Path) -> str:
    """Calculate SHA256 hash of a file.

    Args:
        file_path: Path to file to hash

    Returns:
        Hex-encoded SHA256 hash

    Raises:
        FileNotFoundError: If file does not exist
        IOError: If file cannot be read
    """
    file_path = Path(file_path).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise IOError(f"Not a regular file: {file_path}")

    hash_obj = hashlib.sha256()

    try:
        with file_path.open("rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    except Exception as e:
        raise IOError(f"Failed to read file {file_path}: {e}") from e


def sha256_content(content: Union[str, bytes], encoding: str = "utf-8") -> str:
    """Calculate SHA256 hash of content.

    Args:
        content: Content to hash (string or bytes)
        encoding: Text encoding for string content

    Returns:
        Hex-encoded SHA256 hash
    """
    hash_obj = hashlib.sha256()

    if isinstance(content, str):
        content_bytes = content.encode(encoding)
    else:
        content_bytes = content

    hash_obj.update(content_bytes)
    return hash_obj.hexdigest()


def verify_hash(
    file_path: Path,
    expected_hash: str,
    algorithm: str = HASH_ALGORITHM,
) -> bool:
    """Verify file matches expected hash.

    Args:
        file_path: Path to file to verify
        expected_hash: Expected hash value
        algorithm: Hash algorithm (only 'sha256' supported)

    Returns:
        True if hash matches, False otherwise

    Raises:
        ValueError: If algorithm is not supported
        FileNotFoundError: If file does not exist
        IOError: If file cannot be read
    """
    if algorithm != "sha256":
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    actual_hash = sha256_file(file_path)
    return actual_hash.lower() == expected_hash.lower()


def hash_directory_tree(base_path: Path, exclude_patterns: set[str] = None) -> dict[str, str]:
    """Calculate hashes for all files in a directory tree.

    Args:
        base_path: Root directory to hash
        exclude_patterns: Set of filename patterns to exclude

    Returns:
        Dict mapping relative paths to SHA256 hashes

    Raises:
        FileNotFoundError: If base_path does not exist
        IOError: If directory cannot be read
    """
    base_path = Path(base_path).resolve()
    exclude_patterns = exclude_patterns or set()

    if not base_path.exists():
        raise FileNotFoundError(f"Directory not found: {base_path}")

    if not base_path.is_dir():
        raise IOError(f"Not a directory: {base_path}")

    file_hashes = {}

    try:
        for file_path in base_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Check exclude patterns
            relative_path = file_path.relative_to(base_path)
            if any(pattern in str(relative_path) for pattern in exclude_patterns):
                continue

            file_hash = sha256_file(file_path)
            file_hashes[str(relative_path)] = file_hash

        return file_hashes

    except Exception as e:
        raise IOError(f"Failed to hash directory tree {base_path}: {e}") from e


def compare_hashes(
    current_hashes: dict[str, str],
    expected_hashes: dict[str, str],
) -> dict[str, str]:
    """Compare two hash dictionaries and return differences.

    Args:
        current_hashes: Current file hashes
        expected_hashes: Expected file hashes

    Returns:
        Dict mapping file paths to difference types:
        - 'modified': File exists but hash differs
        - 'missing': File expected but not found
        - 'extra': File found but not expected
    """
    differences = {}

    # Check for modified and missing files
    for file_path, expected_hash in expected_hashes.items():
        if file_path not in current_hashes:
            differences[file_path] = "missing"
        elif current_hashes[file_path] != expected_hash:
            differences[file_path] = "modified"

    # Check for extra files
    for file_path in current_hashes:
        if file_path not in expected_hashes:
            differences[file_path] = "extra"

    return differences
