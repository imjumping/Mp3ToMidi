import os
import numpy as np
import librosa
import pretty_midi
from pydub import AudioSegment
import tkinter as tk
from tkinter import filedialog

# 忽略 pkg_resources 警告（可选）
import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

def mp3_to_midi(mp3_path, midi_output_path, sr=22050):
    print("加载 MP3 文件...")
    try:
        audio = AudioSegment.from_mp3(mp3_path)
    except Exception as e:
        print(f"读取 MP3 失败: {e}")
        return False

    # 转为 mono，统一采样率
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(sr)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    samples = samples / max(1e-6, np.max(np.abs(samples)))  # 归一化，避免除零

    print("提取音高 (pitch)...")
    f0, voiced_flag, voiced_probs = librosa.pyin(
        samples,
        fmin=librosa.note_to_hz('C2'),
        fmax=librosa.note_to_hz('C7'),
        sr=sr,
        frame_length=2048,
        hop_length=512
    )

    times = librosa.times_like(f0, sr=sr, hop_length=512)

    print("转换为 MIDI 音符...")
    midi = pretty_midi.PrettyMIDI()
    piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
    piano = pretty_midi.Instrument(program=piano_program)

    min_note_dur = 0.1
    velocity = 100

    last_note = None
    note_start_time = None

    for i, (pitch, time) in enumerate(zip(f0, times)):
        if np.isnan(pitch):
            if last_note is not None:
                duration = time - note_start_time
                if duration >= min_note_dur:
                    note = pretty_midi.Note(
                        velocity=velocity,
                        pitch=int(round(librosa.hz_to_midi(last_note))),
                        start=note_start_time,
                        end=time
                    )
                    piano.notes.append(note)
                last_note = None
        else:
            if last_note is None:
                last_note = pitch
                note_start_time = time
            else:
                if abs(pitch - last_note) > 1.5:
                    duration = time - note_start_time
                    if duration >= min_note_dur:
                        note = pretty_midi.Note(
                            velocity=velocity,
                            pitch=int(round(librosa.hz_to_midi(last_note))),
                            start=note_start_time,
                            end=time
                        )
                        piano.notes.append(note)
                    last_note = pitch
                    note_start_time = time
                else:
                    last_note = (last_note + pitch) / 2

    if last_note is not None and note_start_time < times[-1]:
        duration = times[-1] - note_start_time
        if duration >= min_note_dur:
            note = pretty_midi.Note(
                velocity=velocity,
                pitch=int(round(librosa.hz_to_midi(last_note))),
                start=note_start_time,
                end=times[-1]
            )
            piano.notes.append(note)

    midi.instruments.append(piano)
    try:
        midi.write(midi_output_path)
        print(f"MIDI 已保存至: {midi_output_path}")
        return True
    except Exception as e:
        print(f"保存 MIDI 失败: {e}")
        return False


def main():
    # 初始化 tkinter
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 创建 output 文件夹
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    print("请选择一个 MP3 文件...")
    mp3_path = filedialog.askopenfilename(
        title="选择 MP3 文件",
        filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
    )

    if not mp3_path:
        print("❌ 未选择文件，程序退出。")
        return

    print(f"已选择文件: {mp3_path}")
    filename = os.path.splitext(os.path.basename(mp3_path))[0]
    midi_path = os.path.join(output_dir, f"{filename}_piano.mid")

    # 转换
    success = mp3_to_midi(mp3_path, midi_path)

    if success:
        print("🎉 转换完成！")
    else:
        print("❌ 转换失败，请检查文件或安装 ffmpeg。")

    # 可选：保持窗口几秒
    input("按回车键退出...")


if __name__ == "__main__":
    main()