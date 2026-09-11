import logging
import threading
import time

from app.config import get_settings
from app.ml.route_scorer import route_scorer
from app.ml.traffic_predictor import traffic_predictor
from app.ml.trainer import retrain_models
from app.ml.travel_time_model import travel_time_model
from app.services.history_service import history_service
from app.services.realtime_feed import incident_feed

logger = logging.getLogger(__name__)

_TRAIN_LOCK = threading.Lock()


class ModelRegistry:
    """Tracks ML model state, schedules background auto-retraining and
    exposes a single /models/info report for the UI."""

    def __init__(self):
        self.settings = get_settings()
        self.report: dict | None = None
        self.training = False
        self.last_trained_at: float | None = None
        self._reserved_count = 0

    def maybe_auto_retrain(self, history_count: int) -> dict | None:
        """Trigger a background retrain when enough new real trips arrived."""
        if self.training:
            return None
        threshold = self.settings.auto_retrain_threshold
        if (
            history_count >= threshold
            and (history_count - self._reserved_count) >= threshold
        ):
            self._reserved_count = history_count
            worker = threading.Thread(target=self._train_background, daemon=True)
            worker.start()
            logger.info(f"Auto-retrain scheduled at {history_count} history samples")
            return {"started": True, "history_count": history_count}
        return None

    def _train_background(self):
        with _TRAIN_LOCK:
            if self.training:
                return
            self.training = True
        try:
            report = retrain_models()
            with _TRAIN_LOCK:
                self.report = report
                self.last_trained_at = time.time()
            incident_feed.publish({"type": "model", "payload": self.info()})
            logger.info("Background model retrain finished")
        except Exception:  # noqa: BLE001
            logger.exception("Background retrain failed")
        finally:
            with _TRAIN_LOCK:
                self.training = False

    def train_now(self) -> dict:
        """Synchronous retrain (used by POST /api/v1/models/retrain)."""
        with _TRAIN_LOCK:
            if self.training:
                return {"training_in_progress": True}
            self.training = True
        try:
            report = retrain_models()
            with _TRAIN_LOCK:
                self.report = report
                self.last_trained_at = time.time()
                self._reserved_count = history_service.get_count()
            incident_feed.publish({"type": "model", "payload": self.info()})
            return report
        finally:
            with _TRAIN_LOCK:
                self.training = False

    def load_saved(self) -> None:
        """Reload persisted ML models at startup so AI is active right away."""
        travel_time_model._load_model()
        traffic_predictor._load_model()
        route_scorer._load_model()
        count = history_service.get_count()
        for predictor in (traffic_predictor, route_scorer):
            predictor.history_samples = min(
                int(count), self.settings.ai_blend_max_samples
            )
        logger.info(
            f"Saved models loaded | history={count} "
            f"| travel_time={travel_time_model.samples}s "
            f"can_predict={travel_time_model.can_predict()}"
        )

    def info(self) -> dict:
        traffic_blend = traffic_predictor.history_samples / max(
            1, self.settings.ai_blend_max_samples
        )
        return {
            "history_count": history_service.get_count(),
            "auto_retrain_threshold": self.settings.auto_retrain_threshold,
            "ml_min_history_samples": self.settings.ml_min_history_samples,
            "training": self.training,
            "last_trained_at": self.last_trained_at,
            "travel_time": travel_time_model.info(),
            "traffic": {
                "trained": traffic_predictor.is_trained,
                "history_samples": traffic_predictor.history_samples,
                "blend_weight": round(min(1.0, traffic_blend), 3),
                "metrics": traffic_predictor.last_metrics,
            },
            "route_scorer": {
                "trained": route_scorer.is_trained,
                "history_samples": route_scorer.history_samples,
                "metrics": route_scorer.last_metrics,
            },
        }


registry = ModelRegistry()
