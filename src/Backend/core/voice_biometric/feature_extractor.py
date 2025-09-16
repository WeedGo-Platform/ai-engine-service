"""
Production Voice Feature Extractor
Implements ECAPA-TDNN and ResNet34-SE for robust speaker embeddings
"""

import numpy as np
import torch
import torchaudio
import onnxruntime as ort
from typing import Dict, Optional, Tuple, Union
from pathlib import Path
import logging
import librosa
import soundfile as sf
from scipy import signal
import yaml
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AudioFeatures:
    """Container for extracted audio features"""
    embedding: np.ndarray
    sample_rate: int
    duration: float
    quality_score: float
    metadata: Dict

class VoiceFeatureExtractor:
    """
    Production-ready feature extraction using state-of-the-art models
    """

    def __init__(self, config_path: str = "config/voice_auth_config.yaml"):
        """Initialize with configuration"""
        self.config = self._load_config(config_path)
        self.sample_rate = self.config['audio']['sample_rate']

        # Initialize ONNX Runtime sessions
        self.ecapa_session = None
        self.resnet_session = None

        # Load models
        self._load_models()

        # Audio preprocessing parameters
        self.n_fft = 512
        self.hop_length = 160
        self.n_mels = 80

        logger.info("Voice Feature Extractor initialized")

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._get_default_config()

        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        # Replace environment variables
        return self._replace_env_vars(config)

    def _get_default_config(self) -> Dict:
        """Return default configuration"""
        return {
            'models': {
                'speaker_verification': {
                    'primary': {
                        'path': 'models/voice/biometric/speaker_verification/ecapa_tdnn.onnx',
                        'embedding_size': 192,
                        'sample_rate': 16000
                    },
                    'secondary': {
                        'path': 'models/voice/biometric/speaker_verification/resnet34_se.onnx',
                        'embedding_size': 256,
                        'sample_rate': 16000
                    },
                    'fusion': {
                        'strategy': 'weighted_concat',
                        'primary_weight': 0.6,
                        'secondary_weight': 0.4
                    }
                }
            },
            'audio': {
                'sample_rate': 16000,
                'channels': 1,
                'preprocessing': {
                    'normalize': True,
                    'remove_silence': True,
                    'noise_reduction': True
                }
            }
        }

    def _replace_env_vars(self, config: Dict) -> Dict:
        """Replace environment variables in config"""
        import os
        import re

        def replace(value):
            if isinstance(value, str):
                # Pattern: ${VAR_NAME:default_value}
                pattern = r'\$\{([^:}]+)(?::([^}]*))?\}'

                def replacer(match):
                    var_name = match.group(1)
                    default = match.group(2) or ''
                    return os.getenv(var_name, default)

                return re.sub(pattern, replacer, value)
            elif isinstance(value, dict):
                return {k: replace(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace(v) for v in value]
            return value

        return replace(config)

    def _load_models(self):
        """Load ONNX models for inference"""
        try:
            # ONNX Runtime providers
            providers = ['CPUExecutionProvider']

            # Session options for optimization
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.inter_op_num_threads = 2
            sess_options.intra_op_num_threads = 2

            # Load ECAPA-TDNN
            ecapa_path = Path(self.config['models']['speaker_verification']['primary']['path'])
            if ecapa_path.exists():
                self.ecapa_session = ort.InferenceSession(
                    str(ecapa_path),
                    sess_options,
                    providers=providers
                )
                logger.info(f"Loaded ECAPA-TDNN model from {ecapa_path}")
            else:
                logger.warning(f"ECAPA-TDNN model not found at {ecapa_path}")

            # Load ResNet34-SE
            resnet_path = Path(self.config['models']['speaker_verification']['secondary']['path'])
            if resnet_path.exists():
                self.resnet_session = ort.InferenceSession(
                    str(resnet_path),
                    sess_options,
                    providers=providers
                )
                logger.info(f"Loaded ResNet34-SE model from {resnet_path}")
            else:
                logger.warning(f"ResNet34-SE model not found at {resnet_path}")

        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            # Fall back to placeholder if models not available
            logger.warning("Using fallback feature extraction")

    def preprocess_audio(
        self,
        audio_data: Union[bytes, np.ndarray],
        source_sr: Optional[int] = None
    ) -> np.ndarray:
        """
        Preprocess audio for feature extraction

        Args:
            audio_data: Raw audio bytes or numpy array
            source_sr: Original sample rate (if known)

        Returns:
            Preprocessed audio array
        """
        # Convert bytes to numpy array if needed
        if isinstance(audio_data, bytes):
            audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
            audio = audio / 32768.0  # Normalize to [-1, 1]
            source_sr = source_sr or 16000
        else:
            audio = audio_data

        # Resample if necessary
        if source_sr and source_sr != self.sample_rate:
            audio = librosa.resample(
                audio,
                orig_sr=source_sr,
                target_sr=self.sample_rate
            )

        # Remove silence
        if self.config['audio']['preprocessing']['remove_silence']:
            audio = self._remove_silence(audio)

        # Noise reduction
        if self.config['audio']['preprocessing']['noise_reduction']:
            audio = self._reduce_noise(audio)

        # Normalize
        if self.config['audio']['preprocessing']['normalize']:
            audio = self._normalize_audio(audio)

        return audio

    def _remove_silence(self, audio: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """Remove silence from audio"""
        # Simple energy-based VAD
        frame_length = int(0.025 * self.sample_rate)  # 25ms frames
        hop_length = int(0.010 * self.sample_rate)     # 10ms hop

        energy = librosa.feature.rms(
            y=audio,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]

        # Find non-silent frames
        non_silent = energy > threshold

        # Expand non-silent regions slightly
        from scipy.ndimage import binary_dilation
        non_silent = binary_dilation(non_silent, iterations=2)

        # Convert frame indices to sample indices
        non_silent_samples = np.repeat(non_silent, hop_length)[:len(audio)]

        # Extract non-silent audio
        if non_silent_samples.any():
            audio = audio[non_silent_samples]

        return audio

    def _reduce_noise(self, audio: np.ndarray) -> np.ndarray:
        """Apply spectral subtraction for noise reduction"""
        # Estimate noise from first 0.5 seconds
        noise_duration = int(0.5 * self.sample_rate)
        if len(audio) > noise_duration:
            noise_profile = audio[:noise_duration]

            # Compute noise spectrum
            noise_fft = np.fft.rfft(noise_profile)
            noise_power = np.abs(noise_fft) ** 2

            # Apply spectral subtraction
            audio_fft = np.fft.rfft(audio)
            audio_power = np.abs(audio_fft) ** 2

            # Subtract noise (with oversubtraction factor)
            alpha = 2.0  # Oversubtraction factor
            clean_power = audio_power - alpha * noise_power[:len(audio_power)]
            clean_power = np.maximum(clean_power, 0.1 * audio_power)  # Spectral floor

            # Reconstruct audio
            phase = np.angle(audio_fft)
            clean_fft = np.sqrt(clean_power) * np.exp(1j * phase)
            audio = np.fft.irfft(clean_fft, n=len(audio))

        return audio

    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to [-1, 1] range"""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val * 0.95  # Leave some headroom
        return audio

    def extract_ecapa_embedding(self, audio: np.ndarray) -> Optional[np.ndarray]:
        """Extract embedding using ECAPA-TDNN model"""
        if self.ecapa_session is None:
            return None

        try:
            # Prepare input for ONNX model
            # ECAPA-TDNN expects [batch, samples]
            audio_input = audio.reshape(1, -1).astype(np.float32)

            # Run inference
            input_name = self.ecapa_session.get_inputs()[0].name
            output_name = self.ecapa_session.get_outputs()[0].name

            embedding = self.ecapa_session.run(
                [output_name],
                {input_name: audio_input}
            )[0]

            # Normalize embedding
            embedding = embedding.squeeze()
            embedding = embedding / np.linalg.norm(embedding)

            return embedding

        except Exception as e:
            logger.error(f"Error extracting ECAPA embedding: {str(e)}")
            return None

    def extract_resnet_embedding(self, audio: np.ndarray) -> Optional[np.ndarray]:
        """Extract embedding using ResNet34-SE model"""
        if self.resnet_session is None:
            return None

        try:
            # Convert audio to mel-spectrogram for ResNet
            mel_spec = self._compute_melspectrogram(audio)

            # ResNet expects [batch, channels, height, width]
            mel_input = mel_spec.reshape(1, 1, *mel_spec.shape).astype(np.float32)

            # Run inference
            input_name = self.resnet_session.get_inputs()[0].name
            output_name = self.resnet_session.get_outputs()[0].name

            embedding = self.resnet_session.run(
                [output_name],
                {input_name: mel_input}
            )[0]

            # Normalize embedding
            embedding = embedding.squeeze()
            embedding = embedding / np.linalg.norm(embedding)

            return embedding

        except Exception as e:
            logger.error(f"Error extracting ResNet embedding: {str(e)}")
            return None

    def _compute_melspectrogram(self, audio: np.ndarray) -> np.ndarray:
        """Compute mel-spectrogram for audio"""
        # Compute STFT
        stft = librosa.stft(
            audio,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )

        # Convert to mel scale
        mel_spec = librosa.feature.melspectrogram(
            S=np.abs(stft) ** 2,
            sr=self.sample_rate,
            n_mels=self.n_mels
        )

        # Convert to log scale
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        return mel_spec_db

    def extract_embeddings(
        self,
        audio_data: Union[bytes, np.ndarray],
        source_sr: Optional[int] = None
    ) -> AudioFeatures:
        """
        Extract voice embeddings using multiple models

        Args:
            audio_data: Raw audio data
            source_sr: Original sample rate

        Returns:
            AudioFeatures object with embeddings and metadata
        """
        # Preprocess audio
        audio = self.preprocess_audio(audio_data, source_sr)

        # Calculate audio quality
        quality_score = self._assess_audio_quality(audio)

        # Extract embeddings from both models
        ecapa_emb = self.extract_ecapa_embedding(audio)
        resnet_emb = self.extract_resnet_embedding(audio)

        # Fuse embeddings based on configuration
        fusion_strategy = self.config['models']['speaker_verification']['fusion']['strategy']

        if fusion_strategy == 'weighted_concat' and ecapa_emb is not None and resnet_emb is not None:
            # Weighted concatenation
            w1 = self.config['models']['speaker_verification']['fusion']['primary_weight']
            w2 = self.config['models']['speaker_verification']['fusion']['secondary_weight']

            embedding = np.concatenate([
                ecapa_emb * w1,
                resnet_emb * w2
            ])
        elif fusion_strategy == 'mean' and ecapa_emb is not None and resnet_emb is not None:
            # Mean fusion
            embedding = (ecapa_emb + resnet_emb) / 2
        elif ecapa_emb is not None:
            # Use primary model only
            embedding = ecapa_emb
        elif resnet_emb is not None:
            # Fall back to secondary model
            embedding = resnet_emb
        else:
            # Fallback: Use simple acoustic features
            logger.warning("Using fallback acoustic features")
            embedding = self._extract_fallback_features(audio)

        # Normalize final embedding
        embedding = embedding / np.linalg.norm(embedding)

        # Create features object
        features = AudioFeatures(
            embedding=embedding,
            sample_rate=self.sample_rate,
            duration=len(audio) / self.sample_rate,
            quality_score=quality_score,
            metadata={
                'fusion_strategy': fusion_strategy,
                'models_used': {
                    'ecapa': ecapa_emb is not None,
                    'resnet': resnet_emb is not None
                },
                'embedding_dim': len(embedding)
            }
        )

        return features

    def _assess_audio_quality(self, audio: np.ndarray) -> float:
        """Assess audio quality (0-1 score)"""
        quality_factors = []

        # 1. Signal-to-noise ratio
        snr = self._estimate_snr(audio)
        quality_factors.append(min(snr / 30, 1.0))  # Normalize to 0-1

        # 2. Duration check
        duration = len(audio) / self.sample_rate
        min_duration = self.config['audio']['duration']['min_seconds']
        max_duration = self.config['audio']['duration']['max_seconds']

        if min_duration <= duration <= max_duration:
            quality_factors.append(1.0)
        else:
            quality_factors.append(0.5)

        # 3. Clipping detection
        clipping_ratio = np.sum(np.abs(audio) > 0.99) / len(audio)
        quality_factors.append(1.0 - min(clipping_ratio * 100, 1.0))

        # 4. Energy distribution
        energy = np.sum(audio ** 2) / len(audio)
        quality_factors.append(min(energy * 10, 1.0))

        # Average quality score
        return np.mean(quality_factors)

    def _estimate_snr(self, audio: np.ndarray) -> float:
        """Estimate signal-to-noise ratio"""
        # Simple SNR estimation using silent vs voiced segments
        frame_length = int(0.025 * self.sample_rate)
        hop_length = int(0.010 * self.sample_rate)

        energy = librosa.feature.rms(
            y=audio,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]

        # Assume bottom 20% is noise
        sorted_energy = np.sort(energy)
        noise_threshold_idx = int(len(sorted_energy) * 0.2)
        noise_level = np.mean(sorted_energy[:noise_threshold_idx])

        # Top 20% is signal
        signal_threshold_idx = int(len(sorted_energy) * 0.8)
        signal_level = np.mean(sorted_energy[signal_threshold_idx:])

        if noise_level > 0:
            snr_db = 20 * np.log10(signal_level / noise_level)
        else:
            snr_db = 40  # High SNR if no noise detected

        return max(0, snr_db)

    def _extract_fallback_features(self, audio: np.ndarray) -> np.ndarray:
        """Extract simple acoustic features as fallback"""
        features = []

        # MFCCs
        mfccs = librosa.feature.mfcc(
            y=audio,
            sr=self.sample_rate,
            n_mfcc=13
        )
        features.extend(mfccs.mean(axis=1))
        features.extend(mfccs.std(axis=1))

        # Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(
            y=audio,
            sr=self.sample_rate
        )
        features.append(spectral_centroid.mean())
        features.append(spectral_centroid.std())

        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio)
        features.append(zcr.mean())
        features.append(zcr.std())

        # Pad to standard size
        target_size = 192  # Match ECAPA-TDNN size
        features = np.array(features)

        if len(features) < target_size:
            features = np.pad(features, (0, target_size - len(features)))
        else:
            features = features[:target_size]

        return features

    def compare_embeddings(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
        metric: str = 'cosine'
    ) -> float:
        """
        Compare two embeddings

        Args:
            embedding1: First embedding
            embedding2: Second embedding
            metric: Similarity metric ('cosine', 'euclidean')

        Returns:
            Similarity score (0-1 for cosine, distance for euclidean)
        """
        if metric == 'cosine':
            # Cosine similarity
            similarity = np.dot(embedding1, embedding2)
            # Embeddings should be normalized, so this gives cosine similarity
            return float(similarity)

        elif metric == 'euclidean':
            # Euclidean distance
            distance = np.linalg.norm(embedding1 - embedding2)
            return float(distance)

        else:
            raise ValueError(f"Unknown metric: {metric}")

# Singleton instance
_feature_extractor = None

def get_feature_extractor(config_path: Optional[str] = None) -> VoiceFeatureExtractor:
    """Get or create feature extractor instance"""
    global _feature_extractor

    if _feature_extractor is None:
        _feature_extractor = VoiceFeatureExtractor(config_path or "config/voice_auth_config.yaml")

    return _feature_extractor