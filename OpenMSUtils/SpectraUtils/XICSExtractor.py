import numpy as np
from typing import List
from dataclasses import dataclass
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor

from .MZMLUtils import MZMLReader
from .MSObject import MSObject
from .SpectraConverter import SpectraConverter

@dataclass
class XICResult:
    """XIC 结果类"""
    rt_array: np.ndarray  # 保留时间数组
    intensity_array: np.ndarray  # 强度数组
    mz: float  # 目标质荷比
    ppm_error: float  # PPM 误差
    ion_type: str = ""  # 离子类型 ([M+1], [M+2], [M+3], [M+4], b4, y7)
    charge: int = 0  # 电荷状态

@dataclass
class FragmentIon:
    """碎片离子信息类"""
    ion_type: str  # 例如 y7, b10
    charge: int  # 电荷状态
    mz: float  # 质荷比
    
@dataclass
class PolymerInfo:
    """聚合物信息类"""
    sequence: str  # 原始序列
    modified_sequence: str  # 修饰后序列
    charge: int  # 前体离子电荷
    mz: float  # 前体离子质荷比
    rt: float  # 保留时间
    rt_start: float  # 保留时间起点
    rt_stop: float  # 保留时间终点
    fragment_ions: List[FragmentIon]  # 碎片离子列表

class XICSExtractor:
    """XIC 提取器类"""
    
    def __init__(self, mzml_file: str, ppm_tolerance: float = 10.0):
        """
        初始化 XIC 提取器
        
        参数:
            mzml_file: mzML 文件路径
            ppm_tolerance: 质量容差 (ppm)
        """
        self.mzml_file = mzml_file
        self.ppm_tolerance = ppm_tolerance
        self.reader = MZMLReader()
        self.ms_objects = []
        self.ms1_objects = []
        self.ms2_objects = []
        self.ms2_objects_indices = {}
        
    def load_mzml(self):
        """加载 mzML 文件并转换为 MSObject 列表"""
        print(f"正在读取 mzML 文件: {self.mzml_file}")
        mzml_obj = self.reader.read(self.mzml_file, parse_spectra=True, parallel=True)
        
        if not mzml_obj.run or not mzml_obj.run.spectra_list:
            raise ValueError("未能从 mzML 文件中读取到谱图数据")
            
        print("正在将谱图转换为 MSObject...")
        self.ms_objects = []
        self.ms1_objects = []
        self.ms2_objects = []
        for spectrum in tqdm(mzml_obj.run.spectra_list, desc="转换谱图"):
            ms_obj = SpectraConverter.to_msobject(spectrum)
            # 分类 MS1 和 MS2 谱图
            self.ms_objects.append(ms_obj)
            if ms_obj.level == 1:
                self.ms1_objects.append(ms_obj)
            elif ms_obj.level == 2:
                self.ms2_objects.append(ms_obj)
        del mzml_obj

        self.ms1_objects.sort(key=lambda x: x.retention_time)
        self.ms2_objects.sort(key=lambda x: x.retention_time)

        self.ms2_objects_indices = {}
        for index, ms2 in enumerate(self.ms2_objects):
            second = int(ms2.retention_time)  # 获取当前 MS2 谱图的保留时间的秒数
            if second not in self.ms2_objects_indices:
                self.ms2_objects_indices[second] = index
            else:
                if ms2.retention_time < self.ms2_objects[self.ms2_objects_indices[second]].retention_time:
                    self.ms2_objects_indices[second] = index
            
        print(f"共读取 {len(self.ms_objects)} 个谱图，其中 MS1: {len(self.ms1_objects)}，MS2: {len(self.ms2_objects)}")
        
    def _calculate_isotope_mzs(self, mz: float, charge: int, num_isotopes: int = 4) -> List[float]:
        """计算同位素峰的质荷比"""
        isotope_mzs = [mz]
        for i in range(1, num_isotopes):
            # 碳同位素间隔约为 1.0033 Da
            isotope_mz = mz + (i * 1.00335483507) / charge
            isotope_mzs.append(isotope_mz)
        return isotope_mzs
    
    def _filter_ms2_by_rt_and_precursor(self, rt_start: float, rt_stop: float, precursor_mz: float) -> List[MSObject]:
        """根据保留时间筛选 MS2 谱图"""
        filtered_ms2 = []

        start_second = int(rt_start)
        while start_second not in self.ms2_objects_indices:
            start_second -= 1
        start_index = self.ms2_objects_indices[start_second]

        for ms2 in self.ms2_objects[start_index:]:
            if not (rt_start <= ms2.retention_time <= rt_stop):
                continue

            if not (ms2.precursor.isolation_window[0] <= precursor_mz <= ms2.precursor.isolation_window[1]):
                continue

            if (ms2.retention_time > rt_stop):
                break
            
            filtered_ms2.append(ms2)
            
        return filtered_ms2

    def _filter_ms2_by_precursor(self, precursor_mz: float) -> List[MSObject]:
        """根据前体离子质荷比筛选 MS2 谱图"""
        filtered_ms2 = []
        
        for ms2 in self.ms2_objects:
            if not (ms2.precursor.isolation_window[0] <= precursor_mz <= ms2.precursor.isolation_window[1]):
                continue
            
            filtered_ms2.append(ms2)
            
        return filtered_ms2
    
    def _extract_xic_from_ms1(self, mz: float, rt_start: float, rt_stop: float, ppm_tolerance: float) -> XICResult:
        """从 MS1 谱图中提取 XIC"""
        rt_values = []
        intensity_values = []
        mz_delta_ppm_sum = 0
        count = 0
        
        mz_min = mz * (1 - ppm_tolerance / 1e6)
        mz_max = mz * (1 + ppm_tolerance / 1e6)
        
        for ms1 in self.ms1_objects:
            # 检查保留时间是否在范围内
            if not (rt_start <= ms1.retention_time <= rt_stop):
                continue
                
            # 查找最接近目标 m/z 的峰
            closest_peak_idx = None
            min_delta = float('inf')
            
            for i, peak_mz in enumerate([item[0] for item in ms1.peaks]):
                if mz_min <= peak_mz <= mz_max:
                    delta = abs(peak_mz - mz)
                    if delta < min_delta:
                        min_delta = delta
                        closest_peak_idx = i
            
            if closest_peak_idx is not None:
                peak_mz = ms1.peaks[closest_peak_idx][0]
                peak_intensity = ms1.peaks[closest_peak_idx][1]
                
                rt_values.append(ms1.retention_time)
                intensity_values.append(peak_intensity)
                
                # 计算 ppm 误差
                ppm_error = (peak_mz - mz) / mz * 1e6
                mz_delta_ppm_sum += abs(ppm_error)
                count += 1
            else:
                # 如果没有找到峰，添加零强度
                rt_values.append(ms1.retention_time)
                intensity_values.append(0)
        
        # 计算平均 ppm 误差
        avg_ppm_error = mz_delta_ppm_sum / count if count > 0 else 0
        
        return XICResult(
            rt_array=np.array(rt_values),
            intensity_array=np.array(intensity_values),
            mz=mz,
            ppm_error=avg_ppm_error
        )
    
    def _extract_xic_from_ms2(self, mz: float, precursor_mz: float, rt_start: float, rt_stop: float, ppm_tolerance: float, filtered_ms2: List[MSObject] = None) -> XICResult:
        """从 MS2 谱图中提取 XIC"""
        rt_values = []
        intensity_values = []
        mz_delta_ppm_sum = 0
        count = 0
        
        mz_min = mz * (1 - ppm_tolerance / 1e6)
        mz_max = mz * (1 + ppm_tolerance / 1e6)
        
        ms2_list = filtered_ms2 if filtered_ms2 else self._filter_ms2_by_precursor(precursor_mz)
        for ms2 in ms2_list:
            # 检查保留时间是否在范围内
            if not (rt_start <= ms2.retention_time <= rt_stop):
                continue
                
            # 查找最接近目标 m/z 的峰
            closest_peak_idx = None
            min_delta = float('inf')
            
            for i, peak_mz in enumerate([item[0] for item in ms2.peaks]):
                if mz_min <= peak_mz <= mz_max:
                    delta = abs(peak_mz - mz)
                    if delta < min_delta:
                        min_delta = delta
                        closest_peak_idx = i
            
            if closest_peak_idx is not None:
                peak_mz = ms2.peaks[closest_peak_idx][0]
                peak_intensity = ms2.peaks[closest_peak_idx][1]
                
                rt_values.append(ms2.retention_time)
                intensity_values.append(peak_intensity)
                
                # 计算 ppm 误差
                ppm_error = (peak_mz - mz) / mz * 1e6
                mz_delta_ppm_sum += abs(ppm_error)
                count += 1
            else:
                # 如果没有找到峰，添加零强度
                rt_values.append(ms2.retention_time)
                intensity_values.append(0)
        
        # 计算平均 ppm 误差
        avg_ppm_error = mz_delta_ppm_sum / count if count > 0 else 0
        
        return XICResult(
            rt_array=np.array(rt_values),
            intensity_array=np.array(intensity_values),
            mz=mz,
            ppm_error=avg_ppm_error
        )
    
    def extract_precursor_xics(self, precursor: PolymerInfo, num_isotopes: int = 4) -> List[XICResult]:
        """提取前体离子的 XIC，包括同位素峰"""
        if not self.ms1_objects:
            raise ValueError("请先加载 mzML 文件")
            
        precursor_mz = precursor.mz
        charge = precursor.charge
        rt_start = precursor.rt_start
        rt_stop = precursor.rt_stop
        
        # 计算同位素峰的质荷比
        isotope_mzs = self._calculate_isotope_mzs(precursor_mz, charge, num_isotopes)
        
        # 提取每个同位素峰的 XIC
        xic_results = []
        for i, mz in enumerate(isotope_mzs):
            xic = self._extract_xic_from_ms1(mz, rt_start, rt_stop, self.ppm_tolerance)
            xic.ion_type = f"[M+{i}]"
            xic.charge = charge
            xic_results.append(xic)
            
        return xic_results
    
    def extract_fragment_xics(self, peptide_info: PolymerInfo) -> List[XICResult]:
        """提取碎片离子的 XIC"""
        if not self.ms2_objects:
            raise ValueError("请先加载 mzML 文件")
            
        rt_start = peptide_info.rt_start
        rt_stop = peptide_info.rt_stop

        filtered_ms2 = self._filter_ms2_by_rt_and_precursor(rt_start, rt_stop, peptide_info.mz)
            
        # 提取每个碎片离子的 XIC
        xic_results = []
        for fragment in peptide_info.fragment_ions:
            xic = self._extract_xic_from_ms2(fragment.mz, peptide_info.mz, rt_start, rt_stop, self.ppm_tolerance, filtered_ms2)
            xic.ion_type = fragment.ion_type
            xic.charge = fragment.charge
            xic_results.append(xic)
            
        return xic_results

