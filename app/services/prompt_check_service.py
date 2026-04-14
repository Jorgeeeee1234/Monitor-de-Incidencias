from app.services.rule_engine_service import RuleEngineService


class PromptCheckService:
    MULTIMATCH_MODE = "MULTIMATCH"

    def __init__(self):
        self.rule_engine = RuleEngineService()

    def get_available_detectors(self):
        detectors = self.rule_engine.get_available_detectors()
        detectors.append(
            {
                "key": self.MULTIMATCH_MODE,
                "enabled": False,
                "description": "Modo multimatch (usa endpoint dedicado).",
                "is_default": False,
            }
        )
        return detectors

    def _sanitize_detectors(self, detectors: list[str] | None):
        if not detectors:
            return None

        cleaned = []
        for detector in detectors:
            detector_key = str(detector).upper().strip()
            if not detector_key:
                continue
            if detector_key == self.MULTIMATCH_MODE:
                continue
            if detector_key in cleaned:
                continue
            cleaned.append(detector_key)
        return cleaned or None

    def analyze_input(self, content: str, detectors: list[str] | None = None):
        selected_detectors = self._sanitize_detectors(detectors)
        detection = self.rule_engine.detect(content, detectors=selected_detectors)

        return {
            "incident_detected": bool(detection["matched"]),
            "input_detected": bool(detection["matched"]),
            "output_detected": False,
            "detectors_used": detection.get("detectors_applied", []),
            "category": detection.get("category"),
            "severity": detection.get("severity"),
            "rule_name": detection.get("rule_name"),
            "detection_method": detection.get("detection_method"),
        }

    def analyze_input_multimatch(self, content: str, detectors: list[str] | None = None):
        selected_detectors = self._sanitize_detectors(detectors)
        detection = self.rule_engine.detect_multimatch(content, detectors=selected_detectors)

        return {
            "incident_detected": bool(detection["matched"]),
            "input_detected": bool(detection["matched"]),
            "output_detected": False,
            "detectors_used": detection.get("detectors_applied", []),
            "match_count": int(detection.get("match_count", 0)),
            "matches": detection.get("matches", []),
            "top_match": detection.get("top_match"),
            "category": detection.get("category"),
            "severity": detection.get("severity"),
            "rule_name": detection.get("rule_name"),
            "detection_method": detection.get("detection_method"),
        }
