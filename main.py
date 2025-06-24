import os
import sys
import platform
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core_aq1 import AquesTalkSynthesizer
from core_aq2 import AquesTalk2Synthesizer
from text_to_ja import ChineseToHiragana
import re


def safefilename(text, maxlen=20):
    # 只保留中英文、数字，其他替换为下划线，截断长度
    name = re.sub(r'[^\w\u4e00-\u9fff]', '_', text)
    return name[:maxlen]

class AquesSynthesizer:
    """
    整合 AquesTalk1 和 AquesTalk2 的统一语音合成器。
    参数:
        engine: 'aq1' 或 'aq2'
        voice:  对应音色（aq1为子目录名，aq2为phont文件名）
        dll_base: DLL 基础目录
        dic_dir: 字典目录
    """
    def __init__(self, engine: str, voice: str, dll_base: str, dic_dir: str):
        self.engine = engine.lower()
        self.synth = None

        if self.engine == 'aq1':
            aqtk_path = os.path.join(dll_base, voice, 'AquesTalk.dll')
            aqk2k_path = os.path.join(dll_base, '..', 'AqKanji2Koe.dll')
            self.synth = AquesTalkSynthesizer(
                aqtk_path=aqtk_path,
                aqk2k_path=aqk2k_path,
                dic_path=dic_dir
            )
        elif self.engine == 'aq2':
            aqtk2_path = os.path.join(dll_base, 'AquesTalk2.dll')
            aqk2k_path = os.path.join(dll_base, '..', 'AqKanji2Koe.dll')
            phont_path = os.path.join(dll_base, 'phont', voice)
            self.synth = AquesTalk2Synthesizer(
                aqtk2_path=aqtk2_path,
                aqk2k_path=aqk2k_path,
                dic_path=dic_dir,
                phont_path=phont_path
            )
        else:
            raise ValueError("engine 只能为 'aq1' 或 'aq2'")

    def synthesize(self, text, speed=100, pitch=100, volume=100):
        if self.engine == 'aq1':
            # aq1: pitch_factor为float，100为标准
            pitch_factor = pitch / 100.0
            return self.synth.synthesize(text, speed=speed, pitch_factor=pitch_factor, volume=volume)
        else:
            # aq2: pitch为百分比
            return self.synth.synthesize(text, speed=speed, pitch=pitch, volume=volume)

    def close(self):
        if self.synth:
            self.synth.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def get_prefix(text, maxlen=20):
        return safefilename(text, maxlen)


if __name__ == '__main__':
    text1 = "これはAquesTalk1のテストです"
    text2 = "これはAquesTalk2のテストです"
    converter = ChineseToHiragana()

    # 检查架构
    if platform.architecture()[0] != '32bit':
        print("警告：此脚本假定使用 32 位 DLL，但当前 Python 环境不是 32 位。")

    # 测试 AquesTalk2（aq2）+ 油库里音色
    try:
        with AquesSynthesizer(
                engine='aq2',
                voice='aq_yukkuri.phont',
                dll_base='.\\aqtk2',
                dic_dir='.\\aq_dic'
        ) as synth:
            wav = synth.synthesize(converter.convert(text2), speed=100, pitch=100, volume=100)
            with open('.\\output\\test_aq2.wav', 'wb') as f:
                f.write(wav)
            print("AquesTalk2 合成并保存 test_aq2.wav")
    except Exception as e:
        print(f"AquesTalk2 测试失败: {e}")

    # 测试 AquesTalk1（aq1）+ f1 音色
    try:
        with AquesSynthesizer(
                engine='aq1',
                voice='f1',
                dll_base='.\\aqtk1',
                dic_dir='.\\aq_dic'
        ) as synth:
            wav = synth.synthesize(converter.convert(text2), speed=100, pitch=100, volume=100)
            with open('.\\output\\test_aq1.wav', 'wb') as f:
                f.write(wav)
            print("AquesTalk1 合成并保存 test_aq1.wav")
    except Exception as e:
        print(f"AquesTalk1 测试失败: {e}")
