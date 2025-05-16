# File: modules/audio/recorder.py
"""
麦克风 + WebRTC‑VAD 录音器，检测到一句话后回调／yield 完整 PCM bytes。
"""
import collections
import sounddevice as sd
import webrtcvad
import wave
import io
import time


class Recorder:
    def __init__(
        self,
        rate: int = 16000,
        frame_ms: int = 30,
        silence_limit: float = 0.8,
        channels: int = 1,
        aggressiveness: int = 2,
    ):
        self.rate = rate
        self.frame_bytes = int(rate * frame_ms / 1000) * 2 * channels  # int16=2字节
        self.silence_limit = silence_limit
        self.channels = channels
        self.vad = webrtcvad.Vad(aggressiveness)

    @staticmethod
    def _frames_to_wav(rate, channels, frames):
        """将 int16 PCM bytes 列表拼成单声道 WAV bytes"""
        with io.BytesIO() as buf:
            wf = wave.open(buf, "wb")
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            wf.writeframes(b"".join(frames))
            wf.close()
            return buf.getvalue()

    def record_stream(self):
        """生成器：检测到一句话时 yield WAV bytes"""
        buffer = collections.deque(
            maxlen=int(self.silence_limit * 1000 / 30)
        )  # 30 ms 块数
        voiced = []
        is_recording = False

        with sd.RawInputStream(
            samplerate=self.rate,
            blocksize=int(self.frame_bytes / 2),
            dtype="int16",
            channels=self.channels,
        ) as stream:
            while True:
                frame, _ = stream.read(int(self.frame_bytes / 2))
                frame_bytes = bytes(frame)
                is_speech = self.vad.is_speech(frame_bytes, self.rate)

                if is_speech:
                    if not is_recording:
                        voiced.clear()
                        is_recording = True
                    voiced.append(frame_bytes)
                    buffer.clear()  # 语音块内不计静音
                elif is_recording:
                    buffer.append(frame_bytes)
                    if len(buffer) == buffer.maxlen:
                        # 达到静音阈值，结束录音
                        wav_bytes = self._frames_to_wav(
                            self.rate, self.channels, voiced
                        )
                        yield {"wav": wav_bytes, "ts": time.time()}
                        is_recording = False
                # 若一直静音，则保持监听
