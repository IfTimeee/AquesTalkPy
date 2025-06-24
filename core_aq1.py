import ctypes
import os
import platform
import struct
import wave  # 用于处理 WAV 文件
import audioop  # 用于执行音频操作
import io  # 用于在内存中处理字节流


class AquesTalkSynthesizer:
    """
    一个封装了 AquesTalk 和 AqKanji2Koe 功能的语音合成器类。
    通过 'with' 语句使用可以确保资源被正确释放。
    """
    STANDARD_SAMPLE_RATE = 8000  # AquesTalk 的标准采样率是 8kHz

    def __init__(self, aqtk_path: str, aqk2k_path: str, dic_path: str):
        """
        初始化合成器。

        :param aqtk_path: AquesTalk.dll 的路径。
        :param aqk2k_path: AqKanji2Koe.dll 的路径。
        :param dic_path: aq_dic 字典目录的路径。
        """
        self.h_aqk2k = None

        try:
            self.aqk2k = ctypes.WinDLL(aqk2k_path)
            self.aqtk = ctypes.CDLL(aqtk_path)
        except OSError as e:
            raise OSError(f"无法加载 DLL。请检查路径是否正确以及 Python 架构是否匹配。错误: {e}")

        self._define_prototypes()

        err_code = ctypes.c_int()
        abs_dic_path = os.path.abspath(dic_path)

        self.h_aqk2k = self.aqk2k.AqKanji2Koe_Create(abs_dic_path.encode('mbcs'), ctypes.byref(err_code))

        if not self.h_aqk2k:
            raise RuntimeError(f"AqKanji2Koe_Create 初始化失败，错误码: {err_code.value}。请检查字典路径和权限。")

    def _define_prototypes(self):
        """一个内部辅助方法，用于集中设置所有 ctypes 函数原型。"""
        # AqKanji2Koe_Create
        self.aqk2k.AqKanji2Koe_Create.restype = ctypes.c_void_p
        self.aqk2k.AqKanji2Koe_Create.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]

        # AqKanji2Koe_Convert_utf8
        self.aqk2k.AqKanji2Koe_Convert_utf8.restype = ctypes.c_int
        self.aqk2k.AqKanji2Koe_Convert_utf8.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]

        # AqKanji2Koe_Release
        self.aqk2k.AqKanji2Koe_Release.restype = None
        self.aqk2k.AqKanji2Koe_Release.argtypes = [ctypes.c_void_p]

        # AquesTalk_Synthe_Utf8
        self.aqtk.AquesTalk_Synthe_Utf8.restype = ctypes.POINTER(ctypes.c_ubyte)
        self.aqtk.AquesTalk_Synthe_Utf8.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]

        # AquesTalk_FreeWave
        self.aqtk.AquesTalk_FreeWave.restype = None
        self.aqtk.AquesTalk_FreeWave.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]

    def synthesize(self, text: str, speed: int = 100, pitch_factor: float = 1.0, volume: int = 100) -> bytes:
        """
        将日文文本合成为 WAV 音频数据，并可调整音程和音量。

        :param text: 要合成的日文文本 (UTF-8)。
        :param speed: 语速 (50-300)。
        :param pitch_factor: 音程系数。1.0为标准音程，大于1.0音程变高，小于1.0音程变低。
        :param volume: 音量百分比 (0-300)。100为标准音量。
        :return: WAV 格式的音频数据 (bytes)。
        """
        koe_string = self._convert_to_koe(text)
        wav_data = self._synthesize_from_koe(koe_string, speed)

        # --- 音量调整的核心逻辑 (使用 audioop) ---
        if volume != 100:
            # 将 0-300 的音量值转换为 0.0-3.0 的增益因子
            gain_factor = volume / 100.0

            try:
                # 使用 wave 模块从内存中解析 WAV 数据
                with io.BytesIO(wav_data) as wav_buffer:
                    with wave.open(wav_buffer, 'rb') as wf:
                        params = wf.getparams()
                        sampwidth = wf.getsampwidth()  # 获取样本宽度 (应为 2 for 16-bit)
                        frames = wf.readframes(wf.getnframes())

                # 使用 audioop.mul 应用音量增益，它会自动处理削波
                processed_frames = audioop.mul(frames, sampwidth, gain_factor)

                # 将修改后的帧数据与原始头部信息重新组合成新的 WAV 数据
                with io.BytesIO() as new_wav_buffer:
                    with wave.open(new_wav_buffer, 'wb') as wf_out:
                        wf_out.setparams(params)
                        wf_out.writeframes(processed_frames)
                    wav_data = new_wav_buffer.getvalue()  # 更新 wav_data 以便后续处理

            except (wave.Error, audioop.error) as e:
                print(f"音量调整失败: {e}")
                # 在音量调整失败时，返回未经修改的原始数据
                pass

        # --- 音程调整的核心逻辑 (在音量调整之后) ---
        if pitch_factor != 1.0:
            mutable_wav = bytearray(wav_data)
            new_sample_rate = int(self.STANDARD_SAMPLE_RATE * pitch_factor)
            packed_rate = struct.pack('<I', new_sample_rate)
            mutable_wav[24:28] = packed_rate
            new_byte_rate = int(new_sample_rate * 1 * 2)
            packed_byte_rate = struct.pack('<I', new_byte_rate)
            mutable_wav[28:32] = packed_byte_rate
            return bytes(mutable_wav)

        return wav_data

    def _convert_to_koe(self, text: str) -> str:
        """内部方法：将文本转换为语音记号列 (Koe)。"""
        input_bytes = text.encode('utf-8')
        buffer_size = len(input_bytes) * 2 + 256
        koe_buffer = ctypes.create_string_buffer(buffer_size)

        ret = self.aqk2k.AqKanji2Koe_Convert_utf8(self.h_aqk2k, input_bytes, koe_buffer, buffer_size)
        if ret != 0:
            raise RuntimeError(f"AqKanji2Koe_Convert_utf8 转换失败，错误码: {ret}")

        return koe_buffer.value.decode('utf-8')

    def _synthesize_from_koe(self, koe_string: str, speed: int) -> bytes:
        """内部方法：从语音记号列 (Koe) 合成音频。"""
        koe_bytes = koe_string.encode('utf-8')
        wav_size = ctypes.c_int()

        wav_ptr = self.aqtk.AquesTalk_Synthe_Utf8(koe_bytes, speed, ctypes.byref(wav_size))

        if not wav_ptr:
            raise RuntimeError(f"AquesTalk_Synthe_Utf8 合成失败，错误码: {wav_size.value}")

        wav_data = bytes(ctypes.string_at(wav_ptr, wav_size.value))
        self.aqtk.AquesTalk_FreeWave(wav_ptr)

        return wav_data

    def close(self):
        """明确地释放 AqKanji2Koe 句柄。"""
        if self.h_aqk2k:
            self.aqk2k.AqKanji2Koe_Release(self.h_aqk2k)
            self.h_aqk2k = None
            print("AqKanji2Koe 句柄已成功释放。")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# --- 使用示例 ---
if __name__ == '__main__':
    if platform.architecture() != '32bit':
        print("警告：此脚本假定使用 32 位 DLL，但当前 Python 环境不是 32 位。")

    AQK2K_DLL_PATH = '.\\AqKanji2Koe.dll'
    AQTK_DLL_PATH = '.\\aqtk1\\f1\\AquesTalk.dll'
    DIC_DIR_PATH = '.\\aq_dic\\'

    try:
        with AquesTalkSynthesizer(aqtk_path=AQTK_DLL_PATH, aqk2k_path=AQK2K_DLL_PATH,
                                  dic_path=DIC_DIR_PATH) as synthesizer:
            print("合成器初始化成功。")

            input_text = "音量と音程を調整するテストです。"

            # 1. 标准音量 (100%)
            print("\n正在合成标准音量...")
            wav_normal = synthesizer.synthesize(input_text, speed=100, volume=100)
            with open('output_volume_normal.wav', 'wb') as f:
                f.write(wav_normal)
            print("已保存: output_volume_normal.wav")

            # 2. 较大音量 (150%)
            print("\n正在合成较大音量...")
            wav_loud = synthesizer.synthesize(input_text, speed=100, volume=150)
            with open('output_volume_loud.wav', 'wb') as f:
                f.write(wav_loud)
            print("已保存: output_volume_loud.wav")

            # 3. 较小音量 (50%)
            print("\n正在合成较小音量...")
            wav_quiet = synthesizer.synthesize(input_text, speed=100, volume=50)
            with open('output_volume_quiet.wav', 'wb') as f:
                f.write(wav_quiet)
            print("已保存: output_volume_quiet.wav")

            # 4. 组合效果：高音程 + 大音量
            print("\n正在合成组合效果 (高音程+大音量)...")
            wav_combo = synthesizer.synthesize(input_text, speed=100, pitch_factor=1.2, volume=130)
            with open('output_combo.wav', 'wb') as f:
                f.write(wav_combo)
            print("已保存: output_combo.wav")

    except (RuntimeError, OSError) as e:
        print(f"发生错误: {e}")
