# Сравнение моделей

Детальный анализ и сравнение всех 18 конфигураций моделей.

## Полная таблица результатов

| Конфигурация | Тип модели | Accuracy | Precision | Recall | F1-Score | Время (сек) |
|--------------|-----------|----------|-----------|--------|----------|-------------|
| svc_rbf_c1 | SVC | **0.7105** | **0.7879** | 0.4127 | 0.5417 | 1.65 |
| svc_rbf_c10 | SVC | 0.7039 | 0.7500 | 0.4286 | 0.5455 | 1.74 |
| random_forest_small | RandomForest | 0.7039 | 0.7059 | 0.4800 | 0.5714 | 1.90 |
| catboost_shallow | CatBoost | 0.7039 | 0.6875 | 0.5000 | 0.5794 | 1.47 |
| catboost_deep | CatBoost | 0.7039 | 0.6471 | **0.5238** | **0.5946** | **1.36** |
| svc_linear | SVC | 0.6974 | 0.6875 | 0.4918 | 0.5741 | 1.44 |
| logistic_regression_l1 | LogisticRegression | 0.6908 | 0.6786 | 0.4628 | 0.5524 | 1.84 |
| gradient_boosting_slow | GradientBoosting | 0.6842 | 0.6538 | 0.4800 | 0.5556 | 1.74 |
| random_forest_medium | RandomForest | 0.6776 | 0.6316 | 0.4576 | 0.5333 | 1.83 |
| logistic_regression_elasticnet | LogisticRegression | 0.6776 | 0.6296 | 0.4424 | 0.5243 | 1.48 |
| logistic_regression_l2_weak | LogisticRegression | 0.6711 | 0.6154 | 0.4242 | 0.5024 | 1.52 |
| logistic_regression_l2_strong | LogisticRegression | 0.6645 | 0.5942 | 0.4100 | 0.4858 | 1.49 |
| gradient_boosting_fast | GradientBoosting | 0.6579 | 0.5714 | 0.4000 | 0.4706 | 1.68 |
| random_forest_large | RandomForest | 0.6513 | 0.5556 | 0.3793 | 0.4510 | 2.12 |
| gradient_boosting_deep | GradientBoosting | 0.6447 | 0.5357 | 0.3659 | 0.4348 | 1.91 |
| random_forest_sqrt | RandomForest | 0.6316 | 0.5000 | 0.3333 | 0.4000 | 2.37 |
| knn_k5_distance | KNN | 0.6382 | 0.5185 | 0.3500 | 0.4179 | 1.42 |
| knn_k3_uniform | KNN | 0.6184 | 0.4667 | 0.3182 | 0.3784 | 1.38 |

---

## Анализ по типам моделей

### SVC (Support Vector Classifier)

| Конфигурация | Kernel | C | Accuracy | F1-Score |
|--------------|--------|---|----------|----------|
| svc_rbf_c1 | RBF | 1.0 | **0.7105** | 0.5417 |
| svc_rbf_c10 | RBF | 10.0 | 0.7039 | 0.5455 |
| svc_linear | Linear | 1.0 | 0.6974 | 0.5741 |

**Выводы:**

- RBF kernel превосходит linear на этом датасете
- Увеличение C с 1 до 10 не улучшает результаты
- Высокая precision (0.75-0.79), но низкий recall

---

### RandomForest

| Конфигурация | n_estimators | max_depth | Accuracy | F1-Score |
|--------------|--------------|-----------|----------|----------|
| random_forest_small | 50 | 5 | **0.7039** | **0.5714** |
| random_forest_medium | 100 | 10 | 0.6776 | 0.5333 |
| random_forest_large | 200 | 15 | 0.6513 | 0.4510 |
| random_forest_sqrt | 100 | None | 0.6316 | 0.4000 |

**Выводы:**

- **Меньше деревьев = лучше** на этом датасете
- Переобучение при увеличении сложности модели
- Ограничение глубины (max_depth=5) улучшает генерализацию

---

### CatBoost

| Конфигурация | depth | iterations | Accuracy | F1-Score |
|--------------|-------|------------|----------|----------|
| catboost_shallow | 4 | 100 | 0.7039 | 0.5794 |
| catboost_deep | 6 | 200 | 0.7039 | **0.5946** |

**Выводы:**

- Обе конфигурации дают одинаковую accuracy
- Deep вариант даёт лучший F1-Score
- Самое быстрое обучение среди всех моделей

---

### GradientBoosting

| Конфигурация | learning_rate | n_estimators | Accuracy | F1-Score |
|--------------|---------------|--------------|----------|----------|
| gradient_boosting_slow | 0.05 | 100 | **0.6842** | **0.5556** |
| gradient_boosting_fast | 0.2 | 50 | 0.6579 | 0.4706 |
| gradient_boosting_deep | 0.1 | 100 | 0.6447 | 0.4348 |

**Выводы:**

- Низкий learning_rate (0.05) даёт лучшие результаты
- Агрессивное обучение (0.2) приводит к переобучению

---

### LogisticRegression

| Конфигурация | penalty | C | Accuracy | F1-Score |
|--------------|---------|---|----------|----------|
| logistic_regression_l1 | L1 | 1.0 | **0.6908** | **0.5524** |
| logistic_regression_elasticnet | ElasticNet | 1.0 | 0.6776 | 0.5243 |
| logistic_regression_l2_weak | L2 | 0.1 | 0.6711 | 0.5024 |
| logistic_regression_l2_strong | L2 | 10.0 | 0.6645 | 0.4858 |

**Выводы:**

- L1 регуляризация лучше L2 на этом датасете
- Сильная L2 регуляризация (C=10) ухудшает результаты

---

### KNN

| Конфигурация | n_neighbors | weights | Accuracy | F1-Score |
|--------------|-------------|---------|----------|----------|
| knn_k5_distance | 5 | distance | 0.6382 | 0.4179 |
| knn_k3_uniform | 3 | uniform | 0.6184 | 0.3784 |

**Выводы:**

- KNN показывает худшие результаты среди всех моделей
- Distance weighting немного лучше uniform
- Вероятно, требуется больше признаков или feature engineering

---

## Влияние гиперпараметров

### Сложность модели vs Accuracy

```
Простые модели (мало параметров):
  random_forest_small (50 деревьев): 0.7039 ✓
  catboost_shallow (depth=4): 0.7039 ✓

Сложные модели (много параметров):
  random_forest_large (200 деревьев): 0.6513 ✗
  random_forest_sqrt (без ограничения глубины): 0.6316 ✗
```

**Вывод:** На небольшом датасете (757 строк) простые модели обобщают лучше.

### Время обучения vs Качество

| Модель | Время (сек) | Accuracy | Эффективность |
|--------|-------------|----------|---------------|
| catboost_deep | 1.36 | 0.7039 | Высокая |
| svc_rbf_c1 | 1.65 | 0.7105 | Высокая |
| random_forest_sqrt | 2.37 | 0.6316 | Низкая |

**Вывод:** Нет прямой корреляции между временем и качеством.

---

## Рекомендации по выбору модели

### Для production (accuracy важнее)

```python
# SVC с RBF kernel
from sklearn.svm import SVC

model = SVC(
    kernel='rbf',
    C=1.0,
    gamma='scale',
    random_state=42
)
```

### Для баланса precision/recall

```python
# CatBoost deep
from catboost import CatBoostClassifier

model = CatBoostClassifier(
    depth=6,
    iterations=200,
    learning_rate=0.1,
    random_state=42,
    verbose=False
)
```

### Для быстрого прототипирования

```python
# RandomForest small
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=50,
    max_depth=5,
    random_state=42,
    n_jobs=-1
)
```

---

## Следующие шаги

1. **Feature Engineering**
   - Создание взаимодействий признаков
   - Биннинг возраста и fare
   - Добавление title из имени

2. **Работа с дисбалансом**
   - SMOTE для oversampling
   - Class weights в моделях

3. **Ансамбли**
   - VotingClassifier из топ-3 моделей
   - Stacking с мета-моделью

4. **Кросс-валидация**
   - Stratified K-Fold для надёжной оценки
   - Bayesian optimization гиперпараметров
