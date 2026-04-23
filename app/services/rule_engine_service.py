import re
import unicodedata
import os
import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, field_validator

from app.services.ai_classifier_service import AIClassifierService


class _RuleSchema(BaseModel):
    name: str
    pattern: str
    category: str
    severity: str
    description: Optional[str] = None

    @field_validator("severity")
    @classmethod
    def _check_severity(cls, v: str) -> str:
        valid = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
        if v.upper() not in valid:
            raise ValueError(f"severity '{v}' must be one of {valid}")
        return v.upper()

    @field_validator("pattern")
    @classmethod
    def _check_pattern(cls, v: str) -> str:
        try:
            re.compile(v)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern '{v}': {exc}") from exc
        return v


class RuleEngineService:
    DEFAULT_DETECTOR = "GENERAL"
    ML_CLASSIFIER_DETECTOR = "AI_CLASSIFIER"
    DEFAULT_AI_MODEL = os.getenv("AI_CLASSIFIER_DEFAULT_MODEL", "xlmr").strip().lower()
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
            raw_rulesets = {"general": rules_config}
        else:
            raw_rulesets = {
                "general": rules_config.get("general", []),
                "prompt_injection_specific": rules_config.get("prompt_injection_specific", []),
                "privilege_escalation_specific": rules_config.get("privilege_escalation_specific", []),
                "sensitive_info_specific": rules_config.get("sensitive_info_specific", []),
            }

        self.rulesets = {}
        for ruleset_name, rules in raw_rulesets.items():
            validated = []
            for raw_rule in (rules or []):
                try:
                    validated.append(_RuleSchema(**raw_rule).model_dump())
                except Exception as exc:
                    raise ValueError(
                        f"Invalid rule in ruleset '{ruleset_name}': {exc}"
                    ) from exc
            self.rulesets[ruleset_name] = validated

        self.detectors = data.get("detectors", {}) or {
            self.DEFAULT_DETECTOR: {
                "enabled": True,
                "description": "Detector general con reglas base.",
                "ruleset": "general",
            }
        }
        self.ai_classifier = AIClassifierService()

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
            if detector_key == self.ML_CLASSIFIER_DETECTOR:
                continue
            ruleset_name = self.detectors.get(detector_key, {}).get("ruleset", "general")
            rules = self.rulesets.get(ruleset_name, [])
            for rule in rules:
                resolved.append((detector_key, rule))
        return resolved

    def _normalize(self, text: str) -> str:
        return unicodedata.normalize("NFKD", text)

    def get_available_detectors(self):
        available = []
        for detector_key, config in self.detectors.items():
            enabled = bool(config.get("enabled", True))
            description = config.get("description", "")

            if detector_key == self.ML_CLASSIFIER_DETECTOR:
                service_ready = self.ai_classifier.is_available()
                enabled = enabled and service_ready
                if not service_ready:
                    description = (
                        f"{description} Requiere el servicio local de Prompt Guard activo."
                    ).strip()

            available.append(
                {
                    "key": detector_key,
                    "enabled": enabled,
                    "description": description,
                    "is_default": detector_key == self.DEFAULT_DETECTOR,
                }
            )

        return available

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

    def _run_ai_classifier(self, text: str, model: str | None, selected_detectors: list[str]):
        if self.ML_CLASSIFIER_DETECTOR not in selected_detectors:
            return None

        selected_model = (model or self.DEFAULT_AI_MODEL).strip().lower()
        if selected_model not in {"llama", "xlmr"}:
            raise ValueError("Invalid AI classifier model. Use 'llama' or 'xlmr'.")

        match = self.ai_classifier.detect(text, model=selected_model)
        if not match["matched"]:
            return {
                "matched": False,
                "rule_name": None,
                "category": None,
                "severity": None,
                "confidence": 0.0,
                "detection_method": match["detection_method"],
                "detectors_applied": selected_detectors,
                "detector_triggered": None,
            }

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

    def detect(self, text: str, model: str | None = None, detectors: list[str] | None = None):
        selected_detectors = self._normalize_detectors(detectors)
        active_rules = self._resolve_rules(selected_detectors)
        normalized_text = self._normalize(text)

        for detector_key, rule in active_rules:
            if re.search(rule["pattern"], normalized_text, flags=re.IGNORECASE):
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

        ai_match = self._run_ai_classifier(text, model, selected_detectors)
        if ai_match and ai_match["matched"]:
            return ai_match

        return {
            "matched": False,
            "rule_name": None,
            "category": None,
            "severity": None,
            "confidence": 0.0,
            "detection_method": ai_match["detection_method"] if ai_match else "none",
            "detectors_applied": selected_detectors,
            "detector_triggered": None,
        }

    def detect_multimatch(
        self,
        text: str,
        detectors: list[str] | None = None,
        model: str | None = None,
    ):
        selected_detectors = self._normalize_detectors(detectors)
        active_rules = self._resolve_rules(selected_detectors)
        normalized_text = self._normalize(text)
        matches = []

        for detector_key, rule in active_rules:
            if re.search(rule["pattern"], normalized_text, flags=re.IGNORECASE):
                matches.append(self._build_match_result(detector_key, rule))

        ai_match = self._run_ai_classifier(text, model, selected_detectors)
        if ai_match and ai_match["matched"]:
            matches.append(
                {
                    "detector_triggered": ai_match["detector_triggered"],
                    "rule_name": ai_match["rule_name"],
                    "category": ai_match["category"],
                    "severity": ai_match["severity"],
                    "confidence": ai_match["confidence"],
                    "detection_method": ai_match["detection_method"],
                }
            )

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
                "detection_method": ai_match["detection_method"] if ai_match else "none",
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
