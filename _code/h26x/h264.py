'CODE logic from <T-REC-H.264-202408-I!!PDF-E.pdf>'


from typing import Generator
from h264_bs import BitStream
from h264_sps import SPS
from h264_pps import PPS
from h264_slice_header import SliceHeader
from h264_slice_data import SliceData
from h264_define import NalUnitType

class H264():
    '''
    从h264中拆分出nalu数据，并进行数据预处理
    '''
    def nal_unit(self, hex):
        # self.hex += hex # 调试nalu对比字节用 
        bs = BitStream(hex, self.sps, self.pps)
        forbidden_zero_bit = bs.read_bits(1)
        if forbidden_zero_bit != 0 :
            raise("forbidden_zero_bit must zero")
        # 当前unit重要程序表示，表示是否可丢弃当前数据。
        nal_ref_idc = bs.read_bits(2)
        nal_unit_type = bs.read_bits(5)
        match nal_unit_type:
            case NalUnitType.IDR:
                slice_header = SliceHeader(bs, self.sps, self.pps, nal_unit_type, nal_ref_idc)
                # print(slice_header.__dict__)
                SliceData(bs, slice_header)
            case NalUnitType.SPS:
                self.sps = SPS(bs)
                # print(self.sps.__dict__)
            case NalUnitType.PPS:
                self.pps = PPS(bs, self.sps)
                # print(self.pps.__dict__)
            # case _:
                # print(f'not support nal_unit_type: {nal_unit_type}')

    def open(self, size) -> Generator[bytearray, None, None]:
        '''
        - size
            对大文件进行分割，单次读取全部数据有可能造成内存泄漏。
            适当调大本值，可以加快文件读取速度。
        '''
        with open(self.filename, "rb") as f:
            # start code prefix 文件开头必须是这样的
            startCode = f.read(3)
            if startCode != bytes([0, 0, 1]):
                if startCode != bytes([0, 0, 0]):
                    raise('start code error:' + startCode)
                else:
                    prefix = f.read(1)
                    if prefix != bytes([1]):
                        raise('start code error:' + startCode + prefix)
            while tmp := f.read(size):
                # 每次读取一块并返回
                yield bytearray(tmp)

    def __init__(self, filename):
        'filename 输入文件必须是h264文件路径'
        self.filename = filename

        # --------->
        self.hex = bytearray()
        self.sps:SPS = None
        self.pps:PPS = None
        # --------->
        
        current_hex = bytearray() # 当前nalu的数据
        # 掐头移除StartCode [000001|00000001]放置open中
        for hex in self.open(1024):
            # - 1 是因为长度对比下标
            hex_len = len(hex) - 1
            # 当前hex读取字节位
            hex_position = 0
            # 数据位读完。
            while hex_len >= hex_position:
                if hex[hex_position] != 0:
                    current_hex += hex[hex_position:hex_position+1]
                    hex_position += 1
                    continue
                # 防止长度溢出。
                if hex_position+1 >= hex_len: 
                    current_hex += hex[hex_position:]
                    break
                if hex[hex_position+1] != 0:
                    current_hex += hex[hex_position:hex_position+2]
                    hex_position += 2
                    continue
                # 防止长度溢出。
                if hex_position+2 >= hex_len: 
                    current_hex += hex[hex_position:]
                    break
                if hex[hex_position+2] == 0:
                    if hex[hex_position+3] == 1:  # 0x00000001 分割。
                        self.nal_unit(current_hex)
                        hex_position += 4
                        # 置为空开始下一次循环迭代
                        current_hex = bytearray() 
                        continue
                    else:
                        raise ('NALU header 0x000000 HIT! 永远不可能出现的场景')
                elif hex[hex_position+2] == 1:  # 0x000001 分割。
                        self.nal_unit(current_hex)
                        hex_position += 3
                        # 置为空开始下一次循环迭代
                        current_hex = bytearray() 
                        continue
                # 7.4.1 NAL unit semantics
                elif hex[hex_position+2] == 2:
                    raise ('NALU header 0x000002 HIT! 永远不可能出现的场景')
                elif hex[hex_position+2] == 3:  
                    # RBSP => SODB; 处理000003的透明传输情况
                    current_hex += hex[hex_position:hex_position+2]
                    hex_position += 3
                else:
                    current_hex += hex[hex_position:hex_position+3]
                    hex_position += 3
        if len(current_hex):
            self.nal_unit(current_hex)
        # 去尾


if __name__ == "__main__":
    nal = H264("_tmp/baseline.h264")
    # FILE_OUT = open(nal.filename + 'rbsp', "wb")
    # FILE_OUT.write(nal.hex)
