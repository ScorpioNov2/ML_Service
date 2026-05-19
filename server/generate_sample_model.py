"""
generate_sample_model.py
────────────────────────
Creates a tiny sklearn LogisticRegression model and saves it as
./models/model.pkl so the backend has a default model to fall back on.

Run once before starting the server:
    python generate_sample_model.py
"""

# import pickle
# from pathlib import Path

# import numpy as np
# from sklearn.linear_model import LogisticRegression

# MODELS_DIR = Path("./models")
# OUTPUT_PATH = MODELS_DIR / "model.pkl"

# RANDOM_STATE = 42
# N_SAMPLES = 100
# N_FEATURES = 2


# def main() -> None:
#     MODELS_DIR.mkdir(parents=True, exist_ok=True)

#     rng = np.random.default_rng(RANDOM_STATE)
#     X = rng.standard_normal((N_SAMPLES, N_FEATURES))
#     y = (X[:, 0] + X[:, 1] > 0).astype(int)

#     model = LogisticRegression(random_state=RANDOM_STATE)
#     model.fit(X, y)

#     with OUTPUT_PATH.open("wb") as fh:
#         pickle.dump(model, fh)

#     print(f"✅  Sample model saved to {OUTPUT_PATH}")
#     print(f"   Features expected: {N_FEATURES} numeric columns (feature_0, feature_1)")


# if __name__ == "__main__":
#     main()
