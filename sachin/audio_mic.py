import io
import httpx
import sounddevice as sd
import wavio

# Parameters for recording
duration = 5  # seconds
sample_rate = 16000  # Hz
channels = 1  # mono

print("Recording...")

# Record audio from microphone
audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels)
sd.wait()  # Wait until recording is finished

print("Recording finished.")

# Save recorded audio to an in-memory WAV file
wav_io = io.BytesIO()
wavio.write(wav_io, audio_data, sample_rate, sampwidth=2)
wav_io.seek(0)  # Reset pointer to start of file

# Prepare files dict for httpx
files = {
    'file': ('microphone.wav', wav_io, 'audio/wav'),
    'model': (None, 'Systran/faster-whisper-small')  # or your required model
}

# Send POST request
response = httpx.post('https://dwani-whisper.hf.space/v1/audio/transcriptions', files=files)

print("Response:")
print(response.text)
