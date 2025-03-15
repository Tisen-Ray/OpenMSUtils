class FDRUtils():
    def __init__(self):
        pass

    def get_fdr_list(self, score, label):
        """
        Calculate the False Discovery Rate (FDR) based on the given score and label.

        Parameters:
        score (float): The score to evaluate.
        label (int): The label indicating whether the score is positive (1) or negative (0).

        Returns:
        list: A list containing the FDR values.
        """
        # Sort scores in descending order and track original indices
        sorted_indices = sorted(range(len(score)), key=lambda i: score[i], reverse=True)
        
        # Create sorted lists of scores and labels
        sorted_scores = [score[i] for i in sorted_indices]
        sorted_labels = [label[i] for i in sorted_indices]
        
        # Calculate FDR values
        fdr_list = []
        target_count = 0
        decoy_count = 0
        
        for i in range(len(sorted_scores)):
            if sorted_labels[i] == 1:
                target_count += 1
            else:
                decoy_count += 1
                
            if target_count == 0:
                fdr_list.append(0)
            else:
                fdr_list.append(float(decoy_count) / target_count)
        
        # Calculate q-values using monotonic FDR
        min_fdr = fdr_list[-1]
        fdr_list_mono = []
        
        for i in range(len(fdr_list)-1, -1, -1):
            if min_fdr > fdr_list[i]:
                min_fdr = fdr_list[i]
            fdr_list_mono.append(min_fdr)
            
        fdr_list_mono.reverse()
        
        # Map q-values back to original order
        result_list = [0] * len(score)
        for i, orig_idx in enumerate(sorted_indices):
            result_list[orig_idx] = fdr_list_mono[i]
            
        return result_list

    def get_fdr_counts(self, score, label, threshold=0.01):
        fdr_list = self.get_fdr_list(score, label)
        count_below_threshold = sum(1 for fdr in fdr_list if fdr < threshold)
        return count_below_threshold
    