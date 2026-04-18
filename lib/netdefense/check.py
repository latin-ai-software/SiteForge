import re
from typing import List, Dict

class MalwareChecker:
    def __init__(self):
        # Einfache Keyword-Liste (harmlos, rein textbasiert)
        self.suspicious_keywords = [
            "powershell", "Invoke-WebRequest", "wget", "curl",
            "base64", "eval(", "exec(", "subprocess", "import os",
            "rm -rf", "chmod 777", "payload", "shellcode",
            "registry", "CreateObject", "WScript"
        ]

        # Regex-Muster für obfuskierte oder ungewöhnliche Inhalte
        self.patterns = {
            "base64_like": re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
            "hex_blob": re.compile(r"(?:[0-9a-fA-F]{2}\s*){16,}"),
            "suspicious_url": re.compile(r"https?://[^\s]+"),
        }

    def check_text(self, text: str) -> Dict[str, List[str]]:
        """Analysiert Text auf verdächtige Muster."""
        findings = {
            "keywords": [],
            "patterns": [],
            "score": 0
        }

        # Keyword-Check
        for kw in self.suspicious_keywords:
            if kw.lower() in text.lower():
                findings["keywords"].append(kw)
                findings["score"] += 1

        # Regex-Checks
        for name, pattern in self.patterns.items():
            if pattern.search(text):
                findings["patterns"].append(name)
                findings["score"] += 1

        return findings

    def is_suspicious(self, text: str, threshold: int = 2) -> bool:
        """Gibt True zurück, wenn der Text verdächtig wirkt."""
        result = self.check_text(text)
        return result["score"] >= threshold