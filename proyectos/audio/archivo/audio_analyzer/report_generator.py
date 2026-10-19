import json
from datetime import datetime
from typing import Dict, Any
import numpy as np


class ReportGenerator:
    """Handles report generation and export."""

    @staticmethod
    def export_report(analysis_results: Dict[str, Any], file_path: str):
        """Export analysis results to JSON with proper type conversion."""

        def convert_to_serializable(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, np.generic):
                return obj.item()
            return obj

        report = {
            'timestamp': datetime.now().isoformat(),
            'analysis': {
                key: convert_to_serializable(value)
                for key, value in analysis_results.items()
            }
        }

        with open(file_path, 'w') as f:
            json.dump(report, f, indent=2)
