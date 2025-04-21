from lxml import etree
from .ParamObject import CVParam, UserParam

class ScanWindow(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._cv_params = []
            self._user_params = []
            return
            
        self._cv_params = []
        self._user_params = []
        for child in etree_element:
            if child.tag.endswith("cvParam"):
                self._cv_params.append(CVParam(child))
            elif child.tag.endswith("userParam"):
                self._user_params.append(UserParam(child))
    
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
    
    @property
    def cv_params(self):
        return self._cv_params
    
    @cv_params.setter
    def cv_params(self, value):
        self._cv_params = value

    @property
    def user_params(self):
        return self._user_params
    
    @user_params.setter
    def user_params(self, value):
        self._user_params = value
    
    @property
    def attrib(self):
        return self._attrib
    
    @attrib.setter
    def attrib(self, value):
        self._attrib = value

    def to_xml(self) -> etree._Element:
        element = etree.Element("scanWindow")
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
        return element

class Scan(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._cv_params = []
            self._user_params = []
            self._scan_windows = []
            self._attrib = {}
            return
            
        self._cv_params = []
        self._user_params = []
        self._scan_windows = []
        self._attrib = etree_element.attrib

        for child in etree_element:
            if child.tag.endswith("cvParam"):
                self._cv_params.append(CVParam(child))
            elif child.tag.endswith("userParam"):
                self._user_params.append(UserParam(child))
            elif child.tag.endswith("scanWindowList"):
                self._parse_scan_window_list(child)
    
    def _parse_scan_window_list(self, etree_element: etree._Element):
        for child in etree_element:
            if child.tag.endswith("scanWindow"):
                self._scan_windows.append(ScanWindow(child))
                
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
        
    def add_scan_window(self, scan_window:ScanWindow):
        self._scan_windows.append(scan_window)
    
    @property
    def cv_params(self):
        return self._cv_params
    
    @cv_params.setter
    def cv_params(self, value):
        self._cv_params = value

    @property
    def user_params(self):
        return self._user_params
    
    @user_params.setter
    def user_params(self, value):
        self._user_params = value
    
    @property
    def scan_windows(self):
        return self._scan_windows
    
    @scan_windows.setter
    def scan_windows(self, value):
        self._scan_windows = value
    
    @property
    def attrib(self):
        return self._attrib
    
    @attrib.setter
    def attrib(self, value):
        self._attrib = value

    def to_xml(self) -> etree._Element:
        element = etree.Element("scan")
        for key, value in self._attrib.items():
            element.set(key, value)
            
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
            
        if len(self._scan_windows) > 0:
            window_list = etree.SubElement(element, "scanWindowList")
            window_list.set("count", str(len(self._scan_windows)))
            
            for window in self._scan_windows:
                window_list.append(window.to_xml())
                
        return element

class BinaryDataArray(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._cv_params = []
            self._user_params = []
            self._binary = None
            self._attrib = {}
            return

        self._cv_params = []
        self._user_params = []
        self._binary = None
        self._attrib = etree_element.attrib

        for child in etree_element:
            if child.tag.endswith("cvParam"):
                self._cv_params.append(CVParam(child))
            elif child.tag.endswith("userParam"):
                self._user_params.append(UserParam(child))
            elif child.tag.endswith("binary"):
                self._binary = child.text
    
    @property
    def attrib(self):
        """获取属性字典"""
        return self._attrib
    
    @attrib.setter
    def attrib(self, value):
        """设置属性字典"""
        self._attrib = value
    
    @property
    def cv_params(self):
        """获取CV参数列表"""
        return self._cv_params
    
    @cv_params.setter
    def cv_params(self, value):
        """设置CV参数列表"""
        self._cv_params = value
    
    @property
    def user_params(self):
        """获取用户参数列表"""
        return self._user_params
    
    @user_params.setter
    def user_params(self, value):
        """设置用户参数列表"""
        self._user_params = value
    
    @property
    def binary(self):
        """获取二进制数据"""
        return self._binary
    
    @binary.setter
    def binary(self, value):
        """设置二进制数据"""
        self._binary = value
    
    def add_cv_param(self, cv_param):
        """添加CV参数"""
        self._cv_params.append(cv_param)
    
    def add_user_param(self, user_param):
        """添加用户参数"""
        self._user_params.append(user_param)
    
    
    def to_xml(self) -> etree._Element:
        element = etree.Element("binaryDataArray")
        for key, value in self._attrib.items():
            element.set(key, value)
            
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
            
        if self._binary is not None:
            binary = etree.SubElement(element, "binary")
            binary.text = self._binary
            
        return element

class IsolationWindow(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._cv_params = []
            self._user_params = []
            return
            
        self._cv_params = []
        self._user_params = []
        for child in etree_element:
            if child.tag.endswith("cvParam"):
                self._cv_params.append(CVParam(child))
            elif child.tag.endswith("userParam"):
                self._user_params.append(UserParam(child))
    
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
    
    @property
    def cv_params(self):
        return self._cv_params
    
    @cv_params.setter
    def cv_params(self, value):
        self._cv_params = value

    @property
    def user_params(self):
        return self._user_params
    
    @user_params.setter
    def user_params(self, value):
        self._user_params = value

    @property
    def attrib(self):
        return self._attrib

    @attrib.setter
    def attrib(self, value):
        self._attrib = value
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("isolationWindow")
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
        return element

class SelectedIon(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._cv_params = []
            self._user_params = []
            return
            
        self._cv_params = []
        self._user_params = []
        for child in etree_element:
            if child.tag.endswith("cvParam"):
                self._cv_params.append(CVParam(child))
            elif child.tag.endswith("userParam"):
                self._user_params.append(UserParam(child))
    
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
    
    @property
    def cv_params(self):
        return self._cv_params
    
    @cv_params.setter
    def cv_params(self, value):
        self._cv_params = value

    @property
    def user_params(self):
        return self._user_params
    
    @user_params.setter
    def user_params(self, value):
        self._user_params = value
    
    @property
    def attrib(self):
        return self._attrib

    @attrib.setter
    def attrib(self, value):
        self._attrib = value
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("selectedIon")
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
        return element

class Activation(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._cv_params = []
            self._user_params = []
            return
            
        self._cv_params = []
        self._user_params = []
        for child in etree_element:
            if child.tag.endswith("cvParam"):
                self._cv_params.append(CVParam(child))
            elif child.tag.endswith("userParam"):
                self._user_params.append(UserParam(child))
    
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
    
    @property
    def cv_params(self):
        return self._cv_params
    
    @cv_params.setter
    def cv_params(self, value):
        self._cv_params = value

    @property
    def user_params(self):
        return self._user_params
    
    @user_params.setter
    def user_params(self, value):
        self._user_params = value
    
    @property
    def attrib(self):
        return self._attrib

    @attrib.setter
    def attrib(self, value):
        self._attrib = value
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("activation")
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
        return element

class Precursor(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._attrib = {}
            self._isolation_window = None
            self._selected_ions = []
            self._activation = None
            return
            
        self._attrib = etree_element.attrib
        self._isolation_window = None
        self._selected_ions = []
        self._activation = None
        
        for child in etree_element:
            if child.tag.endswith("isolationWindow"):
                self._isolation_window = IsolationWindow(child)
            elif child.tag.endswith("selectedIonList"):
                for selected_ion in [selected_ion for selected_ion in child if selected_ion.tag.endswith("selectedIon")]:
                    self._selected_ions.append(SelectedIon(selected_ion))
            elif child.tag.endswith("activation"):
                self._activation = Activation(child)
    
    def add_selected_ion(self, selected_ion:SelectedIon):
        self._selected_ions.append(selected_ion)
        
    @property
    def isolation_window(self):
        return self._isolation_window

    @isolation_window.setter
    def isolation_window(self, value):
        self._isolation_window = value
    
    @property
    def selected_ions(self):
        return self._selected_ions
    
    @selected_ions.setter
    def selected_ions(self, value):
        self._selected_ions = value
        
    @property
    def activation(self):
        return self._activation
    
    @activation.setter
    def activation(self, value):
        self._activation = value
    
    @property
    def attrib(self):
        return self._attrib
    
    @attrib.setter
    def attrib(self, value):
        self._attrib = value

    def to_xml(self) -> etree._Element:
        element = etree.Element("precursor")
        for key, value in self._attrib.items():
            element.set(key, value)
            
        if self._isolation_window is not None:
            element.append(self._isolation_window.to_xml())
            
        if len(self._selected_ions) > 0:
            selected_ion_list = etree.SubElement(element, "selectedIonList")
            selected_ion_list.set("count", str(len(self._selected_ions)))
            for selected_ion in self._selected_ions:
                selected_ion_list.append(selected_ion.to_xml())
                
        if self._activation is not None:
            element.append(self._activation.to_xml())
            
        return element

class Spectrum(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._cv_params = []
            self._user_params = []
            self._scan_list = []
            self._precursors = []
            self._binary_data_arrays = []
            self._attrib = {}
            return
        
        self._cv_params = []
        self._user_params = []
        self._scan_list = []
        self._precursors = []
        self._binary_data_arrays = []
        self._attrib = etree_element.attrib

        for child in etree_element:
            if child.tag.endswith("cvParam"):
                self._cv_params.append(CVParam(child))
            elif child.tag.endswith("userParam"):
                self._user_params.append(UserParam(child))
            elif child.tag.endswith("scanList"):
                self._parse_scan_list(child)
            elif child.tag.endswith("precursorList"):
                self._parse_precursor_list(child)
            elif child.tag.endswith("binaryDataArrayList"):
                self._parse_binary_data_array_list(child)

    def _parse_scan_list(self, etree_element: etree._Element):
        for child in etree_element:
            if child.tag.endswith("scan"):
                self._scan_list.append(Scan(child))
                
    def _parse_precursor_list(self, etree_element: etree._Element):
        for child in etree_element:
            if child.tag.endswith("precursor"):
                self._precursors.append(Precursor(child))
                
    def _parse_binary_data_array_list(self, etree_element: etree._Element):
        for child in etree_element:
            if child.tag.endswith("binaryDataArray"):
                self._binary_data_arrays.append(BinaryDataArray(child))
                
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
        
    def add_precursor(self, precursor:Precursor):
        self._precursors.append(precursor)
    
    def add_scan(self, scan:Scan):
        self._scan_list.append(scan)
        
    def add_binary_data_array(self, array:BinaryDataArray):
        self._binary_data_arrays.append(array)

    @property
    def attrib(self):
        """获取属性字典"""
        return self._attrib
    
    @attrib.setter
    def attrib(self, value):
        """设置属性字典"""
        self._attrib = value
    
    @property
    def cv_params(self):
        """获取CV参数列表"""
        return self._cv_params
    
    @cv_params.setter
    def cv_params(self, value):
        """设置CV参数列表"""
        self._cv_params = value
    
    @property
    def user_params(self):
        """获取用户参数列表"""
        return self._user_params
    
    @user_params.setter
    def user_params(self, value):
        """设置用户参数列表"""
        self._user_params = value
    
    @property
    def scan_list(self):
        """获取扫描列表"""
        return self._scan_list
    
    @scan_list.setter
    def scan_list(self, value):
        """设置扫描列表"""
        self._scan_list = value
    
    @property
    def precursor_list(self):
        """获取前体离子列表"""
        return self._precursors
    
    @precursor_list.setter
    def precursor_list(self, value):
        """设置前体离子列表"""
        self._precursors = value

    @property
    def binary_data_arrays(self):
        """获取二进制数据数组"""
        return self._binary_data_arrays
    
    @binary_data_arrays.setter
    def binary_data_arrays(self, value):
        """设置二进制数据数组"""
        self._binary_data_arrays = value

    def to_xml(self) -> etree._Element:
        element = etree.Element("spectrum")
        for key, value in self._attrib.items():
            element.set(key, value)
            
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
            
        if len(self._scan_list) > 0:
            scan_list = etree.SubElement(element, "scanList")
            scan_list.set("count", str(len(self._scan_list)))
            for scan in self._scan_list:
                scan_list.append(scan.to_xml())
                
        if len(self._precursors) > 0:
            precursor_list = etree.SubElement(element, "precursorList")
            precursor_list.set("count", str(len(self._precursors)))
            for precursor in self._precursors:
                precursor_list.append(precursor.to_xml())
                
        if len(self._binary_data_arrays) > 0:
            binary_list = etree.SubElement(element, "binaryDataArrayList")
            binary_list.set("count", str(len(self._binary_data_arrays)))
            for array in self._binary_data_arrays:
                binary_list.append(array.to_xml())
                
        return element

class Chromatogram(object):

    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._cv_params = []
            self._user_params = []
            self._binary_data_arrays = []
            self._attrib = {}
            return
        
        self._cv_params = []
        self._user_params = []
        self._binary_data_arrays = []
        self._attrib = etree_element.attrib

        for child in etree_element:
            if child.tag.endswith("cvParam"):
                self._cv_params.append(CVParam(child))
            elif child.tag.endswith("userParam"):
                self._user_params.append(UserParam(child))
            elif child.tag.endswith("binaryDataArrayList"):
                self._parse_binary_data_array_list(child)
    
    def _parse_binary_data_array_list(self, etree_element: etree._Element):
        for child in etree_element:
            if child.tag.endswith("binaryDataArray"):
                self._binary_data_arrays.append(BinaryDataArray(child))
    
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
    
    def add_binary_data_array(self, array:BinaryDataArray):
        self._binary_data_arrays.append(array)
        
    @property
    def cv_params(self):
        return self._cv_params
    
    @cv_params.setter
    def cv_params(self, value):
        self._cv_params = value

    @property
    def user_params(self):
        return self._user_params
    
    @user_params.setter
    def user_params(self, value):
        self._user_params = value

    @property
    def binary_data_arrays(self):
        return self._binary_data_arrays
    
    @binary_data_arrays.setter
    def binary_data_arrays(self, value):
        self._binary_data_arrays = value
    
    @property
    def attrib(self):
        return self._attrib
    
    @attrib.setter
    def attrib(self, value):
        self._attrib = value
    
    def to_xml(self) -> etree._Element:
        element = etree.Element("chromatogram")
        for key, value in self._attrib.items():
            element.set(key, value)
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
            
        if len(self._binary_data_arrays) > 0:
            binary_list = etree.SubElement(element, "binaryDataArrayList")
            binary_list.set("count", str(len(self._binary_data_arrays)))
            for array in self._binary_data_arrays:
                binary_list.append(array.to_xml())
                
        return element
  
class Run(object):
    def __init__(self, etree_element: etree._Element = None, parse_spectra = True, parse_chromatograms = True):
        """
        初始化 Run 类
        
        Args:
            etree_element: XML元素
            parse_spectra: 是否解析谱图列表，默认为True
            parse_chromatograms: 是否解析色谱图列表，默认为True
        """
        if etree_element is None:
            self._attrib = {}
            self._cv_params = []
            self._user_params = []
            self._spectra_list = []
            self._chromatogram_list = []
            return
            
        self._cv_params = []
        self._user_params = []
        self._spectra_list = []
        self._chromatogram_list = []
        self._attrib = etree_element.attrib
        
        for child in etree_element:
            if child.tag.endswith("cvParam"):
                self._cv_params.append(CVParam(child))
            elif child.tag.endswith("userParam"):
                self._user_params.append(UserParam(child))
            elif child.tag.endswith("spectrumList") and parse_spectra:
                self._parse_spectra_list(child)
            elif child.tag.endswith("chromatogramList") and parse_chromatograms:
                self._parse_chromatogram_list(child)

    def _parse_spectra_list(self, etree_element: etree._Element):
        for child in etree_element:
            if child.tag.endswith("spectrum"):
                self._spectra_list.append(Spectrum(child))

    def _parse_chromatogram_list(self, etree_element: etree._Element):
        for child in etree_element:
            if child.tag.endswith("chromatogram"):
                self._chromatogram_list.append(Chromatogram(child))
            
    @property
    def attrib(self):
        """获取属性字典"""
        return self._attrib
    
    @attrib.setter
    def attrib(self, value):
        """设置属性字典"""
        self._attrib = value
    
    @property
    def cv_params(self):
        """获取CV参数列表"""
        return self._cv_params
    
    @cv_params.setter
    def cv_params(self, value):
        """设置CV参数列表"""
        self._cv_params = value
    
    @property
    def user_params(self):
        """获取用户参数列表"""
        return self._user_params
    
    @user_params.setter
    def user_params(self, value):
        """设置用户参数列表"""
        self._user_params = value
    
    @property
    def spectra_list(self):
        """获取谱图列表"""
        return self._spectra_list
    
    @spectra_list.setter
    def spectra_list(self, value):
        """设置谱图列表"""
        self._spectra_list = value
    
    @property
    def chromatogram_list(self):
        """获取色谱图列表"""
        return self._chromatogram_list
    
    @chromatogram_list.setter
    def chromatogram_list(self, value):
        """设置色谱图列表"""
        self._chromatogram_list = value
    
    def add_spectrum(self, spectrum):
        """添加谱图"""
        self._spectra_list.append(spectrum)
    
    def add_chromatogram(self, chromatogram):
        """添加色谱图"""
        self._chromatogram_list.append(chromatogram)
    
    def add_cv_param(self, cv_param):
        """添加CV参数"""
        self._cv_params.append(cv_param)
    
    def add_user_param(self, user_param):
        """添加用户参数"""
        self._user_params.append(user_param)

    def to_xml(self) -> etree._Element:
        element = etree.Element("run")
        for key, value in self._attrib.items():
            element.set(key, value)
            
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
            
        if len(self._spectra_list) > 0:
            spectrum_list = etree.SubElement(element, "spectrumList")
            spectrum_list.set("count", str(len(self._spectra_list)))
            for spectrum in self._spectra_list:
                spectrum_list.append(spectrum.to_xml())
            
        if len(self._chromatogram_list) > 0:
            chromatogram_list = etree.SubElement(element, "chromatogramList")
            chromatogram_list.set("count", str(len(self._chromatogram_list)))
            for chromatogram in self._chromatogram_list:
                chromatogram_list.append(chromatogram.to_xml())

        return element

class MZMLObject(object):
    def __init__(self, etree_element: etree._Element = None, parse_spectra=True, parse_chromatograms=True):
        """
        初始化 MZMLObject 类
        
        Args:
            etree_element: XML元素
            parse_spectra: 是否解析谱图列表，默认为True
            parse_chromatograms: 是否解析色谱图列表，默认为True
        """
        if etree_element is None:
            self.nsmap = None
            self.attrib = {}
            self.cv_list = None
            self.file_description = None
            self.referenceable_param_group_list = None
            self.sample_list = None
            self.instrument_configuration_list = None
            self.software_list = None
            self.data_processing_list = None
            self.acquisition_list = None
            self.run = None
            return
            
        self.nsmap = etree_element.nsmap
        self.attrib = etree_element.attrib
        self.cv_list = None
        self.file_description = None
        self.referenceable_param_group_list = None
        self.sample_list = None
        self.instrument_configuration_list = None
        self.software_list = None
        self.data_processing_list = None
        self.acquisition_list = None
        self.run = None

        for child in etree_element:
            if child.tag.endswith('cvList'):
                self.cv_list = child
        
            if child.tag.endswith('fileDescription'):
                self.file_description = child

            if child.tag.endswith('referenceableParamGroupList'):
                self.referenceable_param_group_list = child
        
            if child.tag.endswith('sampleList'):
                self.sample_list = child
                
            if child.tag.endswith('instrumentConfigurationList'):
                self.instrument_configuration_list = child
        
            if child.tag.endswith('softwareList'):
                self.software_list = child
                
            if child.tag.endswith('dataProcessingList'):
                self.data_processing_list = child

            if child.tag.endswith('run'):
                # 创建Run对象，但根据参数决定是否解析spectrumList和chromatogramList
                self.run = Run(child, parse_spectra, parse_chromatograms)

    def add_cv_param(self, cv_param:CVParam):
        self.cv_list.append(cv_param)
