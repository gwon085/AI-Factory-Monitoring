import pickle

# 모델 로드
with open("decision_tree_sensor.pkl", "rb") as f:
    model = pickle.load(f)

print("Decision Tree 모델 로드 완료")
