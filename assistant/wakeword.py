import logging
logger = logging.getLogger(__name__)

import threading
import pyaudio
import numpy as np
import time

_wakeword_thread = None
_wakeword_active = False
_wakeword_callback = None

def _wakeword_worker():
    global _wakeword_active
    try:
        from openwakeword.model import Model
        logger.info("[JARVIS] Loading Wake Word model ('hey_jarvis')...")
        owwModel = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
        
        audio = pyaudio.PyAudio()
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = 1280
        
        while True:
            if not _wakeword_active:
                time.sleep(0.5)
                continue
                
            try:
                mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
                logger.info("[JARVIS] Wake word listening started. Say 'Hey Jarvis'...")
                
                while _wakeword_active:
                    data = np.frombuffer(mic_stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
                    prediction = owwModel.predict(data)
                    
                    # Check if 'hey_jarvis' was detected above a threshold
                    score = prediction.get('hey_jarvis', 0.0)
                    if score > 0.6:
                        logger.info(f"\n[JARVIS] Wake word detected! (Score: {score})")
                        if _wakeword_callback:
                            # We MUST close stream before callback so the main microphone can be used by speech_recognition
                            mic_stream.stop_stream()
                            mic_stream.close()
                            
                            _wakeword_callback()
                        
                        # Wait a bit after callback completes
                        time.sleep(1)
                        break
                        
                # If _wakeword_active became false during the inner loop
                if not mic_stream.is_stopped():
                    mic_stream.stop_stream()
                    mic_stream.close()
                
            except Exception as e:
                logger.info(f"[WakeWord Error] Microphone error: {e}")
                time.sleep(2)
                
    except ImportError:
        logger.info("[JARVIS] openwakeword not installed. Hands-free mode disabled.")
    except Exception as e:
        logger.info(f"[JARVIS] Failed to start wake word engine: {e}")

def start_wakeword_engine(callback):
    global _wakeword_thread, _wakeword_active, _wakeword_callback
    _wakeword_callback = callback
    _wakeword_active = True
    
    if _wakeword_thread is None or not _wakeword_thread.is_alive():
        _wakeword_thread = threading.Thread(target=_wakeword_worker, daemon=True)
        _wakeword_thread.start()

def pause_wakeword():
    global _wakeword_active
    _wakeword_active = False

def resume_wakeword():
    global _wakeword_active
    _wakeword_active = True
