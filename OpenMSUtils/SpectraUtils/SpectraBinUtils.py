import numpy as np
from typing import List, Dict, Tuple, Union, Optional
from .MSObject import MSObject


class SpectraBinUtils:
    @staticmethod
    def generate_bin_indices(data: MSObject|list[float], bin_size: float=1.0) -> Dict[int, int]:
        """
        根据输入的MSObject或者质荷比列表生成bin索引
        
        参数:
            data: MSObject对象或者质荷比列表
            bin_size: bin的大小
            
        返回:
            包含mz到索引映射的字典
        """
        # 提取mz值
        mz_values = []
        if isinstance(data, MSObject):
            if data.peaks is not None:
                mz_values = [peak[0] for peak in data.peaks]
            else:
                raise TypeError("unsupported MSObject type")
        else:
            mz_values = data
            
        # 检查mz值是否单调递增
        for i in range(1, len(mz_values)):
            if mz_values[i] < mz_values[i-1]:
                raise ValueError("mz list must be monotonically increasing")
        
        # 生成bin范围和索引
        mz_to_index = {}
        if not mz_values:
            return mz_to_index
        
        current_index = 0
        current_bin_number = (int(mz_values[0] / bin_size))
        
        for mz in mz_values:
            if mz >= current_bin_number * bin_size:
                current_bin_number = (int(mz / bin_size))

            # 将bin边界（bin_size的整数倍）映射到索引
            mz_to_index[current_bin_number] = current_index
            current_index += 1
            
        return mz_to_index
    
