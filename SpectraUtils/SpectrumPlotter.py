import numpy as np
import matplotlib.pyplot as plt


class SpectrumPlotter:
    def __init__(self, data):
        self.data = self.process_spectrum(data)

    def process_spectrum(self, in_datas):
        processed_datas = []
        for entry in in_datas:
            spectrum = {'RT': 0.0, 'peaks': []}

            if 'RTime' in entry:
                spectrum['RT'] = float(entry['RTime'])
            if 'RTINSECONDS' in entry:
                spectrum['RT'] = float(entry['RTINSECONDS'])

            spectrum['peaks'] = entry['peaks']
            processed_datas.append(spectrum)
        return processed_datas

    def plot_mz(self, index):
        spectrum = self.data[index]
        data = spectrum['peaks']
        # 提取 mz 和 intensity 数据
        mz_values = [entry['mz'] for entry in data]
        intensity_values = [entry['intensity'] for entry in data]

        # 绘制质谱图
        plt.figure(figsize=(10, 6))
        plt.stem(mz_values, intensity_values, linefmt='r-', markerfmt='bo', basefmt='g-')
        # 设置标题和标签
        plt.title("Mass Spectrum")
        plt.xlabel("m/z")
        plt.ylabel("Intensity")
        # 显示图形
        plt.show()

    def plot_contour(self, cmap='viridis', xlabel='Time', ylabel='m/z', title='2D Mass Spectrum (Contour)'):
        """
        绘制二维质谱图的等高线图。

        参数:
        cmap: str, 默认 'viridis'
            颜色映射（colormap）。
        xlabel: str, 默认 'Time'
            X 轴标签。
        ylabel: str, 默认 'm/z'
            Y 轴标签。
        title: str, 默认 '2D Mass Spectrum (Contour)'
            图表标题。
        """
        X, Y = np.meshgrid(self.time_points, self.mz_values)
        plt.figure(figsize=(10, 8))
        cp = plt.contourf(X, Y, self.intensity_matrix, cmap=cmap)
        plt.colorbar(cp, label='Intensity')
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.show()

    def plot_surface(self, cmap='viridis', xlabel='Time', ylabel='m/z', title='2D Mass Spectrum (Surface)'):
        """
        绘制三维表面图。

        参数:
        cmap: str, 默认 'viridis'
            颜色映射（colormap）。
        xlabel: str, 默认 'Time'
            X 轴标签。
        ylabel: str, 默认 'm/z'
            Y 轴标签。
        title: str, 默认 '2D Mass Spectrum (Surface)'
            图表标题。
        """
        from mpl_toolkits.mplot3d import Axes3D

        X, Y = np.meshgrid(self.time_points, self.mz_values)
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(X, Y, self.intensity_matrix, cmap=cmap)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_zlabel('Intensity')
        ax.set_title(title)
        plt.show()








if __name__ == "__main__":
    pass
    # import numpy as np
    # import matplotlib.pyplot as plt
    # from mpl_toolkits.mplot3d import Axes3D
    #
    # # 创建数据
    # x = np.arange(4)  # x 坐标的标签
    # y = np.arange(3)  # y 坐标的标签
    # x, y = np.meshgrid(x, y)  # 创建一个网格
    #
    # z = np.zeros_like(x)  # 底面高度设为0
    # dx = np.ones_like(z)  # 每个柱子的宽度
    # dy = np.ones_like(z)  # 每个柱子的深度
    # dz = np.random.randint(1, 10, size=z.shape)  # 柱子的高度，随机生成
    #
    # # 创建图形和3D坐标轴
    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')
    #
    # # 绘制三维柱状图
    # ax.bar3d(x=x.flatten(), y=y.flatten(), z=z.flatten(), dx=dx.flatten(), dy=dy.flatten(), dz=dz.flatten(), color='c')
    #
    # # 设置标题和标签
    # ax.set_title('3D Bar Chart Example')
    # ax.set_xlabel('X')
    # ax.set_ylabel('Y')
    # ax.set_zlabel('Z')
    #
    # # 显示图形
    # plt.show()

