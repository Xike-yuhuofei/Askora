"""
中文分词服务
基于 jieba 的中文分词封装，支持专业术语词典、停用词过滤、关键词提取

功能：
- 中文分词
- 停用词过滤
- 专业词典加载
- 关键词提取（带权重）
- 中英混合分词
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

# 停用词表（扩展版）
STOPWORDS = {
    # 中文停用词
    "的",
    "了",
    "在",
    "是",
    "我",
    "有",
    "和",
    "就",
    "不",
    "人",
    "都",
    "一",
    "一个",
    "上",
    "也",
    "很",
    "到",
    "说",
    "要",
    "去",
    "你",
    "会",
    "着",
    "没有",
    "看",
    "好",
    "自己",
    "这",
    "什么",
    "怎么",
    "如何",
    "请",
    "帮",
    "能",
    "可以",
    "吗",
    "呢",
    "啊",
    "吧",
    "哦",
    "嗯",
    "呀",
    "啦",
    "这个",
    "那个",
    "这些",
    "那些",
    "但是",
    "不过",
    "而且",
    "因为",
    "所以",
    "如果",
    "虽然",
    "或者",
    "以及",
    "怎样",
    "怎么样",
    "为什么",
    # 英文停用词
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "do",
    "does",
    "did",
    "have",
    "has",
    "had",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "can",
    "need",
    "dare",
    "ought",
    "used",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "at",
    "by",
    "from",
    "as",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "out",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "because",
    "but",
    "and",
    "or",
    "if",
    "while",
    "although",
    "though",
    "about",
    "up",
    "down",
    "left",
    "right",
    "first",
    "last",
    "also",
    "enough",
    "still",
    "already",
    "yet",
}


class ChineseTokenizer:
    """
    中文分词器

    封装 jieba，提供：
    - 标准中文分词
    - 停用词过滤
    - 专业词典加载
    - 关键词加权提取
    """

    def __init__(self):
        self._initialized = False
        self._tokenizer = None
        self._custom_dicts_loaded = False

    def _ensure_initialized(self) -> None:
        """延迟初始化 jieba（首次调用时加载，避免冷启动开销）"""
        if self._initialized:
            return

        import jieba
        import jieba.posseg as pseg

        self._tokenizer = jieba
        self._pseg = pseg

        # 加载自定义词典
        self._load_custom_dicts()

        self._initialized = True
        logger.info("chinese_tokenizer_initialized")

    def _load_custom_dicts(self) -> None:
        """加载专业词典"""
        if self._custom_dicts_loaded:
            return

        dicts_dir = Path(__file__).parent / "dicts"

        if dicts_dir.exists():
            for dict_file in dicts_dir.glob("*.txt"):
                try:
                    self._tokenizer.load_userdict(str(dict_file))
                    logger.debug(f"custom_dict_loaded: {dict_file.name}")
                except Exception as e:
                    logger.warning(f"custom_dict_load_failed: {dict_file.name}, error: {e}")

        self._custom_dicts_loaded = True

    def tokenize(self, text: str, with_pos: bool = False) -> list[str | tuple[str, str]]:
        """
        对文本进行分词

        Args:
            text: 输入文本
            with_pos: 是否返回词性标注

        Returns:
            分词结果列表
        """
        self._ensure_initialized()

        if not text or not text.strip():
            return []

        if with_pos:
            words = self._pseg.cut(text)
            return [(w.word, w.flag) for w in words]
        else:
            return list(self._tokenizer.cut(text))

    def tokenize_with_stopwords(self, text: str) -> list[str]:
        """
        分词并过滤停用词

        Args:
            text: 输入文本

        Returns:
            过滤停用词后的分词结果
        """
        tokens = self.tokenize(text, with_pos=False)
        return [
            token
            for token in tokens
            if isinstance(token, str) and token.strip() and token.lower() not in STOPWORDS
        ]

    def extract_keywords(
        self,
        text: str,
        top_k: int = 10,
        with_weight: bool = True,
    ) -> list[tuple[str, float]]:
        """
        提取关键词（带权重）

        权重规则：
        - 名词(n): 权重 1.0
        - 动词(v): 权重 0.8
        - 形容词(a): 权重 0.6
        - 其他: 权重 0.4

        Args:
            text: 输入文本
            top_k: 返回前 N 个关键词
            with_weight: 是否使用词性加权

        Returns:
            [(关键词, 权重), ...]
        """
        self._ensure_initialized()

        if not text or not text.strip():
            return []

        # 分词 + 词性标注
        words = self._pseg.cut(text)

        # 词频统计 + 权重计算
        freq_dict: dict[str, float] = {}

        for word in words:
            token = word.word.strip()
            if not token or token.lower() in STOPWORDS:
                continue

            # 计算权重
            if with_weight:
                weight = self._get_pos_weight(word.flag)
            else:
                weight = 1.0

            # 累加频率 * 权重
            token_key = token.lower()
            freq_dict[token_key] = freq_dict.get(token_key, 0) + weight

        # 排序取 Top-K
        sorted_keywords = sorted(
            freq_dict.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return sorted_keywords[:top_k]

    def _get_pos_weight(self, pos_flag: str) -> float:
        """根据词性获取权重"""
        # 名词（n）、专有名词（nr/nz/nt）
        if pos_flag.startswith("n"):
            return 1.0
        # 动词（v）
        elif pos_flag.startswith("v"):
            return 0.8
        # 形容词（a）
        elif pos_flag.startswith("a"):
            return 0.6
        # 副词（d）
        elif pos_flag.startswith("d"):
            return 0.5
        # 其他
        else:
            return 0.4

    def load_custom_dict(self, dict_path: str) -> None:
        """
        动态加载自定义词典

        Args:
            dict_path: 词典文件路径
        """
        self._ensure_initialized()

        if os.path.exists(dict_path):
            self._tokenizer.load_userdict(dict_path)
            logger.info(f"custom_dict_loaded_dynamic: {dict_path}")
        else:
            logger.warning(f"custom_dict_not_found: {dict_path}")

    def get_keywords_set(self, text: str, top_k: int = 10) -> set[str]:
        """
        获取关键词集合（便捷方法，用于 RAG 检索）

        Args:
            text: 输入文本
            top_k: 关键词数量

        Returns:
            关键词集合
        """
        keywords = self.extract_keywords(text, top_k=top_k, with_weight=True)
        return {kw for kw, _ in keywords}


# 全局单例
_tokenizer_instance: Optional[ChineseTokenizer] = None


def get_tokenizer() -> ChineseTokenizer:
    """获取分词器单例"""
    global _tokenizer_instance
    if _tokenizer_instance is None:
        _tokenizer_instance = ChineseTokenizer()
    return _tokenizer_instance
