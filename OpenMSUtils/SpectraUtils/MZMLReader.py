from lxml import etree
import re
import base64
import struct
import zlib
from tqdm import tqdm
from .MSObject import MSObject

class MZMLReader(object):
    def __init__(self):
        super().__init__()

    def read(self, filename):
        """
        读取MZML文件并解析为MSObject对象列表
        """
        meta_data = {}
        spectrum = []
        xml_tree = etree.parse(filename)
        root = xml_tree.getroot()
        if root.tag.endswith('indexedmzML'): # 如果文件中存在indexList标签
            index_list, end_offset = self._get_offset_list(root)
            with open(filename, 'rb') as file:
                for index in tqdm(range(len(index_list)), desc="Reading spectra"):
                    file.seek(index_list[index]['offset'])
                    # 读取从当前offset到下一个offset之间的内容
                    if index == len(index_list) - 1:
                        data = file.read(end_offset - index_list[index]['offset']).split(b'</spectrum>')[0] + b'</spectrum>\n'
                    else:
                        data = file.read(index_list[index+1]['offset'] - index_list[index]['offset'])
                    ms_obj = self._parse_spectrum_to_msobject(data)
                    spectrum.append(ms_obj)
        else:
            raise ValueError("No indexedmzML found in the root element")
        
        return meta_data, spectrum

    def _get_offset_list(self, root):
        """
        从XML根节点获取所有offset值并构建列表
        Args:
            root: XML根节点
        Returns:
            list: 包含所有offset值的列表
        """
        offset_list = []
        index_root = None
        for child in root:
            if child.tag.endswith('indexList'):
                index_root = child
                break
        if index_root is None:
            raise ValueError("No indexList found in the root element")
        
        # 遍历所有offset节点
        spectrum_index_root = index_root[0]
        for offset_elem in [child for child in spectrum_index_root if child.tag.endswith('offset')]:
            offset_value = offset_elem.text
            id_ref = offset_elem.get('idRef')
            offset_list.append({
                'idRef': id_ref,
                'offset': int(offset_value)
            })

        chromatogram_index_root = index_root[1]  # 获取chromatogram_index节点
        # 遍历所有offset节点, usually one
        for offset_elem in [child for child in chromatogram_index_root if child.tag.endswith('offset')]:
            end_offset = offset_elem.text

        if end_offset is None:
            raise ValueError("No end offset found in the indexList element")
                
        return offset_list, int(end_offset)

    def _parse_spectrum_to_msobject(self, spectrum_str):
        """
        将XML格式的质谱数据解析为MSObject对象
        Args:
            spectrum_str: XML格式的质谱字符串
        Returns:
            MSObject: 包含质谱数据的MSObject对象
        """
        # 解析XML字符串
        spectrum_elem = etree.fromstring(spectrum_str)
        
        # 创建MSObject对象
        ms_obj = MSObject()
        
        # scan number
        id_str = spectrum_elem.get('id')
        scan_match = re.search(r'scan=(\d+)', id_str)
        if scan_match:
            scan_number = int(scan_match.group(1))
        else: # 如果没有匹配到scan=xxx格式,则为-1
            scan_number = -1
        ms_obj.set_scan_info(scan_number=scan_number)
        
        # 遍历cvParam节点获取基本信息
        for cv_param in [child for child in spectrum_elem if child.tag.endswith('cvParam')]:
            name = cv_param.get('name')
            value = cv_param.get('value', '')
            # 获取MS level
            if name == "ms level":
                ms_obj.set_level(int(value))
            else: 
                ms_obj.set_additional_info(name, value) # 存储其他信息到additional_info
        
        # 获取scan信息
        if spectrum_elem.find(".//scanList") is not None:
            scans = spectrum_elem.find(".//scanList").findall(".//scan")
            if len(scans) > 1:
                print("Warning: Multiple scanList found in the spectrum element, only the first one will be used")
            scan = scans[0]
            for cv_param in [child for child in scan if child.tag.endswith('cvParam')]:
                name = cv_param.get('name')
                value = cv_param.get('value', '')
                if name == "scan start time":
                    ms_obj.set_scan_info(retention_time=float(value))
                elif name == "ion mobility drift time":
                    ms_obj.set_scan_info(drift_time=float(value))
                else:
                    ms_obj.set_scan_additional_info(name, value)
            # 获取scan window
            if scan.find(".//scanWindowList") is not None:
                scan_windows = scan.find(".//scanWindowList").findall("scanWindow")
                if len(scan_windows) > 1:
                    print("Warning: Multiple scanWindowList found in the scan element, only the first one will be used")
                scan_window = scan_windows[0]
                scan_window_lower_limit = None
                scan_window_upper_limit = None
                for cv_param in [child for child in scan_window if child.tag.endswith('cvParam')]:
                    name = cv_param.get('name')
                    value = cv_param.get('value', '')
                    if name == "scan window lower limit":
                        scan_window_lower_limit = float(value)
                    elif name == "scan window upper limit":
                        scan_window_upper_limit = float(value)
                if scan_window_lower_limit is not None and scan_window_upper_limit is not None:
                    ms_obj.set_scan_info(scan_window=(scan_window_lower_limit, scan_window_upper_limit))

        # 获取precursor信息
        if spectrum_elem.find(".//precursorList") is not None:
            precursors = spectrum_elem.find(".//precursorList").findall("precursor")
            if len(precursors) > 1:
                print("Warning: Multiple precursorList found in the spectrum element, only the first one will be used")
            precursor = precursors[0]
            # get ref_scan_number
            ref_str = precursor.get('spectrumRef')
            ref_match = re.search(r'scan=(\d+)', ref_str)
            if ref_match:
                ref_scan_number = int(ref_match.group(1))
            else:
                ref_scan_number = -1
            ms_obj.set_precursor(ref_scan_number=ref_scan_number)
            # get isolation window
            isolation_window = precursor.find(".//isolationWindow")
            if isolation_window is not None:
                isolation_window_center = None
                isolation_window_lower_limit = None
                isolation_window_upper_limit = None
                for cv_param in [child for child in isolation_window if child.tag.endswith('cvParam')]:
                    name = cv_param.get('name')
                    value = cv_param.get('value', '')
                    if name == "isolation window lower offset":
                        isolation_window_lower_limit = float(value)
                    elif name == "isolation window upper offset":
                        isolation_window_upper_limit = float(value)
                    elif name == "isolation window target m/z":
                        isolation_window_center = float(value)
                ms_obj.set_precursor(isolation_window=(isolation_window_center-isolation_window_lower_limit, isolation_window_center+isolation_window_upper_limit))
            # get selected ion
            if precursor.find(".//selectedIonList") is not None:
                selected_ions = precursor.find(".//selectedIonList").findall("selectedIon")
                if len(selected_ions) > 1:
                    print("Warning: Multiple selectedIonList found in the precursor element, only the first one will be used")
                selected_ion = selected_ions[0]
                for cv_param in [child for child in selected_ion if child.tag.endswith('cvParam')]:
                    name = cv_param.get('name')
                    value = cv_param.get('value', '')
                    if name == "selected ion m/z":
                        mz = float(value)
                        ms_obj.set_precursor(mz=mz)
                    elif name == "charge state":
                        charge = int(value)
                        ms_obj.set_precursor(charge=charge)
            # get activation method
            activation = precursor.find(".//activation")
            if activation is not None:
                for cv_param in [child for child in activation if child.tag.endswith('cvParam')]:
                    name = cv_param.get('name')
                    value = cv_param.get('value', '')
                    if name == "collision energy":
                        ms_obj.set_precursor(activation_energy=float(value))
                    else:
                        ms_obj.set_precursor(activation_method=name)
                
        # 获取mz和intensity数组
        if spectrum_elem.find(".//binaryDataArrayList") is not None:
            binary_arrays = spectrum_elem.find(".//binaryDataArrayList").findall("binaryDataArray")
            if len(binary_arrays) >= 2:
                # 解码base64编码的数据
                # 获取m/z和intensity数组的编码格式和压缩信息
                mz_binary_array = binary_arrays[0]
                mz_is_64_bit = False
                mz_is_compressed = False
                mz_values = []
                for cv_param in [child for child in mz_binary_array if child.tag.endswith('cvParam')]:
                    name = cv_param.get('name')
                    value = cv_param.get('value', '')
                    if name == "64-bit float":
                        mz_is_64_bit = True
                    elif name == "zlib compression":
                        mz_is_compressed = True
                    elif name == "32-bit float":
                        mz_is_64_bit = False
                    elif name == "no compression":
                        mz_is_compressed = False

                # 解码binary数据
                mz_binary_data = mz_binary_array.find("binary").text
                if mz_binary_data:
                    mz_binary_data = base64.b64decode(mz_binary_data)
                    if mz_is_compressed:
                        mz_binary_data = zlib.decompress(mz_binary_data)
                    # 根据位数解包数据
                    if mz_is_64_bit:
                        num_floats = len(mz_binary_data) // 8
                        mz_values = struct.unpack('d' * num_floats, mz_binary_data)
                    else:
                        num_floats = len(mz_binary_data) // 4
                        mz_values = struct.unpack('f' * num_floats, mz_binary_data)
                
                # 获取intensity数组
                intensity_binary_array = binary_arrays[1]
                intensity_values = []
                intensity_is_64_bit = False
                intensity_is_compressed = False
                for cv_param in [child for child in intensity_binary_array if child.tag.endswith('cvParam')]:
                    name = cv_param.get('name')
                    value = cv_param.get('value', '')
                    if name == "64-bit float":
                        intensity_is_64_bit = True
                    elif name == "zlib compression":
                        intensity_is_compressed = True
                    elif name == "32-bit float":
                        intensity_is_64_bit = False
                    elif name == "no compression":
                        intensity_is_compressed = False
                
                # 解码binary数据
                intensity_binary_data = intensity_binary_array.find("binary").text
                if intensity_binary_data:
                    intensity_binary_data = base64.b64decode(intensity_binary_data)
                    if intensity_is_compressed:
                        intensity_binary_data = zlib.decompress(intensity_binary_data)
                    # 根据位数解包数据
                    if intensity_is_64_bit:
                        num_floats = len(intensity_binary_data) // 8
                        intensity_values = struct.unpack('d' * num_floats, intensity_binary_data)
                    else:
                        num_floats = len(intensity_binary_data) // 4
                        intensity_values = struct.unpack('f' * num_floats, intensity_binary_data)

                # 添加峰值数据
                for mz, intensity in zip(mz_values, intensity_values):
                    if intensity > 0:
                        ms_obj.add_peak(mz=mz, intensity=intensity)
        
        return ms_obj

if __name__ == "__main__":
    file_path = 'D:\\code\\Python\\MS\\NADataFormer\\rawData\\20181121a_HAP1_tRNA_19.mzML'
    reader = MZMLReader()
    ms_data = reader.read(file_path)

    print(ms_data)
