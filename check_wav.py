from pydub import AudioSegment
import numpy as np

# 假设你的 MP3 文件名为 "your_mp3_file.mp3"
audio = AudioSegment.from_mp3("role_cards/brian/tmp_audio/text.mp3")

duration_ms = len(audio)       # 获取时长，单位是毫秒

duration_seconds = duration_ms / 1000.0  # 将毫秒转换为秒

sample_rate = audio.frame_rate  # 获取采样率
num_frames = audio.frame_count(ms=duration_ms)
sample_width = audio.sample_width
num_channles = audio.channels
raw_audio_data = audio.raw_data



print(f"采样率 (sampleRate): {sample_rate}")
print(num_frames)
print(sample_width)
print(num_channles)
print(f"时长 (毫秒): {duration_ms}")
print(f"时长 (秒): {duration_seconds}")
print(f"近似的帧数 (numFrames，即总采样点数): {num_frames}")
print(np.frombuffer(raw_audio_data, dtype=np.int16).dtype)