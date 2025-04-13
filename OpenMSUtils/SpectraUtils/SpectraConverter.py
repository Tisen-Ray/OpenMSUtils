import base64
import struct
import zlib
from typing import Type, Any

from .MSObject import MSObject
from .MZMLUtils import Spectrum as MZMLSpectrum, BinaryDataArray, CVParam
from .MGFUtils import MGFSpectrum
from .MSFileUtils import MSSpectrum

class SpectraConverter:
    """
    用于不同格式的质谱数据与MSObject之间的转换
    支持多种格式的质谱数据，如mzML、MGF、MS1/MS2等
    """
    
    @staticmethod
    def to_msobject(spectrum: Any) -> MSObject:
        """
        将不同格式的质谱数据转换为MSObject
        
        Args:
            spectrum: 质谱数据对象，可以是MZMLSpectrum、MGFSpectrum或MSSpectrum
            
        Returns:
            MSObject对象
            
        Raises:
            TypeError: 如果输入的对象类型不受支持
        """
        if isinstance(spectrum, MZMLSpectrum):
            return SpectraConverter._mzml_to_msobject(spectrum)
        elif isinstance(spectrum, MGFSpectrum):
            return SpectraConverter._mgf_to_msobject(spectrum)
        elif isinstance(spectrum, MSSpectrum):
            return SpectraConverter._ms_to_msobject(spectrum)
        else:
            raise TypeError(f"Unsupported spectrum type: {type(spectrum).__name__}")
    
    @staticmethod
    def to_spectra(ms_object: MSObject, spectra_type: Type) -> Any:
        """
        将MSObject转换为指定类型的质谱数据
        
        Args:
            ms_object: MSObject对象
            spectra_type: 目标质谱数据类型，如MZMLSpectrum、MGFSpectrum或MSSpectrum
            
        Returns:
            指定类型的质谱数据对象
            
        Raises:
            TypeError: 如果目标类型不受支持
        """
        if spectra_type == MZMLSpectrum:
            return SpectraConverter._msobject_to_mzml(ms_object)
        elif spectra_type == MGFSpectrum:
            return SpectraConverter._msobject_to_mgf(ms_object)
        elif spectra_type == MSSpectrum:
            return SpectraConverter._msobject_to_ms(ms_object)
        else:
            raise TypeError(f"Unsupported target spectrum type: {spectra_type.__name__}")
    
    @staticmethod
    def _mzml_to_msobject(spectrum: MZMLSpectrum) -> MSObject:
        """
        将mzML的Spectrum对象转换为MSObject
        
        Args:
            spectrum: MZMLObject中的Spectrum对象
            
        Returns:
            MSObject对象
        """
        # 创建MSObject
        ms_object = MSObject()
        
        # 设置MS级别
        ms_level = 1  # 默认为MS1
        for cv_param in spectrum.cv_params:
            if cv_param.attrib.get('accession') == 'MS:1000511':  # MS Level
                ms_level = int(cv_param.attrib.get('value', '1'))
                break
        ms_object.set_level(ms_level)
        
        # 处理scan信息
        if spectrum.scan_list and len(spectrum.scan_list) > 0:
            scan = spectrum.scan_list[0]
            scan_number = -1
            retention_time = 0.0
            drift_time = 0.0
            scan_window = (0.0, 0.0)
            
            # 获取scan number
            if 'index' in spectrum.attrib:
                scan_number = int(spectrum.attrib.get('index'))
            if 'id' in spectrum.attrib:
                # 尝试从id中提取scan number
                id_str = spectrum.attrib.get('id', '')
                if 'scan=' in id_str:
                    scan_number = int(id_str.split('scan=')[1].split()[0]) # 如果id中包含scan number，则提取scan number
            
            # 获取retention time和drift time
            for cv_param in scan.cv_params:
                accession = cv_param.attrib.get('accession', '')
                if accession == 'MS:1000016':  # scan start time
                    value = float(cv_param.attrib.get('value', '0'))
                    unit = cv_param.attrib.get('unitAccession', '')
                    # 转换为秒
                    if unit == 'UO:0000031':  # minutes
                        retention_time = value * 60
                    elif unit == 'UO:0000028':  # milliseconds
                        retention_time = value / 1000
                    else:
                        retention_time = value
                elif accession == 'MS:1002476':  # ion mobility drift time
                    value = float(cv_param.attrib.get('value', '0'))
                    unit = cv_param.attrib.get('unitAccession', '')
                    # 转换为秒
                    if unit == 'UO:0000031':  # minutes
                        drift_time = value * 60
                    elif unit == 'UO:0000028':  # milliseconds
                        drift_time = value / 1000
                    else:
                        drift_time = value
            
            # 获取scan window
            if scan.scan_windows and len(scan.scan_windows) > 0:
                scan_window_obj = scan.scan_windows[0]
                low = 0.0
                high = 0.0
                for cv_param in scan_window_obj.cv_params:
                    accession = cv_param.attrib.get('accession', '')
                    if accession == 'MS:1000501':  # scan window lower limit
                        low = float(cv_param.attrib.get('value', '0'))
                    elif accession == 'MS:1000500':  # scan window upper limit
                        high = float(cv_param.attrib.get('value', '0'))
                scan_window = (low, high)
            
            ms_object.set_scan(scan_number, retention_time, drift_time, scan_window)
            
            # 添加scan的额外信息
            for cv_param in scan.cv_params:
                name = cv_param.attrib.get('name', '')
                value = cv_param.attrib.get('value', '')
                if name and value and name not in ['scan start time', 'ion mobility drift time']:
                    ms_object.set_scan_additional_info(name, value)
        
        # 处理precursor信息
        if spectrum.precursor_list and len(spectrum.precursor_list) > 0:
            precursor = spectrum.precursor_list[0]
            ref_scan_number = -1
            mz = 0.0
            charge = 0
            activation_method = 'unknown'
            activation_energy = 0.0
            isolation_window = (0.0, 0.0)
            
            # 获取参考scan number
            if 'spectrumRef' in precursor.attrib:
                ref_id = precursor.attrib.get('spectrumRef', '')
                if 'scan=' in ref_id:
                    ref_scan_number = int(ref_id.split('scan=')[1].split()[0])
            
            # 获取isolation window
            if precursor.isolation_window:
                low = 0.0
                high = 0.0
                target = 0.0
                for cv_param in precursor.isolation_window.cv_params:
                    accession = cv_param.attrib.get('accession', '')
                    if accession == 'MS:1000827':  # isolation window target m/z
                        target = float(cv_param.attrib.get('value', '0'))
                    elif accession == 'MS:1000828':  # isolation window lower offset
                        low = float(cv_param.attrib.get('value', '0'))
                    elif accession == 'MS:1000829':  # isolation window upper offset
                        high = float(cv_param.attrib.get('value', '0'))
                isolation_window = (target - low, target + high)
            
            # 获取selected ion信息
            if precursor.selected_ions and len(precursor.selected_ions) > 0:
                selected_ion = precursor.selected_ions[0]
                for cv_param in selected_ion.cv_params:
                    accession = cv_param.attrib.get('accession', '')
                    if accession == 'MS:1000744':  # selected ion m/z
                        mz = float(cv_param.attrib.get('value', '0'))
                    elif accession == 'MS:1000041':  # charge state
                        charge = int(cv_param.attrib.get('value', '0'))
            
            # 获取activation信息
            if precursor.activation:
                for cv_param in precursor.activation.cv_params:
                    accession = cv_param.attrib.get('accession', '')
                    # 检查激活方法
                    if accession in ['MS:1000133', 'MS:1000134', 'MS:1000422', 'MS:1000250']:
                        activation_method = cv_param.attrib.get('name', 'unknown')
                    # 检查激活能量
                    elif accession == 'MS:1000045':  # collision energy
                        activation_energy = float(cv_param.attrib.get('value', '0'))
            
            ms_object.set_precursor(ref_scan_number, mz, charge, activation_method, 
                                   activation_energy, isolation_window)
        
        # 处理峰值数据
        if spectrum.binary_data_arrays and len(spectrum.binary_data_arrays) >= 2:
            mz_array = None
            intensity_array = None
            
            # 找到m/z和intensity数组
            for binary_data_array in spectrum.binary_data_arrays:
                array_type = None
                precision = 64  # 默认为双精度
                compression = False
                
                for cv_param in binary_data_array.cv_params:
                    accession = cv_param.attrib.get('accession', '')
                    if accession == 'MS:1000514':  # m/z array
                        array_type = 'mz'
                    elif accession == 'MS:1000515':  # intensity array
                        array_type = 'intensity'
                    elif accession == 'MS:1000521':  # 32-bit float
                        precision = 32
                    elif accession == 'MS:1000523':  # 64-bit float
                        precision = 64
                    elif accession == 'MS:1000574':  # zlib compression
                        compression = True
                
                if array_type and binary_data_array.binary:
                    # 解码二进制数据
                    decoded_data = base64.b64decode(binary_data_array.binary)
                    
                    # 解压缩(如果需要)
                    if compression:
                        decoded_data = zlib.decompress(decoded_data)
                    
                    # 根据精度解析数据
                    if precision == 32:
                        fmt = 'f' * (len(decoded_data) // 4)
                        values = struct.unpack(fmt, decoded_data)
                    else:  # 64-bit
                        fmt = 'd' * (len(decoded_data) // 8)
                        values = struct.unpack(fmt, decoded_data)
                    
                    if array_type == 'mz':
                        mz_array = values
                    elif array_type == 'intensity':
                        intensity_array = values
            
            # 如果找到了m/z和intensity数组，则添加峰值
            if mz_array and intensity_array:
                ms_object.clear_peaks()  # 清除现有峰值
                for mz, intensity in zip(mz_array, intensity_array):
                    ms_object.add_peak(mz, intensity)
        
        # 添加额外信息
        for cv_param in spectrum.cv_params:
            name = cv_param.attrib.get('name', '')
            value = cv_param.attrib.get('value', '')
            if name and name != 'ms level':
                ms_object.set_additional_info(name, value)
        
        return ms_object
    
    @staticmethod
    def _msobject_to_mzml(ms_object: MSObject) -> MZMLSpectrum:
        """
        将MSObject转换为mzML的Spectrum对象
        
        Args:
            ms_object: MSObject对象
            
        Returns:
            MZMLObject中的Spectrum对象
        """
        # 创建Spectrum对象
        spectrum = MZMLSpectrum()
        
        # 设置基本属性
        spectrum.attrib = {
            'index': str(ms_object.scan_number),
            'id': f'scan={ms_object.scan_number}',
            'defaultArrayLength': str(len(ms_object.peaks))
        }
        
        # 添加MS级别
        ms_level_param = CVParam()
        ms_level_param.attrib = {
            'cvRef': 'MS',
            'accession': 'MS:1000511',
            'name': 'ms level',
            'value': str(ms_object.level)
        }
        spectrum.add_cv_param(ms_level_param)
        
        # 添加scan信息
        from OpenMSUtils.SpectraUtils.MZMLUtils import Scan as MZMLScan, ScanWindow
        
        mzml_scan = MZMLScan()
        mzml_scan._attrib = {'scanNumber': str(ms_object.scan_number)}
        
        # 添加retention time
        if ms_object.retention_time > 0:
            rt_param = CVParam()
            rt_param._attrib = {
                'cvRef': 'MS',
                'accession': 'MS:1000016',
                'name': 'scan start time',
                'value': str(ms_object.retention_time / 60),  # 转换为分钟
                'unitCvRef': 'UO',
                'unitAccession': 'UO:0000031',
                'unitName': 'minute'
            }
            mzml_scan.add_cv_param(rt_param)
        
        # 添加drift time
        if ms_object.scan.drift_time > 0:
            dt_param = CVParam()
            dt_param._attrib = {
                'cvRef': 'MS',
                'accession': 'MS:1002476',
                'name': 'ion mobility drift time',
                'value': str(ms_object.scan.drift_time * 1000),  # 转换为毫秒
                'unitCvRef': 'UO',
                'unitAccession': 'UO:0000028',
                'unitName': 'millisecond'

            }
            mzml_scan.add_cv_param(dt_param)
        
        # 添加scan window
        if ms_object.scan.scan_window != (0.0, 0.0):
            scan_window = ScanWindow()
            
            # 添加下限
            low_param = CVParam()
            low_param._attrib = {
                'cvRef': 'MS',
                'accession': 'MS:1000501',
                'name': 'scan window lower limit',
                'value': str(ms_object.scan.scan_window[0])
            }
            scan_window.add_cv_param(low_param)
            
            # 添加上限
            high_param = CVParam()
            high_param._attrib = {
                'cvRef': 'MS',
                'accession': 'MS:1000500',
                'name': 'scan window upper limit',
                'value': str(ms_object.scan.scan_window[1])
            }
            scan_window.add_cv_param(high_param)
            
            mzml_scan._scan_windows = [scan_window]
        
        # 添加scan的额外信息
        for key, value in ms_object.scan.additional_info.items():
            user_param = CVParam()
            user_param._attrib = {
                'name': key,
                'value': str(value)
            }
            mzml_scan.add_cv_param(user_param)
        
        spectrum._scan_list = [mzml_scan]
        
        # 添加precursor信息
        if ms_object.level > 1:
            from OpenMSUtils.SpectraUtils.MZMLUtils import Precursor as MZMLPrecursor
            from OpenMSUtils.SpectraUtils.MZMLUtils import IsolationWindow, SelectedIon, Activation
            
            mzml_precursor = MZMLPrecursor()
            
            # 设置参考spectrum
            if ms_object.precursor.ref_scan_number > 0:
                mzml_precursor._attrib = {
                    'spectrumRef': f'scan={ms_object.precursor.ref_scan_number}'
                }
            
            # 添加isolation window
            if ms_object.precursor.isolation_window != (0.0, 0.0):
                isolation_window = IsolationWindow()
                
                # 计算target m/z和offset
                target = (ms_object.precursor.isolation_window[0] + ms_object.precursor.isolation_window[1]) / 2
                low_offset = target - ms_object.precursor.isolation_window[0]
                high_offset = ms_object.precursor.isolation_window[1] - target
                
                # 添加target m/z
                target_param = CVParam()
                target_param._attrib = {
                    'cvRef': 'MS',
                    'accession': 'MS:1000827',
                    'name': 'isolation window target m/z',
                    'value': str(target)
                }
                isolation_window.add_cv_param(target_param)
                
                # 添加lower offset
                low_param = CVParam()
                low_param._attrib = {
                    'cvRef': 'MS',
                    'accession': 'MS:1000828',
                    'name': 'isolation window lower offset',
                    'value': str(low_offset)
                }
                isolation_window.add_cv_param(low_param)
                
                # 添加upper offset
                high_param = CVParam()
                high_param._attrib = {
                    'cvRef': 'MS',
                    'accession': 'MS:1000829',
                    'name': 'isolation window upper offset',
                    'value': str(high_offset)
                }
                isolation_window.add_cv_param(high_param)
                
                mzml_precursor._isolation_window = isolation_window
            
            # 添加selected ion
            if ms_object.precursor.mz > 0:
                selected_ion = SelectedIon()
                
                # 添加m/z
                mz_param = CVParam()
                mz_param._attrib = {
                    'cvRef': 'MS',
                    'accession': 'MS:1000744',
                    'name': 'selected ion m/z',
                    'value': str(ms_object.precursor.mz)
                }
                selected_ion.add_cv_param(mz_param)
                
                # 添加charge
                if ms_object.precursor.charge != 0:
                    charge_param = CVParam()
                    charge_param._attrib = {
                        'cvRef': 'MS',
                        'accession': 'MS:1000041',
                        'name': 'charge state',
                        'value': str(ms_object.precursor.charge)
                    }
                    selected_ion.add_cv_param(charge_param)
                
                mzml_precursor._selected_ions = [selected_ion]
            
            # 添加activation
            activation = Activation()
            
            # 添加激活方法
            if ms_object.precursor.activation_method != 'unknown':
                # 根据激活方法名称选择合适的accession
                method_accessions = {
                    'CID': 'MS:1000133',
                    'HCD': 'MS:1000422',
                    'ETD': 'MS:1000598',
                    'ECD': 'MS:1000250'
                }
                
                method_accession = method_accessions.get(ms_object.precursor.activation_method, 'MS:1000133')
                
                method_param = CVParam()
                method_param._attrib = {
                    'cvRef': 'MS',
                    'accession': method_accession,
                    'name': ms_object.precursor.activation_method
                }
                activation.add_cv_param(method_param)
            
            # 添加激活能量
            if ms_object.precursor.activation_energy > 0:
                energy_param = CVParam()
                energy_param._attrib = {
                    'cvRef': 'MS',
                    'accession': 'MS:1000045',
                    'name': 'collision energy',
                    'value': str(ms_object.precursor.activation_energy)
                }
                activation.add_cv_param(energy_param)
            
            mzml_precursor._activation = activation
            
            spectrum._precursors = [mzml_precursor]
        
        # 添加峰值数据
        if ms_object.peaks:
            # 分离m/z和intensity
            mz_values = [peak[0] for peak in ms_object.peaks]
            intensity_values = [peak[1] for peak in ms_object.peaks]
            
            # 创建m/z数组
            mz_array = BinaryDataArray()
            mz_array._attrib = {'encodedLength': '0'}
            
            # 添加m/z数组的CV参数
            mz_type_param = CVParam()
            mz_type_param._attrib = {
                'cvRef': 'MS',
                'accession': 'MS:1000514',
                'name': 'm/z array'
            }
            mz_array.add_cv_param(mz_type_param)
            
            # 添加精度
            mz_precision_param = CVParam()
            mz_precision_param._attrib = {
                'cvRef': 'MS',
                'accession': 'MS:1000523',
                'name': '64-bit float'
            }
            mz_array.add_cv_param(mz_precision_param)
            
            # 添加压缩
            mz_compression_param = CVParam()
            mz_compression_param._attrib = {
                'cvRef': 'MS',
                'accession': 'MS:1000574',
                'name': 'zlib compression'
            }
            mz_array.add_cv_param(mz_compression_param)
            
            # 编码m/z数据
            mz_binary = struct.pack('d' * len(mz_values), *mz_values)
            mz_compressed = zlib.compress(mz_binary)
            mz_encoded = base64.b64encode(mz_compressed).decode('ascii')
            mz_array._binary = mz_encoded
            
            # 创建intensity数组
            intensity_array = BinaryDataArray()
            intensity_array._attrib = {'encodedLength': '0'}
            
            # 添加intensity数组的CV参数
            intensity_type_param = CVParam()
            intensity_type_param._attrib = {
                'cvRef': 'MS',
                'accession': 'MS:1000515',
                'name': 'intensity array'
            }
            intensity_array.add_cv_param(intensity_type_param)
            
            # 添加精度
            intensity_precision_param = CVParam()
            intensity_precision_param._attrib = {
                'cvRef': 'MS',
                'accession': 'MS:1000523',
                'name': '64-bit float'
            }
            intensity_array.add_cv_param(intensity_precision_param)
            
            # 添加压缩
            intensity_compression_param = CVParam()
            intensity_compression_param._attrib = {
                'cvRef': 'MS',
                'accession': 'MS:1000574',
                'name': 'zlib compression'
            }
            intensity_array.add_cv_param(intensity_compression_param)
            
            # 编码intensity数据
            intensity_binary = struct.pack('d' * len(intensity_values), *intensity_values)
            intensity_compressed = zlib.compress(intensity_binary)
            intensity_encoded = base64.b64encode(intensity_compressed).decode('ascii')
            intensity_array._binary = intensity_encoded
            
            spectrum._binary_data_arrays = [mz_array, intensity_array]

        name_info_dict = {
            'centroid spectrum': {'cvRef': 'MS', 'accession': 'MS:1000127', 'name': 'centroid spectrum'},
            'MSn spectrum': {'cvRef': 'MS', 'accession': 'MS:1000580', 'name': 'MSn spectrum'},
            'positive scan': {'cvRef': 'MS', 'accession': 'MS:1000130', 'name': 'positive scan'},
            'base peak m/z': {'cvRef': 'MS', 'accession': 'MS:1000504', 'unitCvRef': 'MS',
                              'unitAccession': 'MS:1000040', 'unitName': 'm/z', 'name': 'base peak m/z'},
            'base peak intensity': {'cvRef': 'MS', 'accession': 'MS:1000505', 'unitCvRef': 'MS',
                                    'unitAccession': 'MS:1000131', 'unitName': 'number of detector counts',
                                    'name': 'base peak intensity'},
            'total ion current': {'cvRef': 'MS', 'accession': 'MS:1000285', 'name': 'total ion current'},
            'lowest observed m/z': {'cvRef': 'MS', 'accession': 'MS:1000528', 'unitCvRef': 'MS',
                                    'unitAccession': 'MS:1000040', 'unitName': 'm/z', 'name': 'lowest observed m/z'},
            'highest observed m/z': {'cvRef': 'MS', 'accession': 'MS:1000527', 'unitCvRef': 'MS',
                                     'unitAccession': 'MS:1000040', 'unitName': 'm/z', 'name': 'highest observed m/z'}
        }
        # 添加额外信息
        for key, value in ms_object.additional_info.items():
            user_param = CVParam()
            if key in name_info_dict:
                user_param.attrib = name_info_dict[key]
                user_param.attrib['value'] = str(value)
            else:
                user_param.attrib = {
                    'name': key,
                    'value': str(value)
                }
            spectrum.add_cv_param(user_param)
        
        return spectrum
    
    @staticmethod
    def _mgf_to_msobject(spectrum: MGFSpectrum) -> MSObject:
        """
        将MGF的Spectrum对象转换为MSObject
        
        Args:
            spectrum: MGFSpectrum对象
            
        Returns:
            MSObject对象
        """
        # 创建MSObject
        ms_object = MSObject()
        
        # 设置MS级别（MGF通常是MS2）
        ms_object.set_level(2)
        
        # 设置scan信息
        # MGF没有明确的scan number，使用0作为默认值
        scan_number = 0
        
        # 从title中尝试提取scan number
        if spectrum.title and "scan=" in spectrum.title.lower():
            try:
                scan_parts = spectrum.title.lower().split("scan=")[1].split()[0]
                scan_number = int(scan_parts)
            except (ValueError, IndexError):
                pass
        
        ms_object.set_scan(scan_number=scan_number, retention_time=spectrum.rtinseconds)
        
        # 设置前体离子信息
        ms_object.set_precursor(mz=spectrum.pepmass, charge=spectrum.charge)
        
        # 添加峰值
        for mz, intensity in spectrum.peaks:
            ms_object.add_peak(mz, intensity)
        
        # 添加额外信息
        for key, value in spectrum.additional_info.items():
            ms_object.set_additional_info(key, value)
        
        # 如果有title，添加为额外信息
        if spectrum.title:
            ms_object.set_additional_info("TITLE", spectrum.title)
        
        return ms_object
    
    @staticmethod
    def _msobject_to_mgf(ms_object: MSObject) -> MGFSpectrum:
        """
        将MSObject转换为MGF的Spectrum对象
        
        Args:
            ms_object: MSObject对象
            
        Returns:
            MGFSpectrum对象
        """
        # 创建MGFSpectrum
        mgf_spectrum = MGFSpectrum()
        
        # 设置标题（使用scan number）
        mgf_spectrum.title = f"Scan={ms_object.scan.scan_number}"
        
        # 设置肽质量（前体离子m/z）
        if ms_object.precursor and ms_object.precursor.mz > 0:
            mgf_spectrum.pepmass = ms_object.precursor.mz
        
        # 设置电荷
        if ms_object.precursor and ms_object.precursor.charge != 0:
            mgf_spectrum.charge = ms_object.precursor.charge
        
        # 设置保留时间
        if ms_object.scan and ms_object.scan.retention_time > 0:
            mgf_spectrum.rtinseconds = ms_object.scan.retention_time
        
        # 添加峰值
        for mz, intensity in ms_object.peaks:
            mgf_spectrum.add_peak(mz, intensity)
        
        # 添加额外信息
        for key, value in ms_object.additional_info.items():
            if key != "TITLE":  # 避免重复添加标题
                mgf_spectrum.set_additional_info(key, value)
        
        return mgf_spectrum
    
    @staticmethod
    def _ms_to_msobject(spectrum: MSSpectrum) -> MSObject:
        """
        将MS1/MS2的Spectrum对象转换为MSObject
        
        Args:
            spectrum: MSSpectrum对象
            
        Returns:
            MSObject对象
        """
        # 创建MSObject
        ms_object = MSObject()
        
        # 设置MS级别
        ms_object.set_level(spectrum.level)
        
        # 设置scan信息
        ms_object.set_scan(scan_number=spectrum.scan_number, retention_time=spectrum.retention_time)
        
        # 设置前体离子信息（如果是MS2）
        if spectrum.level == 2:
            ms_object.set_precursor(mz=spectrum.precursor_mz, charge=spectrum.precursor_charge)
        
        # 添加峰值
        for mz, intensity in spectrum.peaks:
            ms_object.add_peak(mz, intensity)
        
        # 添加额外信息
        for key, value in spectrum.additional_info.items():
            ms_object.set_additional_info(key, value)
        
        return ms_object
    
    @staticmethod
    def _msobject_to_ms(ms_object: MSObject) -> MSSpectrum:
        """
        将MSObject转换为MS1/MS2的Spectrum对象
        
        Args:
            ms_object: MSObject对象
            
        Returns:
            MSSpectrum对象
        """
        # 创建MSSpectrum
        ms_spectrum = MSSpectrum(level=ms_object.level)
        
        # 设置扫描编号
        ms_spectrum.scan_number = ms_object.scan.scan_number
        
        # 设置保留时间
        ms_spectrum.retention_time = ms_object.scan.retention_time
        
        # 设置前体离子信息（如果是MS2）
        if ms_object.level == 2 and ms_object.precursor:
            ms_spectrum.precursor_mz = ms_object.precursor.mz
            ms_spectrum.precursor_charge = ms_object.precursor.charge
        
        # 添加峰值
        for mz, intensity in ms_object.peaks:
            ms_spectrum.add_peak(mz, intensity)
        
        # 添加额外信息
        for key, value in ms_object.additional_info.items():
            ms_spectrum.set_additional_info(key, value)
        
        return ms_spectrum 