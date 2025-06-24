import re
from typing import Sequence, Any, List

from llama_index.core.node_parser import NodeParser
from llama_index.core.schema import BaseNode, Document, TextNode

from app.data_indexing.file.document_splitter.utils import convert_chinese_to_number

# 汉字章节编号
NUM_STR = "零一二三四五六七八九十百千"
# 编正则
PART_REGEX = re.compile(rf"^\s*第([{NUM_STR}]+)编+.*")
# 章正则
CHAPTER_REGEX = re.compile(rf"^\s*第([{NUM_STR}]+)章+.*")
# 节正则
SECTION_REGEX = re.compile(rf"^\s*第([{NUM_STR}]+)节+.*")
# 条正则
ARTICLE_REGEX = re.compile(rf"^(\s|　| )*第([{NUM_STR}]+)条.*")

# 预编译零宽字符清理正则表达式
ZERO_WIDTH_PATTERN = re.compile(r"[\u200B\u200C\u200D\uFEFF]")


def has_article_pattern(text: str) -> bool:
    """检查文档中是否包含条文模式"""
    lines = [text for text in text.splitlines() if text.strip()]
    for line in lines:
        if ARTICLE_REGEX.search(line):
            return True
    return False


def clean_and_check_blank(s: str) -> bool:
    """优化版本：只在需要时才进行正则替换"""
    # 首先检查是否为空，避免不必要的正则操作
    if not s or s.strip() == "":
        return True

    # 只有当字符串包含零宽字符时才进行替换
    if ZERO_WIDTH_PATTERN.search(s):
        s = ZERO_WIDTH_PATTERN.sub("", s)

    return s.strip() == ""


def none_match(text: str, patterns: Sequence[re.Pattern]) -> bool:
    """使用预编译的正则表达式"""
    for pattern in patterns:
        if pattern.match(text):
            return False
    return True


def read_with_article_pattern(document: Document) -> List[TextNode]:
    text = document.text
    result = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    part, chapter, section, article = None, None, None, None

    # 预编译的模式列表
    all_patterns = [PART_REGEX, CHAPTER_REGEX, SECTION_REGEX, ARTICLE_REGEX]

    i = 0
    while i < len(lines):
        line = lines[i]
        if clean_and_check_blank(line):
            i = i + 1
            continue

        _content_type = None
        _text = None
        if PART_REGEX.match(line):
            part = convert_chinese_to_number(PART_REGEX.match(line).group(1))
            _content_type = 1
        elif CHAPTER_REGEX.match(line):
            chapter = convert_chinese_to_number(CHAPTER_REGEX.match(line).group(1))
            _content_type = 2
        elif SECTION_REGEX.match(line):
            section = convert_chinese_to_number(SECTION_REGEX.match(line).group(1))
            _content_type = 3
        elif ARTICLE_REGEX.match(line):
            _content_type = 4
            article = convert_chinese_to_number(ARTICLE_REGEX.match(line).group(2))
            has_more = line.endswith(":") or (i + 1 < len(lines) and none_match(lines[i + 1], all_patterns))
            if has_more:
                if line.startswith("　　"):
                    line = line[2:]
                # 说明还有具体的小条例或者更多信息
                _line = [line]
                temp_index = i + 1
                temp_text = lines[temp_index]
                while temp_index < len(lines) and none_match(temp_text, all_patterns):
                    if temp_text.startswith("　　"):
                        temp_text = temp_text[2:]
                    _line.append('\n')
                    _line.append(temp_text)
                    temp_index += 1
                    if temp_index < len(lines):
                        temp_text = lines[temp_index]
                    else:
                        break
                i = temp_index - 1
                _text = ''.join(_line)

        if not _text:
            _text = line

        extra_info = {"part": part, "chapter": chapter, "section": section, "article": article,
                      "content_type": _content_type}
        node = TextNode(text=_text, extra_info=extra_info)

        result.append(node)
        i = i + 1

    return result


def read_without_article_pattern(document: Document) -> List[TextNode]:
    lines = [line.strip() for line in document.text.splitlines() if line.strip()]
    return [TextNode(text=line) for line in lines]


class LegalSplitter(NodeParser):
    def _parse_nodes(self, _nodes: Sequence[BaseNode], show_progress: bool = False, **kwargs: Any) -> List[TextNode]:
        result = []
        for node in _nodes:
            if isinstance(node, Document):
                text = node.text
                if has_article_pattern(text):
                    result.extend(read_with_article_pattern(node))
                else:
                    result.extend(read_without_article_pattern(node))

        return result