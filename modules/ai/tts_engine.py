#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音合成引擎模块

实现文本到语音的转换功能，修复 runAndWait 阻塞问题
"""

import time
import threading
import queue
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import signal
import sys

try:
    import pyttsx3

    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️ pyttsx3未安装，语音合成功能将被禁用")


class TTSPriority(Enum):
    """语音播报优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TTSRequest:
    """语音合成请求"""
    text: str
    priority: TTSPriority
    voice_id: Optional[str] = None
    rate: Optional[int] = None
    volume: Optional[float] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def __lt__(self, other):
        """支持优先级队列比较"""
        return self.priority.value < other.priority.value


class TTSEngine:
    """语音合成引擎"""

    def __init__(self):
        self.engine = None
        self.is_initialized = False
        self.is_speaking = False
        self.request_queue = queue.PriorityQueue()
        self.worker_thread = None
        self.running = False
        self._lock = threading.Lock()
        self._speech_finished = threading.Event()

        # 默认配置
        self.default_config = {
            "rate": 180,  # 语速 (words per minute)
            "volume": 0.8,  # 音量 (0.0-1.0)
            "voice_id": None  # 语音ID (None为默认)
        }

        self._initialize_engine()

    def _on_start(self, name):
        """语音开始回调"""
        print(f"🎵 语音开始播放: {name}")

    def _on_word(self, name, location, length):
        """语音播放单词回调"""
        pass  # 不输出，避免日志过多

    def _on_end(self, name, completed):
        """语音结束回调"""
        print(f"🏁 语音播放结束: {name}, completed={completed}")
        self._speech_finished.set()

    def _initialize_engine(self):
        """初始化TTS引擎"""
        if not TTS_AVAILABLE:
            print("❌ TTS引擎初始化失败: pyttsx3未安装")
            return

        try:
            self.engine = pyttsx3.init()

            # 设置回调函数
            self.engine.connect('started-utterance', self._on_start)
            self.engine.connect('started-word', self._on_word)
            self.engine.connect('finished-utterance', self._on_end)

            # 设置默认参数
            self.engine.setProperty('rate', self.default_config['rate'])
            self.engine.setProperty('volume', self.default_config['volume'])

            # 获取可用语音
            voices = self.engine.getProperty('voices')
            if voices:
                # 优先选择中文语音
                chinese_voice = None
                for voice in voices:
                    if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                        chinese_voice = voice
                        break

                if chinese_voice:
                    self.engine.setProperty('voice', chinese_voice.id)
                    print(f"✅ 选择中文语音: {chinese_voice.name}")
                else:
                    print(f"✅ 使用默认语音: {voices[0].name}")

            self.is_initialized = True
            print("✅ TTS引擎初始化成功")

            # 启动工作线程
            self._start_worker_thread()

        except Exception as e:
            print(f"❌ TTS引擎初始化失败: {e}")
            self.is_initialized = False

    def _start_worker_thread(self):
        """启动工作线程"""
        if self.worker_thread and self.worker_thread.is_alive():
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print("🔊 TTS工作线程已启动")

    def _worker_loop(self):
        """工作线程主循环"""
        while self.running:
            try:
                # 获取请求 (优先级队列会自动排序)
                priority_value, request = self.request_queue.get(timeout=1.0)

                if request is not None:
                    self._process_tts_request(request)

                self.request_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ TTS工作线程错误: {e}")
                # 确保在错误时重置状态
                with self._lock:
                    self.is_speaking = False

    def _process_tts_request(self, request: TTSRequest):
        """处理TTS请求"""
        try:
            # 设置播报状态
            with self._lock:
                self.is_speaking = True

            if not self.is_initialized or not self.engine:
                print(f"📢 TTS模拟播报: {request.text}")
                # 模拟播报时间
                time.sleep(len(request.text) * 0.1)  # 根据文本长度模拟播报时间
                return

            # 设置语音参数
            if request.rate:
                self.engine.setProperty('rate', request.rate)

            if request.volume:
                self.engine.setProperty('volume', request.volume)

            if request.voice_id:
                self.engine.setProperty('voice', request.voice_id)

            # 重置事件
            self._speech_finished.clear()

            # 播报语音
            print(f"🔊 语音播报: {request.text}")

            self.engine.say(request.text)

            # 使用事件驱动方式等待语音完成，而不是 runAndWait()
            def run_engine():
                try:
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"⚠️ runAndWait异常: {e}")
                    self._speech_finished.set()

            # 在单独线程中运行引擎
            engine_thread = threading.Thread(target=run_engine, daemon=True)
            engine_thread.start()

            # 等待语音完成，最多等待10秒
            timeout = max(10.0, len(request.text) * 0.5)  # 根据文本长度动态调整超时
            if self._speech_finished.wait(timeout):
                print("✅ 语音播报正常完成")
            else:
                print("⚠️ 语音播报超时，强制结束")
                try:
                    self.engine.stop()
                except:
                    pass

            # 等待引擎线程结束
            engine_thread.join(timeout=1.0)

            # 恢复默认设置
            try:
                self.engine.setProperty('rate', self.default_config['rate'])
                self.engine.setProperty('volume', self.default_config['volume'])
            except:
                pass

        except Exception as e:
            print(f"❌ 语音播报错误: {e}")
            print(f"📢 文本播报: {request.text}")
        finally:
            # 确保状态总是被重置
            with self._lock:
                self.is_speaking = False

    def speak(self, text: str, priority: TTSPriority = TTSPriority.NORMAL,
              rate: Optional[int] = None, volume: Optional[float] = None) -> bool:
        """添加语音播报请求"""

        if not text or not text.strip():
            return False

        # 创建请求
        request = TTSRequest(
            text=text.strip(),
            priority=priority,
            rate=rate,
            volume=volume
        )

        # 添加到队列 (优先级越高，数值越小)
        priority_value = 5 - priority.value  # 转换为队列优先级

        try:
            self.request_queue.put((priority_value, request), timeout=1.0)
            return True
        except queue.Full:
            print(f"⚠️ TTS队列已满，丢弃请求: {text[:50]}...")
            return False

    def speak_urgent(self, text: str) -> bool:
        """紧急语音播报"""
        return self.speak(text, TTSPriority.URGENT, volume=1.0)

    def speak_normal(self, text: str) -> bool:
        """普通语音播报"""
        return self.speak(text, TTSPriority.NORMAL)

    def speak_low(self, text: str) -> bool:
        """低优先级语音播报"""
        return self.speak(text, TTSPriority.LOW, volume=0.6)

    def interrupt_current(self):
        """中断当前播报"""
        if self.is_initialized and self.engine:
            with self._lock:
                if self.is_speaking:
                    try:
                        self.engine.stop()
                        self._speech_finished.set()
                        self.is_speaking = False
                        print("🔇 语音播报已中断")
                    except Exception as e:
                        print(f"❌ 中断语音播报失败: {e}")

    def clear_queue(self):
        """清空播报队列"""
        while not self.request_queue.empty():
            try:
                self.request_queue.get_nowait()
                self.request_queue.task_done()
            except queue.Empty:
                break
        print("🗑️ TTS队列已清空")

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.request_queue.qsize()

    def is_busy(self) -> bool:
        """检查是否正在播报"""
        if not self.is_initialized:
            return False  # 如果未初始化，认为不忙

        with self._lock:
            return self.is_speaking or not self.request_queue.empty()

    def get_available_voices(self) -> list:
        """获取可用语音列表"""
        if not self.is_initialized or not self.engine:
            return []

        try:
            voices = self.engine.getProperty('voices')
            return [{"id": voice.id, "name": voice.name} for voice in voices]
        except Exception as e:
            print(f"❌ 获取语音列表失败: {e}")
            return []

    def set_voice(self, voice_id: str) -> bool:
        """设置语音"""
        if not self.is_initialized or not self.engine:
            return False

        try:
            self.engine.setProperty('voice', voice_id)
            self.default_config['voice_id'] = voice_id
            print(f"✅ 语音已切换: {voice_id}")
            return True
        except Exception as e:
            print(f"❌ 设置语音失败: {e}")
            return False

    def set_rate(self, rate: int) -> bool:
        """设置语速"""
        if rate < 50 or rate > 400:
            print(f"⚠️ 语速超出范围 (50-400): {rate}")
            return False

        self.default_config['rate'] = rate
        if self.is_initialized and self.engine:
            try:
                self.engine.setProperty('rate', rate)
                print(f"✅ 语速已设置: {rate} WPM")
                return True
            except Exception as e:
                print(f"❌ 设置语速失败: {e}")
                return False
        return True

    def set_volume(self, volume: float) -> bool:
        """设置音量"""
        if volume < 0.0 or volume > 1.0:
            print(f"⚠️ 音量超出范围 (0.0-1.0): {volume}")
            return False

        self.default_config['volume'] = volume
        if self.is_initialized and self.engine:
            try:
                self.engine.setProperty('volume', volume)
                print(f"✅ 音量已设置: {volume:.1f}")
                return True
            except Exception as e:
                print(f"❌ 设置音量失败: {e}")
                return False
        return True

    def get_status(self) -> Dict[str, Any]:
        """获取TTS状态"""
        with self._lock:
            return {
                "initialized": self.is_initialized,
                "speaking": self.is_speaking,
                "queue_size": self.get_queue_size(),
                "config": self.default_config.copy(),
                "available": TTS_AVAILABLE
            }

    def shutdown(self):
        """关闭TTS引擎"""
        print("🔇 正在关闭TTS引擎...")

        self.running = False
        self.clear_queue()

        # 中断当前播报
        if self.is_speaking:
            self.interrupt_current()

        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)

        if self.is_initialized and self.engine:
            try:
                self.engine.stop()
            except:
                pass

        print("✅ TTS引擎已关闭")


# 全局TTS引擎实例
tts_engine = TTSEngine()