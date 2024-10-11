
from enum import Enum

class SliceType(Enum):
    '''Table 7-6  Name association to slice_type'''
    P = 0
    B = 1
    I = 2 
    SP = 3
    SI = 4

    def __eq__(self, other):
        if isinstance(other, int):
            return self.value == other % 5
        return False

class NalUnitType(Enum):
    NotIDR = 0
    'slice_layer_without_partitioning_rbsp 非IDR'
    A = 2
    'slice_data_partition_a_layer_rbsp 分割块'
    B = 3
    'slice_data_partition_b_layer_rbsp 分割块'
    C = 4
    'slice_data_partition_c_layer_rbsp 分割块'
    IDR = 5
    'slice_layer_without_partitioning_rbsp 图像编码条带'
    SEI = 6
    'sei_rbsp 辅助增强信息'
    SPS = 7
    'seq_parameter_set_rbsp 序列参数集'
    PPS = 8
    'pic_parameter_set_rbsp 图像参数集'

    CSE = 20
    'slice_layer_extension_rbsp Coded slice extension 拓展编码'

    CSE3D = 21 
    'slice_layer_extension_rbsp Coded slice extension for a depth view component or a 3D-AVC texture view'
 



    def __eq__(self, other):
        if isinstance(other, int):
            return self.value == other
        return False

class BitStream():
    '''根据 7.2 Specification of syntax functions, categories, and descriptors 文档定义的数据读取方法'''
    def __init__(self, hex:bytearray) -> None:
        self.hex = hex
        self.position = 0
    
    # 读取原始字节流基础函数，移动指针
    def read_bits(self, n) -> int:
        '从字节流 返回n位无符号整数 大字节序列'
        value = 0  # 用于存储读取的值
        while n > 0:
            byte_pos = self.position // 8  # 当前字节的位置
            bit_offset = self.position % 8  # 当前字节的位偏移量
            remaining_bits_in_byte = 8 - bit_offset # 当前字节剩余可用位数
            bits_to_read = min(n, remaining_bits_in_byte) # 计算当前读取的位数，取 n 和剩余位数的最小值
            current_byte = self.hex[byte_pos]  # 从当前字节提取所需的位
            current_bits = (current_byte >> (remaining_bits_in_byte - bits_to_read)) & ((1 << bits_to_read) - 1)
            value = (value << bits_to_read) | current_bits # 将提取到的位拼接到结果中
            self.position += bits_to_read  # 更新位置和剩余要读取的位数
            n -= bits_to_read
        return value
    
    # 哥伦布编码
    def read_ue(self) -> int:
        '''解析 H.264 中的 ue(v) (无符号指数哥伦布编码0阶)'''
        leading_zeros = 0
        while self.read_bits(1) == 0: # 1. 计算前导零的个数
            leading_zeros += 1
        if leading_zeros == 0: # 2. 读取对应数量的位
            return 0  # 特殊情况，前导 0 个数为 0 时，值为 0
        return (1 << leading_zeros) - 1 + self.read_bits(leading_zeros)    
    def read_se(self) -> int:
        code_num = self.read_ue()
        if code_num % 2 == 0:
            return -(code_num // 2) 
        else:
            return code_num // 2 + 1 
    def read_me(self, chroma_format_idc):
        ''' 9.1.2 进行数值对照表 对本数据进行说明。 根据codeNum进行表 9-4 对照返回数据。
            sps.chroma_format_idc  != 0 返回a表 
            sps.chroma_format_idc  == 0 返回b表 
        '''
        codeNum = self.read_ue()
        raise('not support me(v)')

    # 
    def read_ae(self):
        ''' CABAC解析过程 \n
            sps. entropy_coding_mode_flag = 1 才会调用本过程
        '''
        pStateIdx
        valMPS1
        raise('not support ae(v)')
    def read_te(self):
        raise('not support te(v)') 

    # 逻辑验证
    def more_rbsp_data(self):
        return self.position / 8 + 2 > len(self.hex)
    def more_rbsp_trailing_data(self):
        return self.position < len(self.hex)
    def byte_aligned(self):
        return self.position % 8 == 0
    
    def cabac_mb_type(self, sliceType):
        # table 9-25
        if sliceType == SliceType.I:
            ctxIdxOffset = 3
            maxBinIdxCtx = 6
        else:
            raise("mb_type not support " + str(sliceType))
        ctxIdxInc = condTermFlagA + condTermFlagB
        return ctxIdxInc