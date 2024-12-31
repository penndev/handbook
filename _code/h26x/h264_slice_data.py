
from h264_define import SliceType
from h264_slice_mb import MacroBlock
from h264_slice_header import SliceHeader
from h264_bs import BitStream

class SliceData:

    def prevMbAddr(self) -> None|MacroBlock:
        if self.CurrMbAddr < 1:
            return None
        else:
            return self.macroblock[self.CurrMbAddr - 1]

    def getMbAddrNAndLuma4x4BlkIdxN(self, xN, yN, maxW, maxH):
        mbAddrN = xw = yW = None
        if xN < 0 and yN < 0:
            mbAddrD = self.CurrMbAddr - self.bs.sps.PicWidthInMbs - 1
            mbAddrN = self.macroblock.get(mbAddrD, None)
        elif xN < 0 and (0 <= yN <= maxH - 1):
            mbAddrA = self.CurrMbAddr - 1
            mbAddrN = self.macroblock.get(mbAddrA, None)
        elif (0 <= xN <= maxW - 1) and yN < 0:
            mbAddrB = self.CurrMbAddr - self.bs.sps.PicWidthInMbs
            mbAddrN = self.macroblock.get(mbAddrB, None)
        elif xN > maxW - 1 and yN < 0:
            mbAddrC = self.CurrMbAddr - self.bs.sps.PicWidthInMbs + 1
            if (self.CurrMbAddr + 1) % self.bs.sps.PicWidthInMbs == 0:
                mbAddrN = None
            else:
                mbAddrN = self.macroblock.get(mbAddrC, None)
        elif (0 <= xN <= maxW - 1) and (0 <= yN <= maxH - 1):
            mbAddrN = self.macroblock.get(self.CurrMbAddr, None)
        xw = (xN + maxW) % maxW
        yW = (yN + maxH) % maxH
        return mbAddrN, xw, yW


    def mbAddrN(self, N:str) -> None|MacroBlock:
        '''
        @param N: 用于判断当前宏块是否为N宏块
            - A 用于判断当前宏块是否为左侧宏块
            - B 用于判断当前宏块是否为上侧宏块
            - C 用于判断当前宏块是否为左上侧宏块
            - D 用于判断当前宏块是否为右上侧宏块
        '''
        if self.CurrMbAddr != 0:
            raise ("mbAddrN")
        return None

    def __init__(self, bs:BitStream, slice_header:SliceHeader):
        self.bs = bs
        self.header = slice_header

        if bs.pps.entropy_coding_mode_flag:
            while not bs.byte_aligned():
                if 1 != bs.read_bits(1):
                    raise ('slice_data cabac_alignment_one_bit')
            bs.cabac_init_context_variables(
                    slice_header.slice_type,   
                    slice_header.cabac_init_idc,
                    slice_header.SliceQPY 
            )
            bs.cabac_inti_arithmetic_decoding_engine()

        self.CurrMbAddr = slice_header.first_mb_in_slice * (1 + slice_header.MbaffFrameFlag)
        moreDataFlag = 1
        prevMbSkipped = 0

        self.macroblock: dict[int, MacroBlock] = {}
        while True:
            if slice_header.slice_type not in [SliceType.I, SliceType.SI]:
                raise ("SliceType" + slice_header.slice_type)
            if moreDataFlag:
                if slice_header.MbaffFrameFlag and (self.CurrMbAddr%2== 0 or (self.CurrMbAddr%2==1 and prevMbSkipped )):
                    raise ("mb_field_decoding_flag")
                print("self.CurrMbAddr", self.CurrMbAddr)
                # 这样会在当前获取当前的 index为null
                # self.macroblock[self.CurrMbAddr] = MacroBlock(bs, self)
                MacroBlock(bs, self)
                
                


