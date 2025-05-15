import sounddevice as sd
import webrtcvad
import collections
import wave
import tempfile

from NLU import process_audio
from action_handler import handle_action

RATE = 16000
FRAME_DURATION = 30
FRAME_SIZE = int(RATE * FRAME_DURATION / 1000)
CHANNELS = 1

vad = webrtcvad.Vad(2)

def listen_loop(silence_limit=0.8):
    buffer = collections.deque(maxlen=int(silence_limit * 1000 / FRAME_DURATION))
    voiced_frames = []
    is_recording = False

    with sd.RawInputStream(samplerate=RATE,
                           blocksize=FRAME_SIZE,
                           dtype='int16',
                           channels=CHANNELS) as stream:
        print("→ 已进入同步监听模式，等待指令…")
        while True:
            frame, _ = stream.read(FRAME_SIZE)
            frame_bytes = bytes(frame)
            is_speech = vad.is_speech(frame_bytes, RATE)

            if is_speech:
                if not is_recording:
                    print("[录音开始]")
                    is_recording = True
                voiced_frames.append(frame_bytes)
                buffer.append(True)
            else:
                buffer.append(False)
                # 只有当已经开始录制，且检测到连续静音时，才触发处理
                if is_recording and not any(buffer):
                    print("[录音结束，开始同步处理]")
                    # 写临时 wav
                    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                    with wave.open(tmp.name, 'wb') as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(2)
                        wf.setframerate(RATE)
                        wf.writeframes(b''.join(voiced_frames))

                    # 同步调用 ASR+NLU
                    result = process_audio(tmp.name)
                    text = result["text"]
                    intent = result["intent"]
                    slots = result.get("slots", {})
                    print(f"识别文本：{text}")
                    print(f"意图：{intent}    槽位：{slots}")
                    if intent != "Unknown":
                        handle_action(intent)
                    tmp.close()

                    # 重置状态，回到监听
                    voiced_frames.clear()
                    buffer.clear()
                    is_recording = False
                    print("→ 回到监听状态…")

def main():
    try:
        listen_loop(silence_limit=0.8)
    except KeyboardInterrupt:
        print("退出监听。")

if __name__ == "__main__":
    main()
