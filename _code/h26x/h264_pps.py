
from h264_sps import SPS
from h264_bs import BitStream


class PPS():


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

    def __init__(self, bs:BitStream, sps:SPS):
        self.pic_parameter_set_id = bs.read_ue()
        self.seq_parameter_set_id = bs.read_ue()
        self.entropy_coding_mode_flag = bs.read_bits(1)
        self.bottom_field_pic_order_in_frame_present_flag = bs.read_bits(1)
        self.num_slice_groups_minus1 = bs.read_ue()
        if self.num_slice_groups_minus1 > 0:
            self.slice_group_map_type = bs.read_ue()
            if self.slice_group_map_type == 0:
                self.run_length_minus1 = [
                    bs.read_ue() for _ in range(self.num_slice_groups_minus1 + 1)
                ]
            elif self.slice_group_map_type == 2:
                self.top_left = [
                    bs.read_ue() for _ in range(self.num_slice_groups_minus1)
                ]
                self.bottom_right = [
                    bs.read_ue() for _ in range(self.num_slice_groups_minus1)
                ]
            elif self.slice_group_map_type in {3, 4, 5}:
                self.slice_group_change_direction_flag = bs.read_bits(1)
                self.slice_group_change_rate_minus1 = bs.read_ue()
            elif self.slice_group_map_type == 6:
                self.pic_size_in_map_units_minus1 = bs.read_ue()
                self.slice_group_id = [
                    bs.read_bits(1) for _ in range(self.pic_size_in_map_units_minus1 + 1)
                ]
        # 解析默认活动参考帧数
        self.num_ref_idx_l0_default_active_minus1 = bs.read_ue()
        self.num_ref_idx_l1_default_active_minus1 = bs.read_ue()
        # 解析加权预测相关参数
        self.weighted_pred_flag = bs.read_bits(1)
        self.weighted_bipred_idc = bs.read_bits(2)
        # 解析量化参数
        self.pic_init_qp_minus26 = bs.read_se()
        self.pic_init_qs_minus26 = bs.read_se()
        self.chroma_qp_index_offset = bs.read_se()
        # 解析去块滤波相关标志
        self.deblocking_filter_control_present_flag = bs.read_bits(1)
        self.constrained_intra_pred_flag = bs.read_bits(1)
        self.redundant_pic_cnt_present_flag = bs.read_bits(1)
        #
        self.transform_8x8_mode_flag = 0


        self.ScalingList4x4 = {}
        self.ScalingList8x8 = {}
        if bs.more_rbsp_data():
            self.transform_8x8_mode_flag = bs.read_bits(1)
            self.pic_scaling_matrix_present_flag = bs.read_bits(1)
            if self.pic_scaling_matrix_present_flag:
                for i in range(6 + (2 if sps.chroma_format_idc != 3 else 6) * self.transform_8x8_mode_flag):
                    pic_scaling_list_present_flag = bs.read_bits(1)
                    if pic_scaling_list_present_flag:
                        if i < 6:
                            self.ScalingList4x4[i],
                            useDefaultScalingMatrixFlag = self.scaling_list(bs, 16)
                            if useDefaultScalingMatrixFlag:
                                self.ScalingList4x4[i] = SPS.Default_4x4_Intra if i in (0,1,2) else \
                                                           SPS.Default_4x4_Inter
                        else:
                            self.ScalingList8x8[i],
                            useDefaultScalingMatrixFlag = self.scaling_list(bs, 64)
                            if useDefaultScalingMatrixFlag:
                                self.ScalingList8x8[i] = SPS.Default_8x8_Intra if i in (6,8,10) else \
                                                           SPS.Default_8x8_Inter
                    else:
                        if i < 6:
                            self.ScalingList4x4[i] = SPS.Default_4x4_Intra if i in (0,1,2) else \
                                                           SPS.Default_4x4_Inter
                        else:
                            self.ScalingList8x8[i] = SPS.Default_8x8_Intra if i in (6,8,10) else \
                                                           SPS.Default_8x8_Inter
                    self.second_chroma_qp_index_offset = bs.read_se()

        