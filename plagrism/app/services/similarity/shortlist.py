import datetime
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from app.schemas.shortlist import ShortlistedPair, ShortlistReport
from app.schemas.normalization import NormalizedFile
from app.services.similarity.fingerprint import WinnowingFingerprinter
from app.services.similarity.skeleton.service import SkeletonSimilarityService
from app.services.similarity.skeleton.analyzer import SkeletonAnalyzer

class ShortlistingService:
    """
    Service to efficiently identify suspicious submission pairs for deep analysis.
    Uses an inverted index of fingerprints to avoid exhaustive pairwise comparison.
    """

    def __init__(self):
        self.fingerprinter = WinnowingFingerprinter(k=20, window_size=10)
        self.skeleton_service = SkeletonSimilarityService()
        self.skeleton_analyzer = SkeletonAnalyzer()

    async def shortlist(self, 
                        challenge_id: str, 
                        submissions: List[Dict[str, any]], 
                        limit: int = 100) -> ShortlistReport:
        """
        Shortlists suspicious pairs from a list of submissions.
        
        Args:
            challenge_id: ID of the challenge.
            submissions: List of submission data, each containing:
                - 'id': str
                - 'files': Dict[str, str] (path to normalized content)
                - 'language': str
        """
        # 1. Pre-calculate fingerprints and skeletons for all submissions
        processed_data = []
        inverted_index: Dict[int, Set[str]] = defaultdict(set)
        
        for sub in submissions:
            sub_id = sub['id']
            all_hashes: Set[int] = set()
            skeletons = []
            
            for path, content in sub['files'].items():
                # Get token hashes
                fprints = self.fingerprinter.get_fingerprints(content)
                all_hashes.update(fprints)
                
                # Build inverted index
                for h in fprints:
                    inverted_index[h].add(sub_id)
                
                # Get skeleton (for Python)
                if sub['language'] == 'python':
                    skeletons.append(self.skeleton_analyzer.analyze_python(content, path))
            
            processed_data.append({
                'id': sub_id,
                'hashes': all_hashes,
                'skeletons': skeletons,
                'language': sub['language']
            })

        # 2. Find collisions using the inverted index
        collisions: Dict[Tuple[str, str], int] = defaultdict(int)
        for h, sub_ids in inverted_index.items():
            if len(sub_ids) > 1:
                # Every combination in sub_ids has a collision on this hash
                ids_sorted = sorted(list(sub_ids))
                for i in range(len(ids_sorted)):
                    for j in range(i + 1, len(ids_sorted)):
                        collisions[(ids_sorted[i], ids_sorted[j])] += 1

        # 3. Analyze collisions and shortlist
        shortlisted_pairs = []
        data_by_id = {d['id']: d for d in processed_data}
        
        for (id_a, id_b), count in collisions.items():
            # Threshold: at least 5 common fingerprints
            if count < 5:
                continue
                
            sub_a = data_by_id[id_a]
            sub_b = data_by_id[id_b]
            
            # Fast skeleton check
            skel_score = 0.0
            reasons = [f"Found {count} matching token fingerprints"]
            
            if sub_a['skeletons'] and sub_b['skeletons']:
                # Compare first file's skeleton for speed (or average)
                s_res = self.skeleton_service.compare(sub_a['skeletons'][0], sub_b['skeletons'][0])
                skel_score = s_res.overall_score
                if skel_score > 60:
                    reasons.append(f"High structural skeleton similarity ({skel_score}%)")

            # Calculate priority score
            # Collision count is normalized by avg fingerprints
            avg_fprints = (len(sub_a['hashes']) + len(sub_b['hashes'])) / 2.0
            collision_ratio = (count / avg_fprints * 100) if avg_fprints > 0 else 0
            
            priority = (collision_ratio * 0.7) + (skel_score * 0.3)
            
            shortlisted_pairs.append(ShortlistedPair(
                submission_id_a=id_a,
                submission_id_b=id_b,
                token_collision_count=count,
                skeleton_similarity_score=skel_score,
                priority_score=round(priority, 2),
                reasons=reasons,
                challenge_id=challenge_id,
                language=sub_a['language']
            ))

        # Sort by priority and limit
        shortlisted_pairs.sort(key=lambda x: x.priority_score, reverse=True)
        
        return ShortlistReport(
            challenge_id=challenge_id,
            total_candidates_processed=len(submissions),
            shortlisted_pairs=shortlisted_pairs[:limit],
            generated_at=datetime.datetime.utcnow().isoformat()
        )
