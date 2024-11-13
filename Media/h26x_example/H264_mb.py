from __future__ import annotations
from h264_define import BitStream, MbType, SliceType


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from h264_nal import NAL

class MacroBlock():

    def get_coded_block_pattern_inc(self, ctxIdxOffset, binIdx):
        '''9.3.3.1.1.4 太过复杂，暂时返回0'''
        # if ctxIdxOffset == 73: 
        #     luma8x8BlkIdx = binIdx
        #     xA = (luma8x8BlkIdx % 2) * 8 + (-1)
        #     yA = (luma8x8BlkIdx / 2) * 8 + (0)


        #     mbAddrA = self.slice.macroblock[self.slice.CurrMbAddr-1]
        #     condTermFlagA = 1
        #     if not mbAddrA or \
        #         mbAddrA.mb_type.name == 'I_PCM' or \
        #         (   mbAddrA.mb_type.name not in ('P_Skip', 'B_Skip') and \
        #             mbAddrA.CodedBlockPatternLuma >> luma8x8BlkIdxA) & 1) != 0 \
        #         ) or \
        #         mbAddrA.intra_chroma_pred_mode == 0 :
        #         condTermFlagA = 0

        #     mbAddrB = self.slice.macroblock[self.slice.CurrMbAddr-1]
        #     ctxIdxInc = condTermFlagA + 2 * condTermFlagB
        # return ctxIdxInc
        return 0

    def get_coded_block_pattern(self):
        '''Table 9-11 '''
        if self.pps.entropy_coding_mode_flag != 1:
            raise("get_mb_type self.pps.entropy_coding_mode_flag != 1")
        ctxIdxOffset = 73

        # 第一个 bin
        binIdx = 0
        ctxIdxInc = self.get_coded_block_pattern_inc(ctxIdxOffset, binIdx)
        ctxIdx = ctxIdxOffset + ctxIdxInc
        binVal = self.stream.cabac_decode(False, ctxIdx)
        CodedBlockPatternLuma = binVal

        # 第二个 bin (b1)
        binIdx = 1
        ctxIdxInc = self.get_coded_block_pattern_inc(ctxIdxOffset, binIdx)
        ctxIdx = ctxIdxOffset + ctxIdxInc
        binVal = self.stream.cabac_decode(False, ctxIdx)
        CodedBlockPatternLuma += binVal << 1

        # 第三个 bin (b2)
        binIdx = 2
        ctxIdxInc = self.get_coded_block_pattern_inc(ctxIdxOffset, binIdx)
        ctxIdx = ctxIdxOffset + ctxIdxInc
        binVal = self.stream.cabac_decode(False, ctxIdx)
        CodedBlockPatternLuma += binVal << 2

        # 第四个 bin (b3)
        binIdx = 3
        ctxIdxInc = self.get_coded_block_pattern_inc(ctxIdxOffset, binIdx)
        ctxIdx = ctxIdxOffset + ctxIdxInc
        binVal = self.stream.cabac_decode(False, ctxIdx)
        CodedBlockPatternLuma += binVal << 3
        
        CodedBlockPatternChroma = 0
        if self.sps.chroma_format_idc not in (1,3):
            ctxIdxOffset = 77
            binIdx = 0
            ctxIdxInc = self.get_coded_block_pattern_inc(ctxIdxOffset, binIdx)
            ctxIdx = ctxIdxOffset + ctxIdxInc
            binVal = self.stream.cabac_decode(False, ctxIdx)
            if binVal == 0 :
                CodedBlockPatternChroma = 0
            else:
                CodedBlockPatternChroma = 1
                binIdx = 1
                ctxIdxInc = self.get_coded_block_pattern_inc(ctxIdxOffset, binIdx)
                ctxIdx = ctxIdxOffset + ctxIdxInc
                binVal = self.stream.cabac_decode(False, ctxIdx)
                if binVal == 1:
                    CodedBlockPatternChroma = 2
        return CodedBlockPatternLuma + CodedBlockPatternChroma * 16



    def get_intra_chroma_pred_mode(self):
        if self.pps.entropy_coding_mode_flag != 1:
            raise("get_mb_type self.pps.entropy_coding_mode_flag != 1")
        # Table 9-11 
        ctxIdxOffset = 64
        # 9.3.3.1.1.8
        mbAddrA = self.slice.macroblock[self.slice.CurrMbAddr-1]
        condTermFlagA = 1
        if not mbAddrA or \
            mbAddrA.mb_type.name.I_PCM == 0 or \
             mbAddrA.intra_chroma_pred_mode == 0 :
            condTermFlagA = 0
        mbAddrB = self.slice.macroblock[self.slice.CurrMbAddr-1]
        condTermFlagB = 1
        if not mbAddrB or \
            mbAddrB.mb_type.name.I_PCM == 0 or \
            mbAddrB.intra_chroma_pred_mode == 0 :
            condTermFlagB = 0
        ctxIdxInc = condTermFlagA + condTermFlagB 
        ctxIdx = ctxIdxOffset + ctxIdxInc

        binVal = self.stream.cabac_decode(False, ctxIdx)
        if binVal == 0:
            synElVal = 0
        else :
            ctxIdx = ctxIdxOffset + 3; #Table 9-39
            binVal = self.stream.cabac_decode(False, ctxIdx)

        if binVal == 0: #//10
            synElVal = 1 
        else: #11 
            ctxIdx = ctxIdxOffset + 3 #Table 9-39
            binVal = self.stream.cabac_decode(False, ctxIdx)

        if binVal == 0: #110
            synElVal = 2
        else: #111
            synElVal = 3;#TU, cMax=3
        return synElVal

    def mb_pred(self):
        if self.mb_type.MbPartPredMode in ("Intra_4x4",  "Intra_8x8"   "Intra_16x16" ):
            if self.mb_type.MbPartPredMode == "Intra_4x4":
                self.prev_intra4x4_pred_mode_flag = {}
                self.rem_intra4x4_pred_mode = {}
                for luma4x4BlkIdx in range(16):
                    self.prev_intra4x4_pred_mode_flag[luma4x4BlkIdx] = self.stream.cabac_decode(False, ctxIdx = 68)
                    if not self.prev_intra4x4_pred_mode_flag[luma4x4BlkIdx]:
                        self.rem_intra4x4_pred_mode[luma4x4BlkIdx] = self.stream.cabac_decode(False, ctxIdx = 69)
            if self.mb_type.MbPartPredMode == "Intra_8x8":
                if self.slice.slice_type == SliceType.SI:
                    raise("Table 9-11 mb_pred prev_intra8x8_pred_mode_flag no")
                self.prev_intra8x8_pred_mode_flag = {}
                self.rem_intra8x8_pred_mode = {}
                for luma8x8BlkIdx in range(4):
                    self.prev_intra8x8_pred_mode_flag[luma8x8BlkIdx] = self.stream.cabac_decode(False, ctxIdx = 68)
                    if not self.prev_intra8x8_pred_mode_flag[luma8x8BlkIdx]:
                        self.rem_intra8x8_pred_mode[ luma8x8BlkIdx ] = self.stream.cabac_decode(False, ctxIdx = 69)
            if self.pps.chroma_format_idc in (1, 2):
                self.intra_chroma_pred_mode = self.get_intra_chroma_pred_mode()

        elif self.mb_type.MbPartPredMode != "Direct":
            pass

    def get_transform_size_8x8_flag(self):
        '''Table 9-11'''
        if self.pps.entropy_coding_mode_flag != 1:
            raise("get_mb_type self.pps.entropy_coding_mode_flag != 1")
        if self.slice.slice_type != SliceType.I:
            raise('transform_size_8x8_flag != SliceType.I')
        ctxIdxOffset = 399
        # 6.4.8.1 
        # 9.3.3.1.1.10 ctxIdxInc 推导过程
        mbAddrA = self.slice.macroblock[self.slice.CurrMbAddr-1]
        condTermFlagA = 1
        if not mbAddrA or \
            mbAddrA.transform_size_8x8_flag == 0 :
            condTermFlagA = 0
        mbAddrB = self.slice.macroblock[self.slice.CurrMbAddr-1]
        condTermFlagB = 1
        if not mbAddrB or \
            mbAddrB.transform_size_8x8_flag == 0 :
            condTermFlagB = 0
        ctxIdxInc = condTermFlagA + condTermFlagB
        ctxIdx = ctxIdxOffset + ctxIdxInc
        binVal = self.stream.cabac_decode(False, ctxIdx)
        return binVal

    def get_mb_type(self) -> MbType:
        '''6.4.9 说明实现'''
        if self.pps.entropy_coding_mode_flag != 1:
            raise("get_mb_type self.pps.entropy_coding_mode_flag != 1")
        if self.slice.slice_type == SliceType.I:
            ctxIdxOffset = 3
            maxBinIdxCtx = 6
        else:
            raise("mb_type not support " + str(slice.slice_type))
        # 9.3.3.1.1.3 推导mb_type ctxIdxInc 过程
        mbAddrA = self.slice.macroblock[self.slice.CurrMbAddr-1]
        condTermFlagA = 1
        if (not mbAddrA) or \
            (ctxIdxOffset == 0 and mbAddrA.mb_type.name == "SI") or \
            (ctxIdxOffset == 3 and mbAddrA.mb_type.name == "I_NxN") or \
            (ctxIdxOffset == 27 and mbAddrA.mb_type.name in ("B_Skip", "B_Direct_16x16")) :
            condTermFlagA = 0

        mbAddrB = self.slice.macroblock[self.slice.CurrMbAddr-16]
        condTermFlagB = 1
        if (not mbAddrB) or \
            (ctxIdxOffset == 0 and mbAddrB.mb_type.name == "SI") or \
            (ctxIdxOffset == 3 and mbAddrB.mb_type.name == "I_NxN") or \
            (ctxIdxOffset == 27 and mbAddrB.mb_type.name in ("B_Skip", "B_Direct_16x16")) :
            condTermFlagB = 0
        ctxIdxInc = condTermFlagA + condTermFlagB

        # ctxIdx 的增量
        ctxIdx = ctxIdxInc + ctxIdxOffset
        binVal = self.stream.cabac_decode(False, ctxIdx)

        if self.slice.slice_type == SliceType.I:
            # 9.3.2.5 表 9-27－I条带中的宏块类型二值化
            if binVal == 0:  # 0
                synElVal = 0  # I_NxN
            else:  # 1
                # ctxIdx = 276 is used for mb_type where binIdx indicates I_PCM mode
                # For binIdx = 1 in Table 9-39, the value for I/P/SP/B is 276
                ctxIdx = 276
                binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 1

                if binVal == 0:  # 10
                    # In Table 9-39, for binIdx = 2, intra macroblocks for I-slice correspond to 3,
                    # and for P/SP/B slices correspond to 1
                    ctxIdx = ctxIdxOffset + (3 if ctxIdxOffset == 3 else 1)
                    binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 2

                    if binVal == 0:  # 100
                        # In Table 9-39, for binIdx = 3, intra macroblocks for I-slice correspond to 4,
                        # and for P/SP/B slices correspond to 2
                        ctxIdx = ctxIdxOffset + (4 if ctxIdxOffset == 3 else 2)
                        binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 3

                        if binVal == 0:  # 1000
                            # In Table 9-39, for binIdx = 4, the values are derived according to section 9.3.3.1.2
                            if ctxIdxOffset == 3:  # I slice
                                ctxIdx = ctxIdxOffset + 6
                            else:  # P/SP/B slice
                                ctxIdx = ctxIdxOffset + 3

                            binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 4

                            if binVal == 0:  # 10000
                                ctxIdx = ctxIdxOffset + (7 if ctxIdxOffset == 3 else 3)
                                binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 5

                                if binVal == 0:  # 100000
                                    synElVal = 1  # I_16x16_0_0_0
                                else:
                                    synElVal = 2  # I_16x16_1_0_0
                            else:  # 10001
                                ctxIdx = ctxIdxOffset + (7 if ctxIdxOffset == 3 else 3)
                                binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 5

                                if binVal == 0:  # 100010
                                    synElVal = 3  # I_16x16_2_0_0
                                else:
                                    synElVal = 4  # I_16x16_3_0_0
                        else:  # 1001
                            if ctxIdxOffset == 3:  # I slice
                                ctxIdx = ctxIdxOffset + 5
                            else:  # P/SP/B slice
                                ctxIdx = ctxIdxOffset + 2

                            binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 4

                            if binVal == 0:  # 10010
                                ctxIdx = ctxIdxOffset + (6 if ctxIdxOffset == 3 else 3)
                                binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 5

                                if binVal == 0:  # 100100
                                    ctxIdx = ctxIdxOffset + (7 if ctxIdxOffset == 3 else 3)
                                    binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 6

                                    if binVal == 0:  # 1001000
                                        synElVal = 5  # I_16x16_0_1_0
                                    else:
                                        synElVal = 6  # I_16x16_1_1_0
                                else:  # 100101
                                    ctxIdx = ctxIdxOffset + (7 if ctxIdxOffset == 3 else 3)
                                    binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 6

                                    if binVal == 0:  # 1001010
                                        synElVal = 7  # I_16x16_2_1_0
                                    else:
                                        synElVal = 8  # I_16x16_3_1_0
                            else:  # 10011
                                ctxIdx = ctxIdxOffset + (6 if ctxIdxOffset == 3 else 3)
                                binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 5

                                if binVal == 0:  # 100110
                                    ctxIdx = ctxIdxOffset + (7 if ctxIdxOffset == 3 else 3)
                                    binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 6

                                    if binVal == 0:  # 1001100
                                        synElVal = 9  # I_16x16_0_2_0
                                    else:
                                        synElVal = 10  # I_16x16_1_2_0
                                else:  # 100111
                                    ctxIdx = ctxIdxOffset + (7 if ctxIdxOffset == 3 else 3)
                                    binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 6

                                    if binVal == 0:  # 1001110
                                        synElVal = 11  # I_16x16_2_2_0
                                    else:
                                        synElVal = 12  # I_16x16_3_2_0
                    else:  # 101
                        ctxIdx = ctxIdxOffset + (4 if ctxIdxOffset == 3 else 2)
                        binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 3

                        if binVal == 0:  # 1010
                            if ctxIdxOffset == 3:  # I slice
                                ctxIdx = ctxIdxOffset + 6
                            else:  # P/SP/B slice
                                ctxIdx = ctxIdxOffset + 3

                            binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 4

                            if binVal == 0:  # 10100
                                ctxIdx = ctxIdxOffset + (7 if ctxIdxOffset == 3 else 3)
                                binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 5

                                if binVal == 0:  # 101000
                                    synElVal = 13  # I_16x16_0_0_1
                                else:
                                    synElVal = 14  # I_16x16_1_0_1
                            else:  # 10101
                                ctxIdx = ctxIdxOffset + (7 if ctxIdxOffset == 3 else 3)
                                binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 5

                                if binVal == 0:  # 101010
                                    synElVal = 15  # I_16x16_2_0_1
                                else:
                                    synElVal = 16  # I_16x16_3_0_1
                        else:  # 1011
                            ctxIdx = ctxIdxOffset + (5 if ctxIdxOffset == 3 else 2)
                            binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 4

                            if binVal == 0:  # 10110
                                ctxIdx = ctxIdxOffset + (6 if ctxIdxOffset == 3 else 3)
                                binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 5

                                if binVal == 0:  # 101100
                                    ctxIdx = ctxIdxOffset + (7 if ctxIdxOffset == 3 else 3)
                                    binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 6

                                    if binVal == 0:  # 1011000
                                        synElVal = 17  # I_16x16_0_1_1
                                    else:
                                        synElVal = 18  # I_16x16_1_1_1
                                else:  # 101101
                                    ctxIdx = ctxIdxOffset + (7 if ctxIdxOffset == 3 else 3)
                                    binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 6

                                    if binVal == 0:  # 1011010
                                        synElVal = 19  # I_16x16_2_1_1
                                    else:
                                        synElVal = 20  # I_16x16_3_1_1
                            else:  # 10111
                                ctxIdx = ctxIdxOffset + (6 if ctxIdxOffset == 3 else 3)
                                binVal = self.stream.cabac_decode(False, ctxIdx)  # binIdx = 5

            return MbType.I(synElVal)
        else:
            raise("get_mb_type self.slice.slice_type != SliceType.I"); 
        
        # return synElVal

    def __init__(self, nal_slice:NAL, nal_sps:NAL, nal_pps:NAL, stream: BitStream):
        '''
            **处理宏块数据**
            nal_slice 当前nal对象
            nal_sps SPS nal对象
            nal_pps PPS nal对象
            stream 字节流读取对象
        '''
        self.slice = nal_slice
        self.sps = nal_sps
        self.pps = nal_pps
        self.stream = stream

        self.mb_type = self.get_mb_type()

        if self.mb_type.name == "I_PCM":
            raise("mb_type not support " + str(self.mb_type))
        # print("mb_type",mb_type)
        else:
            noSubMbPartSizeLessThan8x8Flag = 1
            if self.mb_type.name != "I_NxN" and \
               self.mb_type.MbPartPredMode == 'Intra_16x16'  and \
               self.mb_type.NumMbPart == 4 :
                raise("mb_type not support 111")
            else:
                if self.pps.transform_8x8_mode_flag == 1 and \
                   self.mb_type.name == "I_NxN":
                    self.transform_size_8x8_flag = self.get_transform_size_8x8_flag()
                    if self.transform_size_8x8_flag == 1:
                        self.mb_type.MbPartPredMode = "Intra_8x8"
                self.mb_pred()
            if self.mb_type.MbPartPredMode == 'Intra_16x16':
                coded_block_pattern = self.get_coded_block_pattern()

