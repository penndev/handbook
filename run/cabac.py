from collections import Counter

def calculate_probabilities(message):
    # 统计每个符号的频率
    freq = Counter(message)
    total_count = len(message)

    # 计算每个符号的概率区间
    probabilities = {}
    low = 0.0
    for char, count in freq.items():
        high = low + (count / total_count)
        probabilities[char] = (low, high)
        low = high
    return probabilities

def arithmetic_encode(message, probabilities):
    low = 0.0
    high = 1.0

    # 对每个符号进行编码，逐步缩小区间
    for char in message:
        char_low, char_high = probabilities[char]
        range_width = high - low
        high = low + range_width * char_high
        low = low + range_width * char_low

    # 返回最终区间中的任意值，作为编码结果
    return (low + high) / 2

# 使用"hello world"进行算术编码
message = "hello world"
probabilities = calculate_probabilities(message)
encoded_value = arithmetic_encode(message, probabilities)

# 输出编码结果和概率表
print(f"符号概率区间: {probabilities}")
print(f"编码后的值: {encoded_value}")
