from src.models.taide import get_taide_model

m = get_taide_model()
print("has task_configs:", bool(getattr(m, "_task_configs", None)))
print("parse_transaction cfg:", m._task_configs.get("parse_transaction", None))
out = m.generate_task("parse_transaction", "午餐吃了80")
print(out)
out = m.generate_task("not_exist_task", "測試")
print(out)
