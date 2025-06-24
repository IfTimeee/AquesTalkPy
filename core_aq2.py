import ctypes
import os
import platform
import struct
import wave
import audioop
import io


class AquesTalk2Synthesizer:
    """
    一个封装了 AquesTalk2 和 AqKanji2Koe 功能的语音合成器类。
    它处理了音色文件加载、双 DLL 调用以及参数调整的全部流程。
    通过 'with' 语句使用可以确保资源被正确释放。
    """
    STANDARD_SAMPLE_RATE = 8000  # AquesTalk2 的标准采样率是 8kHz

    def __init__(self, aqtk2_path: str, aqk2k_path: str, dic_path: str, phont_path: str):
        """
        初始化合成器。

        :param aqtk2_path: AquesTalk2.dll 的路径。
        :param aqk2k_path: AqKanji2Koe.dll 的路径。
        :param dic_path: aq_dic 字典目录的路径。
        :param phont_path: 要使用的音色文件 (.phont) 的路径。
        """
        self.h_aqk2k = None

        # --- 1. 加载音色文件 (.phont) ---
        try:
            with open(phont_path, "rb") as f:
                self.phont_data = f.read()
            # 创建一个 C 兼容的缓冲区，并获取其指针
            self.phont_buffer = ctypes.create_string_buffer(self.phont_data)
            self.p_phont = ctypes.cast(self.phont_buffer, ctypes.c_void_p)
        except FileNotFoundError:
            raise FileNotFoundError(f"音色文件未找到: {phont_path}")

        # --- 2. 加载 DLL (使用 CDLL, 因为新版使用 __cdecl 约定) ---
        try:
            self.aqk2k_dll = ctypes.CDLL(aqk2k_path)
            self.aqtk2_dll = ctypes.CDLL(aqtk2_path)
        except OSError as e:
            raise OSError(f"无法加载 DLL。请检查路径是否正确以及 Python 架构是否匹配。错误: {e}")

        # --- 3. 定义所有函数原型 ---
        self._define_prototypes()

        # --- 4. 初始化 AqKanji2Koe ---
        err_code = ctypes.c_int()
        abs_dic_path = os.path.abspath(dic_path)

        self.h_aqk2k = self.aq_kanji2koe_create(abs_dic_path.encode('mbcs'), ctypes.byref(err_code))

        if not self.h_aqk2k:
            raise RuntimeError(f"AqKanji2Koe_Create 初始化失败，错误码: {err_code.value}。请检查字典路径。")

    def _define_prototypes(self):
        """一个内部辅助方法，用于集中设置所有 ctypes 函数原型。"""
        # --- AqKanji2Koe.dll 函数 (使用未经修饰的函数名) ---
        self.aq_kanji2koe_create = self.aqk2k_dll.AqKanji2Koe_Create
        self.aq_kanji2koe_create.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
        self.aq_kanji2koe_create.restype = ctypes.c_void_p

        self.aq_kanji2koe_convert = self.aqk2k_dll.AqKanji2Koe_Convert_utf8
        self.aq_kanji2koe_convert.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.aq_kanji2koe_convert.restype = ctypes.c_int

        self.aq_kanji2koe_release = self.aqk2k_dll.AqKanji2Koe_Release
        self.aq_kanji2koe_release.argtypes = [ctypes.c_void_p]
        self.aq_kanji2koe_release.restype = None

        # --- AquesTalk2.dll 函数 ---
        self.aquestalk2_synthe = self.aqtk2_dll.AquesTalk2_Synthe_Utf8
        self.aquestalk2_synthe.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_void_p]
        self.aquestalk2_synthe.restype = ctypes.POINTER(ctypes.c_ubyte)

        self.aquestalk2_free_wave = self.aqtk2_dll.AquesTalk2_FreeWave
        self.aquestalk2_free_wave.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
        self.aquestalk2_free_wave.restype = None

    def synthesize(self, text: str, speed: int = 100, pitch: int = 100, volume: int = 100) -> bytes:
        """
        将日文文本合成为 WAV 音频数据，并可调整语速、音程和音量。

        :param text: 要合成的日文文本 (UTF-8)。
        :param speed: 语速 (50-300)。
        :param pitch: 音程百分比 (50-200)。100为标准音程。
        :param volume: 音量百分比 (0-300)。100为标准音量。
        :return: WAV 格式的音频数据 (bytes)。
        """
        koe_string = self._convert_to_koe(text)
        wav_data = self._synthesize_from_koe(koe_string, speed)

        # 应用音量调节
        if volume != 100:
            gain_factor = volume / 100.0
            wav_data = self._apply_volume(wav_data, gain_factor)

        # 应用音程调节
        if pitch != 100:
            pitch_factor = pitch / 100.0
            wav_data = self._apply_pitch(wav_data, pitch_factor)

        return wav_data

    def _convert_to_koe(self, text: str) -> str:
        input_bytes = text.encode('utf-8')
        buffer_size = len(input_bytes) * 2 + 256
        koe_buffer = ctypes.create_string_buffer(buffer_size)

        ret = self.aq_kanji2koe_convert(self.h_aqk2k, input_bytes, koe_buffer, buffer_size)
        if ret != 0:
            raise RuntimeError(f"AqKanji2Koe_Convert_utf8 转换失败，错误码: {ret}")
        return koe_buffer.value.decode('utf-8')

    def _synthesize_from_koe(self, koe_string: str, speed: int) -> bytes:
        koe_bytes = koe_string.encode('utf-8')
        wav_size = ctypes.c_int()

        wav_ptr = self.aquestalk2_synthe(koe_bytes, speed, ctypes.byref(wav_size), self.p_phont)

        if not wav_ptr:
            raise RuntimeError(f"AquesTalk2_Synthe_Utf8 合成失败，错误码: {wav_size.value}")

        wav_data = bytes(ctypes.string_at(wav_ptr, wav_size.value))
        self.aquestalk2_free_wave(wav_ptr)

        return wav_data

    def _apply_volume(self, wav_data: bytes, gain_factor: float) -> bytes:
        try:
            with io.BytesIO(wav_data) as wav_buffer:
                with wave.open(wav_buffer, 'rb') as wf:
                    params = wf.getparams()
                    sampwidth = wf.getsampwidth()
                    frames = wf.readframes(wf.getnframes())

            processed_frames = audioop.mul(frames, sampwidth, gain_factor)

            with io.BytesIO() as new_wav_buffer:
                with wave.open(new_wav_buffer, 'wb') as wf_out:
                    wf_out.setparams(params)
                    wf_out.writeframes(processed_frames)
                return new_wav_buffer.getvalue()
        except (wave.Error, audioop.error) as e:
            print(f"警告：音量调整失败，将返回原始音频。错误: {e}")
            return wav_data

    def _apply_pitch(self, wav_data: bytes, pitch_factor: float) -> bytes:
        mutable_wav = bytearray(wav_data)
        new_sample_rate = int(self.STANDARD_SAMPLE_RATE * pitch_factor)
        packed_rate = struct.pack('<I', new_sample_rate)
        mutable_wav[24:28] = packed_rate
        new_byte_rate = int(new_sample_rate * 1 * 2)  # 1 channel, 2 bytes/sample
        packed_byte_rate = struct.pack('<I', new_byte_rate)
        mutable_wav[28:32] = packed_byte_rate
        return bytes(mutable_wav)

    def close(self):
        """明确地释放 AqKanji2Koe 句柄。"""
        if self.h_aqk2k:
            self.aq_kanji2koe_release(self.h_aqk2k)
            self.h_aqk2k = None
            print("AqKanji2Koe 句柄已成功释放。")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# --- 使用示例 ---
if __name__ == '__main__':
    # 检查架构，AquesTalk2 通常提供 32位和 64位版本，请确保与 Python 匹配
    ARCH = platform.architecture()
    print(f"当前 Python 架构: {ARCH}")
    if ARCH not in ('32bit', '64bit'):
        print("警告：无法识别的 Python 架构。")

    # --- 请根据您的文件结构修改以下路径 ---
    AQK2K_DLL_PATH = '.\\AqKanji2Koe.dll'
    AQTK2_DLL_PATH = '.\\aqtk2\\AquesTalk2.dll'
    DIC_DIR_PATH = '.\\aq_dic'
    PHONT_PATH = '.\\aqtk2\\phont\\aq_yukkuri.phont'  # 使用油库里音色

    try:
        # 使用 with 语句创建实例，可以自动管理资源的释放
        with AquesTalk2Synthesizer(
                aqtk2_path=AQTK2_DLL_PATH,
                aqk2k_path=AQK2K_DLL_PATH,
                dic_path=DIC_DIR_PATH,
                phont_path=PHONT_PATH
        ) as synthesizer:
            print("AquesTalk2 合成器初始化成功。")

            input_text = "これは、使って合成した、全てのパラメータを調整するテスト音声です。"

            # 1. 标准参数
            print("\n1. 正在合成标准语音...")
            wav_normal = synthesizer.synthesize(input_text, speed=100, pitch=100, volume=100)
            with open('aq2_output_normal.wav', 'wb') as f:
                f.write(wav_normal)
            print("   已保存: aq2_output_normal.wav")

            # 2. 调整所有参数
            print("\n2. 正在合成自定义语音 (高速/高音程/大音量)...")
            wav_custom = synthesizer.synthesize(input_text, speed=150, pitch=120, volume=130)
            with open('aq2_output_custom.wav', 'wb') as f:
                f.write(wav_custom)
            print("   已保存: aq2_output_custom.wav")

            # 3. 调整所有参数 (反向)
            print("\n3. 正在合成自定义语音 (低速/低音程/小音量)...")
            wav_custom_low = synthesizer.synthesize(input_text, speed=80, pitch=85, volume=70)
            with open('aq2_output_custom_low.wav', 'wb') as f:
                f.write(wav_custom_low)
            print("   已保存: aq2_output_custom_low.wav")

    except (RuntimeError, OSError, FileNotFoundError) as e:
        print(f"\n发生错误: {e}")
        print(
            "请检查：\n1. DLL、字典和音色文件的路径是否正确。\n2. Python 解释器的位数是否与 DLL 文件匹配 (同为32位或同为64位)。")