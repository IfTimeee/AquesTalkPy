import os
import sys
from flask import Flask, jsonify, request, send_file
import io
import platform
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import AquesSynthesizer
from text_to_ja import ChineseToHiragana

app = Flask(__name__)

AQTK1_BASE = '.\\aqtk1'
AQTK2_BASE = '.\\aqtk2'
DIC_DIR = '.\\aq_dic'


def get_engine_and_paths(voice):
    if voice.endswith('.phont'):
        engine = 'aq2'
        dll_base = AQTK2_BASE
    else:
        engine = 'aq1'
        dll_base = AQTK1_BASE
    return engine, dll_base


@app.route('/voices', methods=['GET'])
def list_voices():
    voices = []
    # aq1 音色
    if os.path.isdir(AQTK1_BASE):
        for name in os.listdir(AQTK1_BASE):
            subdir = os.path.join(AQTK1_BASE, name)
            if os.path.isdir(subdir) and os.path.isfile(os.path.join(subdir, 'AquesTalk.dll')):
                voices.append({'voice': name, 'engine': 'aq1'})
    # aq2 音色
    phont_dir = os.path.join(AQTK2_BASE, 'phont')
    if os.path.isdir(phont_dir):
        for fname in os.listdir(phont_dir):
            if fname.endswith('.phont'):
                voices.append({'voice': fname, 'engine': 'aq2'})
    return jsonify(voices)


@app.route('/synthesize', methods=['POST'])
def synthesize_audio():
    data = request.json
    text = data.get('text')
    voice = data.get('voice')
    speed = int(data.get('speed', 100))
    pitch = int(data.get('pitch', 100))
    volume = int(data.get('volume', 100))

    if not text or not voice:
        return {'error': '缺少 text 或 voice 参数'}, 400
    # 转换日语发音
    text = ChineseToHiragana().convert(text)

    engine, dll_base = get_engine_and_paths(voice)

    try:
        with AquesSynthesizer(
            engine=engine,
            voice=voice,
            dll_base=dll_base,
            dic_dir=DIC_DIR
        ) as synth:
            wav = synth.synthesize(text, speed=speed, pitch=pitch, volume=volume)
            wav_io = io.BytesIO(wav)
            wav_io.seek(0)
            prefix = AquesSynthesizer.get_prefix(data.get('text', 'audio'))
            filename = f"{prefix}.wav"
            return send_file(
                wav_io,
                mimetype='audio/wav',
                as_attachment=True,
                download_name=filename
            )
    except Exception as e:
        return {'error': f'合成失败: {str(e)}'}, 500


if __name__ == '__main__':
    if platform.architecture()[0] != '32bit':
        print("警告：请使用 32 位 Python 环境以兼容 DLL。")
    app.run(host='0.0.0.0', port=5000, debug=True)
