import numpy as np
import matplotlib.pyplot as plt
from .MSObject import MSObject

class SpectrumPlotter:
    def __init__(self):
        pass

    def plot_mz(self, ms_object: MSObject):
        peaks = ms_object.peaks
        if len(peaks) == 0:
            print("No peaks found in the spectrum")
            return
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
    
    def plot_ion_mobility(self, ion_mobility_spectrum: dict, time_range: tuple[float, float] = None, time_bins: int = 500, mz_range: tuple[float, float] = None, mz_bins: int = 500):
        if time_range is None or mz_range is None:
            min_time = min(ion_mobility_spectrum.keys())
            max_time = max(ion_mobility_spectrum.keys())
            min_mz = min([peak.mz for peaks in ion_mobility_spectrum.values() for peak in peaks])
            max_mz = max([peak.mz for peaks in ion_mobility_spectrum.values() for peak in peaks])
            if time_range is None:
                time_range = (min_time, max_time)
            if mz_range is None:
                mz_range = (min_mz, max_mz)
        time_step = (time_range[1] - time_range[0]) / time_bins
        mz_step = (mz_range[1] - mz_range[0]) / mz_bins
        time_list = np.linspace(time_range[0], time_range[1], time_bins)
        mz_list = np.linspace(mz_range[0], mz_range[1], mz_bins)
        ion_mobility_matrix = np.zeros((len(time_list), len(mz_list)))
        for time, peaks in ion_mobility_spectrum.items():
            for peak in peaks:
                mz = peak.mz
                intensity = peak.intensity
                mz_index = (int)((mz - mz_range[0]) / mz_step)
                time_index = (int)((time - time_range[0]) / time_step)
                if mz_index < 0 or mz_index >= len(mz_list) or time_index < 0 or time_index >= len(time_list):
                    continue
                ion_mobility_matrix[time_index][mz_index] += intensity

        plt.imshow(ion_mobility_matrix, cmap="viridis")
        plt.colorbar()
        plt.xlabel("m/z")
        plt.ylabel("Time")
        plt.title("Ion Mobility Spectrum")
        plt.show()

if __name__ == "__main__":
    pass



