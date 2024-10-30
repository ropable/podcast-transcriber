import whisper
from whisper.utils import get_writer


def get_model(model_name: str = "tiny.en", in_memory: bool = False):
    """Return (download if needed) the requested Whisper model (default download
    location is ~/.cache/whisper)."""
    return whisper.load_model(name=model_name, in_memory=in_memory)


def get_transcription(
    model, audio_path: str, language: str = "en", verbose: bool = True
):
    """Transcribe an audio file using a Whisper model, and return a dictionary
    containing the resulting text and segment-level details.
    """
    return model.transcribe(audio=audio_path, language=language, verbose=verbose)


def write_transcription(
    transcription: dict, name: str, output_format="tsv", output_dir="transcripts"
):
    """For the passed-in transcription dict and name, writes an output file of
    the nominated format into `output_dir`."""
    writer = get_writer(output_format, output_dir)
    writer(transcription, f"{name}.{output_format}")
