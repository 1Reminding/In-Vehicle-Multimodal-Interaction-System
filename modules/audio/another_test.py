# import whisper
# import torch
# import sounddevice as sd
# import webrtcvad
# import collections
# import wave
# import tempfile
# import os
# from modules.ai.multimodal_collector import multimodal_collector

# # ASR
# # 全局加载模型（只加载一次）
# DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# MODEL = whisper.load_model("turbo").to(DEVICE)

# def transcribe_file(file_path: str) -> str:
#     """
#     识别指定音频文件，返回转写后的纯文本。
#     支持 wav/mp3/flac 等格式，自动使用 GPU（若可用）或 CPU。
#     """
#     # Whisper 的 transcribe 方法内部会调用 ffmpeg 转码
#     result = MODEL.transcribe(file_path, fp16=(DEVICE == "cuda"))
#     return result["text"].strip()


# # main
# RATE = 16000
# FRAME_DURATION = 30
# FRAME_SIZE = int(RATE * FRAME_DURATION / 1000)
# CHANNELS = 1

# vad = webrtcvad.Vad(3)

# def listen_loop(silence_limit=0.8):
#     buffer = collections.deque(maxlen=int(silence_limit * 1000 / FRAME_DURATION))
#     voiced_frames = []
#     is_recording = False

#     with sd.RawInputStream(samplerate=RATE,
#                            blocksize=FRAME_SIZE,
#                            dtype='int16',
#                            channels=CHANNELS) as stream:
#         print("→ 已进入同步监听模式，等待指令…")
#         while True:
#             frame, _ = stream.read(FRAME_SIZE)
#             frame_bytes = bytes(frame)
#             is_speech = vad.is_speech(frame_bytes, RATE)

#             if is_speech:
#                 if not is_recording:
#                     print("[录音开始]")
#                     is_recording = True
#                 voiced_frames.append(frame_bytes)
#                 buffer.append(True)
#             else:
#                 buffer.append(False)
#                 # 只有当已经开始录制，且检测到连续静音时，才触发处理
#                 if is_recording and not any(buffer):
#                     print("[录音结束，开始同步处理]")
#                     # 写临时 wav
#                     tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
#                     with wave.open(tmp.name, 'wb') as wf:
#                         wf.setnchannels(CHANNELS)
#                         wf.setsampwidth(2)
#                         wf.setframerate(RATE)
#                         wf.writeframes(b''.join(voiced_frames))

#                     tmp.close()

#                     try:
#                         # 对临时文件进行识别
#                         text = transcribe_file(tmp.name)                       

#                         if text:
#                             # 直接执行主线程原本做的事情
#                             print(f"🎤 语音识别: '{text}'")
                            
#                             # 更新多模态收集器
#                             speech_data = {
#                                 "text": text,
#                             }
#                             multimodal_collector.update_speech_data(speech_data)
                    
#                     finally:
#                         # 删除临时文件
#                         try:
#                             os.unlink(tmp.name)
#                         except:
#                             pass

#                     # 重置状态，回到监听
#                     voiced_frames.clear()
#                     buffer.clear()
#                     is_recording = False
#                     print("→ 回到监听状态…")

# # def main():
# #     try:
# #         listen_loop(silence_limit=0.8)
# #     except KeyboardInterrupt:
# #         print("退出监听。")

# # if __name__ == "__main__":
# #     main()
