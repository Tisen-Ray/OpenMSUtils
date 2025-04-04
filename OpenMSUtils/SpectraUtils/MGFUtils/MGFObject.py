class MGFSpectrum(object):
    """
    MGF格式的质谱数据对象
    """
    def __init__(self):
        self._title = ""
        self._pepmass = 0.0
        self._charge = 0
        self._rtinseconds = 0.0
        self._peaks = []
        self._additional_info = {}
    
    @property
    def title(self):
        """获取标题"""
        return self._title
    
    @title.setter
    def title(self, value):
        """设置标题"""
        self._title = value
    
    @property
    def pepmass(self):
        """获取肽质量"""
        return self._pepmass
    
    @pepmass.setter
    def pepmass(self, value):
        """设置肽质量"""
        self._pepmass = value
    
    @property
    def charge(self):
        """获取电荷"""
        return self._charge
    
    @charge.setter
    def charge(self, value):
        """设置电荷"""
        self._charge = value
    
    @property
    def rtinseconds(self):
        """获取保留时间（秒）"""
        return self._rtinseconds
    
    @rtinseconds.setter
    def rtinseconds(self, value):
        """设置保留时间（秒）"""
        self._rtinseconds = value
    
    @property
    def peaks(self):
        """获取峰值列表"""
        return self._peaks
    
    @peaks.setter
    def peaks(self, value):
        """设置峰值列表"""
        self._peaks = value
    
    @property
    def additional_info(self):
        """获取额外信息字典"""
        return self._additional_info
    
    @additional_info.setter
    def additional_info(self, value):
        """设置额外信息字典"""
        self._additional_info = value
    
    def add_peak(self, mz, intensity):
        """添加峰值"""
        self._peaks.append((mz, intensity))
    
    def set_additional_info(self, key, value):
        """设置额外信息"""
        self._additional_info[key] = value
    
    def to_mgf_string(self):
        """转换为MGF格式字符串"""
        lines = ["BEGIN IONS"]
        
        # 添加标题
        if self._title:
            lines.append(f"TITLE={self._title}")
        
        # 添加肽质量
        if self._pepmass > 0:
            lines.append(f"PEPMASS={self._pepmass}")
        
        # 添加电荷
        if self._charge != 0:
            charge_str = str(abs(self._charge))
            charge_str += "+" if self._charge > 0 else "-"
            lines.append(f"CHARGE={charge_str}")
        
        # 添加保留时间
        if self._rtinseconds > 0:
            lines.append(f"RTINSECONDS={self._rtinseconds}")
        
        # 添加额外信息
        for key, value in self._additional_info.items():
            lines.append(f"{key}={value}")
        
        # 添加峰值数据
        for mz, intensity in self._peaks:
            lines.append(f"{mz} {intensity}")
        
        lines.append("END IONS")
        
        return "\n".join(lines)

class MGFObject(object):
    """
    MGF文件对象，包含多个MGFSpectrum
    """
    def __init__(self):
        self._spectra = []
        self._metadata = {}
    
    @property
    def spectra(self):
        """获取谱图列表"""
        return self._spectra
    
    @spectra.setter
    def spectra(self, value):
        """设置谱图列表"""
        self._spectra = value
    
    @property
    def metadata(self):
        """获取元数据字典"""
        return self._metadata
    
    @metadata.setter
    def metadata(self, value):
        """设置元数据字典"""
        self._metadata = value
    
    def add_spectrum(self, spectrum):
        """添加谱图"""
        self._spectra.append(spectrum)
    
    def set_metadata(self, key, value):
        """设置元数据"""
        self._metadata[key] = value
    
    def to_mgf_string(self):
        """转换为MGF格式字符串"""
        # 添加元数据作为注释
        lines = []
        for key, value in self._metadata.items():
            lines.append(f"# {key}={value}")
        
        # 添加所有谱图
        for spectrum in self._spectra:
            lines.append(spectrum.to_mgf_string())
            lines.append("")  # 添加空行分隔谱图
        
        return "\n".join(lines) 