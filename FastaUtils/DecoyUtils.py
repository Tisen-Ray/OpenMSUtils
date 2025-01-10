import random

from FastaWriter import FastaWriter
from FastaReader import FastaReader

class DecoyGenerator:
    def __init__(self):
        pass

    def generate_decoy(self, fasta_file, prefix='Decoy_', decoy_mode=0):
        fasta_reader = FastaReader()
        sequences = fasta_reader.read(fasta_file)
        decoy_sequences = {}
        for head, sequence in sequences.items():
            decoy_head = prefix + head
            decoy_sequence = self._decoy(seq=sequence, mode=decoy_mode)
            decoy_sequences[decoy_head] = decoy_sequence

        for head, sequence in decoy_sequences.items():
            sequences[head] = sequence

        writer = FastaWriter()
        writer.write(sequences=sequences, filename=prefix+fasta_file)

    def _decoy(self, seq, mode=0):
        if mode == 0:
            return seq[::-1]
        else:
            return random.shuffle(seq)

if __name__ == "__main__":
    decoy_generator = DecoyGenerator()
    decoy_generator.generate_decoy(fasta_file='16S_ecoli.fasta')