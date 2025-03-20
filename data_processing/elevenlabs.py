import requests
import os
import json
from dotenv import load_dotenv


def add_voice(name, description="", labels=None, file_paths=None):
    """
    Adds a new voice to ElevenLabs using the provided parameters.
    The API key is automatically loaded from the .env file.

    Parameters:
    - name (str): The name for the new voice.
    - description (str, optional): A brief description of the voice.
    - labels (dict, optional): Labels to categorize the voice. This will be JSON-serialized.
    - file_paths (list of str, optional): List of paths to audio files for voice cloning.

    Returns:
    - dict: Parsed JSON response from the API if successful.

    Raises:
    - Exception: If the API request fails.
    """
    # Load API key directly
    api_key = get_api_key()

    url = "https://api.elevenlabs.io/v1/voices/add"
    headers = {"xi-api-key": api_key}

    # Prepare the multipart form-data payload
    data = {"name": name, "description": description}
    if labels is not None:
        # Convert the labels dictionary to a JSON string as required by the API
        data["labels"] = json.dumps(labels)

    files = []
    file_objs = []  # to track file objects so we can close them later
    if file_paths:
        for path in file_paths:
            if os.path.isfile(path):
                f = open(path, "rb")
                file_objs.append(f)
                # Each file is a tuple: (filename, file-object, mimetype)
                files.append(("files", (os.path.basename(path), f, "audio/mpeg")))
            else:
                print(f"File not found: {path}")

    try:
        response = requests.post(url, headers=headers, data=data, files=files)
    finally:
        # Close all file objects to prevent resource leaks
        for f in file_objs:
            f.close()

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")


# Example usage:
if __name__ == "__main__":
    voice_name = "Jack Test"
    voice_description = "test voice for jack v1"
    audio_files = ["data/jack.wav"]

    try:
        result = add_voice(voice_name, voice_description, None, audio_files)
        print("Voice added successfully:", result)
    except Exception as e:
        print("An error occurred:", e)
