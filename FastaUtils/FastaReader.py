
class FastaReader:
    def __init__(self, filename):
        """
        初始化 FastaReader 类，指定要读取的 fasta 文件路径。
        :param filename: 要读取的 fasta 文件路径
        """
        self.filename = filename
        self.sequences = {}
        self.parse_fasta()

    def parse_fasta(self):
        """
        读取并解析 fasta 文件，将其中的序列和标识符存储在字典中。
        """
        with open(self.filename, 'r') as file:
            current_header = None
            current_sequence = []

            for line in file:
                line = line.strip()
                if line.startswith('>'):  # 以 '>' 开头的是 FASTA 头部行
                    if current_header:  # 如果已经有一个序列，保存之前的序列
                        self.sequences[current_header] = ''.join(current_sequence)
                    current_header = line[1:]  # 去掉 '>'
                    current_sequence = []  # 重置序列
                else:
                    current_sequence.append(line)  # 收集序列的每一行
            # 保存最后一个序列
            if current_header:
                self.sequences[current_header] = ''.join(current_sequence)

    def get_sequences(self):
        """
        获取所有解析的序列。
        :return: 包含所有序列的字典 {header: sequence}
        """
        return self.sequences

    def get_sequence_by_header(self, header):
        """
        根据 FASTA 头部查找序列。
        :param header: 序列的 FASTA 头部
        :return: 对应的序列，如果头部不存在则返回 None
        """
        return self.sequences.get(header, None)

    def clean_sequence(self, sequence):
        """
        清理序列，去掉非 'A', 'T', 'C', 'G', 'U' 的字符。
        :param sequence: 原始序列字符串
        :return: 清理后的序列字符串
        """
        return ''.join([char for char in sequence if char in 'ATCGU'])