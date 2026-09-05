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
        logger.info("[VAVE] Loading Wake Word model ('hey_vave')...")
        owwModel = Model(wakeword_models=["hey_vave"], inference_framework="onnx")
        
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
                logger.info("[VAVE] Wake word listening started. Say 'Hey Vave'...")
                
                while _wakeword_active:
                    data = np.frombuffer(mic_stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
                    prediction = owwModel.predict(data)
                    
                    # Check if 'hey_vave' was detected above a threshold
                    score = prediction.get('hey_vave', 0.0)
                    if score > 0.6:
                        logger.info(f"\n[VAVE] Wake word detected! (Score: {score})")
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
        logger.info("[VAVE] openwakeword not installed. Hands-free mode disabled.")
    except Exception as e:
        logger.info(f"[VAVE] Failed to start wake word engine: {e}")

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
