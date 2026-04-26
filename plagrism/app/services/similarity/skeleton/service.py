from typing import List, Dict
from app.schemas.skeleton import SkeletonFingerprint, SkeletonSimilarityScore

class SkeletonSimilarityService:
    """
    Compares two code skeleton fingerprints to find stylometric or structural similarities.
    """

    def compare(self, source: SkeletonFingerprint, target: SkeletonFingerprint) -> SkeletonSimilarityScore:
        """
        Calculates similarity between two fingerprints.
        
        Robust Fields (Direct structural counts):
        - function_count, class_count, import_count
        - control_flow_counts (if/for/while/try)
        - import_modules
        
        Heuristic Fields (Stylometric indicators):
        - decomposition_ratio (code organization style)
        - max_nesting_depth (algorithmic complexity style)
        - error_handling_patterns
        """
        
        # 1. Structural Match (Robust counts)
        # Using a simple ratio of counts
        struct_score = self._compare_counts(
            [source.function_count, source.class_count, source.import_count],
            [target.function_count, target.class_count, target.import_count]
        )
        
        # 2. Stylometric Match (Heuristics)
        stylo_score = 1.0
        # Decomposition ratio comparison (allow 20% variance)
        if source.decomposition_ratio > 0 and target.decomposition_ratio > 0:
            ratio_diff = abs(source.decomposition_ratio - target.decomposition_ratio) / max(source.decomposition_ratio, target.decomposition_ratio)
            stylo_score *= (1.0 - min(ratio_diff, 1.0))
        
        # Error handling patterns match
        s_err = set(source.error_handling_patterns)
        t_err = set(target.error_handling_patterns)
        if s_err or t_err:
            err_intersect = len(s_err.intersection(t_err))
            err_union = len(s_err.union(t_err))
            stylo_score = (stylo_score + (err_intersect / err_union if err_union > 0 else 1.0)) / 2.0

        # 3. Complexity Match (Nesting & Flow)
        # Compare max nesting
        nest_score = 1.0 - (abs(source.max_nesting_depth - target.max_nesting_depth) / max(source.max_nesting_depth, target.max_nesting_depth, 1))
        
        # Compare control flow patterns
        flow_score = self._compare_dicts(source.control_flow_counts, target.control_flow_counts)
        comp_score = (nest_score + flow_score) / 2.0

        # Weighted Final Score
        # Structural is most reliable, then complexity, then stylometry
        final_score = (struct_score * 0.5) + (comp_score * 0.3) + (stylo_score * 0.2)
        
        matches = []
        if struct_score > 0.8: matches.append("Strong structural count similarity")
        if nest_score > 0.9: matches.append("Identical nesting complexity")
        if s_err.intersection(t_err): matches.append(f"Matching error handling: {list(s_err.intersection(t_err))}")

        return SkeletonSimilarityScore(
            source_id="source",
            target_id="target",
            overall_score=round(final_score * 100, 2),
            structural_match=round(struct_score, 2),
            stylometric_match=round(stylo_score, 2),
            complexity_match=round(comp_score, 2),
            matches=matches
        )

    def _compare_counts(self, s_list: List[int], t_list: List[int]) -> float:
        total_s = sum(s_list)
        total_t = sum(t_list)
        if total_s == 0 and total_t == 0: return 1.0
        if total_s == 0 or total_t == 0: return 0.0
        
        intersection = sum(min(s, t) for s, t in zip(s_list, t_list))
        union = sum(max(s, t) for s, t in zip(s_list, t_list))
        return intersection / union

    def _compare_dicts(self, s_dict: Dict[str, int], t_dict: Dict[str, int]) -> float:
        all_keys = set(s_dict.keys()).union(set(t_dict.keys()))
        if not all_keys: return 1.0
        
        intersection = sum(min(s_dict.get(k, 0), t_dict.get(k, 0)) for k in all_keys)
        union = sum(max(s_dict.get(k, 0), t_dict.get(k, 0)) for k in all_keys)
        return intersection / union if union > 0 else 1.0
