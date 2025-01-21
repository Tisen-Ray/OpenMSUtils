import os
import re
from .MSObject import MSObject

class MS1Reader():
    def __init__(self):
        pass

    def read(self, filename):
        """读取文件并解析元数据和质谱数据"""
        if not os.path.exists(filename) or not filename.endswith('.ms1'):
            print(f"invalid file name: {filename}")
            return

        spectra = []
        meta_data = {}

        with open(filename, 'r') as file:
            lines = file.readlines()

        current_spectrum = None
        for line in lines:
            line = line.strip()

            if line.startswith('H'):  # 头信息行
                key, value = self._parse_header(line)
                if not key is None:
                    meta_data[key] = value

            elif line.startswith('S'):  # 新的质谱数据段
                if current_spectrum is not None:
                    spectra.append(current_spectrum)

                scan_number = int(line.split()[2])
                current_spectrum = MSObject(scan_number=scan_number)

            elif line.startswith('I'):  # 质谱参数行（如：NumberOfPeaks, RetTime等）
                key, value = self._parse_info(line)
                if not key is None:
                    if key == "RTime":
                        RT = float(value)
                        current_spectrum.set_retention_time(retention_time=RT)
                    else:
                        current_spectrum.add_additional_info(key=key, value=value)

            else:  # 质谱数据行
                mz, intensity = self._parse_peak(line)
                current_spectrum.add_peak(mz=mz, intensity=intensity)

        # 在结束时添加最后一组质谱数据
        if current_spectrum is not None:
            spectra.append(current_spectrum)

        return meta_data, spectra

    def _parse_header(self, line):
        """解析头信息行并存储"""
        match = re.match(r'H\s+(\S+)\s+(.*)', line)
        if match:
            key, value = match.groups()
            return key, value
        else:
            return None, None

    def _parse_info(self, line):
        """解析质谱信息行（RetTime）"""
        match = re.match(r'I\s+(\S+)\s+(.*)', line)
        if match:
            key, value = match.groups()
            return key, value
        else:
            return None, None

    def _parse_peak(self, line):
        """解析质谱数据行（质量与强度 pair）"""
        try:
            mz, intensity = map(float, line.split())
            return mz, intensity
        except ValueError:
            pass  # 忽略格式不正确的行

class MS2Reader:
    def __init__(self):
        pass

    def read(self, filename):
        """读取文件并解析元数据和质谱数据"""
        if not os.path.exists(filename) or not filename.endswith('.ms2'):
            print(f"invalid file name: {filename}")
            return

        spectra = []
        meta_data = {}

        with open(filename, 'r') as file:
            lines = file.readlines()

        current_spectrum = None
        for line in lines:
            line = line.strip()

            if line.startswith('H'):  # 头信息行
                key, value = self._parse_header(line)
                if not key is None:
                    meta_data[key] = value

            elif line.startswith('S'):  # 新的质谱数据段
                if current_spectrum is not None:
                    spectra.append(current_spectrum)

                scan_number = int(line.split()[2])
                current_spectrum = MSObject(scan_number=scan_number, level=2)
                precursor_mz = float(line.split()[3])
                current_spectrum.precursor_ion.mz = precursor_mz

            elif line.startswith('I'):  # 质谱参数行（如：NumberOfPeaks, RetTime等）
                key, value = self._parse_info(line)
                if not key is None:
                    if key == "RTime":
                        RT = float(value)
                        current_spectrum.set_retention_time(retention_time=RT)
                    else:
                        current_spectrum.add_additional_info(key=key, value=value)

            elif line.startswith('Z'):
                charge = int(line.split()[1])
                if current_spectrum is not None:
                    current_spectrum.precursor_ion.charge = charge

            else:  # 质谱数据行
                mz, intensity = self._parse_peak(line)
                current_spectrum.add_peak(mz=mz, intensity=intensity)

        # 在结束时添加最后一组质谱数据
        if current_spectrum is not None:
            spectra.append(current_spectrum)

        return meta_data, spectra

    def _parse_header(self, line):
        """解析头信息行并存储"""
        match = re.match(r'H\s+(\S+)\s+(.*)', line)
        if match:
            key, value = match.groups()
            return key, value
        else:
            return None, None

    def _parse_info(self, line):
        """解析质谱信息行（RetTime）"""
        match = re.match(r'I\s+(\S+)\s+(.*)', line)
        if match:
            key, value = match.groups()
            return key, value
        else:
            return None, None

    def _parse_peak(self, line):
        """解析质谱数据行（质量与强度 pair）"""
        try:
            mz, intensity = map(float, line.split())
            return mz, intensity
        except ValueError:
            pass  # 忽略格式不正确的行


if __name__ == "__main__":
    reader = MS1Reader()
    meta, data = reader.read('../../GraphFormer/20181121a_HAP1_tRNA_19.ms1')
    print(meta)
    print(data[0])

    reader = MS2Reader()
    meta, data = reader.read('../../GraphFormer/20181121a_HAP1_tRNA_19.ms2')
    print(meta)
    print(data[0])
