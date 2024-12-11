from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from h264_slice_data import SliceData

from h264_bs import BitStream
from h264_define import MbType

class MacroBlock():

    def get_mb_qp_delta_inc(self):
        '''9.3.3.1.1.5'''
        prevMbAddr = self.slice.macroblock.get(self.slice.CurrMbAddr-1)
        ctxIdxInc = 1
        if prevMbAddr == None or \
           prevMbAddr.mb_type.name in ("P_Skip", "B_Skip", "I_PCM") or \
           (
               prevMbAddr.mb_type.MbPartPredMode != "Intra_16x16" and
               prevMbAddr.CodedBlockPatternChroma == 0 and
               prevMbAddr.CodedBlockPatternLuma == 0
           ) or \
           prevMbAddr.mb_qp_delta == 0:
            ctxIdxInc = 0
        return ctxIdxInc

    def get_mb_qp_delta(self):
        if pps.entropy_coding_mode_flag != 1:
            raise ("get_mb_type pps.entropy_coding_mode_flag != 1")
        ctxIdxOffset = 60
        ctxIdxInc = self.get_mb_qp_delta_inc()
        ctxIdx = ctxIdxOffset + ctxIdxInc
        binVal = bs.cabac_decode(False, ctxIdx)
        synElVal = 0
        if binVal == 0:
            synElVal = 0
        else:
            ctxIdx = ctxIdxOffset + 2
            binVal = bs.cabac_decode(False, ctxIdx)
            binIdx = 1

            while binVal == 1:
                ctxIdx = ctxIdxOffset + 3
                binVal = bs.cabac_decode(False, ctxIdx)
                binIdx += 1
            # Table 9-3 se(v)
            if binIdx & 0x01:  # 奇数
                binIdx = (binIdx + 1) >> 1  # (−1)^(k+1) * Ceil(k÷2)
            else:  # 偶数
                binIdx = -(binIdx >> 1)  # (−1)^(k+1) * Ceil(k÷2)
            synElVal = binIdx
        return synElVal

    def get_coded_block_pattern_inc(self, ctxIdxOffset, binIdx):
        '''9.3.3.1.1.4 太过复杂，暂时返回0'''
        # if ctxIdxOffset == 73:
        #     luma8x8BlkIdx = binIdx
        #     xA = (luma8x8BlkIdx % 2) * 8 + (-1)
        #     yA = (luma8x8BlkIdx / 2) * 8 + (0)

        #     mbAddrA = self.slice.macroblock.get(self.slice.CurrMbAddr-1]
        #     condTermFlagA = 1
        #     if not mbAddrA or \
        #         mbAddrA.mb_type.name == 'I_PCM' or \
        #         (   mbAddrA.mb_type.name not in ('P_Skip', 'B_Skip') and \
        #             mbAddrA.CodedBlockPatternLuma >> luma8x8BlkIdxA) & 1) != 0 \
        #         ) or \
        #         mbAddrA.intra_chroma_pred_mode == 0 :
        #         condTermFlagA = 0

        #     mbAddrB = self.slice.macroblock.get(self.slice.CurrMbAddr-1]
        #     ctxIdxInc = condTermFlagA + 2 * condTermFlagB
        # return ctxIdxInc
        return 0

    def get_coded_block_pattern(self):
        '''Table 9-11 '''
        if pps.entropy_coding_mode_flag != 1:
            raise ("get_mb_type pps.entropy_coding_mode_flag != 1")
        ctxIdxOffset = 73

        # 第一个 bin
        binIdx = 0
        ctxIdxInc = self.get_coded_block_pattern_inc(ctxIdxOffset, binIdx)
        ctxIdx = ctxIdxOffset + ctxIdxInc
        binVal = bs.cabac_decode(False, ctxIdx)
        CodedBlockPatternLuma = binVal

        # 第二个 bin (b1)
        binIdx = 1
        ctxIdxInc = self.get_coded_block_pattern_inc(ctxIdxOffset, binIdx)
        ctxIdx = ctxIdxOffset + ctxIdxInc
        binVal = bs.cabac_decode(False, ctxIdx)
        CodedBlockPatternLuma += binVal << 1

        # 第三个 bin (b2)
        binIdx = 2
        ctxIdxInc = self.get_coded_block_pattern_inc(ctxIdxOffset, binIdx)
        ctxIdx = ctxIdxOffset + ctxIdxInc
        binVal = bs.cabac_decode(False, ctxIdx)
        CodedBlockPatternLuma += binVal << 2

        # 第四个 bin (b3)
        binIdx = 3
        ctxIdxInc = self.get_coded_block_pattern_inc(ctxIdxOffset, binIdx)
        ctxIdx = ctxIdxOffset + ctxIdxInc
        binVal = bs.cabac_decode(False, ctxIdx)
        CodedBlockPatternLuma += binVal << 3

        CodedBlockPatternChroma = 0
        if sps.chroma_format_idc not in (1, 3):
            ctxIdxOffset = 77
            binIdx = 0
            ctxIdxInc = self.get_coded_block_pattern_inc(ctxIdxOffset, binIdx)
            ctxIdx = ctxIdxOffset + ctxIdxInc
            binVal = bs.cabac_decode(False, ctxIdx)
            if binVal == 0:
                CodedBlockPatternChroma = 0
            else:
                CodedBlockPatternChroma = 1
                binIdx = 1
                ctxIdxInc = self.get_coded_block_pattern_inc(
                    ctxIdxOffset, binIdx)
                ctxIdx = ctxIdxOffset + ctxIdxInc
                binVal = bs.cabac_decode(False, ctxIdx)
                if binVal == 1:
                    CodedBlockPatternChroma = 2
        return CodedBlockPatternLuma + CodedBlockPatternChroma * 16

    def get_intra_chroma_pred_mode(self):
        if pps.entropy_coding_mode_flag != 1:
            raise ("get_mb_type pps.entropy_coding_mode_flag != 1")
        # Table 9-11
        ctxIdxOffset = 64
        # 9.3.3.1.1.8
        mbAddrA = self.slice.macroblock.get(self.slice.CurrMbAddr-1)
        condTermFlagA = 1
        if not mbAddrA or \
                mbAddrA.mb_type.name.I_PCM == 0 or \
                mbAddrA.intra_chroma_pred_mode == 0:
            condTermFlagA = 0
        mbAddrB = self.slice.macroblock.get(self.slice.CurrMbAddr-16)
        condTermFlagB = 1
        if not mbAddrB or \
                mbAddrB.mb_type.name.I_PCM == 0 or \
                mbAddrB.intra_chroma_pred_mode == 0:
            condTermFlagB = 0
        ctxIdxInc = condTermFlagA + condTermFlagB
        ctxIdx = ctxIdxOffset + ctxIdxInc

        binVal = bs.cabac_decode(False, ctxIdx)
        if binVal == 0:
            synElVal = 0
        else:
            ctxIdx = ctxIdxOffset + 3  # Table 9-39
            binVal = bs.cabac_decode(False, ctxIdx)

        if binVal == 0:  # //10
            synElVal = 1
        else:  # 11
            ctxIdx = ctxIdxOffset + 3  # Table 9-39
            binVal = bs.cabac_decode(False, ctxIdx)

        if binVal == 0:  # 110
            synElVal = 2
        else:  # 111
            synElVal = 3  # TU, cMax=3
        return synElVal

    def mb_pred(self):
        if self.mb_type.MbPartPredMode in ("Intra_4x4", "Intra_8x8", "Intra_16x16"):
            if self.mb_type.MbPartPredMode == "Intra_4x4":
                self.prev_intra4x4_pred_mode_flag = {}
                self.rem_intra4x4_pred_mode = {}
                for luma4x4BlkIdx in range(16):
                    self.prev_intra4x4_pred_mode_flag[luma4x4BlkIdx] = bs.cabac_decode(
                        False, ctxIdx=68)
                    if not self.prev_intra4x4_pred_mode_flag[luma4x4BlkIdx]:
                        self.rem_intra4x4_pred_mode[luma4x4BlkIdx] = bs.cabac_decode(
                            False, ctxIdx=69)
            if self.mb_type.MbPartPredMode == "Intra_8x8":
                if self.slice.slice_type == SliceType.SI:
                    raise ("Table 9-11 mb_pred prev_intra8x8_pred_mode_flag no")
                self.prev_intra8x8_pred_mode_flag = {}
                self.rem_intra8x8_pred_mode = {}
                for luma8x8BlkIdx in range(4):
                    self.prev_intra8x8_pred_mode_flag[luma8x8BlkIdx] = bs.cabac_decode(
                        False, ctxIdx=68)
                    if not self.prev_intra8x8_pred_mode_flag[luma8x8BlkIdx]:
                        self.rem_intra8x8_pred_mode[luma8x8BlkIdx] = bs.cabac_decode(
                            False, ctxIdx=69)

            if sps.chroma_format_idc in (1, 2):
                self.intra_chroma_pred_mode = self.get_intra_chroma_pred_mode()

        elif self.mb_type.MbPartPredMode != "Direct":
            pass

    def get_transform_size_8x8_flag(self):
        '''Table 9-11'''
        if pps.entropy_coding_mode_flag != 1:
            raise ("get_mb_type pps.entropy_coding_mode_flag != 1")
        if self.slice.slice_type != SliceType.I:
            raise ('transform_size_8x8_flag != SliceType.I')
        ctxIdxOffset = 399
        # 6.4.8.1
        # 9.3.3.1.1.10 ctxIdxInc 推导过程
        mbAddrA = self.slice.macroblock.get(self.slice.CurrMbAddr-1)
        condTermFlagA = 1
        if not mbAddrA or \
                mbAddrA.transform_size_8x8_flag == 0:
            condTermFlagA = 0
        mbAddrB = self.slice.macroblock.get(self.slice.CurrMbAddr-1)
        condTermFlagB = 1
        if not mbAddrB or \
                mbAddrB.transform_size_8x8_flag == 0:
            condTermFlagB = 0
        ctxIdxInc = condTermFlagA + condTermFlagB
        ctxIdx = ctxIdxOffset + ctxIdxInc
        binVal = bs.cabac_decode(False, ctxIdx)
        return binVal


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

    def residual_luma(self, i16x16DClevel, i16x16AClevel, level4x4, level8x8, startIdx, endIdx):
        if startIdx == 0 and self.mb_type.MbPartPredMode == "Intra_16x16":
            self.residual_block(i16x16DClevel, 0, 15, 16)
        for i8x8 in range(4):
            if not self.transform_size_8x8_flag or not pps.entropy_coding_mode_flag:
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
                    if not pps.entropy_coding_mode_flag and self.transform_size_8x8_flag:
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

    def residual(self, startIdx, endIdx):
        if pps.entropy_coding_mode_flag != 1:
            raise ("residual_block_cavlc")
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

    def __init__(self, bs: BitStream, slice: SliceData):
        '''
            **处理宏块数据**
            > 什么是宏块。
        '''
        self.mb_type = bs.get_mb_type()

        if self.mb_type.name == "I_PCM":
            raise ("mb_type not support " + str(self.mb_type))
        # print("mb_type",mb_type)
        else:
            noSubMbPartSizeLessThan8x8Flag = 1
            if self.mb_type.name != "I_NxN" and \
               self.mb_type.MbPartPredMode == 'Intra_16x16' and \
               self.mb_type.NumMbPart == 4:
                raise ("mb_type not support 111")
            else:
                if pps.transform_8x8_mode_flag == 1 and \
                   self.mb_type.name == "I_NxN":
                    self.transform_size_8x8_flag = self.get_transform_size_8x8_flag()
                    if self.transform_size_8x8_flag == 1:
                        self.mb_type.MbPartPredMode = "Intra_8x8"
                self.mb_pred()
            # 初始化变量
            self.CodedBlockPatternLuma = 0
            self.CodedBlockPatternChroma = 0
            if self.mb_type.MbPartPredMode != 'Intra_16x16':
                self.coded_block_pattern = self.get_coded_block_pattern()
                self.CodedBlockPatternLuma = self.coded_block_pattern % 16
                self.CodedBlockPatternChroma = self.coded_block_pattern / 16
                if self.CodedBlockPatternLuma > 0 and \
                        pps.transform_8x8_mode_flag and \
                        self.mb_type.name != "I_NxN" and \
                        noSubMbPartSizeLessThan8x8Flag and \
                        (self.mb_type.name != "B_Direct_16x16" or pps.direct_8x8_inference_flag):
                    self.transform_size_8x8_flag = self.get_transform_size_8x8_flag()
            if self.CodedBlockPatternLuma > 0 or \
                    self.CodedBlockPatternChroma > 0 or \
                    self.mb_type.MbPartPredMode == "Intra_16x16":
                self.mb_qp_delta = self.get_mb_qp_delta()
                self.residual(0, 15)
