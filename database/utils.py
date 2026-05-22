# ==============================================================================
# IMPORTS
# ==============================================================================

import uuid

from datetime import datetime
from pathlib import Path


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def generate_uuid():

    """
    PURPOSE :
        Create a unique identifier for users, messages, files, and chunks.

    OUTPUT :
        str
    """

    return str(uuid.uuid4())


def current_timestamp():

    """
    PURPOSE :
        Return the current UTC timestamp in ISO format.

    OUTPUT :
        str
    """

    return datetime.utcnow().isoformat()


def create_data_directory(path: Path):

    """
    PURPOSE :
        Ensure the local storage directory exists.

    INPUT :
        path : Path

    OUTPUT :
        Path
    """

    path.mkdir(parents=True, exist_ok=True)

    return path


def build_chunk_path(base_dir: Path, file_id: str, chunk_index: int):

    """
    PURPOSE :
        Generate a file chunk storage path.

    INPUT :
        base_dir : Path
        file_id : str
        chunk_index : int

    OUTPUT :
        Path
    """

    return base_dir / f"{file_id}_chunk_{chunk_index}.bin"
