import whisper
from whisper.utils import get_writer


def get_model(model="small.en")
    return whisper.load_model(model)


def get_transcribe(model, audio, language="en", verbose=True):
    return model.transcribe(audio=audio, language=language, verbose=verbose)


def write_transcription(transcribe, name, format="tsv", output_dir="transcripts"):
    writer = get_writer(format, output_dir)
    writer(transcribe, f"{name}.{format}")
