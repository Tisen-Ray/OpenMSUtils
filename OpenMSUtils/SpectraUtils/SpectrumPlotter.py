import numpy as np
import matplotlib.pyplot as plt
from .MSObject import MSObject

class SpectrumPlotter:
    def __init__(self):
        pass

    def plot_mz(self, ms_object: MSObject):
        peaks = ms_object.peaks
        # 提取 mz 和 intensity 数据
        mz_list = [peak.mz for peak in peaks]
        intensity_list = [peak.intensity for peak in peaks]
        max_intensity = max(intensity_list) if intensity_list else 1
        intensity_list = [intensity / max_intensity for intensity in intensity_list]

        plt.figure(figsize=(10, 6))
        plt.stem(mz_list, intensity_list, markerfmt=" ")
        # 设置标题和标签
        plt.title("Mass Spectrum")
        plt.xlabel("m/z")
        plt.ylabel("Intensity")
        plt.show()

if __name__ == "__main__":
    pass



