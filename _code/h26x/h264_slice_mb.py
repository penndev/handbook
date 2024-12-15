from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from h264_slice_data import SliceData

from h264_define import SliceType
from h264_bs import BitStream

class MacroBlock():

    def get_coded_block_flag(self):
        # //9.3.3.1.1.9  ctxIdxInc
        '''Table 9-11'''
        if pps.entropy_coding_mode_flag != 1:
            raise ("get_mb_type pps.entropy_coding_mode_flag != 1")
        if self.slice.slice_type != SliceType.I:
            raise ('transform_size_8x8_flag != SliceType.I')
        pass

    def residual_block_cabac(self, coeffLevel, startIdx, endIdx, maxNumCoeff):
        if maxNumCoeff != 64 and sps.chroma_format_idc == 3:
            # 是否存在非零的变换系数
            coded_block_flag = self.get_coded_block_flag()

        raise ("residual_block_cabac")

 

    def __init__(self, bs: BitStream, slice: SliceData):
        '''
            **处理宏块数据**
            > 什么是宏块。
        '''
        self.mb_type = bs.mb_type(slice)
        self.transform_size_8x8_flag = 0
        if self.mb_type.name == "I_PCM":
            raise ("I_PCM 不经过预测，变换，量化, 直接解码")
        else:
            noSubMbPartSizeLessThan8x8Flag = 1
            if self.mb_type.name != "I_NxN" and self.mb_type.MbPartPredMode == 'Intra_16x16' and self.mb_type.NumMbPart == 4:
                raise ("子宏块分割未实现")
            else:
                if bs.pps.transform_8x8_mode_flag == 1 and  self.mb_type.name == "I_NxN":
                    self.transform_size_8x8_flag = bs.transform_size_8x8_flag()
                    if self.transform_size_8x8_flag == 1:
                        self.mb_type.MbPartPredMode = "Intra_8x8"
                self.mb_pred(bs, slice)
            # 初始化变量
            self.CodedBlockPatternLuma = 0
            self.CodedBlockPatternChroma = 0
            if self.mb_type.MbPartPredMode != 'Intra_16x16':
                self.coded_block_pattern = bs.coded_block_pattern(slice, self)
                self.CodedBlockPatternLuma = self.coded_block_pattern % 16
                self.CodedBlockPatternChroma = self.coded_block_pattern / 16
                if self.CodedBlockPatternLuma > 0 and \
                        bs.pps.transform_8x8_mode_flag and \
                        self.mb_type.name != "I_NxN" and \
                        noSubMbPartSizeLessThan8x8Flag and \
                        (self.mb_type.name != "B_Direct_16x16" or bs.pps.direct_8x8_inference_flag):
                    self.transform_size_8x8_flag = bs.transform_size_8x8_flag()
            if self.CodedBlockPatternLuma > 0 or self.CodedBlockPatternChroma > 0 or self.mb_type.MbPartPredMode == "Intra_16x16":
                self.mb_qp_delta = bs.mb_qp_delta(slice)
                self.residual(0, 15)

    def mb_pred(self, bs: BitStream, slice: SliceData):
        if self.mb_type.MbPartPredMode in ("Intra_4x4", "Intra_8x8", "Intra_16x16"):
            if self.mb_type.MbPartPredMode == "Intra_4x4":
                self.prev_intra4x4_pred_mode_flag = {}
                self.rem_intra4x4_pred_mode = {}
                for luma4x4BlkIdx in range(16):
                    self.prev_intra4x4_pred_mode_flag[luma4x4BlkIdx] = bs.cabac_decode(False, ctxIdx=68) if bs.pps.entropy_coding_mode_flag else  bs.read_bits(1)
                    if not self.prev_intra4x4_pred_mode_flag[luma4x4BlkIdx]:
                        self.rem_intra4x4_pred_mode[luma4x4BlkIdx] = bs.cabac_decode(False, ctxIdx=69) if bs.pps.entropy_coding_mode_flag else  bs.read_bits(1)
            if self.mb_type.MbPartPredMode == "Intra_8x8":
                if slice.header.slice_type == SliceType.SI:
                    raise ("Table 9-11 mb_pred prev_intra8x8_pred_mode_flag no")
                self.prev_intra8x8_pred_mode_flag = {}
                self.rem_intra8x8_pred_mode = {}
                for luma8x8BlkIdx in range(4):
                    self.prev_intra8x8_pred_mode_flag[luma8x8BlkIdx] = bs.cabac_decode(False, ctxIdx=68) if bs.pps.entropy_coding_mode_flag else  bs.read_bits(1)
                    if not self.prev_intra8x8_pred_mode_flag[luma8x8BlkIdx]:
                        self.rem_intra8x8_pred_mode[luma8x8BlkIdx] = bs.cabac_decode(False, ctxIdx=69) if bs.pps.entropy_coding_mode_flag else  bs.read_bits(1)

            if bs.sps.chroma_format_idc in (1, 2):
                self.intra_chroma_pred_mode = bs.intra_chroma_pred_mode(slice)

        elif self.mb_type.MbPartPredMode != "Direct":
            raise ("self.mb_type.MbPartPredMode != Direct")

    def residual_block_cavlc(self, coeffLevel, startIdx, endIdx, maxNumCoeff, bs:BitStream, slice:SliceData):
        

    def residual(self, startIdx, endIdx, bs:BitStream, slice:SliceData):
        if bs.pps.entropy_coding_mode_flag != 1:
            self.residual_block = self.residual_block_cavlc
        else:
            self.residual_block = self.residual_block_cabac

        Intra16x16DCLevel, Intra16x16ACLevel, LumaLevel4x4, LumaLevel8x8 = self.residual_luma(
            i16x16DClevel={},
            i16x16AClevel={},
            level4x4={},
            level8x8={},
            startIdx=startIdx,
            endIdx=endIdx
        )
        print(Intra16x16DCLevel, Intra16x16ACLevel, LumaLevel4x4, LumaLevel8x8)
        exit("i am here ready finish")
    
    def residual_luma(self, i16x16DClevel, i16x16AClevel, level4x4, level8x8, startIdx, endIdx, bs:BitStream, slice:SliceData):
        if startIdx == 0 and self.mb_type.MbPartPredMode == "Intra_16x16":
            self.residual_block(i16x16DClevel, 0, 15, 16)
        for i8x8 in range(4):
            if not self.transform_size_8x8_flag or not bs.pps.entropy_coding_mode_flag:
                for i4x4 in range(4):
                    if self.CodedBlockPatternLuma & (1 << i8x8):
                        if self.mb_type.MbPartPredMode == "Intra_16x16":
                            self.residual_block(
                                i16x16AClevel[i8x8 * 4 + i4x4], max(0, startIdx - 1), endIdx - 1, 15)
                        else:
                            self.residual_block(
                                level4x4[i8x8 * 4 + i4x4], startIdx, endIdx, 16)
                    elif self.mb_type.MbPartPredMode == "Intra_16x16":
                        for i in range(15):
                            level4x4[i8x8 * 4 + i4x4][i] = 0
                    else:
                        for i in range(16):
                            level4x4[i8x8 * 4 + i4x4][i] = 0
                    if not bs.pps.entropy_coding_mode_flag and self.transform_size_8x8_flag:
                        for i in range(16):
                            level8x8[i8x8][4 * i +
                                           i4x4] = level4x4[i8x8 * 4 + i4x4][i]
            elif self.CodedBlockPatternLuma & (1 << i8x8):
                self.residual_block(
                    level8x8.get(i8x8), 4 * startIdx, 4 * endIdx + 3, 64)
            else:
                for i in range(64):
                    level8x8[i8x8][i] = 0
        return i16x16DClevel, i16x16AClevel, level4x4, level8x8

