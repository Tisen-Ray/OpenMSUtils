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
        解析带修饰标记的序列，例如 "PEP(Phospho)TIDE" 或 "PEP(Phospho (P))TIDE"
        
        参数:
            modified_sequence: 带修饰标记的序列
            
        返回:
            原始序列和修饰信息
        """
        clean_sequence = ""
        modifications = {}
        i = 0
        pos = 0
        
        while i < len(modified_sequence):
            if i < len(modified_sequence) - 1 and modified_sequence[i+1] == '(':
                # 找到一个氨基酸后面跟着修饰
                aa = modified_sequence[i]
                clean_sequence += aa
                pos = len(clean_sequence) - 1
                
                # 找到完整的修饰（处理嵌套括号）
                start = i + 2  # 跳过 '('
                paren_count = 1
                j = start
                
                while j < len(modified_sequence) and paren_count > 0:
                    if modified_sequence[j] == '(':
                        paren_count += 1
                    elif modified_sequence[j] == ')':
                        paren_count -= 1
                    j += 1
                
                if paren_count == 0:
                    mod = modified_sequence[start:j-1]  # 去除最外层括号
                    modifications[pos] = mod
                    i = j  # 更新索引到修饰后的位置
                    continue
            
            # 普通字符
            clean_sequence += modified_sequence[i]
            i += 1
        
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

