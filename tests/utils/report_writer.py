import json
import os
from datetime import datetime


class ReportWriter:
    def __init__(self, path="tests/deep_validation_report.json"):
        self.path = path
        self.report = {
            "run": {
                "timestamp": datetime.now().isoformat(),
            },
            "endpoints": {},
            "pages": {},
            "warnings": [],
            "failures": [],
        }

    def record_endpoint(self, name, data):
        self.report["endpoints"][name] = data

    def record_page(self, name, data):
        self.report["pages"][name] = data

    def warn(self, message):
        self.report["warnings"].append(message)

    def fail(self, message):
        self.report["failures"].append(message)

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.report, f, indent=2)
        return self.path
