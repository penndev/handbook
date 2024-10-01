'CODE logic from <T-REC-H.264-202108-I!!PDF-E.pdf>'
from enum import Enum
from typing import Generator

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

class BitStream():
    '''根据 7.2 Specification of syntax functions, categories, and descriptors 文档定义的数据读取方法'''
    def __init__(self, hex:bytearray) -> None:
        self.hex = hex
        self.position = 0
    def read_bits(self, n) -> int:
        '返回n位无符号整数'
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
            return code_num // 2  # 正数
        else:
            return -(code_num // 2 + 1)  # 负数

class NAL():
    def __init__(self, hex:bytearray):
        self.stream = BitStream(hex)
        self.forbidden_zero_bit = self.stream.read_bits(1)
        self.nal_ref_idc = self.stream.read_bits(2)
        self.nal_unit_type = self.stream.read_bits(5)  
        'Table 7-1 – NAL unit type codes, syntax element categories, and NAL unit type classes'
        if self.nal_unit_type in (14, 20, 21):
            raise('NO 3D SUPPORT')
        
        print(self.__dict__)



class H264(): 
    '''
    B.1 Byte stream NAL unit syntax and semantics
    '''
    def __h264__(self):
        pass
    
    def nal_unit(self, hex):
        if len(hex) == 0: # 头字节引起
            return
        nal = NAL(hex)

    def read_h264(self) -> Generator[bytearray, None, None] :
        with open(self.filename, "rb") as f:
            while chunk := f.read(self.chunk_size):
                yield bytearray(chunk)  # 每次读取一块并返回

    def __init__(self,filename):
        self.hex = bytearray()
        'filename 输入文件必须是h264文件'
        self.filename = filename
        self.chunk_size = 1024
        # 开始分割
        current_nal_unit = bytearray()
        last_hex = bytearray()
        for hex in self.read_h264():
            if len(last_hex):
                hex = last_hex + hex
            current_nal_unit_start_position = 0
            readCounter = 0
            hexLen = len(hex) - 2
            while hexLen > readCounter:
                if hex[readCounter] != 0:
                    readCounter += 1
                    continue
                if hex[readCounter+1] != 0:
                    readCounter += 2
                    continue
                if hex[readCounter+2] == 0:
                    if hex[readCounter+3] == 1: # 0x00000001 分割。
                        # ======
                        current_nal_unit = current_nal_unit + hex[current_nal_unit_start_position:readCounter]
                        self.nal_unit(current_nal_unit)
                        current_nal_unit = bytearray()
                        # ======
                        readCounter += 4
                        current_nal_unit_start_position = readCounter
                        continue
                    else:
                        raise('NALU 0x000000 HIT!')
                elif hex[readCounter+2] == 1: # 0x000001 分割。
                    # ======
                    current_nal_unit = current_nal_unit + hex[current_nal_unit_start_position:readCounter]
                    self.nal_unit(current_nal_unit)
                    current_nal_unit = bytearray()
                    # ======
                    readCounter += 3
                    current_nal_unit_start_position = readCounter
                    continue
                # 7.4.1 NAL unit semantics
                elif hex[readCounter+2] == 2:
                    raise('NALU 0x000002 HIT!')
                elif hex[readCounter+2] == 3: # RBSP BODY filter 03 = SODB
                    del hex[readCounter+2] # //处理透明传输，进行00替换还原
                    hexLen -= 1 
                    readCounter += 2
                else:
                    readCounter += 3
                    
            # 类似处理tcp粘包
            if hex[readCounter + 1] != 0:
                last_hex = bytearray()
                current_nal_unit = current_nal_unit + hex[current_nal_unit_start_position:]
            else: 
                last_hex =  hex[readCounter:]
                current_nal_unit += hex[current_nal_unit_start_position: readCounter]
        current_nal_unit = current_nal_unit + last_hex
        self.nal_unit(current_nal_unit)

if __name__ == "__main__":
    nal = H264("runtime/output.h264")
    # FILE_OUT = open('rbsp.h264', "wb")
    # FILE_OUT.write(nal.hex)
