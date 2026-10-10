import logging
import json
from pathlib import Path
from typing import Dict, Tuple, Optional, Any, List
from datetime import datetime, timedelta

import pandas as pd

from modules.utils import PROJECT_ROOT

logger = logging.getLogger(__name__)

class BenchmarkStore:
    BENCHMARKS_DIR = PROJECT_ROOT / "data" / "benchmarks"

    def __init__(self, benchmarks_dir: Optional[Path] = None):
        self.benchmarks_dir = Path(benchmarks_dir) if benchmarks_dir else self.BENCHMARKS_DIR
        self.benchmarks_dir.mkdir(parents=True, exist_ok=True)

    def _sector_slug(self, sector: str) -> str:
        return "".join(c if c.isalnum() else "_" for c in sector).lower()

    def save(self, sector: str, peer_stats_df: pd.DataFrame, clean_matrix: pd.DataFrame, metadata: Optional[Dict] = None):
        slug = self._sector_slug(sector)
        sector_dir = self.benchmarks_dir / slug
        sector_dir.mkdir(parents=True, exist_ok=True)
        
        peer_stats_df.to_parquet(sector_dir / "peer_stats.parquet")
        clean_matrix.to_parquet(sector_dir / "clean_matrix.parquet")
        
        meta = {
            "sector": sector,
            "timestamp": datetime.now().isoformat(),
            "n_peers": len(clean_matrix),
            "requested_tickers": clean_matrix.attrs.get("requested_tickers", []),
            "failed_tickers": clean_matrix.attrs.get("failed_tickers", []),
        }
        if metadata:
            meta.update(metadata)
            
        with open(sector_dir / "metadata.json", "w") as f:
            json.dump(meta, f, indent=2)
            
        logger.info(f"Saved benchmark for {sector}")

    def load(self, sector: str) -> Optional[Tuple[pd.DataFrame, pd.DataFrame, Dict]]:
        slug = self._sector_slug(sector)
        sector_dir = self.benchmarks_dir / slug
        
        if not sector_dir.exists():
            return None
            
        try:
            peer_stats_df = pd.read_parquet(sector_dir / "peer_stats.parquet")
            clean_matrix = pd.read_parquet(sector_dir / "clean_matrix.parquet")
            with open(sector_dir / "metadata.json", "r") as f:
                metadata = json.load(f)
            return peer_stats_df, clean_matrix, metadata
        except Exception as e:
            logger.error(f"Error loading benchmark for {sector}: {e}")
            return None

    def is_fresh(self, sector: str, max_age_hours: int = 48) -> bool:
        slug = self._sector_slug(sector)
        meta_path = self.benchmarks_dir / slug / "metadata.json"
        if not meta_path.exists():
            return False
            
        with open(meta_path, "r") as f:
            meta = json.load(f)
            
        ts = datetime.fromisoformat(meta["timestamp"])
        return datetime.now() - ts < timedelta(hours=max_age_hours)

    def list_available(self) -> List[str]:
        sectors = []
        for path in self.benchmarks_dir.iterdir():
            if path.is_dir() and (path / "metadata.json").exists():
                with open(path / "metadata.json", "r") as f:
                    meta = json.load(f)
                    sectors.append(meta.get("sector", path.name))
        return sorted(sectors)
