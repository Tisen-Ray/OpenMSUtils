from .MSObject import MSObject
from typing import Dict, List, Tuple

class IonMobilityUtils:
    def __init__(self):
        pass
    
    @staticmethod
    def _merge_peaks_by_mz(peaks: List[Tuple[float, float]], mz_tolerance: float) -> List[Tuple[float, float]]:
        """
        根据m/z容差合并相似m/z值的峰强度
        
        参数:
            peaks: 峰列表，每个峰为(m/z, intensity)元组
            mz_tolerance: m/z容差，单位为ppm
            
        返回:
            合并后的峰列表
        """
        if not peaks:
            return []
        
        # 按m/z值排序
        sorted_peaks = sorted(peaks, key=lambda x: x[0])
        merged_peaks = []
        current_group = [sorted_peaks[0]]
        current_mz = sorted_peaks[0][0]
        
        for peak in sorted_peaks[1:]:
            mz, intensity = peak
            # 计算当前峰与当前组m/z的差异（ppm）
            tolerance_da = current_mz * mz_tolerance / 1e6
            
            if abs(mz - current_mz) <= tolerance_da:
                # 如果在容差范围内，添加到当前组
                current_group.append(peak)
            else:
                # 如果超出容差范围，合并当前组并开始新组
                if current_group:
                    # 计算平均m/z（加权平均）和总强度
                    total_intensity = sum(p[1] for p in current_group)
                    weighted_mz = sum(p[0] * p[1] for p in current_group) / total_intensity if total_intensity > 0 else current_mz
                    merged_peaks.append((weighted_mz, total_intensity))
                
                # 开始新组
                current_group = [peak]
                current_mz = mz
        
        # 处理最后一组
        if current_group:
            total_intensity = sum(p[1] for p in current_group)
            weighted_mz = sum(p[0] * p[1] for p in current_group) / total_intensity if total_intensity > 0 else current_mz
            merged_peaks.append((weighted_mz, total_intensity))
        
        return merged_peaks
    
    @staticmethod
    def parse_ion_mobility(ms_object_list: list[MSObject], rt_range=None, mz_tolerance=10, rt_tolerance=None) -> Dict[float, list[tuple[float, float]]]:
        """
        解析淌度谱数据并返回字典
        
        参数:
            ms_object_list: MSObject对象列表
            rt_range: 保留时间范围，格式为(min_rt, max_rt)
            mz_tolerance: m/z容差，默认为10ppm
            rt_tolerance: 保留时间容差，默认为None
            
        返回:
            ion_mobility_spectrum: 淌度谱字典，键为漂移时间，值为对应的峰列表
        """
        # 如果提供了rt_range，筛选在保留时间范围内的MSObject
        filtered_ms_objects = ms_object_list
        if rt_range is not None:
            min_rt, max_rt = rt_range
            filtered_ms_objects = [ms_obj for ms_obj in ms_object_list if ms_obj.scan.retention_time is not None and min_rt <= ms_obj.scan.retention_time <= max_rt]
        
        # 初始化淌度谱字典
        ion_mobility_spectrum = {}
        # 解析淌度谱数据
        for ms_object in filtered_ms_objects:
            drift_time = ms_object.scan.drift_time
            if not drift_time or drift_time < 0:
                continue

            # 如果提供了rt_tolerance，查找在容差范围内的已有drift_time
            found_key = None
            if rt_tolerance is not None:
                for existing_dt in ion_mobility_spectrum.keys():
                    if abs(existing_dt - drift_time) <= rt_tolerance:
                        found_key = existing_dt
                        break
            
            # 确定使用的键
            key = found_key if found_key is not None else drift_time
            
            # 初始化字典项（如果不存在）
            if key not in ion_mobility_spectrum:
                ion_mobility_spectrum[key] = []
                
            ion_mobility_spectrum[key].extend(ms_object.peaks)
        
        # 对每个漂移时间的峰列表根据mz_tolerance合并相似m/z值的峰
        for drift_time, peaks in ion_mobility_spectrum.items():
            ion_mobility_spectrum[drift_time] = IonMobilityUtils._merge_peaks_by_mz(peaks, mz_tolerance)
        
        return ion_mobility_spectrum


