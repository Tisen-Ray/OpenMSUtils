class Precursor(object):
    def __init__(
        self,
        mz:float = 0.0,
        charge:int = 0,
        ref_scan_number:int = -1,
        isolation_window: tuple[float, float] = None,
        activation_method: str = 'unknown',
        activation_energy: float = 0.0,
    ):
        """
        初始化前体离子信息
        :param precursor_list: 前体离子列表，格式为 [PrecursorIon(mz1, charge1), PrecursorIon(mz2, charge2), ...]
        :param ref_scan_number: 参考扫描序号
        :param isolation_window: 隔离窗口，格式为 (mz1, mz2)
        :param activation_method: 激活方法
        """
        if isolation_window is None:
            self.isolation_window = (0.0, 0.0)
        else:
            self.isolation_window = isolation_window

        self.ref_scan_number = ref_scan_number # 参考扫描序号
        self.mz = mz
        self.charge = charge
        self.activation_method = activation_method
        self.activation_energy = activation_energy
    
    def set_activation(self, method:str = None, energy:float = None):
        if not method is None:
            self.activation_method = method
        if not energy is None:
            self.activation_energy = energy
    
    def set_isolation_window(self, window:tuple[float, float]):
        self.isolation_window = window
    
class Scan(object):
    def __init__(
            self, 
            scan_number:int = -1,
            retention_time:float = 0.0,
            drift_time:float = 0.0,
            scan_window:tuple[float, float] = None,
            additional_info:dict = None
    ):
        if additional_info is None:
            self.additional_info = {}
        else:
            self.additional_info = additional_info

        if scan_window is None:
            self.scan_window = (0.0, 0.0)
        else:
            self.scan_window = scan_window

        self.scan_number = scan_number
        self.retention_time = retention_time
        self.drift_time = drift_time
    
    def set_additional_info(self, key:str, value:any):
        self.additional_info[key] = value
    
class MSObject:
    def __init__(
            self,
            level:int = 1,
            peaks: list[tuple[float, float]]=None,
            precursor: Precursor = None,
            scan: Scan = None,
            additional_info: dict=None
    ):
        """
        初始化 MSObject 类，用于存储质谱的基本信息
        :param level: 几级谱（例如：1表示一级谱，2表示二级谱）
        :param peaks: 谱峰数据，格式为 [(mz1, intensity1), (mz2, intensity2), ...]
        :param precursor: 前体离子信息，Precursor 类的实例
        :param scan: 扫描信息，ScanInfo 类的实例
        :param additional_info: 其他信息，字典类型，默认空字典
        """
        if additional_info is None:# 其他信息，字典类型，默认空字典
            self._additional_info = {}
        else:
            self._additional_info = additional_info   
        if peaks is None:# 谱峰数据 [(mz, intensity), ...]
            self._peaks = []
        else:
            self._peaks = peaks
        if precursor is None:# 前体离子信息，Precursor 实例
            self._precursor = Precursor()
        else:
            self._precursor = precursor
        if scan is None:# 扫描信息，ScanInfo 实例
            self._scan = Scan()
        else:
            self._scan = scan
        self.level = level                        # 几级谱

    @property
    def peaks(self):
        return self._peaks

    @property
    def precursor(self):
        return self._precursor

    @property
    def scan(self):
        return self._scan

    @property
    def scan_number(self):
        return self._scan.scan_number

    @property
    def retention_time(self):
        return self._scan.retention_time

    @property
    def additional_info(self):
        return self._additional_info

    def add_peak(self, mz:float, intensity:float):
        self._peaks.append((mz, intensity))
    
    def clear_peaks(self):
        self._peaks = []

    def set_additional_info(self, key:str, value:any):
        self._additional_info[key] = value
    
    def clear_additional_info(self):
        self._additional_info = {}
    
    def set_level(self, level:int):
        self.level = level
    
    def set_precursor(
            self, 
            ref_scan_number:int=None, 
            mz:float=None, 
            charge:int=None, 
            activation_method:str=None, 
            activation_energy:float=None, 
            isolation_window:tuple[float, float]=None
        ):
        if not ref_scan_number is None:
            self._precursor.ref_scan_number = ref_scan_number
        if not mz is None:
            self._precursor.mz = mz
        if not charge is None:
            self._precursor.charge = charge
        if not activation_method is None:
            self._precursor.activation_method = activation_method
        if not activation_energy is None:
            self._precursor.activation_energy = activation_energy
        if not isolation_window is None:
            self._precursor.isolation_window = isolation_window

    def set_scan(
            self, 
            scan_number:int=None, 
            retention_time:float=None, 
            drift_time:float=None, 
            scan_window:tuple[float, float]=None
        ):
        if not scan_number is None:
            self._scan.scan_number = scan_number
        if not retention_time is None:
            self._scan.retention_time = retention_time
        if not drift_time is None:
            self._scan.drift_time = drift_time
        if not scan_window is None:
            self._scan.scan_window = scan_window
    
    def set_scan_additional_info(self, key:str, value:any):
        self._scan.additional_info[key] = value

if __name__ == "__main__":
    pass

