"""MLflow tracing that degrades to a no-op if MLflow or an experiment isn't configured."""
import functools

from config import MLFLOW_EXPERIMENT

_enabled = False
try:
    import mlflow

    if MLFLOW_EXPERIMENT:
        mlflow.set_tracking_uri("databricks")
        mlflow.set_experiment(MLFLOW_EXPERIMENT)
        _enabled = True
except Exception as e:  # tracing must never break the agent
    print(f"[tracing] disabled: {e}")


def trace(name: str, span_type: str = "UNKNOWN"):
    """Decorator: records the function as an MLflow span when tracing is enabled."""
    def decorator(fn):
        if _enabled:
            return mlflow.trace(name=name, span_type=span_type)(fn)

        @functools.wraps(fn)
        async def passthrough(*args, **kwargs):
            return await fn(*args, **kwargs)
        return passthrough
    return decorator
