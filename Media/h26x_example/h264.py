'CODE logic from <T-REC-H.264-202108-I!!PDF-E.pdf>'

from typing import Generator
from h264_nal import NAL
from h264_define import BitStream

class H264(): 
    '''
    B.1 Byte stream NAL unit syntax and semantics
    '''
    def nal_unit(self, hex):
        if len(hex) == 0: # 头字节引起
            return
        # self.hex = self.hex + hex
        # return
        nal = NAL(BitStream(hex), sps=self.sps_nalu, pps=self.pps_nalu)
        if nal.nal_unit_type == 7:
            self.sps_nalu = nal
        if nal.nal_unit_type == 8:
            self.pps_nalu = nal

    def read_h264(self) -> Generator[bytearray, None, None] :
        with open(self.filename, "rb") as f:
            while chunk := f.read(self.chunk_size):
                yield bytearray(chunk)  # 每次读取一块并返回

    def __init__(self,filename):
        self.sps_nalu = None
        self.pps_nalu = None

        self.hex = bytearray()
        'filename 输入文件必须是h264文件'
        self.filename = filename
        
        # 开始分割
        self.chunk_size = 1024
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
