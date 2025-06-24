# -*- coding: utf-8 -*-

# 依赖库:
# pip install pypinyin pykakasi regex

from pypinyin import pinyin, Style
from pykakasi import kakasi
import regex as re


class ChineseToHiragana:
    """
    一个将包含中文、英文和标点的混合文本转换为日语平假名的转换器。
    该实现严格遵循平凡社《中国語音節表記ガイドライン》的教育版标准，
    并对英文和标点进行优化处理，以实现最高程度的语音保真度。
    """

    def __init__(self):
        # 初始化 pykakasi 转换器
        self._kakasi = kakasi()

        # 为语音合成保留的标点及其日文对应
        self.punctuation_map = {
            '。': '。', '，': '、', '、': '、', '？': '？', '！': '！',
            '.': '。', ',': '、', '?': '？', '!': '！',
            '…': '…', '...': '…', '——': 'ーー'
        }

        # 英文单字母发音映射
        self.english_letter_map = {
            'A': 'エー', 'B': 'ビー', 'C': 'シー', 'D': 'ディー', 'E': 'イー', 'F': 'エフ', 'G': 'ジー',
            'H': 'エイチ', 'I': 'アイ', 'J': 'ジェー', 'K': 'ケー', 'L': 'エル', 'M': 'エム', 'N': 'エヌ',
            'O': 'オー', 'P': 'ピー', 'Q': 'キュー', 'R': 'アール', 'S': 'エス', 'T': 'ティー', 'U': 'ユー',
            'V': 'ブイ', 'W': 'ダブリュー', 'X': 'エックス', 'Y': 'ワイ', 'Z': 'ゼット'
        }

        # 核心转写表：基于平凡社教育版指南的拼音到片假名映射
        self.pinyin_to_katakana_map = {
            # A
            'a': 'アー', 'ai': 'アイ', 'an': 'アン', 'ang': 'アアン', 'ao': 'アオ',
            # O, E, ER
            'o': 'オー', 'ou': 'オウ', 'ong': 'オオン',
            'e': 'オー', 'ei': 'エイ', 'en': 'エン', 'eng': 'エエン', 'er': 'アル',
            # B
            'ba': 'バー', 'bo': 'ボォ', 'bai': 'バイ', 'bei': 'ベイ', 'bao': 'バオ', 'ban': 'バン', 'ben': 'ベン', 'bang': 'バアン', 'beng': 'ベン', 'bi': 'ビィ', 'bie': 'ビエ', 'biao': 'ビアオ', 'bian': 'ビエン', 'bin': 'ビン', 'bing': 'ビイン', 'bu': 'ブー',
            # P
            'pa': 'パー', 'po': 'ポォ', 'pai': 'パイ', 'pei': 'ペイ', 'pao': 'パオ', 'pou': 'ポウ', 'pan': 'パン', 'pen': 'ペン', 'pang': 'パアン', 'peng': 'ペン', 'pi': 'ピィ', 'pie': 'ピエ', 'piao': 'ピアオ', 'pian': 'ピエン', 'pin': 'ピン', 'ping': 'ピイン', 'pu': 'プー',
            # M
            'ma': 'マー', 'mo': 'モォ', 'me': 'メ', 'mai': 'マイ', 'mei': 'メイ', 'mao': 'マオ', 'mou': 'モウ', 'man': 'マン', 'men': 'メン', 'mang': 'マアン', 'meng': 'メン', 'mi': 'ミィ', 'mie': 'ミエ', 'miao': 'ミアオ', 'miu': 'ミウ', 'mian': 'ミエン', 'min': 'ミン', 'ming': 'ミイン', 'mu': 'ムー',
            # F
            'fa': 'ファー', 'fo': 'フォ', 'fei': 'フェイ', 'fen': 'フェン', 'fang': 'フアアン', 'feng': 'フォン', 'fan': 'ファン', 'fou': 'フォウ', 'fu': 'フー',
            # D
            'da': 'ダー', 'de': 'ドー', 'dai': 'ダイ', 'dei': 'デイ', 'dao': 'ダオ', 'dou': 'ドウ', 'dan': 'ダン', 'den': 'デン', 'dang': 'ダアン', 'deng': 'デン', 'dong': 'ドオン', 'di': 'ディ', 'die': 'ディエ', 'diao': 'ディアオ', 'diu': 'ディウ', 'dian': 'ディエン', 'ding': 'ディイン', 'du': 'ドゥー', 'duo': 'ドゥオ', 'dui': 'ドゥイ', 'dun': 'ドゥン', 'duan': 'ドゥアン',
            # T
            'ta': 'ター', 'te': 'トー', 'tai': 'タイ', 'tei': 'テイ', 'tao': 'タオ', 'tou': 'トウ', 'tan': 'タン', 'tang': 'タアン', 'teng': 'テン', 'tong': 'トオン', 'ti': 'ティ', 'tie': 'ティエ', 'tiao': 'ティアオ', 'tian': 'ティエン', 'ting': 'ティイン', 'tu': 'トゥー', 'tuo': 'トゥオ', 'tui': 'トゥイ', 'tun': 'トゥン', 'tuan': 'トゥアン',
            # N
            'na': 'ナー', 'ne': 'ノー', 'nai': 'ナイ', 'nei': 'ネイ', 'nao': 'ナオ', 'nou': 'ノウ', 'nan': 'ナン', 'nen': 'ネン', 'nang': 'ナアン', 'neng': 'ネン', 'nong': 'ノオン', 'ni': 'ニィ', 'nie': 'ニエ', 'niao': 'ニアオ', 'niu': 'ニウ', 'nian': 'ニエン', 'nin': 'ニン', 'niang': 'ニアアン', 'ning': 'ニイン', 'nu': 'ヌー', 'nuo': 'ヌオ', 'nuan': 'ヌアン', 'nü': 'ニュ', 'nüe': 'ニュエ',
            # L
            'la': 'ラー', 'le': 'ロー', 'lai': 'ライ', 'lei': 'レイ', 'lao': 'ラオ', 'lou': 'ロウ', 'lan': 'ラン', 'lang': 'ラアン', 'leng': 'レン', 'long': 'ロオン', 'li': 'リィ', 'lia': 'リア', 'lie': 'リエ', 'liao': 'リアオ', 'liu': 'リウ', 'lian': 'リエン', 'lin': 'リン', 'liang': 'リアアン', 'ling': 'リイン', 'lu': 'ルー', 'luo': 'ルオ', 'lü': 'リュ', 'lüe': 'リュエ', 'luan': 'ルアン',
            # G
            'ga': 'ガー', 'ge': 'ゴー', 'gai': 'ガイ', 'gei': 'ゲイ', 'gao': 'ガオ', 'gou': 'ゴウ', 'gan': 'ガン', 'gen': 'ゲン', 'gang': 'ガアン', 'geng': 'ゲン', 'gong': 'ゴオン', 'gu': 'グー', 'gua': 'グア', 'guo': 'グオ', 'guai': 'グアイ', 'gui': 'グイ', 'gun': 'グン', 'guan': 'グアン', 'guang': 'グアアン',
            # K
            'ka': 'カー', 'ke': 'コー', 'kai': 'カイ', 'kei': 'ケイ', 'kao': 'カオ', 'kou': 'コウ', 'kan': 'カン', 'ken': 'ケン', 'kang': 'カアン', 'keng': 'ケン', 'kong': 'コオン', 'ku': 'クー', 'kua': 'クア', 'kuo': 'クオ', 'kuai': 'クアイ', 'kui': 'クイ', 'kun': 'クン', 'kuan': 'クアン', 'kuang': 'クアアン',
            # H
            'ha': 'ハー', 'he': 'ホー', 'hai': 'ハイ', 'hei': 'ヘイ', 'hao': 'ハオ', 'hou': 'ホウ', 'han': 'ハン', 'hen': 'ヘン', 'hang': 'ハアン', 'heng': 'ヘン', 'hong': 'ホオン', 'hu': 'フー', 'hua': 'フア', 'huo': 'フオ', 'huai': 'フアイ', 'hui': 'フイ', 'hun': 'フン', 'huan': 'フアン', 'huang': 'フアアン',
            # J
            'ji': 'ジィ', 'jia': 'ジャ', 'jie': 'ジェ', 'jiao': 'ジャオ', 'jiu': 'ジウ', 'jian': 'ジエン', 'jin': 'ジン', 'jiang': 'ジアアン', 'jing': 'ジイン', 'jiong': 'ジョン', 'ju': 'ジュ', 'jue': 'ジュエ', 'juan': 'ジュエン', 'jun': 'ジュン',
            # Q
            'qi': 'チィ', 'qia': 'チャ', 'qie': 'チェ', 'qiao': 'チャオ', 'qiu': 'チウ', 'qian': 'チエン', 'qin': 'チン', 'qiang': 'チアアン', 'qing': 'チイン', 'qiong': 'チョン', 'qu': 'チュ', 'que': 'チュエ', 'quan': 'チュエン', 'qun': 'チュン',
            # X
            'xi': 'シィ', 'xia': 'シャ', 'xie': 'シェ', 'xiao': 'シャオ', 'xiu': 'シウ', 'xian': 'シエン', 'xin': 'シン', 'xiang': 'シアアン', 'xing': 'シイン', 'xiong': 'ション', 'xu': 'シュ', 'xue': 'シュエ', 'xuan': 'シュエン', 'xun': 'シュン',
            # ZH
            'zha': 'ヂャー', 'zhe': 'ヂォー', 'zhi': 'ヂー', 'zhai': 'ヂャイ', 'zhei': 'ヂェイ', 'zhao': 'ヂャオ', 'zhou': 'ヂョウ', 'zhan': 'ヂャン', 'zhen': 'ヂェン', 'zhang': 'ヂャアン', 'zheng': 'ヂェン', 'zhong': 'ヂョオン', 'zhu': 'ヂュー', 'zhua': 'ヂュア', 'zhuo': 'ヂュオ', 'zhuai': 'ヂュアイ', 'zhui': 'ヂュイ', 'zhun': 'ヂュン', 'zhuan': 'ヂュアン', 'zhuang': 'ヂュアアン',
            # CH
            'cha': 'チャー', 'che': 'チョー', 'chi': 'チー', 'chai': 'チャイ', 'chao': 'チャオ', 'chou': 'チョウ', 'chan': 'チャン', 'chen': 'チェン', 'chang': 'チャアン', 'cheng': 'チェン', 'chong': 'チョオン', 'chu': 'チュー', 'chua': 'チュア', 'chuo': 'チュオ', 'chuai': 'チュアイ', 'chui': 'チュイ', 'chun': 'チュン', 'chuan': 'チュアン', 'chuang': 'チュアアン',
            # SH
            'sha': 'シャー', 'she': 'ショー', 'shi': 'シー', 'shai': 'シャイ', 'shei': 'シェイ', 'shao': 'シャオ', 'shou': 'ショウ', 'shan': 'シャン', 'shen': 'シェン', 'shang': 'シャアン', 'sheng': 'シェン', 'shu': 'シュー', 'shua': 'シュア', 'shuo': 'シュオ', 'shuai': 'シュアイ', 'shui': 'シュイ', 'shun': 'シュン', 'shuan': 'シュアン',
            # R
            're': 'ロー', 'ri': 'リー', 'rao': 'ラオ', 'rou': 'ロウ', 'ran': 'ラン', 'ren': 'レン', 'rang': 'ラアン', 'reng': 'レン', 'rong': 'ロオン', 'ru': 'ルー', 'ruo': 'ルオ', 'rui': 'ルイ', 'run': 'ルン', 'ruan': 'ルアン',
            # Z
            'za': 'ザー', 'ze': 'ゾー', 'zi': 'ズー', 'zai': 'ザイ', 'zei': 'ゼイ', 'zao': 'ザオ', 'zou': 'ゾウ', 'zan': 'ザン', 'zen': 'ゼン', 'zang': 'ザアン', 'zeng': 'ゼン', 'zong': 'ゾオン', 'zu': 'ズー', 'zuo': 'ズオ', 'zui': 'ズイ', 'zun': 'ズン', 'zuan': 'ズアン',
            # C
            'ca': 'ツァー', 'ce': 'ツォー', 'ci': 'ツー', 'cai': 'ツァイ', 'cao': 'ツァオ', 'cou': 'ツォウ', 'can': 'ツァン', 'cen': 'ツェン', 'cang': 'ツァアン', 'ceng': 'ツェン', 'cong': 'ツォン', 'cu': 'ツー', 'cuo': 'ツオ', 'cui': 'ツイ', 'cun': 'ツン', 'cuan': 'ツアン',
            # S
            'sa': 'サー', 'se': 'ソー', 'si': 'スー', 'sai': 'サイ', 'sao': 'サオ', 'sou': 'ソウ', 'san': 'サン', 'sen': 'セン', 'sang': 'サアン', 'seng': 'セン', 'song': 'ソオン', 'su': 'スー', 'suo': 'スオ', 'sui': 'スイ', 'sun': 'スン', 'suan': 'スアン',
            # Y, W
            'ya': 'ヤー', 'yo': 'ヨー', 'ye': 'イエ', 'yao': 'ヤオ', 'you': 'ヨウ', 'yan': 'イエン', 'yin': 'イン', 'yang': 'ヤン', 'ying': 'イン', 'yong': 'ヨン', 'yi': 'イー', 'yu': 'ユ', 'yue': 'ユエ', 'yuan': 'ユエン', 'yun': 'ユン',
            'wa': 'ワー', 'wo': 'ウオ', 'wai': 'ワイ', 'wei': 'ウェイ', 'wan': 'ワン', 'wen': 'ウェン', 'wang': 'ワン', 'weng': 'ウォン', 'wu': 'ウー'
        }

    def _pinyin_to_katakana(self, pinyin_str: str) -> str:
        """将单个拼音字符串转换为片假名"""
        if pinyin_str.startswith('yu'):
            if pinyin_str == 'yuan': return 'ユエン'
            if pinyin_str == 'yue': return 'ユエ'
            if pinyin_str == 'yun': return 'ユン'
        return self.pinyin_to_katakana_map.get(pinyin_str, '')

    def _english_to_katakana(self, eng_str: str) -> str:
        """将英文单词或字母转换为片假名"""
        if len(eng_str) == 1:
            return self.english_letter_map.get(eng_str.upper(), '')
        else:
            kakasi_inst = kakasi()
            result = kakasi_inst.convert(eng_str)
            return ''.join([item['kana'] for item in result])

    def _katakana_to_hiragana(self, katakana_str: str) -> str:
        """将片假名字符串转换为平假名"""
        kakasi_inst = kakasi()
        result = kakasi_inst.convert(katakana_str)
        return ''.join([item['hira'] for item in result])

    def convert(self, text: str) -> str:
        """
        执行完整的多语言转换流程。
        :param text: 输入的混合文本字符串。
        :return: 转换后的平假名字符串。
        """
        # 使用正则表达式将文本分割为中文、英文、标点和空格等部分
        # \p{Han} 匹配所有汉字
        # [a-zA-Z]+ 匹配英文单词
        # \s+ 匹配空格
        # . 匹配任何其他字符（主要是标点）
        tokens = re.findall(r'(\p{Han}+|[a-zA-Z]+|[\p{Hiragana}\p{Katakana}ー]+|[。、！？…]|[\s]+|.)', text)

        katakana_parts = []
        for token in tokens:
            if re.fullmatch(r'\p{Han}+', token):
                # 中文
                pinyin_list = pinyin(token, style=Style.NORMAL, v_to_u=True)
                syllables = [item for sublist in pinyin_list for item in sublist]
                for syllable in syllables:
                    katakana_parts.append(self._pinyin_to_katakana(syllable))
            elif re.fullmatch(r'[a-zA-Z]+', token):
                # 英文
                katakana_parts.append(self._english_to_katakana(token))
            elif re.fullmatch(r'[\p{Hiragana}\p{Katakana}ー]+', token):
                # 日语假名，直接保留
                katakana_parts.append(token)
            elif token in self.punctuation_map or re.fullmatch(r'[。、！？…]', token):
                # 标点
                katakana_parts.append(self.punctuation_map.get(token, token))
            elif re.fullmatch(r'\s+', token):
                # 空格，直接保留
                katakana_parts.append(token)
            else:
                continue

        katakana_string = "".join(katakana_parts)

        # 最终转换为平假名
        hiragana_string = self._katakana_to_hiragana(katakana_string)

        return hiragana_string


# --- 使用示例 ---
if __name__ == '__main__':
    converter = ChineseToHiragana()

    # 测试用例1：混合日语、中文、英文、标点
    chinese_text_1 = "にぃはお、world. 这个 是test A。这个是test b."
    hiragana_output_1 = converter.convert(chinese_text_1)
    print(f"原文: {chinese_text_1}")
    print(f"平假名输出: {hiragana_output_1}")

    print("-" * 20)

    # 测试用例2：来自用户的具体需求
    chinese_text_2 = "我想用这个生成Yukkuri语音……"
    hiragana_output_2 = converter.convert(chinese_text_2)
    print(f"原文: {chinese_text_2}")
    print(f"平假名输出: {hiragana_output_2}")