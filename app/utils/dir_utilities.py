import os

def find_media_files(directory):
    """
    Recursively finds all .jpg, .jpeg, and .mp4 files in the specified directory
    and returns their paths in an array.
    
    Args:
        directory (str): The directory path to search in.
        
    Returns:
        list: A list of file paths for the found media files.
    """
    media_extensions = {'.jpg', '.jpeg', '.mp4'}
    media_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Get the file extension in lowercase
            ext = os.path.splitext(file)[1].lower()
            if ext in media_extensions:
                # Join the root path with the file name to get the full path
                full_path = os.path.join(root, file)
                media_files.append(full_path)
    
    return media_files

import os
import shutil

def clean_directory(directory_path, exclude_extensions=None, exclude_folders=None):
    """
    Cleans up a directory by removing all its contents, with optional exclusions.
    
    Args:
        directory_path (str): Path to the directory to clean.
        exclude_extensions (list): File extensions to keep (e.g., ['.txt', '.pdf'])
        exclude_folders (list): Folder names to keep (e.g., ['important', 'backup'])
        
    Returns:
        bool: True if successful, False if error occurred.
    """
    try:
        # Verify directory exists
        if not os.path.isdir(directory_path):
            print(f"Directory does not exist: {directory_path}")
            return False

        # Set default empty lists if exclusions not provided
        if exclude_extensions is None:
            exclude_extensions = []
        if exclude_folders is None:
            exclude_folders = []

        # Convert to sets for faster lookups
        exclude_extensions = {ext.lower() for ext in exclude_extensions}
        exclude_folders = {folder.lower() for folder in exclude_folders}

        # Walk through the directory
        for root, dirs, files in os.walk(directory_path, topdown=False):
            # Process files
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                # Skip excluded extensions
                if file_ext in exclude_extensions:
                    continue
                
                try:
                    os.remove(file_path)
                    print(f"Removed file: {file_path}")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")

            # Process directories (skip excluded ones)
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                
                # Skip excluded folders
                if dir_name.lower() in exclude_folders:
                    continue
                
                try:
                    shutil.rmtree(dir_path)
                    print(f"Removed directory: {dir_path}")
                except Exception as e:
                    print(f"Error removing {dir_path}: {e}")

        print(f"Directory cleaned successfully: {directory_path}")
        return True

    except Exception as e:
        print(f"Error cleaning directory {directory_path}: {e}")
        return False