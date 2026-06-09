"""Registry of Epoch AI datasets. Single source of truth for the manifest + ingest."""

from dataclasses import dataclass

BASE = "https://epoch.ai"
LICENSE = "CC BY 4.0"


@dataclass(frozen=True)
class EpochDataset:
    slug: str
    name: str
    explorer_url: str  # human page (source)
    download_url: str  # raw file or, for github, the repo name
    kind: str  # "zip" | "csv" | "github"

    @property
    def citation(self) -> str:
        return (
            f"Epoch AI, 'Data on {self.name}'. Published online at epoch.ai. "
            f"Retrieved from '{self.explorer_url}' [online resource]. License: {LICENSE}."
        )


def _d(slug, name, explorer, download, kind):
    return EpochDataset(slug, name, BASE + explorer, BASE + download, kind)


# Official data-explorer downloads.
DATASETS = [
    _d("ai_models", "AI Models", "/data/ai-models", "/data/ai_models.zip", "zip"),
    _d("ai_companies", "AI Companies", "/data/ai-companies", "/data/ai_companies.zip", "zip"),
    _d("ai_chip_sales", "AI Chip Sales", "/data/ai-chip-sales", "/data/ai_chip_sales.zip", "zip"),
    _d("ai_chip_components", "AI Chip Components", "/data/ai-chip-components", "/data/ai_chip_components.zip", "zip"),
    _d("ai_chip_owners", "AI Chip Owners", "/data/ai-chip-owners", "/data/ai_chip_owners.zip", "zip"),
    _d("gpu_clusters", "GPU Clusters", "/data/gpu-clusters", "/data/gpu_clusters.zip", "zip"),
    _d("data_centers", "Frontier Data Centers", "/data/data-centers", "/data/data_centers/data_centers.zip", "zip"),
    _d("ml_hardware", "Machine Learning Hardware", "/data/machine-learning-hardware", "/data/ml_hardware.zip", "zip"),
    _d("benchmarks", "AI Capabilities", "/benchmarks", "/data/benchmark_data.zip", "zip"),
    _d("polling", "Polling on AI Usage", "/data/polling", "/data/polling_on_ai_usage_mar_2026.csv", "csv"),
]

# Dataset-bearing GitHub repos under github.com/epoch-research (verified at runtime).
GITHUB_REPOS = [
    "data-stock",
    "training-cost-trends",
    "ai-chip-counts",
    "Compute-Trends",
    "MirrorCode-data",
    "open-model-trends",
    "robotic-manipulation-compute",
    "eci-public",
    "lm-algorithmic-progress",
]

GITHUB_DATASETS = [
    EpochDataset(
        slug=repo.lower().replace("-", "_"),
        name=f"GitHub: epoch-research/{repo}",
        explorer_url=f"https://github.com/epoch-research/{repo}",
        download_url=repo,
        kind="github",
    )
    for repo in GITHUB_REPOS
]

ALL = DATASETS + GITHUB_DATASETS


def get(slug: str) -> EpochDataset:
    for d in ALL:
        if d.slug == slug:
            return d
    raise KeyError(f"Unknown dataset {slug!r}. Available: {[d.slug for d in ALL]}")
