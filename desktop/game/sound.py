"""
Audio system and procedural sound generator for Fruit Ninja.
Synthesizes WAV sound effects for blade swooshes, fruit slicing, juice splatters,
bomb explosions, and combo fanfares. Handles missing audio hardware gracefully.
"""

import math
import os
import random
import struct
import wave
from typing import Dict, Optional
import pygame

from config import ASSETS_DIR


class SoundGenerator:
    """
    Synthesizes WAV sound effects programmatically so the game is completely
    self-contained with zero missing asset errors.
    """

    SAMPLE_RATE = 44100

    @classmethod
    def generate_all_sounds(cls, sounds_dir: str):
        """Generates all standard game audio files if not already present."""
        os.makedirs(sounds_dir, exist_ok=True)

        cls._generate_swoosh(os.path.join(sounds_dir, "swoosh.wav"))
        cls._generate_slice(os.path.join(sounds_dir, "slice.wav"))
        cls._generate_splat(os.path.join(sounds_dir, "splat.wav"))
        cls._generate_combo(os.path.join(sounds_dir, "combo.wav"))
        cls._generate_explosion(os.path.join(sounds_dir, "explosion.wav"))
        cls._generate_game_over(os.path.join(sounds_dir, "game_over.wav"))

    @classmethod
    def _write_wav(cls, path: str, samples: list):
        """Writes 16-bit mono PCM WAV file."""
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(cls.SAMPLE_RATE)
            packed = bytearray()
            for s in samples:
                val = int(max(-32767, min(32767, s * 32767.0)))
                packed.extend(struct.pack("<h", val))
            wf.writeframes(packed)

    @classmethod
    def _generate_swoosh(cls, path: str):
        """Blade rushing through air (bandpass filtered white noise with pitch ramp)."""
        duration = 0.22
        n_samples = int(cls.SAMPLE_RATE * duration)
        samples = []
        for i in range(n_samples):
            t = i / cls.SAMPLE_RATE
            progress = t / duration
            # Amplitude envelope: quick attack, smooth decay
            env = math.sin(progress * math.pi) ** 1.5
            # Frequency modulation from 450Hz up to 900Hz and down
            freq = 400 + 600 * math.sin(progress * math.pi)
            noise = (random.random() * 2.0 - 1.0) * 0.45
            tone = math.sin(2.0 * math.pi * freq * t) * 0.55
            samples.append((noise + tone) * env * 0.7)
        cls._write_wav(path, samples)

    @classmethod
    def _generate_slice(cls, path: str):
        """Crisp metallic blade cutting through fruit (sharp high frequency transient)."""
        duration = 0.18
        n_samples = int(cls.SAMPLE_RATE * duration)
        samples = []
        for i in range(n_samples):
            t = i / cls.SAMPLE_RATE
            progress = t / duration
            env = math.exp(-18.0 * progress)
            # High-pitch metal slice
            tone1 = math.sin(2.0 * math.pi * 1800.0 * t) * 0.5
            tone2 = math.sin(2.0 * math.pi * 2700.0 * t) * 0.3
            noise = (random.random() * 2.0 - 1.0) * 0.2
            samples.append((tone1 + tone2 + noise) * env * 0.85)
        cls._write_wav(path, samples)

    @classmethod
    def _generate_splat(cls, path: str):
        """Juicy fruit impact squish."""
        duration = 0.25
        n_samples = int(cls.SAMPLE_RATE * duration)
        samples = []
        for i in range(n_samples):
            t = i / cls.SAMPLE_RATE
            progress = t / duration
            env = math.exp(-12.0 * progress)
            freq = 320.0 * math.exp(-8.0 * progress) + 80.0
            squish = math.sin(2.0 * math.pi * freq * t) * 0.6
            noise = (random.random() * 2.0 - 1.0) * 0.4
            samples.append((squish + noise) * env * 0.75)
        cls._write_wav(path, samples)

    @classmethod
    def _generate_combo(cls, path: str):
        """Musical arpeggio fanfare for combo rewards."""
        duration = 0.45
        n_samples = int(cls.SAMPLE_RATE * duration)
        samples = []
        # Chords: C5, E5, G5, C6
        notes = [523.25, 659.25, 783.99, 1046.50]
        step_len = duration / len(notes)
        for i in range(n_samples):
            t = i / cls.SAMPLE_RATE
            idx = min(len(notes) - 1, int(t / step_len))
            freq = notes[idx]
            sub_t = t - idx * step_len
            sub_progress = sub_t / step_len
            env = math.exp(-4.0 * sub_progress)
            tone = math.sin(2.0 * math.pi * freq * t) * 0.7
            harmonic = math.sin(2.0 * math.pi * (freq * 2) * t) * 0.25
            samples.append((tone + harmonic) * env * 0.65)
        cls._write_wav(path, samples)

    @classmethod
    def _generate_explosion(cls, path: str):
        """Deep explosive bomb blast."""
        duration = 0.6
        n_samples = int(cls.SAMPLE_RATE * duration)
        samples = []
        for i in range(n_samples):
            t = i / cls.SAMPLE_RATE
            progress = t / duration
            env = math.exp(-5.0 * progress)
            noise = (random.random() * 2.0 - 1.0)
            low_rumble = math.sin(2.0 * math.pi * 65.0 * t) * 0.6
            samples.append((noise * 0.6 + low_rumble * 0.4) * env * 0.95)
        cls._write_wav(path, samples)

    @classmethod
    def _generate_game_over(cls, path: str):
        """Dramatic descending gong for round end."""
        duration = 0.8
        n_samples = int(cls.SAMPLE_RATE * duration)
        samples = []
        for i in range(n_samples):
            t = i / cls.SAMPLE_RATE
            progress = t / duration
            env = math.exp(-3.5 * progress)
            freq = 240.0 * (1.0 - progress * 0.5)
            tone = math.sin(2.0 * math.pi * freq * t) * 0.7
            samples.append(tone * env * 0.7)
        cls._write_wav(path, samples)


class SoundManager:
    """
    Manages sound playback with volume controls and fault tolerance.
    """

    def __init__(self, sounds_dir: Optional[str] = None, enabled: bool = True):
        self.enabled = enabled
        self.sounds_dir = sounds_dir or os.path.join(ASSETS_DIR, "sounds")
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.mixer_initialized = False

        self._init_audio()

    def _init_audio(self):
        """Initializes Pygame mixer and synthesizes/loads sound files."""
        if not self.enabled:
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.mixer_initialized = True
        except Exception as e:
            print(f"[SoundManager] Audio initialization notice: {e}. Running in silent mode.")
            self.mixer_initialized = False
            return

        # Ensure sound assets exist
        SoundGenerator.generate_all_sounds(self.sounds_dir)

        # Load sound assets
        sound_files = {
            "swoosh": "swoosh.wav",
            "slice": "slice.wav",
            "splat": "splat.wav",
            "combo": "combo.wav",
            "explosion": "explosion.wav",
            "game_over": "game_over.wav",
        }

        for name, filename in sound_files.items():
            filepath = os.path.join(self.sounds_dir, filename)
            if os.path.exists(filepath):
                try:
                    snd = pygame.mixer.Sound(filepath)
                    snd.set_volume(0.65)
                    self.sounds[name] = snd
                except Exception as e:
                    print(f"[SoundManager] Warning loading {filepath}: {e}")

    def play(self, sound_name: str, volume: Optional[float] = None):
        """Plays a registered sound effect if audio is active."""
        if not self.mixer_initialized or sound_name not in self.sounds:
            return

        snd = self.sounds[sound_name]
        if volume is not None:
            snd.set_volume(max(0.0, min(1.0, volume)))
        snd.play()
