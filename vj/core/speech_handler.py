"""
Speech Handler Module for Dwani AI
Manages speech recognition and text-to-speech functionality
"""

import speech_recognition as sr
import pyttsx3
from typing import Optional, Tuple, Dict
from .config import DwaniConfig
import sounddevice as sd
import wavio
import httpx
import io
import tempfile
import platform
import subprocess
import os
import simpleaudio as sa

class SpeechHandler:
    """Handles speech recognition and text-to-speech operations"""
    
    def __init__(self):
        """Initialize speech recognition and TTS engines"""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = None
        
        # Configure speech recognition
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
    
    def _get_tts_engine(self):
        """Get a fresh TTS engine instance"""
        try:
            if self.tts_engine:
                # Try to stop any running TTS
                try:
                    self.tts_engine.stop()
                except:
                    pass
                # Delete the old engine
                del self.tts_engine
            
            # Create a new engine
            self.tts_engine = pyttsx3.init()
            
            # Configure TTS
            self.tts_engine.setProperty('rate', DwaniConfig.TTS_VOICE_RATE)
            self.tts_engine.setProperty('volume', DwaniConfig.TTS_VOICE_VOLUME)
            
            return self.tts_engine
        except Exception as e:
            print(f"Error creating TTS engine: {e}")
            return None
    
    def _fallback_tts(self, text: str) -> bool:
        """Fallback TTS using Windows built-in speech synthesis"""
        try:
            if platform.system() == "Windows":
                # Use PowerShell's SpeechSynthesizer
                ps_script = f"""
                Add-Type -AssemblyName System.Speech
                $synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer
                $synthesizer.Speak("{text.replace('"', '\\"')}")
                """
                
                subprocess.run([
                    "powershell", "-Command", ps_script
                ], capture_output=True, timeout=30)
                return True
            else:
                # Use espeak on Linux/Mac
                subprocess.run([
                    "espeak", text
                ], capture_output=True, timeout=30)
                return True
                
        except Exception as e:
            print(f"Fallback TTS failed: {e}")
            return False
    
    def listen_to_voice(self) -> Tuple[bool, str]:
        """
        Record audio from the microphone and transcribe using remote Whisper API
        Returns:
            Tuple[bool, str]: (success, text or error_message)
        """
        duration = 5  # seconds
        sample_rate = 16000
        channels = 1
        try:
            print("Recording for 5 seconds... Speak now.")
            audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels)
            sd.wait()
            print("Recording complete. Transcribing...")
            wav_io = io.BytesIO()
            wavio.write(wav_io, audio_data, sample_rate, sampwidth=2)
            wav_io.seek(0)

            files = {
                'file': ('microphone.wav', wav_io, 'audio/wav'),
                'model': (None, 'Systran/faster-whisper-small')
            }

            response = httpx.post('https://dwani-whisper.hf.space/v1/audio/transcriptions', files=files)

            if response.status_code == 200:
                transcription = response.text.strip()
                if transcription:
                    print(f"Transcribed: {transcription}")
                    return True, transcription
                else:
                    print("Transcription empty, try again.")
                    return False, "Transcription empty, try again."
            else:
                print(f"Transcription error: {response.status_code} - {response.text}")
                return False, f"Transcription error: {response.status_code} - {response.text}"
        except Exception as e:
            print(f"Error during recording or transcription: {str(e)}")
            return False, f"Error during recording or transcription: {str(e)}"
    
    def speak_text(self, text: str) -> bool:
        """
        Generate speech using remote TTS API and play it cross-platform
        Args:
            text: Text to speak
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Clean the text first
            cleaned_text = self._clean_text_for_tts(text)
            if not cleaned_text:
                print("No text to speak after cleaning")
                return False
            
            # Use HuggingFace TTS API (as in assistant_v5.py)
            tts_server_url = "https://dwani-whisper.hf.space/v1"
            
            print(f"Generating speech for: {cleaned_text[:50]}...")
            
            res = httpx.post(
                f"{tts_server_url}/audio/speech",
                json={
                    "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
                    "voice": "af_heart",
                    "input": cleaned_text,
                    "response_format": "wav",
                    "speed": 1,
                },
                timeout=60
            )
            
            if res.status_code != 200:
                print(f"TTS API error: {res.status_code} - {res.text}")
                # Try fallback TTS
                return self._fallback_tts(cleaned_text)
            
            # Save the audio to a temporary file
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_path = temp_file.name
                    temp_file.write(res.content)
                
                print(f"Audio saved to: {temp_path}")
                
                # Play the audio based on the operating system
                system = platform.system()
                
                if system == "Windows":
                    return self._play_audio_windows(temp_path)
                elif system == "Darwin":  # macOS
                    return self._play_audio_macos(temp_path)
                elif system == "Linux":
                    return self._play_audio_linux(temp_path)
                else:
                    print(f"Autoplay not supported on {system}. Open {temp_path} manually.")
                    return False
                    
            finally:
                # Clean up temporary file
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                        print(f"Temporary file cleaned: {temp_path}")
                    except Exception as e:
                        print(f"Warning: Could not delete temporary file {temp_path}: {str(e)}")
                        
        except Exception as e:
            print(f"Error generating speech: {str(e)}")
            # Try fallback TTS as last resort
            return self._fallback_tts(text)
    
    def _play_audio_windows(self, audio_path: str) -> bool:
        """Play audio on Windows with multiple fallback methods"""
        try:
            # Method 1: Try simpleaudio first (non-blocking)
            try:
                import threading
                wave_obj = sa.WaveObject.from_wave_file(audio_path)
                play_obj = wave_obj.play()
                
                # Start playback in background thread
                def play_audio():
                    play_obj.wait_done()
                
                audio_thread = threading.Thread(target=play_audio, daemon=True)
                audio_thread.start()
                
                print("Audio playing in background with simpleaudio")
                return True
            except Exception as e:
                print(f"simpleaudio failed: {e}")
            
            # Method 2: Try Windows Media Player (non-blocking)
            try:
                import subprocess
                subprocess.Popen([
                    "start", "wmplayer", audio_path
                ], shell=True)
                print("Audio playing with Windows Media Player")
                return True
            except Exception as e:
                print(f"Windows Media Player failed: {e}")
            
            # Method 3: Try PowerShell audio playback (non-blocking)
            try:
                ps_script = f"""
                Add-Type -AssemblyName System.Media
                $player = New-Object System.Media.SoundPlayer
                $player.SoundLocation = "{audio_path.replace('\\', '\\\\')}"
                $player.Play()
                Start-Sleep -Seconds 2
                $player.Dispose()
                """
                subprocess.Popen([
                    "powershell", "-Command", ps_script
                ])
                print("Audio playing with PowerShell")
                return True
            except Exception as e:
                print(f"PowerShell audio failed: {e}")
            
            # Method 4: Try using playsound library (non-blocking)
            try:
                try:
                    from playsound import playsound  # type: ignore
                except ImportError:
                    print("playsound not available")
                    raise ImportError("playsound not installed")
                
                import threading
                
                def play_sound():
                    playsound(audio_path)
                
                sound_thread = threading.Thread(target=play_sound, daemon=True)
                sound_thread.start()
                
                print("Audio playing with playsound")
                return True
            except ImportError:
                print("playsound not available")
            except Exception as e:
                print(f"playsound failed: {e}")
            
            print("All Windows audio methods failed")
            return False
            
        except Exception as e:
            print(f"Error in Windows audio playback: {e}")
            return False
    
    def _play_audio_macos(self, audio_path: str) -> bool:
        """Play audio on macOS"""
        try:
            subprocess.run(["afplay", audio_path], check=True, timeout=30)
            return True
        except Exception as e:
            print(f"macOS audio playback failed: {e}")
            return False
    
    def _play_audio_linux(self, audio_path: str) -> bool:
        """Play audio on Linux"""
        try:
            subprocess.run(["aplay", audio_path], check=True, timeout=30)
            return True
        except Exception as e:
            print(f"Linux audio playback failed: {e}")
            return False
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text to prevent TTS errors"""
        if not text:
            return ""
        
        # Remove or replace problematic characters
        cleaned = text.replace('\n', ' ').replace('\r', ' ')
        cleaned = cleaned.replace('"', '').replace("'", '')
        cleaned = cleaned.replace('{', '').replace('}', '')
        cleaned = cleaned.replace('[', '').replace(']', '')
        
        # Remove multiple spaces
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Limit length to prevent SAPI5 errors
        if len(cleaned) > 500:
            cleaned = cleaned[:500] + "..."
        
        return cleaned.strip()
    
    def _chunk_text(self, text: str, max_length: int = 200) -> list:
        """Split text into smaller chunks for TTS"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by sentences first
        sentences = text.split('. ')
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If still too long, split by words
        if not chunks or any(len(chunk) > max_length for chunk in chunks):
            chunks = []
            words = text.split()
            current_chunk = ""
            
            for word in words:
                if len(current_chunk) + len(word) + 1 < max_length:
                    current_chunk += word + " "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = word + " "
            
            if current_chunk:
                chunks.append(current_chunk.strip())
        
        return chunks
    
    def speak_emergency_alert(self, message: str) -> bool:
        """
        Speak emergency alert with higher priority
        
        Args:
            message: Emergency message to speak
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Clean and chunk the text to prevent SAPI5 errors
            cleaned_text = self._clean_text_for_tts(message)
            chunks = self._chunk_text(cleaned_text, max_length=150)  # Shorter chunks for emergency
            
            engine = self._get_tts_engine()
            if not engine:
                print("Could not create TTS engine for emergency alert, trying fallback...")
                return self._fallback_tts(f"EMERGENCY ALERT: {cleaned_text}")
            
            # Set higher volume for emergency alerts
            original_volume = engine.getProperty('volume')
            engine.setProperty('volume', 1.0)
            
            # Speak each chunk separately
            success_count = 0
            for chunk in chunks:
                if chunk.strip():  # Only speak non-empty chunks
                    try:
                        engine.say(f"EMERGENCY ALERT: {chunk}")
                        engine.runAndWait()
                        success_count += 1
                    except Exception as chunk_error:
                        print(f"Error speaking emergency chunk '{chunk[:50]}...': {chunk_error}")
                        # Try fallback for this chunk
                        if not self._fallback_tts(f"EMERGENCY ALERT: {chunk}"):
                            print(f"Fallback also failed for emergency chunk: {chunk[:50]}...")
                        else:
                            success_count += 1
            
            # Restore original volume
            engine.setProperty('volume', original_volume)
            return success_count > 0
        except Exception as e:
            print(f"Error in emergency speech: {e}")
            # Try fallback as last resort
            return self._fallback_tts(f"EMERGENCY ALERT: {self._clean_text_for_tts(message)}")
    
    def test_speech_system(self) -> Dict[str, bool]:
        """
        Test speech recognition and TTS systems
        
        Returns:
            Dict[str, bool]: Test results
        """
        results = {
            'microphone_available': False,
            'tts_available': False,
            'speech_recognition': False
        }
        
        # Test microphone
        try:
            with self.microphone as source:
                results['microphone_available'] = True
        except Exception:
            pass
        
        # Test TTS
        try:
            engine = self._get_tts_engine()
            if engine:
                engine.say("Test")
                engine.runAndWait()
                results['tts_available'] = True
        except Exception:
            pass
        
        # Test speech recognition (basic test)
        try:
            self.recognizer.energy_threshold
            results['speech_recognition'] = True
        except Exception:
            pass
        
        return results 