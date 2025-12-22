#!/bin/bash
# Скрипт для очистки всех выходов DVC pipeline

echo "🧹 Cleaning all pipeline outputs..."

# Удалить обработанные данные (кроме raw)
echo "  Removing processed data..."
rm -f data/processed/train.csv
rm -f data/processed/val.csv
rm -f data/processed/test.csv
rm -f data/processed/titanic_processed.csv

# Удалить features
echo "  Removing features..."
rm -rf data/features/

# Удалить модели
echo "  Removing models..."
rm -f models/model.pkl
rm -rf models/experiments/

# Удалить метрики
echo "  Removing metrics..."
find data/processed -name "*.json" -delete 2>/dev/null || true
find data/features -name "*.json" -delete 2>/dev/null || true
find models -name "*.json" -delete 2>/dev/null || true

# Удалить plots
echo "  Removing plots..."
rm -rf models/plots/

echo "✅ Cleanup completed"
echo ""
echo "To rebuild pipeline, run:"
echo "  uv run dvc repro"
