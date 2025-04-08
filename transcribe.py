import os
import json
import torch
import torchaudio
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from tqdm import tqdm
import soundfile as sf
import numpy as np
from pathlib import Path
import concurrent.futures
import logging
import subprocess
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioTranscriber:
    def __init__(self, settings_path="settings.json"):
        self.settings = self._load_settings(settings_path)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Initialize model and processor
        self.processor = WhisperProcessor.from_pretrained(self.settings["model"])
        self.model = WhisperForConditionalGeneration.from_pretrained(self.settings["model"]).to(self.device)
        
        # Create output directories if they don't exist
        os.makedirs(self.settings["output_dir"], exist_ok=True)
        os.makedirs(self.settings["input_dir"], exist_ok=True)

    def _load_settings(self, settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        return settings

    def _convert_audio(self, input_path):
        """Convert audio to WAV format using ffmpeg"""
        try:
            # Create a temporary file for the converted audio
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_path = temp_file.name
            temp_file.close()

            # Convert the audio file to WAV format
            cmd = [
                'ffmpeg', '-i', input_path,
                '-acodec', 'pcm_s16le',  # Use 16-bit PCM
                '-ar', '16000',          # Set sample rate to 16kHz
                '-ac', '1',              # Convert to mono
                '-y',                    # Overwrite output file if it exists
                temp_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            return temp_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Error converting audio file {input_path}: {str(e)}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return None
        except Exception as e:
            logger.error(f"Unexpected error converting audio file {input_path}: {str(e)}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return None

    def _load_audio(self, audio_path):
        try:
            # First try to load directly with soundfile
            try:
                audio, sample_rate = sf.read(audio_path)
            except Exception:
                # If direct loading fails, try converting with ffmpeg
                logger.info(f"Converting audio file {audio_path} to WAV format...")
                converted_path = self._convert_audio(audio_path)
                if converted_path is None:
                    return None
                try:
                    audio, sample_rate = sf.read(converted_path)
                finally:
                    # Clean up the temporary file
                    if os.path.exists(converted_path):
                        os.unlink(converted_path)
            
            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            # Resample to 16kHz if needed
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                audio = resampler(torch.from_numpy(audio).float())
                audio = audio.numpy()
            
            return audio
        except Exception as e:
            logger.error(f"Error loading audio file {audio_path}: {str(e)}")
            return None

    def _transcribe_audio(self, audio_path):
        try:
            # Load and preprocess audio
            audio = self._load_audio(audio_path)
            if audio is None:
                return None

            # Process audio
            input_features = self.processor(
                audio, 
                sampling_rate=16000, 
                return_tensors="pt"
            ).input_features.to(self.device)

            # Generate transcription
            predicted_ids = self.model.generate(input_features, language=self.settings["language"])
            transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

            return transcription
        except Exception as e:
            logger.error(f"Error transcribing {audio_path}: {str(e)}")
            return None

    def _save_transcription(self, audio_path, transcription):
        if transcription is None:
            return

        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        
        for format in self.settings["output_format"]:
            output_path = os.path.join(self.settings["output_dir"], f"{base_name}.{format}")
            
            if format == "txt":
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(transcription)
            elif format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump({"text": transcription}, f, ensure_ascii=False, indent=2)

    def process_file(self, audio_path):
        if self.settings["verbose"]:
            logger.info(f"Processing {audio_path}")
        
        transcription = self._transcribe_audio(audio_path)
        self._save_transcription(audio_path, transcription)
        
        if self.settings["verbose"]:
            logger.info(f"Completed {audio_path}")

    def process_batch(self):
        # Get all audio files in input directory
        audio_files = []
        for ext in ['.wav', '.mp3', '.m4a', '.flac']:
            audio_files.extend(list(Path(self.settings["input_dir"]).glob(f"*{ext}")))
        
        if not audio_files:
            logger.warning("No audio files found in input directory")
            return

        logger.info(f"Found {len(audio_files)} audio files to process")

        # Process files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.settings["batch_size"]) as executor:
            list(tqdm(
                executor.map(self.process_file, audio_files),
                total=len(audio_files),
                desc="Processing files"
            ))

def main():
    transcriber = AudioTranscriber()
    transcriber.process_batch()

if __name__ == "__main__":
    main() 