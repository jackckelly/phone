import os
from typing import Optional
from deepgram import DeepgramClient, PrerecordedOptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DeepgramWrapper:
    def __init__(self):
        """Initialize the Deepgram client with API key from environment variables."""
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not found in environment variables")
        self.client = DeepgramClient(api_key=self.api_key)

    def transcribe_file(
        self, file_path: str, language: str = "en", model: str = "nova-3"
    ) -> Optional[str]:
        """
        Transcribe an audio file using Deepgram.

        Args:
            file_path (str): Path to the audio file
            language (str): Language code (default: 'en' for English)
            model (str): Deepgram model to use (default: 'nova-3')

        Returns:
            Optional[str]: The transcribed text if successful, None otherwise
        """
        try:
            with open(file_path, "rb") as audio:
                source = {"buffer": audio, "mimetype": "audio/wav"}
                options = PrerecordedOptions(
                    model=model, smart_format=True, language=language
                )
                response = self.client.listen.rest.v("1").transcribe_file(
                    source, options
                )
                return response.results.channels[0].alternatives[0].transcript
        except Exception as e:
            print(f"Error transcribing file {file_path}: {str(e)}")
            return None


def main():
    """Example usage of the DeepgramWrapper class."""
    # Example usage
    transcriber = DeepgramWrapper()

    # Replace with your audio file path
    audio_file = "../data/18609188146/files/jack.wav"

    if os.path.exists(audio_file):
        transcript = transcriber.transcribe_file(audio_file)
        if transcript:
            print("Transcription successful:")
            print(transcript)
        else:
            print("Transcription failed")
    else:
        print(f"File not found: {audio_file}")


if __name__ == "__main__":
    main()
