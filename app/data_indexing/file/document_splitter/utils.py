# 中文数字转换为阿拉伯数字工具类
CHINESE_NUMBER = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "百", "千", "万", "亿"]
NUMBER = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100, 1000, 10000, 100000000]
CHINESE_NUM_MAP = dict(zip(CHINESE_NUMBER, NUMBER))


def is_chinese_number(s: str) -> bool:
    """
    判断字符串是否由纯中文数字组成
    """
    return all(char in CHINESE_NUM_MAP for char in s)


def convert_chinese_to_number(s: str) -> int | None:
    """
    将中文数字字符串（如 "三百二十一"）转换为阿拉伯数字（如 321）

    参数:
        s: 中文数字字符串

    返回:
        阿拉伯数字，如果无法转换则返回 None
    """
    if not s or not is_chinese_number(s):
        return None

    values = [CHINESE_NUM_MAP[char] for char in s]

    result = 0
    index = 0
    skip_next = False

    while index < len(values):
        current = values[index]

        if skip_next:
            skip_next = False
            index += 1
            continue

        # 当前为单位数（十百千等）
        if current >= 10:
            if index == 0:
                result += current
            else:
                prev = values[index - 1]
                if prev < 10:
                    # 如：二百 => 2 * 100
                    result += prev * current
                else:
                    # 连续单位：百千 等，取当前单位（如 "百亿" 视作 100000000）
                    result += current
        else:
            # 当前是数字，判断后面是否是单位
            if index + 1 < len(values) and values[index + 1] >= 10:
                result += current * values[index + 1]
                skip_next = True
            else:
                result += current

        index += 1

    return result