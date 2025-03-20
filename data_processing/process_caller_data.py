import os
import yaml
import string
from typing import Dict, List
from pathlib import Path
from deepgram_wrapper import DeepgramWrapper
from elevenlabs_wrapper import ElevenLabsWrapper


def get_workspace_root() -> str:
    """
    Get the workspace root directory (where the data/ folder is located).
    Returns:
        str: Path to the workspace root
    """
    # Since we'll run from data_processing, go up one level
    return os.path.dirname(os.getcwd())


def clean_name(name: str) -> str:
    """
    Clean a name by removing leading and trailing punctuation and whitespace.

    Args:
        name (str): The name to clean

    Returns:
        str: The cleaned name
    """
    return name.strip(string.punctuation + string.whitespace)


def process_caller_folder(folder_path: str, workspace_root: str) -> None:
    """
    Process a single caller folder by transcribing audio files and generating a voice model.

    Args:
        folder_path (str): Path to the caller's folder
        workspace_root (str): Path to the workspace root directory
    """
    # Check if full_metadata.yaml already exists
    metadata_path = os.path.join(folder_path, "full_metadata.yaml")
    if os.path.exists(metadata_path):
        print(f"Skipping {folder_path} - full_metadata.yaml already exists")
        return

    # Load calldata.yaml
    calldata_path = os.path.join(folder_path, "calldata.yaml")
    if not os.path.exists(calldata_path):
        print(f"Error: {calldata_path} not found")
        return

    with open(calldata_path, "r") as f:
        calldata = yaml.safe_load(f)

    # Initialize wrappers
    deepgram = DeepgramWrapper()
    elevenlabs = ElevenLabsWrapper()

    # Create full metadata dictionary with original data
    full_metadata = calldata.copy()

    # List of audio files to process
    audio_files = [
        ("name_file", calldata.get("name_file")),
        ("memory_file", calldata.get("memory_file")),
        ("like_file", calldata.get("like_file")),
        ("hate_file", calldata.get("hate_file")),
        ("message_file", calldata.get("message_file")),
    ]

    # Process each audio file
    valid_audio_files = []
    for file_key, file_path in audio_files:
        if not file_path:
            print(f"Warning: {file_key} not found in calldata.yaml")
            continue

        # Convert relative path to absolute path
        abs_file_path = os.path.join(workspace_root, file_path)
        if not os.path.exists(abs_file_path):
            print(f"Warning: {file_key} file not found at: {abs_file_path}")
            continue

        # Transcribe the audio
        transcript = deepgram.transcribe_file(abs_file_path)
        if transcript:
            # Store transcript with _transcript suffix at top level
            transcript_key = file_key.replace("_file", "_transcript")
            full_metadata[transcript_key] = transcript
            valid_audio_files.append(abs_file_path)
        else:
            print(f"Warning: Failed to transcribe {file_key}")

    # Store the name separately (keeping this for backward compatibility)
    if "name_transcript" in full_metadata:
        full_metadata["name"] = clean_name(full_metadata["name_transcript"])

    # Generate voice using ElevenLabs
    try:
        voice_result = elevenlabs.add_voice(
            name=f"Caller_{calldata['number']}",
            description=f"Voice model for caller {calldata['number']}",
            labels={"type": "caller_voice"},
            file_paths=valid_audio_files,
        )
        full_metadata["voice_id"] = voice_result.get("voice_id")
    except Exception as e:
        print(f"Error generating voice for {folder_path}: {str(e)}")
        full_metadata["voice_id"] = None

    # Save full metadata
    with open(metadata_path, "w") as f:
        yaml.dump(full_metadata, f, default_flow_style=False)


def process_all_callers(data_dir: str = "../data") -> None:
    """
    Process all caller folders in the data directory.

    Args:
        data_dir (str): Path to the data directory containing caller folders
    """
    workspace_root = get_workspace_root()

    # Get all subdirectories in the data directory
    data_path = Path(os.path.join(workspace_root, "data"))
    if not data_path.is_dir():
        print(f"Error: {data_dir} is not a directory")
        return

    for item in data_path.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            print(f"Processing caller folder: {item}")
            process_caller_folder(str(item), workspace_root)


if __name__ == "__main__":
    process_all_callers()
