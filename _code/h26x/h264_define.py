from __future__ import annotations
from typing import Self
from enum import Enum


class NalUnitType(Enum):
    '''
    NAL unit type 类型说明。
    Table 7-1  文档进行了详细说明。
    '''
    
    IDR = 5
    '5 - slice_layer_without_partitioning_rbsp 图像编码条带'
    SPS = 7
    '7 - seq_parameter_set_rbsp 序列参数集 '
    PPS = 8
    '8 - pic_parameter_set_rbsp 图像参数集'

    def __eq__(self, other):
        if isinstance(other, int):
            return self.value == other
        return False


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


class MbType():
    NA = -1

    def __init__(self, mb_type, NameOfMbType, MbPartPredMode, NumMbPart=None, Intra16x16PredMode=None, CodedBlockPatternChroma=None, CodedBlockPatternLuma=None):
        self.mb_type = mb_type
        self.name = NameOfMbType
        self.MbPartPredMode = MbPartPredMode
        self.NumMbPart = NumMbPart
        self.Intra16x16PredMode = Intra16x16PredMode
        self.CodedBlockPatternChroma = CodedBlockPatternChroma
        self.CodedBlockPatternLuma = CodedBlockPatternLuma

    @staticmethod
    def I(mb_type) -> Self:
        '''
            Table 7-11
        '''
        if mb_type == 0:
            return MbType(mb_type, "I_NxN", "Intra_4x4")
        elif mb_type == 5:
            return MbType(mb_type, "I_16x16_0_1_0", "Intra_16x16", None, 0, 1, 0)
        elif mb_type == 7:
            return MbType(mb_type, "I_16x16_2_1_0", "Intra_16x16", None, 2, 1, 0)
        elif mb_type == 8:
            return MbType(mb_type, "I_16x16_3_1_0", "Intra_16x16", None, 3, 1, 0)
        elif mb_type == 13:
            return MbType(mb_type, "I_16x16_0_0_1", "Intra_16x16", None, 0, 0, 15)
        elif mb_type == 17:
            return MbType(mb_type, "I_16x16_0_1_1", "Intra_16x16", None, 0, 1, 15)
        else:
            raise Exception("MbType i mb_type" + str(mb_type))

