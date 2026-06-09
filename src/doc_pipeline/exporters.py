import json
from typing import Dict, List


class JSONLExporter:
    """Saves semantic chunks and vector coordinates into JSONLines files."""
    def __init__(self, output_path: str):
        self.output_path = output_path

    def export(self, chunks: List[Dict]):
        with open(self.output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk) + "\n")
