
from typing import List


def printf(hex): print(f"[{' '.join(f"0x{byte:02x}" for byte in hex)}]")

class slice_layer_without_partitioning_rbsp:
    # 构造方法 __init__
    def __init__(self, hex):
        printf(hex[:20])
        print("===")
        # 7.3.2.8 Slice layer without partitioning RBSP syntax
        # 7.3.3 Slice header syntax
        # 7.3.4 slice_data( )


class NAL:
    ''' 
    network abstract layout 
    7.3.1 NAL unit syntax
    '''

    'forbidden_zero_bit shall be equal to 0.'
    forbidden_zero_bit = None

    '7.4.1 NAL unit semantics | nal_ref_idc '
    nal_ref_idc = None
    
    '7.4.1 NAL unit semantics | nal_unit_type 不同的type是不同的解码结构体'
    nal_unit_type = None 
    data = []
    def setNALU(self, hex):
        self.forbidden_zero_bit = hex[0] >> 7 & 1
        self.nal_ref_idc = hex[0] >> 5 & 3
        self.nal_unit_type = hex[0] & 0x1f
        data = hex[1:]
        if self.nal_unit_type == 5 : # 处理idr帧流
            slice_layer_without_partitioning_rbsp(data)
        return self

class H264: 
    list: List[NAL] = []
    def setFile(self,filename):
        with open(filename, 'rb') as f:
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
                    self.list.append(NAL().setNALU(self.hex[sliceStart:readCount]))
                readCount += startCodeLen
                sliceStart = readCount
        # 最后一个结尾
        self.list.append(NAL().setNALU(self.hex[sliceStart:readCount]))
        
            

if __name__ == "__main__":
    v = H264()
    v.setFile("./vfile/output.h264")
    for e in v.list:
        print("nal-> ", e.forbidden_zero_bit, e.nal_ref_idc, e.nal_unit_type)