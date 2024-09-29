
from typing import List


class SliceHeader:
    def __init__(self, stream):
        self.bit_position = 0 
        self.stream = stream
        self.first_mb_in_slice = self.exGolomb()
        self.slice_type  = self.exGolomb()
        self.pic_parameter_set_id = self.exGolomb()
        self.frame_num = None
        print(self.first_mb_in_slice, self.slice_type, self.pic_parameter_set_id)

    def exGolomb(self):
        result = ""
        while (self.stream[self.bit_position//8] & (1 << (7-self.bit_position%8))) == 0:
            self.bit_position += 1
            result += "0"
        if len(result) == 0:
            self.bit_position += 1
            return 0
        print(self.bit_position)
        for i in range(len(result)+1):
            if (self.stream[self.bit_position//8] & (1 << (7-self.bit_position%8))) == 0:
                result += "0"
            else : 
                result += "1"
            
            self.bit_position += 1
        return result

def printf(hex): print(f"[{" ".join(f"0x{byte:02x}" for byte in hex)}]")

class slice_layer_without_partitioning_rbsp:
    # 构造方法 __init__
    def __init__(self, hex):
        # printf(hex[:20])
        SliceHeader(hex[:20])
        # 7.3.2.8 Slice layer without partitioning RBSP syntax
        # 7.3.3 Slice header syntax
        # 7.3.4 slice_data( )

class NAL:
    """ 
    network abstract layout 
    7.3.1 NAL unit syntax
    """

    "forbidden_zero_bit shall be equal to 0."
    forbidden_zero_bit = None

    "7.4.1 NAL unit semantics | nal_ref_idc "
    nal_ref_idc = None
    
    "7.4.1 NAL unit semantics | nal_unit_type 不同的type是不同的解码结构体"
    nal_unit_type = None 
    data = []
    def __init__(self, hex):
        self.forbidden_zero_bit = hex[0] >> 7 & 1
        self.nal_ref_idc = hex[0] >> 5 & 3
        self.nal_unit_type = hex[0] & 0x1f
        # data = hex[1:]
        print(self.nal_unit_type, self.nal_ref_idc)
        # if self.nal_unit_type == 5 : # 处理idr帧流
        #     slice_layer_without_partitioning_rbsp(data)
        # return self

class H264: 

    # list: List[NAL] = []

    def setNal(self, hex):
        NAL(hex)

    def __init__(self,filename):
        with open(filename, "rb") as f:
            self.hex = bytearray(f.read())
        hexCount = len(self.hex)
        readCount = 0
        sliceStart = 0  
        while hexCount > readCount:
            if self.hex[readCount] != 0 or self.hex[readCount+1] != 0:
                readCount += 1
                continue
            startCodeLen = 0
            if self.hex[readCount+2] == 0:
                if self.hex[readCount+3] == 1: # 0x00000001 分割。
                    startCodeLen = 4
            elif self.hex[readCount+2] == 1: # 0x000001 分割。
                startCodeLen = 3
            elif self.hex[readCount+2] == 3: # 0x000003透明传输字段 emulation_prevention_three_byte 
                del self.hex[readCount+2] # //处理透明传输
                hexCount -= 1
            if startCodeLen == 0:
                readCount += 1
            else:
                if readCount > 0:
                    self.setNal(self.hex[sliceStart:readCount])
                readCount += startCodeLen
                sliceStart = readCount
        self.setNal(self.hex[sliceStart:readCount])# 最后一个结尾

if __name__ == "__main__":
    H264("runtime/output.h264")
