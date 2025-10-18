"""
高性能MSObject类，集成Rust实现
"""

import sys
from typing import List, Tuple, Optional, Dict, Any
from .MSObject import Precursor, Scan

# 尝试导入Rust实现
try:
    import _openms_utils_rust as rust_impl
    RUST_AVAILABLE = True
except ImportError:
    print("Warning: Rust implementation not available, falling back to Python")
    RUST_AVAILABLE = False


class MSObjectRust:
    """
    高性能MSObject类，使用Rust后端实现
    提供与原Python MSObject完全兼容的接口，但具有更高的性能
    """

    def __init__(
            self,
            level: int = 1,
            peaks: Optional[List[Tuple[float, float]]] = None,
            precursor: Optional[Precursor] = None,
            scan: Optional[Scan] = None,
            additional_info: Optional[Dict[str, Any]] = None,
            use_rust: bool = True
    ):
        """
        初始化高性能MSObject

        Args:
            level: MS级别 (1=MS1, 2=MS2, etc.)
            peaks: 峰值数据列表 [(mz, intensity), ...]
            precursor: 前体离子信息
            scan: 扫描信息
            additional_info: 附加信息字典
            use_rust: 是否使用Rust实现 (默认True)
        """
        self._use_rust = use_rust and RUST_AVAILABLE
        self._level = level

        # 初始化元数据
        self._precursor = precursor if precursor is not None else Precursor()
        self._scan = scan if scan is not None else Scan()
        self._additional_info = additional_info if additional_info is not None else {}

        # 初始化峰值数据
        if self._use_rust:
            # 使用Rust实现的Spectrum
            self._rust_spectrum = rust_impl.Spectrum(level=level)
            if peaks:
                # 批量添加峰值到Rust对象
                mz_array = [p[0] for p in peaks]
                intensity_array = [p[1] for p in peaks]
                self._rust_spectrum.add_peaks(mz_array, intensity_array)

            # 注意：Rust Spectrum的scan_number和retention_time是只读的
            # 这些信息会在需要时从Python层同步

            # Python峰值数据缓存 (延迟加载)
            self._python_peaks_cache = None
            self._cache_valid = False
        else:
            # 回退到Python实现
            self._peaks = peaks if peaks is not None else []

    @property
    def level(self) -> int:
        """MS级别"""
        return self._level

    @level.setter
    def level(self, value: int):
        self._level = value
        if self._use_rust:
            self._rust_spectrum.level = value

    @property
    def peaks(self) -> List[Tuple[float, float]]:
        """
        获取峰值数据
        返回格式: [(mz1, intensity1), (mz2, intensity2), ...]
        """
        if self._use_rust:
            if not self._cache_valid:
                # 从Rust对象获取峰值数据
                rust_peaks = self._rust_spectrum.peaks
                self._python_peaks_cache = [(p[0], p[1]) for p in rust_peaks]
                self._cache_valid = True
            return self._python_peaks_cache.copy()
        else:
            return self._peaks.copy()

    @property
    def precursor(self) -> Precursor:
        """前体离子信息"""
        return self._precursor

    @property
    def scan(self) -> Scan:
        """扫描信息"""
        return self._scan

    @property
    def scan_number(self) -> int:
        """扫描序号"""
        return self._scan.scan_number

    @scan_number.setter
    def scan_number(self, value: int):
        self._scan.scan_number = value
        # 注意：Rust Spectrum的scan_number是只读的，不直接同步

    @property
    def retention_time(self) -> float:
        """保留时间(秒)"""
        return self._scan.retention_time

    @retention_time.setter
    def retention_time(self, value: float):
        self._scan.retention_time = value
        # 注意：Rust Spectrum的retention_time是只读的，不直接同步

    @property
    def additional_info(self) -> Dict[str, Any]:
        """附加信息"""
        return self._additional_info

    @property
    def peak_count(self) -> int:
        """峰值数量"""
        if self._use_rust:
            return self._rust_spectrum.peak_count
        else:
            return len(self._peaks)

    @property
    def total_ion_current(self) -> float:
        """总离子流(TIC)"""
        if self._use_rust:
            return self._rust_spectrum.total_ion_current
        else:
            return sum(intensity for _, intensity in self._peaks)

    @property
    def base_peak_intensity(self) -> float:
        """基峰强度"""
        if self._use_rust:
            return self._rust_spectrum.base_peak_intensity
        else:
            return max((intensity for _, intensity in self._peaks), default=0.0)

    @property
    def base_peak_mz(self) -> float:
        """基峰m/z"""
        if self._use_rust:
            return self._rust_spectrum.base_peak_mz
        else:
            if not self._peaks:
                return 0.0
            return max(self._peaks, key=lambda x: x[1])[0]

    def add_peak(self, mz: float, intensity: float):
        """
        添加单个峰值

        Args:
            mz: 质荷比
            intensity: 强度
        """
        if self._use_rust:
            self._rust_spectrum.add_peak(mz, intensity)
            self._cache_valid = False  # 使缓存失效
        else:
            self._peaks.append((mz, intensity))

    def add_peaks(self, peaks: List[Tuple[float, float]]):
        """
        批量添加峰值 (高性能)

        Args:
            peaks: 峰值列表 [(mz, intensity), ...]
        """
        if not peaks:
            return

        if self._use_rust:
            # 高效批量添加到Rust对象
            mz_array = [p[0] for p in peaks]
            intensity_array = [p[1] for p in peaks]
            self._rust_spectrum.add_peaks(mz_array, intensity_array)
            self._cache_valid = False
        else:
            self._peaks.extend(peaks)

    def clear_peaks(self):
        """清除所有峰值"""
        if self._use_rust:
            self._rust_spectrum.clear_peaks()
            self._cache_valid = False
        else:
            self._peaks.clear()

    def sort_peaks(self):
        """按m/z排序峰值"""
        if self._use_rust:
            self._rust_spectrum.sort_peaks()
            self._cache_valid = False
        else:
            self._peaks.sort(key=lambda x: x[0])

    def filter_by_intensity(self, threshold: float) -> int:
        """
        按强度阈值过滤峰值

        Args:
            threshold: 强度阈值

        Returns:
            int: 被移除的峰值数量
        """
        if self._use_rust:
            removed_count = self._rust_spectrum.filter_by_intensity(threshold)
            self._cache_valid = False
            return removed_count
        else:
            original_count = len(self._peaks)
            self._peaks = [(mz, intensity) for mz, intensity in self._peaks if intensity >= threshold]
            return original_count - len(self._peaks)

    def filter_by_mz_range(self, min_mz: float, max_mz: float) -> int:
        """
        按m/z范围过滤峰值

        Args:
            min_mz: 最小m/z
            max_mz: 最大m/z

        Returns:
            int: 被移除的峰值数量
        """
        if self._use_rust:
            removed_count = self._rust_spectrum.filter_by_mz_range(min_mz, max_mz)
            self._cache_valid = False
            return removed_count
        else:
            original_count = len(self._peaks)
            self._peaks = [(mz, intensity) for mz, intensity in self._peaks
                          if min_mz <= mz <= max_mz]
            return original_count - len(self._peaks)

    def get_mz_range(self, min_mz: float, max_mz: float) -> 'MSObjectRust':
        """
        获取指定m/z范围内的峰值，返回新的MSObject

        Args:
            min_mz: 最小m/z
            max_mz: 最大m/z

        Returns:
            MSObjectRust: 新的MSObject，包含指定范围内的峰值
        """
        if self._use_rust:
            # 使用Rust高效实现
            rust_range = self._rust_spectrum.get_mz_range(min_mz, max_mz)
            new_obj = MSObjectRust(
                level=self._level,
                precursor=self._precursor,
                scan=self._scan,
                additional_info=self._additional_info.copy()
            )
            new_obj._rust_spectrum = rust_range
            return new_obj
        else:
            # Python实现
            filtered_peaks = [(mz, intensity) for mz, intensity in self._peaks
                            if min_mz <= mz <= max_mz]
            return MSObjectRust(
                level=self._level,
                peaks=filtered_peaks,
                precursor=self._precursor,
                scan=self._scan,
                additional_info=self._additional_info.copy(),
                use_rust=False
            )

    def normalize(self) -> float:
        """
        归一化谱图到最大强度

        Returns:
            float: 原始最大强度
        """
        if self._use_rust:
            max_intensity = self._rust_spectrum.normalize()
            self._cache_valid = False
            return max_intensity
        else:
            max_intensity = self.base_peak_intensity
            if max_intensity > 0:
                self._peaks = [(mz, intensity/max_intensity) for mz, intensity in self._peaks]
            return max_intensity

    def set_additional_info(self, key: str, value: Any):
        """设置附加信息"""
        self._additional_info[key] = value

    def clear_additional_info(self):
        """清除附加信息"""
        self._additional_info.clear()

    def set_precursor(
            self,
            ref_scan_number: Optional[int] = None,
            mz: Optional[float] = None,
            charge: Optional[int] = None,
            activation_method: Optional[str] = None,
            activation_energy: Optional[float] = None,
            isolation_window: Optional[Tuple[float, float]] = None
        ):
        """设置前体离子信息"""
        if ref_scan_number is not None:
            self._precursor.ref_scan_number = ref_scan_number
        if mz is not None:
            self._precursor.mz = mz
        if charge is not None:
            self._precursor.charge = charge
        if activation_method is not None:
            self._precursor.activation_method = activation_method
        if activation_energy is not None:
            self._precursor.activation_energy = activation_energy
        if isolation_window is not None:
            self._precursor.isolation_window = isolation_window

    def __len__(self) -> int:
        """返回峰值数量"""
        return self.peak_count

    def __iter__(self):
        """迭代峰值数据"""
        return iter(self.peaks)

    def __repr__(self) -> str:
        """字符串表示"""
        if self._use_rust:
            return f"MSObjectRust(level={self._level}, peaks={self.peak_count}, rust=True)"
        else:
            return f"MSObjectRust(level={self._level}, peaks={self.peak_count}, rust=False)"

    def __str__(self) -> str:
        """字符串表示"""
        return self.__repr__()

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            Dict: 包含所有数据的字典
        """
        return {
            'level': self._level,
            'peaks': self.peaks,
            'peak_count': self.peak_count,
            'total_ion_current': self.total_ion_current,
            'base_peak_intensity': self.base_peak_intensity,
            'base_peak_mz': self.base_peak_mz,
            'precursor': {
                'mz': self._precursor.mz,
                'charge': self._precursor.charge,
                'ref_scan_number': self._precursor.ref_scan_number,
                'isolation_window': self._precursor.isolation_window,
                'activation_method': self._precursor.activation_method,
                'activation_energy': self._precursor.activation_energy,
            },
            'scan': {
                'scan_number': self._scan.scan_number,
                'retention_time': self._scan.retention_time,
                'drift_time': self._scan.drift_time,
                'scan_window': self._scan.scan_window,
                'additional_info': self._scan.additional_info,
            },
            'additional_info': self._additional_info,
            'using_rust': self._use_rust,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], use_rust: bool = True) -> 'MSObjectRust':
        """
        从字典创建MSObject

        Args:
            data: 字典数据
            use_rust: 是否使用Rust实现

        Returns:
            MSObjectRust: 新的MSObject实例
        """
        # 创建前体离子
        precursor_data = data.get('precursor', {})
        precursor = Precursor(
            mz=precursor_data.get('mz', 0.0),
            charge=precursor_data.get('charge', 0),
            ref_scan_number=precursor_data.get('ref_scan_number', -1),
            isolation_window=precursor_data.get('isolation_window'),
            activation_method=precursor_data.get('activation_method', 'unknown'),
            activation_energy=precursor_data.get('activation_energy', 0.0),
        )

        # 创建扫描信息
        scan_data = data.get('scan', {})
        scan = Scan(
            scan_number=scan_data.get('scan_number', -1),
            retention_time=scan_data.get('retention_time', 0.0),
            drift_time=scan_data.get('drift_time', 0.0),
            scan_window=scan_data.get('scan_window'),
            additional_info=scan_data.get('additional_info', {}),
        )

        # 创建MSObject
        return cls(
            level=data.get('level', 1),
            peaks=data.get('peaks', []),
            precursor=precursor,
            scan=scan,
            additional_info=data.get('additional_info', {}),
            use_rust=use_rust
        )


# 向后兼容的别名
MSObject = MSObjectRust