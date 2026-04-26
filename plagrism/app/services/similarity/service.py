import datetime
from typing import List, Dict
from app.schemas.normalization import NormalizedFile, NormalizedBlock
from app.schemas.similarity import SimilarityScore, SimilarityReport, MatchDetail
from app.services.similarity.fingerprint import WinnowingFingerprinter

class SimilarityService:
    """
    Service to compute similarity between normalized code entities.
    """

    def __init__(self, k: int = 20, window_size: int = 10):
        """
        Args:
            k: K-gram size for fingerprinting. Higher means more exact matches.
            window_size: Window size for winnowing. Controls fingerprint density.
        """
        self.fingerprinter = WinnowingFingerprinter(k=k, window_size=window_size)

    def compare_files(self, source_file: NormalizedFile, target_file: NormalizedFile) -> SimilarityScore:
        """
        Compares two normalized files and returns a similarity score (0-100).
        
        Score Interpretation:
        - 0-20: Unlikely to be plagiarized (common boilerplate or coincidental patterns).
        - 21-50: Suspicious. Significant overlap in logic or structure.
        - 51-80: High probability of plagiarism. Structure and logic are largely identical.
        - 81-100: Near identical or trivial modifications (variable renaming, whitespace changes).
        """
        source_fprints = self.fingerprinter.get_fingerprints(source_file.normalized_content)
        target_fprints = self.fingerprinter.get_fingerprints(target_file.normalized_content)
        
        # We use a combination of Jaccard (overall similarity) and Containment (one inside another)
        jaccard = WinnowingFingerprinter.calculate_jaccard_similarity(source_fprints, target_fprints)
        containment = WinnowingFingerprinter.calculate_containment_similarity(source_fprints, target_fprints)
        
        # Final score is weighted. We lean towards containment to catch snippets.
        # But we don't want a 10-line file in a 1000-line file to necessarily trigger 100%
        # unless it's a very high percentage of the source.
        final_score_raw = max(jaccard, containment)
        final_score = round(final_score_raw * 100, 2)
        
        return SimilarityScore(
            source_id=source_file.original_path,
            target_id=target_file.original_path,
            score=final_score,
            matching_fingerprints_count=len(source_fprints.intersection(target_fprints)),
            total_fingerprints_source=len(source_fprints),
            total_fingerprints_target=len(target_fprints)
        )

    def compare_blocks(self, source_block: NormalizedBlock, target_block: NormalizedBlock) -> float:
        """
        Compares two logical blocks and returns 0-100 score.
        """
        s_fprints = self.fingerprinter.get_fingerprints(source_block.content)
        t_fprints = self.fingerprinter.get_fingerprints(target_block.content)
        
        jaccard = WinnowingFingerprinter.calculate_jaccard_similarity(s_fprints, t_fprints)
        return round(jaccard * 100, 2)

    def compare_submission(self, 
                           submission_id: str,
                           submission_files: List[NormalizedFile], 
                           corpus_files: List[NormalizedFile],
                           threshold: float = 25.0) -> SimilarityReport:
        """
        Compares all files in a submission against a corpus of existing files.
        Performs both file-level and block-level checks.
        """
        all_scores = []
        
        for s_file in submission_files:
            # File-level check
            for c_file in corpus_files:
                if s_file.original_path == c_file.original_path:
                    continue
                    
                score_obj = self.compare_files(s_file, c_file)
                
                # Check blocks if file-level is high or for deep analysis
                # For now, let's also check all blocks against all corpus blocks
                # (This could be optimized with an index later)
                block_matches = []
                for s_block in s_file.blocks:
                    for c_block in c_file.blocks:
                        b_score = self.compare_blocks(s_block, c_block)
                        if b_score > threshold:
                            block_matches.append(MatchDetail(
                                source_chunk_id=s_block.name,
                                target_chunk_id=c_block.name,
                                similarity_score=b_score,
                                matched_tokens=0 # Placeholder
                            ))
                
                if block_matches:
                    # Update file score if a block has a higher match
                    max_block_score = max(m.similarity_score for m in block_matches)
                    score_obj.score = max(score_obj.score, max_block_score)
                    score_obj.match_details = block_matches
                
                if score_obj.score >= threshold:
                    all_scores.append(score_obj)
        
        all_scores.sort(key=lambda x: x.score, reverse=True)
        
        return SimilarityReport(
            submission_id=submission_id,
            top_matches=all_scores[:50],
            generated_at=datetime.datetime.utcnow().isoformat()
        )
