# Podcast Transcriber

Reference: <https://github.com/openai/whisper>

```python
import feedparser
import requests
import whisper
from slugify import slugify

model = whisper.load_model('small.en')
rss_url = 'https://feeds.redcircle.com/0cc66fc4-ccb8-4c60-8cc6-7367e52c4159'
d = feedparser.parse(rss_url)
episodes = d['entries']

# Note that the RSS feed returns newest episodes first
ep271 = episodes[1]
title = slugify(ep271['title'])
url = ep271['links'][0]['href']
episode_file = f'episodes/{title}.mp3'
outfile = open(episode_file, 'wb')
resp = requests.get(url, stream=True)
for chunk in resp.iter_content(chunk_size=1024*16):
    outfile.write(chunk)
outfile.close()
transcription = model.transcribe(episode_file)
transcript = f'transcripts/{title}.txt'
outfile = open(transcript, 'w')
for segment in transcription['segments']:
    outfile.write(segment['text'] + '\n')
outfile.close()

ep272 = episodes[0]
title = slugify(ep272['title'])
url = ep272['links'][0]['href']
episode_file = f'episodes/{title}.mp3'
outfile = open(episode_file, 'wb')
resp = requests.get(url, stream=True)
for chunk in resp.iter_content(chunk_size=1024*16):
    outfile.write(chunk)
outfile.close()
transcription = model.transcribe(episode_file)
transcript = f'transcripts/{title}.txt'
outfile = open(transcript, 'w')
for segment in transcription['segments']:
    outfile.write(segment['text'] + '\n')
outfile.close()
```
