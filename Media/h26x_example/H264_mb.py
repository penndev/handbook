from __future__ import annotations
from h264_define import BitStream, MbType, SliceType


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from h264_nal import NAL

class MacroBlock():

    def mb_type(self):
        '''6.4.9 说明实现'''
        if self.slice.slice_type == SliceType.I:
            ctxIdxOffset = 3
            maxBinIdxCtx = 6
        else:
            raise("mb_type not support " + str(slice.slice_type))
        # 9.3.3.1.1.3 推导过程
        condTermFlagA = 1
        if True: 
            condTermFlagA = 0
        condTermFlagB = 1
        if True: 
            condTermFlagB = 0

        # ctxIdx 的增量
        ctxIdxInc = condTermFlagA + condTermFlagB
        ctxIdx = ctxIdxInc + ctxIdxOffset
        binVal = self.stream.cabac_decode(False, ctxIdx)
        # 表 9-27－I条带中的宏块类型二值化
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
        return synElVal

    def transform_size_8x8_flag(self):
        '''
        9.3.3.1.1.10 ctxIdxInc 推导过程
        '''
        

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
        NumMbPart = 0
        if self.pps.entropy_coding_mode_flag:
            if self.slice.slice_type == SliceType.I:
                mb_type = self.mb_type()
                if mb_type == MbType.I_PCM:
                    raise("mb_type not support " + str(mb_type))
                # print("mb_type",mb_type)
                else:
                    noSubMbPartSizeLessThan8x8Flag = 1
                    if mb_type != MbType.I_NxN and \
                    (mb_type < 1 or mb_type > 24) and \
                    NumMbPart == 4 :
                        raise("mb_type not support 111")
                    else:
                        if self.pps.transform_8x8_mode_flag == 1 and  mb_type == MbType.I_NxN:
                            raise("mb_type not support 222")
                        
            else:
                raise("slice_type not support " + str(self.slice.slice_type))