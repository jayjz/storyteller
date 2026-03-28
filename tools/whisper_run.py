import whisper

audio = 'stories/002_elijah_still_small_voice/assets/audio/002_elijah_still_small_voice_mixed_20260327_145939.wav'
out = 'stories/002_elijah_still_small_voice/assets/audio/002_elijah_still_small_voice.srt'

print('Loading model...')
model = whisper.load_model('small')

print('Transcribing...')
result = model.transcribe(audio, language='en', fp16=False)

def fmt(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    ms = int((s % 1) * 1000)
    return f'{h:02d}:{m:02d}:{sec:02d},{ms:03d}'

with open(out, 'w', encoding='utf-8') as f:
    for i, seg in enumerate(result['segments'], 1):
        start = fmt(seg['start'])
        end = fmt(seg['end'])
        text = seg['text'].strip()
        f.write(f'{i}\n{start} --> {end}\n{text}\n\n')

print('Done:', out)
print('Segments:', len(result['segments']))
