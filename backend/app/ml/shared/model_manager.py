"""Model loading, saving, and version management."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import torch

from app.config import settings


class ModelManager:
    """Manages model persistence and versioning."""

    def __init__(self, model_dir: str | None = None):
        self.model_dir = Path(model_dir or settings.ML_MODEL_DIR)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def save_model(
        self,
        model: torch.nn.Module,
        model_name: str,
        metadata: dict | None = None,
    ) -> str:
        """Save a PyTorch model with metadata. Returns version string."""
        version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        version_dir = self.model_dir / model_name / version
        version_dir.mkdir(parents=True, exist_ok=True)

        model_path = version_dir / "model.pt"
        torch.save(model.state_dict(), model_path)

        meta = {
            "version": version,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "model_class": model.__class__.__name__,
            **(metadata or {}),
        }
        with open(version_dir / "metadata.json", "w") as f:
            json.dump(meta, f, indent=2)

        latest_path = self.model_dir / model_name / "latest.json"
        with open(latest_path, "w") as f:
            json.dump({"version": version, "path": str(version_dir)}, f)

        return version

    def load_model(
        self,
        model: torch.nn.Module,
        model_name: str,
        version: str | None = None,
    ) -> torch.nn.Module:
        """Load a model. Uses latest version if none specified."""
        if version is None:
            latest_path = self.model_dir / model_name / "latest.json"
            if not latest_path.exists():
                raise FileNotFoundError(f"No trained model found for '{model_name}'")
            with open(latest_path) as f:
                info = json.load(f)
            version = info["version"]

        model_path = self.model_dir / model_name / version / "model.pt"
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        state_dict = torch.load(model_path, weights_only=True)
        model.load_state_dict(state_dict)
        return model

    def load_metadata(self, model_name: str, version: str | None = None) -> dict:
        """Load metadata for a model version."""
        if version is None:
            latest_path = self.model_dir / model_name / "latest.json"
            if not latest_path.exists():
                return {}
            with open(latest_path) as f:
                info = json.load(f)
            version = info["version"]

        meta_path = self.model_dir / model_name / version / "metadata.json"
        if not meta_path.exists():
            return {}
        with open(meta_path) as f:
            return json.load(f)

    def list_versions(self, model_name: str) -> list[str]:
        """List all saved versions for a model."""
        model_path = self.model_dir / model_name
        if not model_path.exists():
            return []
        versions = [
            d.name for d in model_path.iterdir()
            if d.is_dir() and d.name != "__pycache__"
        ]
        return sorted(versions)

    def get_latest_version(self, model_name: str) -> str | None:
        """Get the latest version string for a model."""
        latest_path = self.model_dir / model_name / "latest.json"
        if not latest_path.exists():
            return None
        with open(latest_path) as f:
            return json.load(f)["version"]
