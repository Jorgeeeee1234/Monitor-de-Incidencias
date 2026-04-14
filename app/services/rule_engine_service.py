import re
import yaml
from pathlib import Path


class RuleEngineService:
    DEFAULT_DETECTOR = "GENERAL"
    ML_CLASSIFIER_DETECTOR = "AI_CLASSIFIER"
    SEVERITY_RANK = {
        "CRITICAL": 5,
        "HIGH": 4,
        "MEDIUM": 3,
        "LOW": 2,
        "INFO": 1,
    }

    def __init__(self):
        config_path = Path("config/rules.yml")
        with open(config_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

        rules_config = data.get("rules", {})
        if isinstance(rules_config, list):
            # Backward compatibility for the previous single-list format.
            self.rulesets = {"general": rules_config}
        else:
            self.rulesets = {
                "general": rules_config.get("general", []),
                "prompt_injection_specific": rules_config.get("prompt_injection_specific", []),
                "privilege_escalation_specific": rules_config.get("privilege_escalation_specific", []),
                "sensitive_info_specific": rules_config.get("sensitive_info_specific", []),
            }

        self.detectors = data.get("detectors", {}) or {
            self.DEFAULT_DETECTOR: {
                "enabled": True,
                "description": "Detector general con reglas base.",
                "ruleset": "general",
            }
        }

    def _normalize_detectors(self, detectors: list[str] | None):
        if not detectors:
            detectors = [self.DEFAULT_DETECTOR]

        normalized = []
        for detector in detectors:
            detector_key = str(detector).upper().strip()
            if not detector_key:
                continue
            if detector_key in normalized:
                continue
            if detector_key not in self.detectors:
                raise ValueError(f"Unknown detector: {detector_key}")

            config = self.detectors.get(detector_key, {})
            if not config.get("enabled", True):
                raise ValueError(f"Detector disabled: {detector_key}")

            normalized.append(detector_key)

        if not normalized:
            normalized = [self.DEFAULT_DETECTOR]

        return normalized

    def _resolve_rules(self, detectors: list[str]):
        resolved = []
        for detector_key in detectors:
            ruleset_name = self.detectors.get(detector_key, {}).get("ruleset", "general")
            rules = self.rulesets.get(ruleset_name, [])
            for rule in rules:
                resolved.append((detector_key, rule))
        return resolved

    def get_available_detectors(self):
        return [
            {
                "key": detector_key,
                "enabled": bool(config.get("enabled", True)),
                "description": config.get("description", ""),
                "is_default": detector_key == self.DEFAULT_DETECTOR,
            }
            for detector_key, config in self.detectors.items()
        ]

    def _build_match_result(self, detector_key: str, rule: dict):
        return {
            "detector_triggered": detector_key,
            "rule_name": rule["name"],
            "category": rule["category"],
            "severity": rule["severity"],
            "confidence": 0.90,
            "detection_method": f"regex_rule_engine:{detector_key.lower()}",
        }

    def _select_top_match(self, matches: list[dict]):
        if not matches:
            return None

        def sort_key(match: dict):
            severity = str(match.get("severity", "")).upper()
            return self.SEVERITY_RANK.get(severity, 0)

        return max(matches, key=sort_key)

    def detect(self, text: str, detectors: list[str] | None = None):
        selected_detectors = self._normalize_detectors(detectors)
        active_rules = self._resolve_rules(selected_detectors)

        for detector_key, rule in active_rules:
            if re.search(rule["pattern"], text, flags=re.IGNORECASE):
                match = self._build_match_result(detector_key, rule)
                return {
                    "matched": True,
                    "rule_name": match["rule_name"],
                    "category": match["category"],
                    "severity": match["severity"],
                    "confidence": match["confidence"],
                    "detection_method": match["detection_method"],
                    "detectors_applied": selected_detectors,
                    "detector_triggered": match["detector_triggered"],
                }

        return {
            "matched": False,
            "rule_name": None,
            "category": None,
            "severity": None,
            "confidence": 0.0,
            "detection_method": "none",
            "detectors_applied": selected_detectors,
            "detector_triggered": None,
        }

    def detect_multimatch(self, text: str, detectors: list[str] | None = None):
        selected_detectors = self._normalize_detectors(detectors)
        active_rules = self._resolve_rules(selected_detectors)
        matches = []

        for detector_key, rule in active_rules:
            if re.search(rule["pattern"], text, flags=re.IGNORECASE):
                matches.append(self._build_match_result(detector_key, rule))

        top_match = self._select_top_match(matches)

        if not top_match:
            return {
                "matched": False,
                "match_count": 0,
                "matches": [],
                "top_match": None,
                "rule_name": None,
                "category": None,
                "severity": None,
                "confidence": 0.0,
                "detection_method": "none",
                "detectors_applied": selected_detectors,
                "detector_triggered": None,
            }

        return {
            "matched": True,
            "match_count": len(matches),
            "matches": matches,
            "top_match": top_match,
            "rule_name": top_match["rule_name"],
            "category": top_match["category"],
            "severity": top_match["severity"],
            "confidence": top_match["confidence"],
            "detection_method": top_match["detection_method"],
            "detectors_applied": selected_detectors,
            "detector_triggered": top_match["detector_triggered"],
        }
