from .accurate_molmass import EnhancedFormula
import os
import pandas as pd
from typing import Tuple, Dict
import re

class Modification():
    def __init__(self, name: str, formula: str):
        self.name = name
        self.formula = formula

    @property
    def mass(self):
        parts = self.formula.split('@')
        if len(parts) == 1:
            return EnhancedFormula(parts[0]).isotope.mass
        elif len(parts) == 2 and parts[1]:  # Ensure there is something after '@'
            return EnhancedFormula(parts[0]).isotope.mass - EnhancedFormula(parts[1]).isotope.mass
        else:
            raise ValueError(f"Invalid formula: {self.formula}")

class ModificationUtils():
    @staticmethod
    def parse_modified_sequence(modified_sequence: str) -> Tuple[str, Dict[int, str]]:
        """
        解析带修饰标记的序列，例如 "PEP(Phospho)TIDE"
        
        参数:
            modified_sequence: 带修饰标记的序列
            
        返回:
            原始序列和修饰信息
        """
        # 匹配修饰模式，例如 "(Phospho)"
        pattern = r'([A-Z])(\([^)]+\))'
        
        # 提取原始序列和修饰
        clean_sequence = ""
        modifications = {}
        pos = 0
        
        # 处理序列中的修饰
        last_end = 0
        for match in re.finditer(pattern, modified_sequence):
            # 添加匹配前的部分到清洁序列
            clean_sequence += modified_sequence[last_end:match.start()]
            pos = len(clean_sequence)
            
            # 添加氨基酸
            aa = match.group(1)
            clean_sequence += aa
            
            # 记录修饰
            mod = match.group(2)[1:-1]  # 去除括号
            modifications[pos] = mod
            
            last_end = match.end()
        
        # 添加剩余部分
        clean_sequence += modified_sequence[last_end:]
        
        return clean_sequence, modifications
    
    @staticmethod
    def format_modified_sequence(sequence: str, modifications: Dict[int, str]) -> str:
        """
        将序列和修饰信息格式化为带修饰标记的序列
        
        参数:
            sequence: 原始序列
            modifications: 修饰信息
            
        返回:
            带修饰标记的序列
        """
        result = ""
        for i, aa in enumerate(sequence):
            result += aa
            if i in modifications:
                result += f"({modifications[i]})"
                
        return result

class ProteinModificationRepository():
    def __init__(self):
        self.modifications = None
    
    def load(self, file_path: str):
        if os.path.exists(file_path):
            self.modifications = pd.read_csv(file_path, sep='\t').to_dict(orient='records')
        else:
            raise FileNotFoundError(f"File {file_path} not found")
        
    def find(self, mass: float, tolerance: float = 0.0001) -> list[Modification]:
        results = []
        for modification in self.modifications:
            if abs(modification['Isotopic Mass'] - mass) <= tolerance:
                results.append(Modification(modification['Mod Name'], modification['Formula']))
        return None

