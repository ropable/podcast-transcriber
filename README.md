# Audio Transcriber

A basic project to make use of the OpenAI Whisper general-purpose speech recognition model to transcribe audio files.

Reference: <https://github.com/openai/whisper>

The `transcriber` function expects to be passed a model name to use, a blob container of input audio files, and (optionally) an output blob container for transcripts.

## Podcast example

Download and transcribe a podcast episode like so:

```python
import feedparser
import requests
import whisper
from slugify import slugify

model = whisper.load_model('small.en')
# The BBM podcast RSS URL:
rss_url = 'https://feeds.redcircle.com/0cc66fc4-ccb8-4c60-8cc6-7367e52c4159'
d = feedparser.parse(rss_url)
episodes = d['entries']

# Note that the RSS feed returns newest episodes first
ep = episodes[0]
title = slugify(ep['title'])
url = ep['links'][0]['href']
podcast_path = f'episodes/{title}.mp3'
download = open(podcast_path, 'wb')

resp = requests.get(url, stream=True)
for chunk in resp.iter_content(chunk_size=1024*16):
    download.write(chunk)
download.close()

transcription = model.transcribe(podcast_path)
transcript_path = f'transcripts/{title}.txt'
transcript = open(transcript_path, 'w')

for segment in transcription['segments']:
    transcript.write(segment['text'] + '\n')
transcript.close()
```
