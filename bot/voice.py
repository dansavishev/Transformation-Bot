import os
import json
import wave
import subprocess
import logging
from vosk import Model, KaldiRecognizer

logger = logging.getLogger(__name__)

_model = None

def get_model() -> Model:
    global _model
    if _model is None:
        model_path = os.getenv("VOSK_MODEL_PATH", "vosk-model-small-ru-0.22")
        if not os.path.exists(model_path):
            raise RuntimeError(f"Vosk модель не найдена: {model_path}")
        _model = Model(model_path)
        logger.info("Vosk модель загружена")
    return _model

def transcribe_ogg(ogg_path: str) -> str:
    wav_path = ogg_path.replace(".ogg", ".wav")
    try:
        subprocess.run(
            ["ffmpeg", "-i", ogg_path, "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

        rec = KaldiRecognizer(get_model(), 16000)
        with wave.open(wav_path, "rb") as wf:
            while True:
                data = wf.readframes(4000)
                if not data:
                    break
                rec.AcceptWaveform(data)

        result = json.loads(rec.FinalResult())
        return result.get("text", "").strip()
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
