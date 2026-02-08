"""
TAIDE Model Wrapper - Mac 相容版
TAIDE-LX-7B 模型載入與推論封裝

針對 Mac 優化：
- 使用 CPU 推論（MPS 記憶體不足）
- 支援 4-bit 量化降低記憶體需求（若 bitsandbytes 可用）
- Mock 模式用於測試
- 支援從 config/model/taide.yaml 讀取設定（透過 src.config.get_configs）
"""

import os
import json
import logging
import re
from typing import Any, Dict, Optional
from pathlib import Path

from src.config import get_configs

logger = logging.getLogger(__name__)

# 全域模型實例（Singleton）
_model_instance: Optional["TAIDEModel"] = None

# 環境變數控制
USE_MOCK = os.getenv("USE_MOCK_MODEL", "false").lower() == "true"


class TAIDEModel:
    """
    TAIDE 模型封裝（Mac 相容版）
    """

    def __init__(
        self,
        model_name: str = "taide/TAIDE-LX-7B",
        local_dir: Optional[str] = None,
        device: str = "cpu",  # Mac 強制用 CPU（安全策略）
        torch_dtype: str = "float32",  # CPU 用 float32（安全策略）
        load_in_4bit: bool = True,  # 預設啟用 4-bit 量化（若可用）
        load_in_8bit: bool = False,
        use_mock: Optional[bool] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        # 1) 儲存 config（可能是空 dict）
        self._cfg: Dict[str, Any] = config or {}

        # 2) 從 taide.yaml 讀模型資訊（讀不到就用你原本參數預設）
        cfg_model = self._cfg.get("model", {}) if isinstance(self._cfg.get("model", {}), dict) else {}
        self.model_name = cfg_model.get("name") or model_name

        cfg_local_dir = cfg_model.get("local_dir")
        self.local_dir = (
            local_dir
            or cfg_local_dir
            or os.getenv("TAIDE_MODEL_PATH", "./models/TAIDE-LX-7B")
        )

        # 3) Mac 相容策略：device/dtype 先沿用原本預設（避免 CPU 上用 float16 出事）
        #    你如果未來要支援 GPU，再把這段改成「config 優先」即可。
        self.device = device
        self.torch_dtype = torch_dtype

        # 4) 量化：如果 taide.yaml 有啟用 quantization.enabled，就以它為主
        q = self._cfg.get("quantization", {}) if isinstance(self._cfg.get("quantization", {}), dict) else {}
        q_enabled = bool(q.get("enabled", False))
        q_bits = q.get("bits", 4)

        if q_enabled:
            self.load_in_4bit = (q_bits == 4)
            self.load_in_8bit = (q_bits == 8)
        else:
            self.load_in_4bit = load_in_4bit
            self.load_in_8bit = load_in_8bit

        # 5) 推論預設與任務參數（task_configs）
        self._default_inference = self._cfg.get("inference", {}) if isinstance(self._cfg.get("inference", {}), dict) else {}
        self._task_configs = self._cfg.get("task_configs", {}) if isinstance(self._cfg.get("task_configs", {}), dict) else {}

        # 6) Mock 模式判斷（維持你原本邏輯）
        if use_mock is not None:
            self._use_mock = use_mock
        else:
            self._use_mock = USE_MOCK

        self._model = None
        self._tokenizer = None
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def load(self):
        """載入模型"""
        if self._loaded:
            logger.info("模型已載入")
            return

        # Mock 模式
        if self._use_mock:
            logger.info("使用 Mock 模式（不載入真實模型）")
            self._loaded = True
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # 決定模型路徑
            model_path = self.local_dir if Path(self.local_dir).exists() else self.model_name
            logger.info(f"載入模型: {model_path}")

            # 載入 Tokenizer（trust_remote_code 可從 config 讀，但預設 true）
            load_cfg = self._cfg.get("load", {}) if isinstance(self._cfg.get("load", {}), dict) else {}
            trust_remote_code = bool(load_cfg.get("trust_remote_code", True))

            self._tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=trust_remote_code,
            )

            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            # 載入設定（保持你原本的 Mac/CPU 安全策略）
            low_cpu_mem_usage = bool(load_cfg.get("low_cpu_mem_usage", True))

            load_kwargs: Dict[str, Any] = {
                "trust_remote_code": trust_remote_code,
                "low_cpu_mem_usage": low_cpu_mem_usage,
            }

            # Mac 專用設定：CPU +（可用則量化）
            # - 如果 config 開啟 quantization 但環境沒有 bitsandbytes，也會 fallback
            if self.load_in_4bit or self.load_in_8bit:
                try:
                    from transformers import BitsAndBytesConfig

                    if self.load_in_4bit:
                        load_kwargs["quantization_config"] = BitsAndBytesConfig(
                            load_in_4bit=True,
                            bnb_4bit_compute_dtype=torch.float16,
                            bnb_4bit_use_double_quant=True,
                            bnb_4bit_quant_type="nf4",
                        )
                        logger.info("使用 4-bit 量化")
                    else:
                        load_kwargs["quantization_config"] = BitsAndBytesConfig(
                            load_in_8bit=True,
                        )
                        logger.info("使用 8-bit 量化")

                    # 量化時讓 transformers 自行決定 device map（多數情況會走 auto）
                    # Mac 上通常仍會落在 CPU，但這樣最不容易衝突。
                    load_kwargs["device_map"] = load_cfg.get("device_map", "auto") or "auto"

                except ImportError:
                    logger.warning("bitsandbytes 未安裝，改用 CPU float32 模式")
                    load_kwargs["device_map"] = {"": "cpu"}
                    load_kwargs["torch_dtype"] = torch.float32
            else:
                # 純 CPU 模式（最穩）
                load_kwargs["device_map"] = {"": "cpu"}
                load_kwargs["torch_dtype"] = torch.float32
                logger.info("使用 CPU 模式（未啟用量化）")

            # 載入模型
            self._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                **load_kwargs
            )

            self._loaded = True
            logger.info("模型載入成功")

        except Exception as e:
            logger.error(f"模型載入失敗: {e}")
            raise

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        do_sample: Optional[bool] = None,
        repetition_penalty: float = 1.1,
        **kwargs,
    ) -> str:
        """生成文本（保留你原本 API；新增 do_sample 可覆蓋）"""

        if not self._loaded:
            self.load()

        # Mock 模式：回傳假的 JSON
        if self._use_mock:
            return self._mock_generate(prompt)

        import torch

        # Tokenize
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=2048
        )

        # 移到正確的 device
        if self._model is not None:
            inputs = {k: v.to(self._model.device) for k, v in inputs.items()}

        # do_sample 決定：若未指定，沿用你原本「temperature>0 才抽樣」的邏輯
        if do_sample is None:
            do_sample = temperature > 0

        # 生成
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature if temperature > 0 else 1.0,
                top_p=top_p,
                top_k=top_k,
                do_sample=do_sample,
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
                repetition_penalty=repetition_penalty,
            )

        # 解碼（只取生成的部分）
        input_length = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][input_length:]
        response = self._tokenizer.decode(generated_tokens, skip_special_tokens=True)

        return response.strip()

    def generate_task(self, task_name: str, prompt: str, **overrides) -> str:
        """
        用 taide.yaml 的 task_configs[task_name] 套用推論參數後生成。
        - 若 task_name 不存在：退回 inference 預設，再退回 generate() 預設
        - overrides（呼叫時傳入）優先度最高
        """
        task_cfg = self._task_configs.get(task_name, {}) if isinstance(self._task_configs.get(task_name, {}), dict) else {}

        def pick(key: str, default: Any) -> Any:
            if key in overrides:
                return overrides[key]
            if key in task_cfg:
                return task_cfg[key]
            if key in self._default_inference:
                return self._default_inference[key]
            return default

        max_new_tokens = int(pick("max_new_tokens", 256))
        temperature = float(pick("temperature", 0.7))
        top_p = float(pick("top_p", 0.9))
        top_k = int(pick("top_k", 50))
        do_sample = bool(pick("do_sample", temperature > 0))
        repetition_penalty = float(pick("repetition_penalty", 1.1))

        # 重要：若 do_sample=False，temperature 仍可保留，但不抽樣（讓輸出可重現）
        return self.generate(
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            do_sample=do_sample,
            repetition_penalty=repetition_penalty,
        )

    def _mock_generate(self, prompt: str) -> str:
        """Mock 模式的假回應（保留你原本行為）"""
        amount_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)', prompt)
        amount = float(amount_match.group(1).replace(',', '')) if amount_match else 100

        is_income = any(kw in prompt for kw in ['薪水', '入帳', '收入', '獎金', '紅包'])

        mock_response = {
            "amount": amount,
            "transaction_type": "income" if is_income else "expense",
            "description": "Mock 測試交易",
            "merchant": None,
            "time_hint": None
        }

        return json.dumps(mock_response, ensure_ascii=False)

    def unload(self):
        """釋放模型記憶體（保留你原本邏輯）"""
        if self._model is not None:
            del self._model
            self._model = None
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
        self._loaded = False

        # 清理 GPU 記憶體
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except Exception:
            pass

        logger.info("模型已釋放")


def get_taide_model(use_mock: Optional[bool] = None) -> TAIDEModel:
    """
    取得 TAIDE 模型實例（Singleton）

    Args:
        use_mock: 是否使用 Mock 模式（可覆蓋環境變數 USE_MOCK_MODEL）

    Returns:
        TAIDEModel 實例
    """
    global _model_instance

    if _model_instance is None:
        taide_cfg: Dict[str, Any] = {}
        try:
            taide_cfg = get_configs()["taide"]
        except Exception as e:
            # 不讓 config 問題直接造成服務掛掉（保留原有行為：使用內建預設）
            logger.warning(f"無法載入 taide.yaml，將使用內建預設: {e}")
            taide_cfg = {}

        _model_instance = TAIDEModel(use_mock=use_mock, config=taide_cfg)

    return _model_instance


def reset_model():
    """重置模型實例"""
    global _model_instance
    if _model_instance is not None:
        _model_instance.unload()
        _model_instance = None
