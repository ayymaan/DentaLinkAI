from pathlib import Path
import pickle


class DemoModel:
    def __init__(self, weight: float):
        self.weight = weight

    def predict_proba(self, X):
        probs = []
        for row in X:
            base = sum(row) * self.weight
            prob = 1 / (1 + pow(2.71828, -base))
            probs.append([1 - prob, prob])
        return probs


BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    for name, weight in [("appointment", 0.01), ("payment", 0.02), ("treatment", 0.03)]:
        path = MODELS_DIR / f"{name}_model.joblib"
        with path.open("wb") as f:
            pickle.dump(DemoModel(weight), f)


if __name__ == "__main__":
    main()
