
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

    def mbAddrN(self, N:str) -> None|MacroBlock:
        if self.CurrMbAddr != 0:
            raise ("mbAddrN")
        return None

    def __init__(self, bs:BitStream, slice_header:SliceHeader):
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
                self.macroblock[self.CurrMbAddr] = MacroBlock(bs, self)
                
                


