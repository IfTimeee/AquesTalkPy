import sys
import os
import tempfile
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit, QLineEdit, QPushButton,
    QSlider, QFileDialog, QHBoxLayout, QVBoxLayout, QMessageBox, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtMultimedia import QSound
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from text_to_ja import ChineseToHiragana
from main import AquesSynthesizer

DIC_DIR = '.\\aq_dic'
AQTK1_BASE = '.\\aqtk1'
AQTK2_BASE = '.\\aqtk2'
DEFAULT_AQ2_PHONT = 'aq_yukkuri.phont'


class YukkuriWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yukkuri语音生成器 (PyQt5)")
        self.selected_voice = DEFAULT_AQ2_PHONT
        self.selected_engine = 'aq2'
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("输入文本:"))
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)

        # 批量合成提示
        hint_label = QLabel("支持用;（英文分号）分割文本进行批量合成")
        hint_label.setStyleSheet("color: gray; font-size: 15px;")
        hint_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(hint_label)

        # 音色选择
        h_phont = QHBoxLayout()
        h_phont.addWidget(QLabel("音色选择:"))
        self.voice_tree = QTreeWidget()
        self.voice_tree.setHeaderHidden(True)
        self._populate_voice_tree()
        self.voice_tree.itemClicked.connect(self.on_voice_selected)
        h_phont.addWidget(self.voice_tree)
        self.phont_edit = QLineEdit(self._get_voice_path(self.selected_engine, self.selected_voice))
        self.phont_edit.setReadOnly(True)
        h_phont.addWidget(self.phont_edit)
        layout.addLayout(h_phont)

        # 参数调节
        h_params = QHBoxLayout()
        # 语速
        h_params.addWidget(QLabel("语速:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 300)
        self.speed_slider.setValue(100)
        self.speed_edit = QLineEdit("100")
        self.speed_edit.setFixedWidth(45)
        h_params.addWidget(self.speed_slider)
        h_params.addWidget(self.speed_edit)
        self.speed_slider.valueChanged.connect(lambda v: self.speed_edit.setText(str(v)))
        self.speed_edit.editingFinished.connect(lambda: self.speed_slider.setValue(self._get_int_from_edit(self.speed_edit, 100, 50, 300)))
        # 音高
        h_params.addWidget(QLabel("音高:"))
        self.pitch_slider = QSlider(Qt.Horizontal)
        self.pitch_slider.setRange(50, 200)
        self.pitch_slider.setValue(100)
        self.pitch_edit = QLineEdit("100")
        self.pitch_edit.setFixedWidth(45)
        h_params.addWidget(self.pitch_slider)
        h_params.addWidget(self.pitch_edit)
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_edit.setText(str(v)))
        self.pitch_edit.editingFinished.connect(lambda: self.pitch_slider.setValue(self._get_int_from_edit(self.pitch_edit, 100, 50, 200)))
        # 音量
        h_params.addWidget(QLabel("音量:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 300)
        self.volume_slider.setValue(100)
        self.volume_edit = QLineEdit("100")
        self.volume_edit.setFixedWidth(45)
        h_params.addWidget(self.volume_slider)
        h_params.addWidget(self.volume_edit)
        self.volume_slider.valueChanged.connect(lambda v: self.volume_edit.setText(str(v)))
        self.volume_edit.editingFinished.connect(lambda: self.volume_slider.setValue(self._get_int_from_edit(self.volume_edit, 100, 0, 300)))
        layout.addLayout(h_params)

        # 按钮
        h_btns = QHBoxLayout()
        btn_gen = QPushButton("生成WAV")
        btn_gen.clicked.connect(self.generate_wav)
        h_btns.addWidget(btn_gen)
        btn_preview = QPushButton("预览")
        btn_preview.clicked.connect(self.preview_wav)
        h_btns.addWidget(btn_preview)
        btn_batch = QPushButton("批量生成WAV")
        btn_batch.clicked.connect(self.batch_generate_wav)
        h_btns.addWidget(btn_batch)
        btn_exit = QPushButton("退出")
        btn_exit.clicked.connect(self.close)
        h_btns.addWidget(btn_exit)
        layout.addLayout(h_btns)
        self.setLayout(layout)


    def _populate_voice_tree(self):
        self.voice_tree.clear()
        # AquesTalk2
        aq2_root = QTreeWidgetItem(self.voice_tree, ["AquesTalk2"])
        phont_dir = os.path.join(AQTK2_BASE, 'phont')
        if os.path.isdir(phont_dir):
            for fname in sorted(os.listdir(phont_dir)):
                if fname.endswith('.phont'):
                    QTreeWidgetItem(aq2_root, [fname])
        # AquesTalk1
        aq1_root = QTreeWidgetItem(self.voice_tree, ["AquesTalk1"])
        if os.path.isdir(AQTK1_BASE):
            for name in sorted(os.listdir(AQTK1_BASE)):
                subdir = os.path.join(AQTK1_BASE, name)
                if os.path.isdir(subdir) and os.path.isfile(os.path.join(subdir, 'AquesTalk.dll')):
                    QTreeWidgetItem(aq1_root, [name])
        self.voice_tree.collapseAll()

    def on_voice_selected(self, item, _):
        parent = item.parent()
        if parent is None:
            return
        if parent.text(0) == "AquesTalk2":
            self.selected_voice = item.text(0)
            self.selected_engine = "aq2"
        elif parent.text(0) == "AquesTalk1":
            self.selected_voice = item.text(0)
            self.selected_engine = "aq1"
        self.phont_edit.setText(self._get_voice_path(self.selected_engine, self.selected_voice))

    def _get_voice_path(self, engine, voice):
        if engine == "aq2":
            return os.path.join(AQTK2_BASE, "phont", voice)
        else:
            return os.path.join(AQTK1_BASE, voice, "AquesTalk.dll")

    def _get_int_from_edit(self, edit, default, minv, maxv):
        try:
            v = int(edit.text())
            return max(minv, min(maxv, v))
        except Exception:
            return default

    def preview_wav(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入文本")
            return
        try:
            ja_text = ChineseToHiragana().convert(text)
            with AquesSynthesizer(
                engine=self.selected_engine,
                voice=self.selected_voice,
                dll_base=AQTK2_BASE if self.selected_engine == "aq2" else AQTK1_BASE,
                dic_dir=DIC_DIR
            ) as synth:
                wav = synth.synthesize(
                    ja_text,
                    speed=self._get_int_from_edit(self.speed_edit, 100, 50, 300),
                    pitch=self._get_int_from_edit(self.pitch_edit, 100, 50, 200),
                    volume=self._get_int_from_edit(self.volume_edit, 100, 0, 300)
                )
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                    f.write(wav)
                    temp_path = f.name
                QSound.play(temp_path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"合成失败: {e}")

    def generate_wav(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入文本")
            return
        # 生成安全的文件名前缀
        prefix = AquesSynthesizer.get_prefix(text)
        default_name = f"{prefix}.wav"
        save_path, _ = QFileDialog.getSaveFileName(self, "保存WAV文件", default_name, "WAV文件 (*.wav)")
        if not save_path:
            return
        try:
            ja_text = ChineseToHiragana().convert(text)
            with AquesSynthesizer(
                    engine=self.selected_engine,
                    voice=self.selected_voice,
                    dll_base=AQTK2_BASE if self.selected_engine == "aq2" else AQTK1_BASE,
                    dic_dir=DIC_DIR
            ) as synth:
                wav = synth.synthesize(
                    ja_text,
                    speed=self._get_int_from_edit(self.speed_edit, 100, 50, 300),
                    pitch=self._get_int_from_edit(self.pitch_edit, 100, 50, 200),
                    volume=self._get_int_from_edit(self.volume_edit, 100, 0, 300)
                )
                with open(save_path, 'wb') as f:
                    f.write(wav)
            QMessageBox.information(self, "完成", f"已保存: {save_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"合成失败: {e}")

    def batch_generate_wav(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入文本")
            return
        texts = [t.strip() for t in text.split(';') if t.strip()]
        if not texts:
            QMessageBox.warning(self, "提示", "没有可用的分句")
            return
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存文件夹")
        if not dir_path:
            return
        try:
            for idx, t in enumerate(texts, 1):
                prefix = AquesSynthesizer.get_prefix(t)
                filename = f"{prefix}_{idx}.wav"
                save_path = os.path.join(dir_path, filename)
                ja_text = ChineseToHiragana().convert(t)
                with AquesSynthesizer(
                        engine=self.selected_engine,
                        voice=self.selected_voice,
                        dll_base=AQTK2_BASE if self.selected_engine == "aq2" else AQTK1_BASE,
                        dic_dir=DIC_DIR
                ) as synth:
                    wav = synth.synthesize(
                        ja_text,
                        speed=self._get_int_from_edit(self.speed_edit, 100, 50, 300),
                        pitch=self._get_int_from_edit(self.pitch_edit, 100, 50, 200),
                        volume=self._get_int_from_edit(self.volume_edit, 100, 0, 300)
                    )
                    with open(save_path, 'wb') as f:
                        f.write(wav)
            QMessageBox.information(self, "完成", f"已批量生成 {len(texts)} 个WAV文件")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"批量合成失败: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = YukkuriWindow()
    win.show()
    sys.exit(app.exec_())
