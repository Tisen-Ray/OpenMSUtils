import os

from MSObject import MSObject


class MGFReader:
    def __init__(self):
        pass

    def read(self, filename):
        """ 读取 MGF 文件并解析数据 """
        if not os.path.exists(filename) or not filename.endswith('.mgf'):
            print(f"invalid file name: {filename}")
            return

        spectra = []
        meta_data = {}

        with open(filename, 'r') as file:
            lines = file.readlines()

        for line in lines:
            line = line.strip()
            # 跳过空行和注释行
            if not line or line.startswith('#'):
                continue

            # 检测到 BEGIN IONS，开始读取一个新的质谱数据
            if line.startswith('BEGIN IONS'):
                current_spectra = MSObject(level=2)

            # 检测到 END IONS，结束当前质谱数据
            elif line.startswith('END IONS'):
                if current_spectra:
                    spectra.append(current_spectra)

            # 解析谱图参数，如 TITLE, PEPMASS, CHARGE 等
            elif '=' in line:
                if current_spectra:
                    param_name, param_value = line.split('=', 1)
                    param_name = param_name.strip()
                    param_value = param_value.strip()
                    if param_name == "RTINSECONDS":
                        RT = float(param_value)
                        current_spectra.set_retention_time(RT)
                    elif param_name == "PEPMASS":
                        precursor_mz = float(param_value.split()[0])
                        current_spectra.precursor_ion.mz = precursor_mz
                    elif param_name == "CHARGE":
                        if param_value.endswith('-'):
                            charge = -1 * int(param_value[:-1]) # 去掉最后的 '-' 字符
                        elif param_value.endswith('+'):
                            charge = int(param_value[:-1])
                        else:
                            charge = 0
                        current_spectra.precursor_ion.charge = charge
                    else:
                        current_spectra.add_additional_info(key=param_name, value=param_value)

            # 解析峰值数据（质量和强度）
            else:
                try:
                    mz, intensity = map(float, line.split())
                    if current_spectra:
                        current_spectra.add_peak(mz=mz, intensity=intensity)
                except ValueError:
                    continue

        return meta_data, spectra

if __name__ == "__main__":
    reader = MGFReader()
    meta, spectra = reader.read("./20181121a_HAP1_tRNA_19.mgf")
    print(meta)
    print(spectra[0])