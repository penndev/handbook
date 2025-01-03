from __future__ import annotations
from typing import Self

from h264_bs import BitStream

class SPS():
    Default_4x4_Intra = [6, 13, 13, 20, 20, 20, 28, 28, 28, 28, 32, 32, 32, 37, 37, 42]
    
    Default_4x4_Inter = [10, 14, 14, 20, 20, 20, 24, 24, 24, 24, 27, 27, 27, 30, 30, 34]

    Default_8x8_Intra = [
        6, 10, 10, 13, 11, 13, 16, 16, 16, 16, 18, 18, 18, 18, 18, 23,
        23, 23, 23, 23, 23, 25, 25, 25, 25, 25, 25, 25, 27, 27, 27, 27,
        27, 27, 27, 27, 29, 29, 29, 29, 29, 29, 29, 31, 31, 31, 31, 31,
        31, 33, 33, 33, 33, 33, 36, 36, 36, 36, 38, 38, 38, 40, 40, 42
    ]

    Default_8x8_Inter = [
        9, 13, 13, 15, 13, 15, 17, 17, 17, 17, 19, 19, 19, 19, 19, 21,
        21, 21, 21, 21, 21, 22, 22, 22, 22, 22, 22, 22, 24, 24, 24, 24,
        24, 24, 24, 24, 25, 25, 25, 25, 25, 25, 25, 27, 27, 27, 27, 27,
        27, 28, 28, 28, 28, 28, 30, 30, 30, 30, 32, 32, 32, 33, 33, 35
    ]

    @staticmethod
    def scaling_list(bs: BitStream, size_of_scaling_list):
        use_default_scaling_matrix_flag = False
        last_scale = 8
        next_scale = 8
        scaling_list = {}
        for j in range(size_of_scaling_list):
            if next_scale != 0:
                delta_scale = bs.read_se()
                next_scale = (last_scale + delta_scale + 256) % 256
                use_default_scaling_matrix_flag = (j == 0 and next_scale == 0)
            scaling_list[j] = last_scale if next_scale == 0 else next_scale
            last_scale = scaling_list[j]
        return scaling_list, use_default_scaling_matrix_flag

    def hrd_parameters(self, bs: BitStream):
        self.cpb_cnt_minus1 = bs.read_ue()
        self.bit_rate_scale = bs.read_bits(4)
        self.cpb_size_scale = bs.read_bits(4)
        self.bit_rate_value_minus1 = []
        self.cpb_size_value_minus1 = []
        self.cbr_flag = []
        for _ in range(self.cpb_cnt_minus1 + 1):
            self.bit_rate_value_minus1.append(bs.read_uev())
            self.cpb_size_value_minus1.append(bs.read_uev())
            self.cbr_flag.append(bs.read_bits(1))
        self.initial_cpb_removal_delay_length_minus1 = bs.read_bits(5)
        self.cpb_removal_delay_length_minus1 = bs.read_bits(5)
        self.dpb_output_delay_length_minus1 = bs.read_bits(5)
        self.time_offset_length = bs.read_bits(5)

    def __init__(self, bs:BitStream):
        self.profile_idc = bs.read_bits(8)
        'profile_idc level_idc 在附件A中给出规定。验证是否符合解码要求'
        self.constraint_set0_flag = bs.read_bits(1)
        self.constraint_set1_flag = bs.read_bits(1)
        self.constraint_set2_flag = bs.read_bits(1)
        self.constraint_set3_flag = bs.read_bits(1)
        self.constraint_set4_flag = bs.read_bits(1)
        self.constraint_set5_flag = bs.read_bits(1)
        self.reserved_zero_2bits = bs.read_bits(2)
        self.level_idc = bs.read_bits(8)
        self.seq_parameter_set_id = bs.read_ue()

        # 赋予默认值
        self.chroma_format_idc = 1
        '''
        0 只有亮度无色度的意思
        1 4:2:0 采样
        2 4:2:2 
        3 4:4:4
        '''
        self.separate_colour_plane_flag = 0
        '当 4:4:4 此标志位用来处理色彩展示方式'
        self.bit_depth_luma_minus8 = 0
        self.bit_depth_chroma_minus8 = 0
        self.qpprime_y_zero_transform_bypass_flag = 0
        self.seq_scaling_matrix_present_flag = 0
        # self.
        self.scaling_list_4x4 = {}
        self.scaling_list_8x8 = {}
        # 默认赋值完成
        
        if self.profile_idc in (100, 110, 122, 244, 44, 83, 86, 118, 128, 138, 139, 134, 135):
            self.chroma_format_idc = bs.read_ue()
            if self.chroma_format_idc == 3:
                self.separate_colour_plane_flag = bs.read_bits(1)
            self.bit_depth_luma_minus8 = bs.read_ue()
            self.bit_depth_chroma_minus8 = bs.read_ue()

            self.qpprime_y_zero_transform_bypass_flag = bs.read_bits(1)
            self.seq_scaling_matrix_present_flag = bs.read_bits(1)

            if self.seq_scaling_matrix_present_flag == 1:
                seq_scaling_list_present_flag = {}
                for i in range(8 if self.chroma_format_idc != 3 else 12):
                    seq_scaling_list_present_flag[i] = bs.read_bits(1)
                    if seq_scaling_list_present_flag[i]:
                        if i < 6:
                            self.scaling_list_4x4[i],
                            useDefaultScalingMatrixFlag = self.scaling_list(bs, 16)
                            if useDefaultScalingMatrixFlag:
                                self.scaling_list_4x4[i] = SPS.Default_4x4_Intra if i in (0,1,2) else \
                                                           SPS.Default_4x4_Inter
                        else:
                            self.scaling_list_8x8[i],
                            useDefaultScalingMatrixFlag = self.scaling_list(bs, 64)
                            if useDefaultScalingMatrixFlag:
                                self.scaling_list_8x8[i] = SPS.Default_8x8_Intra if i in (6,8,10) else \
                                                           SPS.Default_8x8_Inter
                    else:
                        if i < 6:
                            self.scaling_list_4x4[i] = SPS.Default_4x4_Intra if i in (0,1,2) else \
                                                           SPS.Default_4x4_Inter
                        else:
                            self.scaling_list_8x8[i] = SPS.Default_8x8_Intra if i in (6,8,10) else \
                                                           SPS.Default_8x8_Inter
        
        self.ChromaArrayType = self.chroma_format_idc
        self.SubWidthC = None
        self.SubHeightC = None
        if self.chroma_format_idc == 1:
            self.SubWidthC = 2
            self.SubHeightC = 2
        elif self.chroma_format_idc == 2:
            self.SubWidthC = 2
            self.SubHeightC = 1
        elif self.chroma_format_idc == 3:
            self.SubWidthC = 1
            self.SubHeightC = 1

        self.MbWidthC = 16 // self.SubWidthC
        self.MbHeightC = 16 // self.SubHeightC

        # Table 6-1 – SubWidthC, and SubHeightC values derived from chroma_format_idc and separate_colour_plane_flag


        # 亮度和色度的比特深度
        self.BitDepthY = 8 + self.bit_depth_luma_minus8
        self.QpBdOffsetY = 6 * self.bit_depth_luma_minus8
        self.BitDepthC = 8 + self.bit_depth_chroma_minus8
        self.QpBdOffsetC = 6 * self.bit_depth_chroma_minus8
        #

        self.log2_max_frame_num_minus4 = bs.read_ue()
        # 用于计算图像的大小
        self.pic_order_cnt_type = bs.read_ue()
        if self.pic_order_cnt_type == 0:
            self.log2_max_pic_order_cnt_lsb_minus4 = bs.read_ue()
        elif self.pic_order_cnt_type == 1:
            self.delta_pic_order_always_zero_flag = bs.read_bits(1)
            self.offset_for_non_ref_pic = bs.read_ue()
            self.offset_for_top_to_bottom_field = bs.read_ue()
            self.num_ref_frames_in_pic_order_cnt_cycle = bs.read_ue()
            self.offset_for_ref_frame = {}
            for i in range(self.num_ref_frames_in_pic_order_cnt_cycle):
                self.offset_for_ref_frame[1] = bs.read_se()
        self.num_ref_frames = bs.read_ue()
        'num_ref_frames 用于计算图像的大小'
        self.gaps_in_frame_num_value_allowed_flag = bs.read_bits(1)
        self.pic_width_in_mbs_minus1 = bs.read_ue()
        '是以宏块为单位的图像宽度'
        self.pic_height_in_map_units_minus1 = bs.read_ue()
        '是以条块为单位的图像高度'



        self.mb_adaptive_frame_field_flag = 0
        '是否是帧场自适应'
        self.frame_mbs_only_flag = bs.read_bits(1)
        '是否是帧编码'
        if self.frame_mbs_only_flag != 1:
            self.mb_adaptive_frame_field_flag = bs.read_bits(1)
        self.direct_8x8_inference_flag = bs.read_bits(1)
        self.frame_cropping_flag = bs.read_bits(1)
        if self.frame_cropping_flag == 1:
            self.frame_crop_left_offset = bs.read_ue()
            self.frame_crop_right_offset = bs.read_ue()
            self.frame_crop_top_offset = bs.read_ue()
            self.frame_crop_bottom_offset = bs.read_ue()
        self.vui_parameters_present_flag = bs.read_bits(1)
        if self.vui_parameters_present_flag == 1:
            self.aspect_ratio_info_present_flag = bs.read_bits(1)
            if self.aspect_ratio_info_present_flag:
                self.aspect_ratio_idc = bs.read_bits(8)
                if self.aspect_ratio_idc == 255:
                    self.sar_width = bs.read_bits(16)
                    self.sar_height = bs.read_bits(16)
            self.overscan_info_present_flag = bs.read_bits(1)
            if self.overscan_info_present_flag:
                self.overscan_appropriate_flag = bs.read_bits(1)
            self.video_signal_type_present_flag = bs.read_bits(1)
            if self.video_signal_type_present_flag:
                self.video_format = bs.read_bits(3)
                self.video_full_range_flag = bs.read_bits(1)
                self.colour_description_present_flag = bs.read_bits(1)
                if self.colour_description_present_flag:
                    self.colour_primaries = bs.read_bits(8)
                    self.transfer_characteristics = bs.read_bits(8)
                    self.matrix_coefficients = bs.read_bits(8)
            self.chroma_loc_info_present_flag = bs.read_bits(1)
            if self.chroma_loc_info_present_flag:
                self.chroma_sample_loc_type_top_field = bs.read_ue()
                self.chroma_sample_loc_type_bottom_field = bs.read_ue()
            self.timing_info_present_flag = bs.read_bits(1)
            if self.timing_info_present_flag:
                self.num_units_in_tick = bs.read_bits(32)
                self.time_scale = bs.read_bits(32)
                self.fixed_frame_rate_flag = bs.read_bits(1)

            self.nal_hrd_parameters_present_flag = bs.read_bits(1)
            if self.nal_hrd_parameters_present_flag:
                self.hrd_parameters()  # NAL HRD parameters

            self.vcl_hrd_parameters_present_flag = bs.read_bits(1)
            if self.vcl_hrd_parameters_present_flag:
                self.hrd_parameters()  # VCL HRD parameters

            if self.nal_hrd_parameters_present_flag or self.vcl_hrd_parameters_present_flag:
                self.low_delay_hrd_flag = bs.read_bits(1)

            self.pic_struct_present_flag = bs.read_bits(1)
            self.bitstream_restriction_flag = bs.read_bits(1)

            if self.bitstream_restriction_flag:
                self.motion_vectors_over_pic_boundaries_flag = bs.read_bits(1)
                self.max_bytes_per_pic_denom = bs.read_ue()
                self.max_bits_per_mb_denom = bs.read_ue()
                self.log2_max_mv_length_horizontal = bs.read_ue()
                self.log2_max_mv_length_vertical = bs.read_ue()
                self.max_num_reorder_frames = bs.read_ue()
                self.max_dec_frame_buffering = bs.read_ue()

        # bs.rbsp_trailing_bits()

        ## 逻辑条件
        self.PicHeightInMapUnits = self.pic_height_in_map_units_minus1 + 1
        # self.PicSizeInMapUnits = PicWidthInMbs * PicHeightInMapUnits

        self.PicWidthInMbs = self.pic_width_in_mbs_minus1 + 1

        self.FrameHeightInMbs = ( 2 - self.frame_mbs_only_flag ) * self.PicHeightInMapUnits

  


        ## 逻辑条件 end