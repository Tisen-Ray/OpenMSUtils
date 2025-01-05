import re

class MS1Reaser():
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = []  # 存储所有质谱数据
        self.metadata = {}  # 存储头信息（元数据）

    def read_file(self):
        """读取文件并解析元数据和质谱数据"""
        with open(self.file_path, 'r') as file:
            lines = file.readlines()

        current_spectrum = None
        for line in lines:
            line = line.strip()

            if line.startswith('H'):  # 头信息行
                self.parse_header(line)

            elif line.startswith('S'):  # 新的质谱数据段
                if current_spectrum is not None:
                    self.data.append(current_spectrum)

                scan_number = int(line.split()[2])
                current_spectrum = {'scan_number': scan_number, 'peaks': []}

            elif line.startswith('I'):  # 质谱参数行（如：NumberOfPeaks, RetTime等）
                self.parse_spectrum_info(line, current_spectrum)

            else:  # 质谱数据行
                self.parse_spectrum_data(line, current_spectrum)

        # 在结束时添加最后一组质谱数据
        if current_spectrum is not None:
            self.data.append(current_spectrum)

    def parse_header(self, line):
        """解析头信息行并存储"""
        match = re.match(r'H\s+(\S+)\s+(.*)', line)
        if match:
            key, value = match.groups()
            self.metadata[key] = value

    def parse_spectrum_info(self, line, current_spectrum):
        """解析质谱信息行（RetTime）"""
        match = re.match(r'I\s+(\S+)\s+(.*)', line)
        if match:
            key, value = match.groups()
            current_spectrum[key] = value

    def parse_spectrum_data(self, line, current_spectrum):
        """解析质谱数据行（质量与强度 pair）"""
        try:
            mz, intensity = map(float, line.split())
            current_spectrum['peaks'].append({'mz': mz, 'intensity': intensity})
        except ValueError:
            pass  # 忽略格式不正确的行

    def get_metadata(self):
        """返回文件头信息"""
        return self.metadata

    def get_spectra(self):
        """返回解析后的质谱数据"""
        return self.data

class MS2Reader:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = []  # 存储所有质谱数据
        self.metadata = {}  # 存储头信息（元数据）

    def read_file(self):
        """读取文件并解析元数据和质谱数据"""
        with open(self.filepath, 'r') as file:
            lines = file.readlines()

        current_spectrum = None

        for line in lines:
            line = line.strip()

            if line.startswith('H'):  # 头信息行
                self.parse_header(line)

            elif line.startswith('S'):  # 新的质谱数据段
                if current_spectrum is not None:
                    self.data.append(current_spectrum)

                scan_number = int(line.split()[2])
                precursor_mz = float(line.split()[3])
                current_spectrum = {'scan_number': scan_number, 'precursor_mz': precursor_mz, 'peaks': []}

            elif line.startswith('I'):  # 质谱参数行（如：NumberOfPeaks, RetTime等）
                self.parse_info(line, current_spectrum)

            elif line.startswith('Z'):
                charge = int(line.split()[1])
                if current_spectrum is not None:
                    current_spectrum['precursor_charge'] = charge

            else:  # 质谱数据行
                self.parse_spectrum_data(line, current_spectrum)

        # Don't forget to append the last spectrum data
        if current_spectrum:
            self.data.append(current_spectrum)

    def parse_header(self, line):
        """解析头信息行并存储"""
        match = re.match(r'H\s+(\S+)\s+(.*)', line)
        if match:
            key, value = match.groups()
            self.metadata[key] = value

    def parse_info(self, line, current_spectrum):
        """解析质谱信息行（RetTime）"""
        match = re.match(r'I\s+(\S+)\s+(.*)', line)
        if match:
            key, value = match.groups()
            current_spectrum[key] = value

    def parse_spectrum_data(self, line, current_spectrum):
        """解析质谱数据行（质量与强度 pair）"""
        try:
            mz, intensity = map(float, line.split())
            current_spectrum['peaks'].append({'mz': mz, 'intensity': intensity})
        except ValueError:
            pass  # 忽略格式不正确的行

    def get_metadata(self):
        """返回文件头信息"""
        return self.metadata

    def get_spectra(self):
        """返回解析后的质谱数据"""
        return self.data


if __name__ == "__main__":
    reader = MS1Reaser('../../GraphFormer/20181121a_HAP1_tRNA_19.ms1')
    reader.read_file()
    print(reader.get_spectra()[0])

    reader = MS2Reader('../../GraphFormer/20181121a_HAP1_tRNA_19.ms2')
    reader.read_file()
    print(reader.get_spectra()[0])
