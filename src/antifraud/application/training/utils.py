import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, precision_recall_curve
from sklearn.model_selection import train_test_split


def load_and_preprocess_data(file_path):
    """Загружает и предобрабатывает данные."""
    if file_path.endswith(".parquet"):
        df = pd.read_parquet(file_path)
    else:
        df = pd.read_csv(file_path)

    # Feature Engineering
    df["hour"] = (df["Time"] // 3600) % 24
    df["is_night"] = df["hour"].between(1, 5).astype(int)

    # Простейшие агрегаты (для примера)
    df["mean_amount"] = df["Amount"].mean()
    df["amount_ratio"] = df["Amount"] / (df["mean_amount"] + 1e-9)

    # Временные признаки (разница между транзакциями)
    df = df.sort_values("Time")
    df["recency"] = df["Time"].diff().fillna(0)

    # Rolling window (количество транзакций за последний час)
    # В реальном времени это делается через Feature Store
    df["tx_1h"] = 1  # заглушка
    df["tx_24h"] = 1  # заглушка
    df["tx_7d"] = 1  # заглушка

    return df


def get_splits(df, target="Class", test_size=0.2):
    """Разделяет данные на train/test."""
    X = df.drop(target, axis=1)
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=42
    )

    return X_train, X_test, y_train, y_test


def evaluate_model(model, X_test, y_test):
    """Оценивает качество модели."""
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))
    return classification_report(y_test, y_pred, output_dict=True)


def find_optimal_threshold(model, X_test, y_test, target_precision=0.8):
    """Находит порог вероятности для заданного уровня точности."""
    probs = model.predict_proba(X_test)[:, 1]
    precisions, _recalls, thresholds = precision_recall_curve(y_test, probs)

    # thresholds на один элемент короче, поэтому сравниваем с precisions[:-1]
    valid_indices = np.where(precisions[:-1] >= target_precision)[0]
    if len(valid_indices) == 0:
        return 0.5

    return thresholds[valid_indices[0]]
