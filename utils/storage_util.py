# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

from typing import Any, Dict
import json
import os
import shutil
import tempfile
import uuid

from utils.gevent_util import gevent_spawn

"""
This module contains utility functions for path manipulation and file operations.

Functions in this module that perform I/O operations, such as reading,
writing, or modifying files and directories, should be called using
gevent_spawn to ensure asynchronous execution.

"""


def generate_unique_filename(fileName):
    """
    Generates a unique filename using a UUID and preserves the file extension.

    Args:
        fileName (str): The original filename, including the extension.

    Returns:
        str: A new unique filename with the same extension as the original.
    """
    file_ext = os.path.splitext(fileName)[1]
    return f"{str(uuid.uuid4())}{file_ext.lower()}"


def get_abs_path(*paths):
    """
    Returns the absolute path by joining the current working directory with the provided paths.

    Args:
        *paths (str): One or more paths to be joined.

    Returns:
        str: The absolute path constructed by joining the current working directory with the input paths.
    """
    current_directory = os.environ.get("PWD", os.getcwd())
    return os.path.join(current_directory, *paths)


def join_path(*paths):
    """
    Joins multiple paths into one.

    Args:
        *paths (str): One or more paths to be joined.

    Returns:
        str: The resulting joined path.
    """
    return os.path.join(*paths)


def get_file_name_from_path(path):
    """
    Extracts the filename from a given file path.

    Args:
        path (str): The file path.

    Returns:
        str: The name of the file extracted from the path.
    """
    return os.path.basename(path)


def path_exists(path):
    """
    Should be called using gevent_spawn to ensure asynchronous execution.
    Checks if a given path exists.

    Args:
        path (str): The path to check.

    Returns:
        bool: `True` if the path exists, `False` otherwise.
    """
    return os.path.exists(path)


def list_dir(dir_path):
    """
    Should be called using gevent_spawn to ensure asynchronous execution.
    Lists the files and directories in a given directory.

    Args:
        dir_path (str): The directory path.

    Returns:
        list: A list of filenames and directory names in the specified directory.
    """
    return os.listdir(dir_path)


def create_dir(dir_name):
    """
    Should be called using gevent_spawn to ensure asynchronous execution.
    Creates a new directory.

    Args:
        dir_name (str): The name of the directory to create.
    """
    dir_path = get_abs_path(dir_name)
    create_dir_path(dir_path)


def get_dir_from_path(path):
    """
    Extracts the directory path from a given full file path.

    Args:
        path (str): The full file path.

    Returns:
        str: The directory path.
    """
    return os.path.dirname(path)


def create_dir_path(dir_path):
    """
    Should be called using gevent_spawn to ensure asynchronous execution.
    Creates the directory at the specified path if it does not already exist.

    Args:
        dir_path (str): The path of the directory to create.
    """
    if not path_exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)


def delete_path(path):
    """
    Should be called using gevent_spawn to ensure asynchronous execution.
    Deletes the file or directory at the specified path.

    Args:
        path (str): The path to the file or directory to delete.
    """
    os.remove(path)


def rename_path(old_path, new_path):
    """
    Should be called using gevent_spawn to ensure asynchronous execution.
    Renames a file or directory.

    Args:
        old_path (str): The current path of the file or directory.
        new_path (str): The new path (name) for the file or directory.
    """
    os.rename(old_path, new_path)


def split_file_name_ext(file_name):
    """
    Splits a filename into the name and extension.

    Args:
        file_name (str): The name of the file.

    Returns:
        tuple: A tuple containing the file name and its extension.
    """
    return os.path.splitext(file_name)


def create_temp_dir():
    """
    Creates a temporary directory and returns its path.

    Should be called using gevent_spawn to ensure asynchronous execution.
    Returns:
        str: The path of the newly created temporary directory.
    """
    # Create a temporary directory
    return tempfile.mkdtemp()


def remove_temp_dir(path):
    """
    Removes the temporary directory specified by the path.

    Should be called using gevent_spawn to ensure asynchronous execution.

    :param path: Path to the directory to be removed.
    """
    # Check if the directory exists
    if os.path.isdir(path):
        shutil.rmtree(path)


def read_file(path: str, mode: str = 'r', encoding: str = None) -> str:
    """
    Should be called using gevent_spawn to ensure asynchronous execution.
    
    Reads the content of a file.

    Args:
        path (str): The path to the file.
        mode (str): The mode in which to open the file (default is 'r').

    Returns:
        str: The content of the file.
    """
    if encoding:
        with open(path, mode, encoding=encoding) as file:
            return file.read()
    else:
        with open(path, mode) as file:
            return file.read()


def write_file(path: str, content: str, mode: str = 'w', encoding: str = None) -> None:
    """
    Should be called using gevent_spawn to ensure asynchronous execution.

    Writes content to a file.

    Args:
        path (str): The path to the file.
        content (str): The content to write to the file.
        mode (str): The mode in which to open the file (default is 'w').
    """
    if encoding:
        with open(path, mode, encoding=encoding) as file:
            file.write(content)
    else:
        with open(path, mode) as file:
            file.write(content)
