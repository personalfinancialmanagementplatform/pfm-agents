from src.config import get_configs

cfgs = get_configs()
print("taide model:", cfgs["taide"]["model"]["name"])
print("news timezone:", cfgs["news"]["meta"]["timezone"])
print("OK")
