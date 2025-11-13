# npx @github/copilot
 

import xgboost as xgb
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

print("# Load sample data")
data = fetch_california_housing()
X, y = data.data, data.target

print("# Split into train and test sets")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("# Create DMatrix for XGBoost")
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

print("# Set parameters")
params = {
    'objective': 'reg:squarederror',
    'max_depth': 4,
    'eta': 0.1,
    'seed': 42
}

print("# Train model")
model = xgb.train(params, dtrain, num_boost_round=100)

print("# Predict")
y_pred = model.predict(dtest)

print("# Evaluate")
mse = mean_squared_error(y_test, y_pred)
print(f"Mean Squared Error: {mse:.2f}")