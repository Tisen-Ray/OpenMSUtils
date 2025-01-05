class FastaWriter:
    def __init__(self, file_path):
        """初始化 FastaWriter 对象，并指定输出文件路径"""
        self.file_path = file_path

    def write_to_fasta(self, sequences):
        """
        将解析后的序列写入新的 FASTA 文件。
        :param output_filename: 输出文件路径
        """
        with open(self.file_path, 'w') as output_file:
            for header, sequence in sequences.items():
                output_file.write(f'>{header}\n')
                # 将序列分为多行，每行不超过 80 个字符
                for i in range(0, len(sequence), 80):
                    output_file.write(f'{sequence[i:i + 80]}\n')


if __name__ == "__main__":
    sequence_dict = {
        "seq1": "AATTCC",
        "seq2": "GCGCGA",
        "seq3": "TTGCAA"
    }

    # 创建 FastaWriter 实例，指定输出文件路径
    fasta_writer = FastaWriter("output.fasta")

    # 将字典写入 FASTA 文件
    fasta_writer.write_to_fasta(sequence_dict)