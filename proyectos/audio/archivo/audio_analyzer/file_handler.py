import soundfile as sf
import librosa
import moviepy as mp
from pathlib import Path
from tempfile import NamedTemporaryFile
import logging
from typing import Tuple, Optional
import numpy as np
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class AudioFileError(Exception):
    """Custom exception for audio file operations."""
    pass


class AudioFileHandler:
    """Handles loading and saving of audio files."""

    SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.mp4'}

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    @contextmanager
    def _video_clip_context(self, file_path: str):
        """Context manager for video file handling."""
        clip = None
        try:
            clip = mp.VideoFileClip(file_path)
            yield clip
        finally:
            if clip is not None:
                clip.close()

    def load_file(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file with fallback options."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise AudioFileError(f"Unsupported format: {path.suffix}")

        try:
            if path.suffix.lower() == '.mp4':
                return self._load_from_video(file_path)

            # Try soundfile first
            try:
                audio_data, sr = sf.read(file_path)
                if sr != self.sample_rate:
                    audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
                return audio_data, self.sample_rate
            except:
                # Fallback to librosa
                return librosa.load(file_path, sr=self.sample_rate)

        except Exception as e:
            raise AudioFileError(f"Failed to load audio: {str(e)}")

    def _load_from_video(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Extract audio from video file."""
        with NamedTemporaryFile(suffix='.wav') as temp_audio:
            with self._video_clip_context(file_path) as video:
                video.audio.write_audiofile(temp_audio.name, verbose=False, logger=None)
                return self.load_file(temp_audio.name)
