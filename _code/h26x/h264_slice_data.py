
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
            if self.CurrMbAddr % self.bs.sps.PicWidthInMbs != 0:
                mbAddrD = self.CurrMbAddr - self.bs.sps.PicWidthInMbs - 1
                mbAddrN = self.macroblock.get(mbAddrD, None)
        elif xN < 0 and (0 <= yN <= maxH - 1):
            if self.CurrMbAddr % self.bs.sps.PicWidthInMbs != 0:
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
    
    def NextMbAddress(self, n:int) -> int:
        i = n + 1
        if n >= self.header.PicSizeInMbs:
            raise ("i >= slice_header.PicSizeInMbs")
        # while i < self.header.PicSizeInMbs and self.header.MbToSliceGroupMap[i] != self.header.MbToSliceGroupMap[n]:
        #     i += 1
        # print("self.header.PicSizeInMbs", self.header.PicSizeInMbs)
        # exit(0)
        return i

    def __init__(self, bs:BitStream, slice_header:SliceHeader):
        self.bs = bs
        self.header = slice_header

        self.QPY_prev = slice_header.SliceQPY # 逻辑计算

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
        moreDataFlag = True
        prevMbSkipped = 0
        mb_skip_flag = False
        self.macroblock: dict[int, MacroBlock] = {}
        while True:
            if slice_header.slice_type not in [SliceType.I, SliceType.SI]:
                raise ("SliceType" + slice_header.slice_type)
            if moreDataFlag:
                if slice_header.MbaffFrameFlag and (self.CurrMbAddr%2== 0 or (self.CurrMbAddr%2==1 and prevMbSkipped )):
                    raise ("mb_field_decoding_flag")
                # 这样会在当前获取当前的 index为null
                # self.macroblock[self.CurrMbAddr] = MacroBlock(bs, self)
                print("self.CurrMbAddr", self.CurrMbAddr)
                MacroBlock(bs, self)
                self.macroblock[self.CurrMbAddr].Parse()


            if not bs.pps.entropy_coding_mode_flag:
                moreDataFlag = bs.more_rbsp_data()
            else:
                if slice_header.slice_type not in [SliceType.I, SliceType.SI]:
                    prevMbSkipped = mb_skip_flag
                if( slice_header.MbaffFrameFlag and self.CurrMbAddr % 2 == 0 ):
                    moreDataFlag = 1
                else:
                    end_of_slice_flag = bs.end_of_slice_flag()
                    moreDataFlag = not end_of_slice_flag
            self.CurrMbAddr = self.NextMbAddress( self.CurrMbAddr )
            if not moreDataFlag:
                break
        print("结束")