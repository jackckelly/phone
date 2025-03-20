import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ElevenLabsWrapper:
    def __init__(self):
        """Initialize the Deepgram transcriber with API key from environment variables."""
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not found in environment variables")

    def add_voice(self, name, description="", labels=None, file_paths=None):
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
        api_key = os.getenv("ELEVENLABS_API_KEY")

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


if __name__ == "__main__":
    """Main function to demonstrate ElevenLabsWrapper usage."""
    try:
        # Initialize the wrapper
        eleven_labs = ElevenLabsWrapper()

        # Example: Create a new voice with audio files
        # Replace these paths with actual audio file paths
        audio_files = ["path/to/audio1.mp3", "path/to/audio2.mp3"]

        # Example labels for voice categorization
        labels = {"category": "custom", "language": "en", "gender": "neutral"}

        # Create a new voice
        result = eleven_labs.add_voice(
            name="My Custom Voice",
            description="A custom voice created using ElevenLabs API",
            labels=labels,
            file_paths=audio_files,
        )
        print(f"Successfully created voice: {result}")

    except Exception as e:
        print(f"Error: {str(e)}")
