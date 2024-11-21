import argparse
import logging
import os
import sys
from tempfile import TemporaryDirectory
from typing import Optional

import whisper
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobClient, ContainerClient
from dotenv import load_dotenv
from whisper.utils import get_writer

# Load environment variables.
load_dotenv()
# Assumes a connection string secret present as an environment variable.
CONN_STR = os.getenv("AZURE_CONNECTION_STRING")

# Configure logging for the default logger and for the `azure` logger.
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
LOGGER.addHandler(handler)

# Set the logging level for all azure-* libraries (the azure-storage-blob library uses this one).
# Reference: https://learn.microsoft.com/en-us/azure/developer/python/sdk/azure-sdk-logging
azure_logger = logging.getLogger("azure")
azure_logger.setLevel(logging.WARNING)


def get_model(
    model_name: str = "tiny.en",
    download_root: Optional[str] = None,
    in_memory: bool = False,
):
    """Return (download if needed) the requested Whisper model (default download
    location is ~/.cache/whisper)."""
    return whisper.load_model(
        name=model_name, download_root=download_root, in_memory=in_memory
    )


def get_transcription(
    model, audio_path: str, language: str = "en", verbose: bool = True
):
    """Transcribe an audio file using a Whisper model, and return a dictionary
    containing the resulting text and segment-level details.
    """
    try:
        return model.transcribe(audio=audio_path, language=language, verbose=verbose)
    except RuntimeError:
        LOGGER.warning(f"{audio_path} could not be processed")
        return


def write_transcription(
    transcription: dict, name: str, output_format="tsv", output_dir="transcripts"
):
    """For the passed-in transcription dict and name, writes an output file of
    the nominated format into `output_dir`."""
    writer = get_writer(output_format, output_dir)
    writer(result=transcription, audio_path=f"{name}.{output_format}")
    return writer


def get_audio_paths(conn_str, container_name):
    """
    Check Azure blob storage for the list of uploaded audio files, returns a
    list of paths.
    """
    try:
        container_client = ContainerClient.from_connection_string(
            conn_str, container_name
        )
        blob_list = container_client.list_blobs()
        remote_blobs = [blob.name for blob in blob_list]
    except ResourceNotFoundError:
        remote_blobs = []

    return remote_blobs


def get_blob_client(conn_str, container_name, blob_name):
    return BlobClient.from_connection_string(
        conn_str,
        container_name,
        blob_name,
    )


if __name__ == "__main__":
    """
    Imputs:
        - Azure container of input audio files
        - Model name (optional)
        - Transcript format (optional)
        - Output container of transcript files (optional)

    Outputs:
        - Transcript files of the nominated format in the output container
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--container",
        help="Blob container of input audio files",
        action="store",
        required=True,
    )
    parser.add_argument(
        "-m",
        "--model",
        help="Whisper speech recognition model name to use (optional)",
        default="tiny.en",
        action="store",
        required=False,
    )
    parser.add_argument(
        "-f",
        "--format",
        help="Transcript output format (optional)",
        default="tsv",
        action="store",
        required=False,
    )
    parser.add_argument(
        "-d",
        "--dest-container",
        help="Destination blob container for transcript files (optional)",
        action="store",
        required=False,
    )
    args = parser.parse_args()

    input_container_name = args.container
    model_name = args.model
    format = args.format
    if not args.dest_container:
        # Set the destination container to be the same as the source.
        output_container_name = input_container_name
    else:
        output_container_name = args.dest_container

    LOGGER.info(f"Instantiating {model_name} model")
    model = get_model(model_name)

    # First, get a directory listing for the nominated input container.
    audio_paths = get_audio_paths(CONN_STR, input_container_name)
    audio_allowlist = [".mp3", ".m4a"]

    for blob_name in audio_paths:
        name, ext = os.path.splitext(blob_name)
        if ext.lower() not in audio_allowlist:
            LOGGER.info(f"Skipping {blob_name}")
            continue  # Skip obvious non-audio files.

        # Download the audio file locally to the temp directory.
        local_dest = TemporaryDirectory()
        dest_path = os.path.join(local_dest.name, blob_name)
        blob_client = BlobClient.from_connection_string(
            CONN_STR, input_container_name, blob_name
        )

        try:
            LOGGER.info(f"Downloading {blob_name}")
            with open(dest_path, "wb") as downloaded_blob:
                download_stream = blob_client.download_blob()
                downloaded_blob.write(download_stream.readall())
        except Exception as e:
            LOGGER.error(f"Exception during download of {blob_name}, aborting")
            LOGGER.exception(e)
            continue

        # Get the transcript for this downloaded audio file.
        LOGGER.info(f"Deriving transcription for {dest_path}")
        transcription = get_transcription(model=model, audio_path=dest_path)

        # Write the transcription.
        audio_path = f"{name}.{format}"
        LOGGER.info(f"Writing transcription to {audio_path}")
        writer = get_writer(output_format=format, output_dir=local_dest.name)
        writer(result=transcription, audio_path=f"{name}.{format}")

        # Upload the transcription file to the container.
        LOGGER.info(f"Uploading to blob {audio_path}")
        blob_client = BlobClient.from_connection_string(
            CONN_STR, output_container_name, f"{audio_path}"
        )
        with open(os.path.join(local_dest.name, audio_path), "rb") as source_data:
            blob_client.upload_blob(source_data, overwrite=True)
