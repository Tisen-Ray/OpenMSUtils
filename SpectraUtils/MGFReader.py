class MGFReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = []

    def read(self):
        """ 读取 MGF 文件并解析数据 """
        spectrum = None
        with open(self.file_path, 'r') as file:
            lines = file.readlines()

        for line in lines:
            line = line.strip()

            # 跳过空行和注释行
            if not line or line.startswith('#'):
                continue

            # 检测到 BEGIN IONS，开始读取一个新的质谱数据
            if line.startswith('BEGIN IONS'):
                if spectrum:
                    self.data.append(spectrum)
                spectrum = {'peaks': []}

            # 检测到 END IONS，结束当前质谱数据
            elif line.startswith('END IONS'):
                if spectrum:
                    self.data.append(spectrum)
                spectrum = None

            # 解析谱图参数，如 TITLE, PEPMASS, CHARGE 等
            elif '=' in line:
                param_name, param_value = line.split('=', 1)
                param_name = param_name.strip()
                param_value = param_value.strip()
                if spectrum is not None:
                    spectrum[param_name] = param_value

            # 解析峰值数据（质量和强度）
            else:
                try:
                    mz, intensity = map(float, line.split())
                    if spectrum is not None:
                        spectrum['peaks'].append({'mz': mz, 'intensity': intensity})
                except ValueError:
                    # 如果当前行不能被解析为浮动值，跳过
                    continue

    def get_spectra(self):
        """ 返回解析后的质谱数据 """
        return self.data

    def get_peaks(self, spectrum_index):
        """ 获取特定谱图的峰数量 """
        if 0 <= spectrum_index < len(self.data):
            return self.data[spectrum_index]['peaks']
        return None

if __name__ == "__main__":
    reader = MGFReader("./20181121a_HAP1_tRNA_26.mgf")
    reader.read()
    print(reader.get_spectra()[0])