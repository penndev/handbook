from __future__ import annotations
import json
import math
from h264_define import BitStream, MbType, NalUnitType, SliceType
from H264_mb import MacroBlock

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from h264_nal import NAL


class NAL():
    '7 单元结构体的实现'

    def dec_ref_pic_marking(self):
        if self.idr_pic_flag:
            self.no_output_of_prior_pics_flag = self.stream.read_bits(1)
            self.long_term_reference_flag = self.stream.read_bits(1)
        else:
            adaptive_ref_pic_marking_mode_flag = self.stream.read_bits(1)
            if adaptive_ref_pic_marking_mode_flag:
                while True:
                    self.memory_management_control_operation = self.read_ue()
                    if self.memory_management_control_operation in [1, 3]:
                        self.difference_of_pic_nums_minus1 = self.read_ue()
                    if self.memory_management_control_operation == 2:
                        self.long_term_pic_num = self.read_ue()
                    if self.memory_management_control_operation in [3, 6]:
                        self.long_term_frame_idx = self.read_ue()
                    if self.memory_management_control_operation == 4:
                        self.max_long_term_frame_idx_plus1 = self.read_ue()
                    if self.memory_management_control_operation == 0:
                        break

    def pred_weight_table(self):
        self.luma_log2_weight_denom = self.stream.read_ue()

        if self.sps.chroma_format_idc != 0:  # 读取色度权重的对数值
            self.chroma_log2_weight_denom = self.stream.read_ue()
        for i in range(self.num_ref_idx_l0_active_minus1 + 1):
            luma_weight_l0_flag = self.stream.read_bits(1)
            if luma_weight_l0_flag:
                self.luma_weight_l0[i] = self.stream.read_se()
                self.luma_offset_l0[i] = self.stream.read_se()
            if self.sps.chroma_array_type != 0:
                chroma_weight_l0_flag = self.stream.read_bits(1)
                if chroma_weight_l0_flag:
                    for j in range(2):
                        self.chroma_weight_l0[i][j] = self.read_se()
                        self.chroma_offset_l0[i][j] = self.read_se()
        if self.slice_type % 5 == 1:
            # 处理 L1 引用帧的权重和偏移
            for i in range(self.num_ref_idx_l1_active_minus1 + 1):
                luma_weight_l1_flag = self.stream.read_bits(1)
                if luma_weight_l1_flag:
                    self.luma_weight_l1[i] = self.read_se()
                    self.luma_offset_l1[i] = self.read_se()

                if self.chroma_array_type != 0:
                    chroma_weight_l1_flag = self.stream.read_bits(1)
                    if chroma_weight_l1_flag:
                        for j in range(2):
                            self.chroma_weight_l1[i][j] = self.read_se()
                            self.chroma_offset_l1[i][j] = self.read_se()

    def ref_pic_list_modification(self):
        if self.slice_type % 5 != 2 and self.slice_type % 5 != 4:
            # 读取 ref_pic_list_modification_flag_l0
            self.ref_pic_list_modification_flag_l0 = self.stream.read_bits(1)
            if self.ref_pic_list_modification_flag_l0:
                # 循环解析 modification_of_pic_nums_idc
                while True:
                    modification_of_pic_nums_idc = self.stream.read_ue()
                    if modification_of_pic_nums_idc == 0 or modification_of_pic_nums_idc == 1:
                        self.abs_diff_pic_num_minus1 = self.stream.read_ue()
                    elif modification_of_pic_nums_idc == 2:
                        self.long_term_pic_num = self.stream.read_ue()
                    elif modification_of_pic_nums_idc == 3:
                        break  # 退出循环
        if self.slice_type % 5 == 1:  # 如果 slice_type 是 B 类型，需要处理 ref_pic_list_modification_flag_l1
            self.ref_pic_list_modification_flag_l1 = self.stream.read_bits(1)
            if self.ref_pic_list_modification_flag_l1:
                while True:
                    modification_of_pic_nums_idc = self.stream.read_ue()
                    if modification_of_pic_nums_idc == 0 or modification_of_pic_nums_idc == 1:
                        self.abs_diff_pic_num_minus1 = self.stream.read_ue()
                    elif modification_of_pic_nums_idc == 2:
                        self.long_term_pic_num = self.stream.read_ue()
                    elif modification_of_pic_nums_idc == 3:
                        break  # 退出循环

    def hrd_parameters(self):
        self.cpb_cnt_minus1 = self.stream.read_ue()
        self.bit_rate_scale = self.stream.read_bits(4)
        self.cpb_size_scale = self.stream.read_bits(4)
        self.bit_rate_value_minus1 = []
        self.cpb_size_value_minus1 = []
        self.cbr_flag = []
        for _ in range(self.cpb_cnt_minus1 + 1):
            self.bit_rate_value_minus1.append(self.stream.read_uev())
            self.cpb_size_value_minus1.append(self.stream.read_uev())
            self.cbr_flag.append(self.stream.read_bits(1))
        self.initial_cpb_removal_delay_length_minus1 = self.stream.read_bits(5)
        self.cpb_removal_delay_length_minus1 = self.stream.read_bits(5)
        self.dpb_output_delay_length_minus1 = self.stream.read_bits(5)
        self.time_offset_length = self.stream.read_bits(5)

    def vui_parameters(self):
        self.aspect_ratio_info_present_flag = self.stream.read_bits(1)
        if self.aspect_ratio_info_present_flag:
            self.aspect_ratio_idc = self.stream.read_bits(8)
            if self.aspect_ratio_idc == 255:  # Extended_SAR, typically denoted as 255
                self.sar_width = self.stream.read_bits(16)
                self.sar_height = self.stream.read_bits(16)
        self.overscan_info_present_flag = self.stream.read_bits(1)
        if self.overscan_info_present_flag:
            self.overscan_appropriate_flag = self.stream.read_bits(1)
        self.video_signal_type_present_flag = self.stream.read_bits(1)
        if self.video_signal_type_present_flag:
            self.video_format = self.stream.read_bits(3)
            self.video_full_range_flag = self.stream.read_bits(1)
            self.colour_description_present_flag = self.stream.read_bits(1)
            if self.colour_description_present_flag:
                self.colour_primaries = self.stream.read_bits(8)
                self.transfer_characteristics = self.stream.read_bits(8)
                self.matrix_coefficients = self.stream.read_bits(8)
        self.chroma_loc_info_present_flag = self.stream.read_bits(1)
        if self.chroma_loc_info_present_flag:
            # Exp-Golomb-coded value (ue(v))
            self.chroma_sample_loc_type_top_field = self.stream.read_ue()
            # Exp-Golomb-coded value (ue(v))
            self.chroma_sample_loc_type_bottom_field = self.stream.read_ue()
        self.timing_info_present_flag = self.stream.read_bits(1)
        if self.timing_info_present_flag:
            self.num_units_in_tick = self.stream.read_bits(32)
            self.time_scale = self.stream.read_bits(32)
            self.fixed_frame_rate_flag = self.stream.read_bits(1)

        self.nal_hrd_parameters_present_flag = self.stream.read_bits(1)
        if self.nal_hrd_parameters_present_flag:
            self.hrd_parameters()  # NAL HRD parameters

        self.vcl_hrd_parameters_present_flag = self.stream.read_bits(1)
        if self.vcl_hrd_parameters_present_flag:
            self.hrd_parameters()  # VCL HRD parameters

        if self.nal_hrd_parameters_present_flag or self.vcl_hrd_parameters_present_flag:
            self.low_delay_hrd_flag = self.stream.read_bits(1)

        self.pic_struct_present_flag = self.stream.read_bits(1)
        self.bitstream_restriction_flag = self.stream.read_bits(1)

        if self.bitstream_restriction_flag:
            self.motion_vectors_over_pic_boundaries_flag = self.stream.read_bits(
                1)
            self.max_bytes_per_pic_denom = self.stream.read_ue()
            self.max_bits_per_mb_denom = self.stream.read_ue()
            self.log2_max_mv_length_horizontal = self.stream.read_ue()
            self.log2_max_mv_length_vertical = self.stream.read_ue()
            self.max_num_reorder_frames = self.stream.read_ue()
            self.max_dec_frame_buffering = self.stream.read_ue()

    def seq_parameter_set_data(self):
        self.profile_idc = self.stream.read_bits(8)
        self.constraint_set0_flag = self.stream.read_bits(1)
        self.constraint_set1_flag = self.stream.read_bits(1)
        self.constraint_set2_flag = self.stream.read_bits(1)
        self.constraint_set3_flag = self.stream.read_bits(1)
        self.reserved_zero_4bits = self.stream.read_bits(4)
        self.level_idc = self.stream.read_bits(8)
        self.seq_parameter_set_id = self.stream.read_ue()
        self.separate_colour_plane_flag = 0
        self.log2_max_frame_num_minus4 = 0
        self.frame_mbs_only_flag = 0
        self.pic_order_cnt_type = 0
        self.mb_adaptive_frame_field_flag = 0
        if self.profile_idc in (100, 110, 122, 244, 44, 83, 86, 118, 128, 138, 139, 134, 135):
            self.chroma_format_idc = self.stream.read_ue()
            if self.chroma_format_idc == 3:
                self.separate_colour_plane_flag = self.stream.read_bits(1)
            self.bit_depth_luma_minus8 = self.stream.read_ue()
            self.bit_depth_chroma_minus8 = self.stream.read_ue()
            self.qpprime_y_zero_transform_bypass_flag = self.stream.read_bits(
                1)
            self.seq_scaling_matrix_present_flag = self.stream.read_bits(1)
            if self.seq_scaling_matrix_present_flag == 1:
                for i in range(8 if self.chroma_format_idc != 3 else 12):
                    # seq_scaling_list_present_flag
                    self.stream.read_bits(1)
                    # UseDefaultScalingMatrix4x4Flag
            self.log2_max_frame_num_minus4 = self.stream.read_ue()
            self.pic_order_cnt_type = self.stream.read_ue()
            if self.pic_order_cnt_type == 0:
                self.log2_max_pic_order_cnt_lsb_minus4 = self.stream.read_ue()
            elif self.pic_order_cnt_type == 1:
                self.delta_pic_order_always_zero_flag = self.stream.read_bits(
                    1)
                self.offset_for_non_ref_pic = self.stream.read_ue()
                self.offset_for_top_to_bottom_field = self.stream.read_ue()
                self.num_ref_frames_in_pic_order_cnt_cycle = self.stream.read_ue()
                for i in range(self.num_ref_frames_in_pic_order_cnt_cycle):
                    # offset_for_ref_frame[i]
                    self.stream.read_se()
            self.num_ref_frames = self.stream.read_ue()
            self.gaps_in_frame_num_value_allowed_flag = self.stream.read_bits(
                1)
            self.pic_width_in_mbs_minus1 = self.stream.read_ue()
            self.pic_height_in_map_units_minus1 = self.stream.read_ue()
            self.frame_mbs_only_flag = self.stream.read_bits(1)
            self.mb_adaptive_frame_field_flag = 0
            if self.frame_mbs_only_flag != 1:
                self.mb_adaptive_frame_field_flag = self.stream.read_bits(1)
            self.direct_8x8_inference_flag = self.stream.read_bits(1)
            self.frame_cropping_flag = self.stream.read_bits(1)
            if self.frame_cropping_flag == 1:
                self.frame_crop_left_offset = self.stream.read_ue()
                self.frame_crop_right_offset = self.stream.read_ue()
                self.frame_crop_top_offset = self.stream.read_ue()
                self.frame_crop_bottom_offset = self.stream.read_ue()
            self.vui_parameters_present_flag = self.stream.read_bits(1)
            if self.vui_parameters_present_flag == 1:
                self.vui_parameters()

    def pic_parameter_set_rbsp(self):
        '传说中的pps数据'
        self.pic_parameter_set_id = self.stream.read_ue()
        self.seq_parameter_set_id = self.stream.read_ue()
        self.entropy_coding_mode_flag = self.stream.read_bits(1)
        self.bottom_field_pic_order_in_frame_present_flag = self.stream.read_bits(
            1)
        self.num_slice_groups_minus1 = self.stream.read_ue()
        if self.num_slice_groups_minus1 > 0:
            self.slice_group_map_type = self.stream.read_ue()
            if self.slice_group_map_type == 0:
                self.run_length_minus1 = [self.stream.read_ue(
                ) for _ in range(self.num_slice_groups_minus1 + 1)]
            elif self.slice_group_map_type == 2:
                self.top_left = [self.stream.read_ue()
                                 for _ in range(self.num_slice_groups_minus1)]
                self.bottom_right = [self.stream.read_ue()
                                     for _ in range(self.num_slice_groups_minus1)]
            elif self.slice_group_map_type in {3, 4, 5}:
                self.slice_group_change_direction_flag = self.stream.read_bits(
                    1)
                self.slice_group_change_rate_minus1 = self.stream.read_ue()
            elif self.slice_group_map_type == 6:
                self.pic_size_in_map_units_minus1 = self.stream.read_ue()
                self.slice_group_id = [self.stream.read_bits(
                    1) for _ in range(self.pic_size_in_map_units_minus1 + 1)]
        # 解析默认活动参考帧数
        self.num_ref_idx_l0_default_active_minus1 = self.stream.read_ue()
        self.num_ref_idx_l1_default_active_minus1 = self.stream.read_ue()
        # 解析加权预测相关参数
        self.weighted_pred_flag = self.stream.read_bits(1)
        self.weighted_bipred_idc = self.stream.read_bits(2)
        # 解析量化参数
        self.pic_init_qp_minus26 = self.stream.read_se()
        self.pic_init_qs_minus26 = self.stream.read_se()
        self.chroma_qp_index_offset = self.stream.read_se()
        # 解析去块滤波相关标志
        self.deblocking_filter_control_present_flag = self.stream.read_bits(1)
        self.constrained_intra_pred_flag = self.stream.read_bits(1)
        self.redundant_pic_cnt_present_flag = self.stream.read_bits(1)
        # 如果有更多的 RBSP 数据
        if self.stream.more_rbsp_data():
            self.transform_8x8_mode_flag = self.stream.read_bits(1)
            self.pic_scaling_matrix_present_flag = self.stream.read_bits(1)
            if self.pic_scaling_matrix_present_flag:
                pic_scaling_list_present_flag = []
                # scaling_list = []
                for i in range(6 + ((self.sps.chroma_format_idc != 3) * 2) * self.transform_8x8_mode_flag):
                    pic_scaling_list_present_flag.append(
                        self.stream.read_bits(1))
                    if pic_scaling_list_present_flag[i]:
                        pass
                        # if i < 6:
                        #     scaling_list.append(self.scaling_list(ScalingList4x4[i], 16, UseDefaultScalingMatrix4x4Flag[i]))
                        # else:
                        #     scaling_list.append(self.scaling_list(ScalingList8x8[i - 6], 64, UseDefaultScalingMatrix8x8Flag[i - 6]))
                # self.pic_scaling_list_present_flag = pic_scaling_list_present_flag
                # self.scaling_list = scaling_list
            self.second_chroma_qp_index_offset = self.stream.read_se()

    def seq_parameter_set_rbsp(self):
        '传说中的 sps 后续理解再解释 penndev'
        self.seq_parameter_set_data()
        # self.stream.rbsp_trailing_bits()

    def slice_header(self):
        # 动态给的
        self.idr_pic_flag = 1 if self.nal_unit_type == NalUnitType.IDR else 0
        ##
        self.first_mb_in_slice = self.stream.read_ue()
        self.slice_type = self.stream.read_ue()
        self.pic_parameter_set_id = self.stream.read_ue()
        if self.sps.separate_colour_plane_flag:
            self.colour_plane_id = self.stream.read_bits(2)
        self.frame_num = self.stream.read_bits(
            self.sps.log2_max_frame_num_minus4 + 4)
        self.field_pic_flag = 0
        self.MbaffFrameFlag = 0
        if not self.sps.frame_mbs_only_flag:
            self.field_pic_flag = self.stream.read_bits(1)
            if self.field_pic_flag:
                self.bottom_field_flag = self.stream.read_bits(1)
                self.MbaffFrameFlag = 1 if self.sps.mb_adaptive_frame_field_flag and (
                    not self.field_pic_flag) else 0
        if self.idr_pic_flag:
            self.idr_pic_id = self.stream.read_ue()
        if self.sps.pic_order_cnt_type == 0:
            self.pic_order_cnt_lsb = self.stream.read_bits(
                self.sps.log2_max_pic_order_cnt_lsb_minus4 + 4)
            if self.pps.bottom_field_pic_order_in_frame_present_flag and not getattr(self, 'field_pic_flag', False):
                self.delta_pic_order_cnt_bottom = self.stream.read_se()
        if self.sps.pic_order_cnt_type == 1 and not self.delta_pic_order_always_zero_flag:
            self.delta_pic_order_cnt_0 = self.stream.read_se()
            if self.pps.bottom_field_pic_order_in_frame_present_flag and not getattr(self, 'field_pic_flag', False):
                self.delta_pic_order_cnt_1 = self.stream.read_se()
        if self.pps.redundant_pic_cnt_present_flag:
            self.redundant_pic_cnt = self.stream.read_ue()
        if self.slice_type == SliceType.B:
            self.direct_spatial_mv_pred_flag = self.stream.read_bits(1)
        if self.slice_type in [SliceType.P, SliceType.SP, SliceType.B]:
            self.num_ref_idx_active_override_flag = self.stream.read_bits(1)
            if self.num_ref_idx_active_override_flag:
                self.num_ref_idx_l0_active_minus1 = self.stream.read_ue()
                if self.slice_type == SliceType.B:
                    self.num_ref_idx_l1_active_minus1 = self.stream.read_ue()
        if self.nal_unit_type in [NalUnitType.CSE, NalUnitType.CSE3D]:
            self.ref_pic_list_mvc_modification()
        else:
            self.ref_pic_list_modification()
        if (self.pps.weighted_pred_flag == 1 and self.slice_type in [SliceType.P, SliceType.SP]) or \
           (self.pps.weighted_bipred_idc == 1 and self.slice_type == SliceType.B):  # pred_weight_table
            self.pred_weight_table()
        if self.nal_ref_idc != 0:  # dec_ref_pic_marking
            self.dec_ref_pic_marking()
        self.cabac_init_idc = 0
        if self.pps.entropy_coding_mode_flag and self.slice_type not in [SliceType.I, SliceType.SI]:
            self.cabac_init_idc = self.stream.read_ue()
        self.slice_qp_delta = self.stream.read_se()
        if self.slice_type in [SliceType.SP, SliceType.SI]:
            if self.slice_type == SliceType.SP:
                self.sp_for_switch_flag = self.stream.read_bits(1)
            self.slice_qs_delta = self.stream.read_se()
        if self.pps.deblocking_filter_control_present_flag:
            self.disable_deblocking_filter_idc = self.stream.read_ue()
            if self.disable_deblocking_filter_idc != 1:
                self.slice_alpha_c0_offset_div2 = self.stream.read_se()
                self.slice_beta_offset_div2 = self.stream.read_se()
        if self.pps.num_slice_groups_minus1 > 0 and 3 <= self.pps.slice_group_map_type <= 5:
            pic_size = (self.sps.pic_width_in_mbs_minus1 + 1) * \
                (self.sps.pic_height_in_map_units_minus1 + 1)
            max = (pic_size + self.pps.slice_group_change_rate_minus1) // (
                self.pps.slice_group_change_rate_minus1 + 1)
            self.slice_group_change_cycle = self.stream.read_bits(
                math.ceil(math.log2(max + 1)))

    def slice_data(self):
        self.SliceQPY = 26 + self.pps.pic_init_qp_minus26 + self.slice_qp_delta

        if self.pps.entropy_coding_mode_flag:
            while not self.stream.byte_aligned():
                if 1 != self.stream.read_bits(1):
                    raise ('slice_data cabac_alignment_one_bit')
            # =========初始化cabac参数
            self.stream.cabac_init_context_variables(
                self.slice_type, self.cabac_init_idc, self.SliceQPY)
            self.stream.cabac_inti_arithmetic_decoding_engine()
            # =========
        self.CurrMbAddr = self.first_mb_in_slice * (1 + self.MbaffFrameFlag)
        moreDataFlag = 1
        prevMbSkipped = 0

        moreDataFlag = 1
        prevMbSkipped = 0
        self.macroblock: dict[int, MacroBlock] = {}
        while True:
            if self.slice_type not in [SliceType.I, SliceType.SI]:
                raise ("SliceType" + self.slice_type)
            if moreDataFlag:
                if self.MbaffFrameFlag and \
                    (self.CurrMbAddr % 2 == 0 or
                     (self.CurrMbAddr % 2 == 1 and prevMbSkipped)
                     ):
                    raise ('MbaffFrameFlag error')
                self.macroblock[self.CurrMbAddr] = MacroBlock(
                    self, self.sps, self.pps, self.stream)
                # print(self.macroblock[self.CurrMbAddr].__dict__)
                exit(0)
                return

    def slice_layer_without_partitioning_rbsp(self):
        '处理图像数据'
        self.slice_header()
        self.slice_data()

    def to_dict(self):
        '格式化所有的字段，进行适配'
        attributes = self.__dict__.copy()
        del attributes["sps"]
        del attributes["pps"]
        del attributes["stream"]
        return attributes

    def __init__(self, stream: BitStream, sps: NAL, pps: NAL):
        self.sps = sps
        self.pps = pps
        self.stream = stream
        # NAL header
        self.forbidden_zero_bit = self.stream.read_bits(1)
        self.nal_ref_idc = self.stream.read_bits(2)
        self.nal_unit_type = self.stream.read_bits(5)
        'Table 7-1 – NAL unit type codes, syntax element categories, and NAL unit type classes'
        if self.nal_unit_type == NalUnitType.IDR:  # 处理图像帧
            self.slice_layer_without_partitioning_rbsp()
        elif self.nal_unit_type == NalUnitType.SEI:
            pass
        elif self.nal_unit_type == NalUnitType.SPS:  # sps
            self.seq_parameter_set_rbsp()
        elif self.nal_unit_type == NalUnitType.PPS:  # pps
            self.pic_parameter_set_rbsp()
        else:
            print('NO SUPPORT ', self.nal_unit_type)
            return
        print(json.dumps(self.to_dict(), indent=4))
