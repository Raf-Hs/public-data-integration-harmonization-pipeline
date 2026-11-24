"""Entry point for running the pipeline."""

from src.pipeline.pipeline import run_pipeline

if __name__ == "__main__":
    summary = run_pipeline()
    print(summary["passed"])
