class PrecursorIon:
    def __init__(self, mz:float = 0.0, charge:int = 0):
        """
        初始化前体离子信息
        :param mz: 质荷比
        :param charge: 电荷
        """
        self.mz = mz        # 质荷比
        self.charge = charge # 电荷

    def __repr__(self):
        return f"PrecursorIon(mz={self.mz}, charge={self.charge})"

class Peak:
    def __init__(self, mz:float = 0.0, intensity:float = 0.0):
        self.mz = mz
        self.intensity = intensity

    def __repr__(self):
        return f"Peak(mz={self.mz}, intensity={self.intensity})"


class MSObject:
    def __init__(
            self,
            scan_number: int = -1,
            retention_time: float = 0.0,
            peaks: list[Peak]=None,
            precursor_ion: PrecursorIon = None,
            level:int = 1,
            additional_info: dict=None
    ):
        """
        初始化 MSObject 类，用于存储质谱的基本信息
        :param scan_number: 扫描序号
        :param retention_time: 保留时间
        :param peaks: 谱峰数据，格式为 [(mz1, intensity1), (mz2, intensity2), ...]
        :param precursor_ion: 前体离子信息，PrecursorIon 类的实例
        :param level: 几级谱（例如：1表示一级谱，2表示二级谱）
        :param additional_info: 其他信息，字典类型，默认空字典
        """
        if additional_info is None:
            additional_info = {}
        if peaks is None:
            peaks = []
        if precursor_ion is None:
            precursor_ion = PrecursorIon()
        self.scan_number = scan_number            # 扫描序号
        self.retention_time = retention_time      # 保留时间
        self.peaks = peaks                        # 谱峰数据 [(mz, intensity), ...]
        self.precursor_ion = precursor_ion        # 前体离子信息，PrecursorIon 实例
        self.level = level                        # 几级谱
        self.additional_info = additional_info    # 其他信息

    def __repr__(self):
        return (f"MSObject(scan_number={self.scan_number}, retention_time={self.retention_time}, "
                f"peaks={self.peaks}, precursor_ion={self.precursor_ion}, "
                f"level={self.level}, additional_info={self.additional_info})")

    def add_peak(self, peak: Peak):
        self.peaks.append(peak)

    def add_peak(self, mz:float, intensity:float):
        self.peaks.append(Peak(mz=mz, intensity=intensity))

    def set_peaks(self, peaks: list[Peak]):
        self.peaks = peaks

    def get_peaks(self):
        """获取所有谱峰的 mz 值"""
        return self.peaks

    def set_scan_number(self, scan_number: int):
        self.scan_number = scan_number

    def get_scan_number(self):
        return self.scan_number

    def set_retention_time(self, retention_time: float):
        self.retention_time = retention_time

    def get_retention_time(self):
        return self.retention_time

    def set_precursor_ion(self, precursor_ion:PrecursorIon):
        self.precursor_ion = precursor_ion

    def set_precursor_ion(self, mz:float, charge:int):
        self.precursor_ion = PrecursorIon(mz=mz, charge=charge)

    def get_precursor_ion(self):
        return self.precursor_ion

    def set_level(self, level: int):
        self.level = level

    def get_level(self):
        return self.level

    def set_additional_info(self, additional_info: dict):
        self.additional_info = additional_info

    def add_additional_info(self, key, value):
        """添加额外的质谱信息"""
        self.additional_info[key] = value

    def get_additional_info(self):
        return self.additional_info