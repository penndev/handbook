from __future__ import annotations
from typing import Self
from enum import Enum, IntEnum

class ChromaType(IntEnum):
    Blue = 0
    '''色度cb 蓝'''
    Red = 1
    '''色度cr 红'''

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

    def isInterProd(self):
        '''判断是否是帧间预测'''
        return self.MbPartPredMode in ('Pred_L0', 'Pred_L1', 'BiPred')


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

class MbPredMode(Enum):
    '''宏块预测模型'''
    Intra_4x4 = 0
    Intra_8x8 = 1
    Intra_16x16 = 2

    def Block4x4ZigzagScan(o: dict[int, int]) -> dict[int, dict[int]]:
        '''
        将一维数组的字典形式按照 Zigzag 扫描顺序转化为 4x4 的嵌套字典形式
            >Figure 8-8  4x4 block scans. (a) Zig-zag scan. (b) Field scan (informative)

        @param o: 包含 16 个元素的一维数组，以索引为键的字典形式
        @return: 嵌套字典形式，外层键为行索引，内层键为列索引
        '''
        
        zigzag_order = [
            0, 1, 5, 6,
            2, 4, 7, 12,
            3, 8, 11, 13,
            9, 10, 14, 15
        ]
        c = {i: {} for i in range(4)}
        for index, zigzag_index in enumerate(zigzag_order):
            row = index // 4
            col = index % 4
            c[row][col] = o.get(zigzag_index, 0)
        return c

    def Block8x8ZigzagScan(o: dict[int, int]) -> dict[int, dict[int]]:
        '''
        将一维数组的字典形式按照 Zigzag 扫描顺序转化为 8x8 的嵌套字典形式
            >Figure 8-9  8x8 block scans. (a) Zig-zag scan. (b) Field scan (informative)

        @param o: 包含 64 个元素的一维数组，以索引为键的字典形式
        @return: 嵌套字典形式，外层键为行索引，内层键为列索引
        '''
        zigzag_order = [
            0, 1, 5, 6, 14, 15, 27, 28,
            2, 4, 7, 13, 16, 26, 29, 42,
            3, 8, 12, 17, 25, 30, 41, 43,
            9, 11, 18, 24, 31, 40, 44, 53,
            10, 19, 23, 32, 39, 45, 52, 54,
            20, 22, 33, 38, 46, 51, 55, 60,
            21, 34, 37, 47, 50, 56, 59, 61,
            35, 36, 48, 49, 57, 58, 62, 63
        ]
        c = {i: {} for i in range(8)}
        for index, zigzag_index in enumerate(zigzag_order):
            row = index // 8
            col = index % 8
            c[row][col] = o.get(zigzag_index, 0)

        return c

class Intra4x4PredMode(IntEnum):
    '''
        4x4 帧内预测的类型
    '''
    Intra_4x4_Vertical = 0
    Intra_4x4_Horizontal = 1
    Intra_4x4_DC = 2
    Intra_4x4_Diagonal_Down_Left = 3
    Intra_4x4_Diagonal_Down_Right = 4
    Intra_4x4_Vertical_Right = 5
    Intra_4x4_Horizontal_Down = 6
    Intra_4x4_Vertical_Left = 7
    Intra_4x4_Horizontal_Up = 8


