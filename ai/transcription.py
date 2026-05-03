# ГОЛОСОВОЙ МОДУЛЬ ОТКЛЮЧЁН ВРЕМЕННО
# import json
# import logging
# import os
# import subprocess
# import tempfile
# import wave
# from pathlib import Path
# from vosk import Model, KaldiRecognizer
# from config import VOSK_MODEL_PATH
#
# logger = logging.getLogger(__name__)
#
# _model: Model | None = None
#
#
# def _get_model() -> Model:
#     global _model
#     if _model is None:
#         if not Path(VOSK_MODEL_PATH).exists():
#             raise FileNotFoundError(f"Vosk model not found at: {VOSK_MODEL_PATH}")
#         _model = Model(VOSK_MODEL_PATH)
#     return _model
#
#
# def _ogg_to_wav(ogg_path: str, wav_path: str) -> None:
#     result = subprocess.run(
#         ["ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path],
#         capture_output=True,
#     )
#     if result.returncode != 0:
#         raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()}")
#
#
# def transcribe(ogg_path: str) -> str:
#     model = _get_model()
#     with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
#         wav_path = tmp.name
#     try:
#         _ogg_to_wav(ogg_path, wav_path)
#         with wave.open(wav_path, "rb") as wf:
#             rec = KaldiRecognizer(model, wf.getframerate())
#             results = []
#             while True:
#                 data = wf.readframes(4000)
#                 if not data:
#                     break
#                 if rec.AcceptWaveform(data):
#                     res = json.loads(rec.Result())
#                     results.append(res.get("text", ""))
#             final = json.loads(rec.FinalResult())
#             results.append(final.get("text", ""))
#         text = " ".join(t for t in results if t).strip()
#         logger.info("Transcribed audio: %d chars", len(text))
#         return text
#     finally:
#         os.unlink(wav_path)

import logging

logger = logging.getLogger(__name__)


def transcribe(ogg_path: str) -> str:
    logger.warning("Voice module is disabled")
    return ""
