"""
TAIDE Model Wrapper - Mac 相容版
TAIDE-LX-7B 模型載入與推論封裝

針對 Mac 優化：
- 使用 CPU 推論（MPS 記憶體不足）
- 支援 4-bit 量化降低記憶體需求
- Mock 模式用於測試
"""

import os
import json
import logging
import re
from typing import Any, Dict, List, Optional
from pathlib import Path

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
        device: str = "cpu",  # Mac 強制用 CPU
        torch_dtype: str = "float32",  # CPU 用 float32
        load_in_4bit: bool = True,  # 預設啟用 4-bit 量化
        load_in_8bit: bool = False,
        use_mock: Optional[bool] = None,
    ):
        self.model_name = model_name
        self.local_dir = local_dir or os.getenv("TAIDE_MODEL_PATH", "./models/TAIDE-LX-7B")
        self.device = device
        self.torch_dtype = torch_dtype
        self.load_in_4bit = load_in_4bit
        self.load_in_8bit = load_in_8bit
        
        # Mock 模式判斷
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
            
            # 載入 Tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token
            
            # 載入設定
            load_kwargs = {
                "trust_remote_code": True,
                "low_cpu_mem_usage": True,
            }
            
            # Mac 專用設定：使用 CPU + 量化
            if self.load_in_4bit:
                try:
                    from transformers import BitsAndBytesConfig
                    load_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4"
                    )
                    load_kwargs["device_map"] = "auto"
                    logger.info("使用 4-bit 量化")
                except ImportError:
                    logger.warning("bitsandbytes 未安裝，改用 CPU 模式")
                    load_kwargs["device_map"] = {"": "cpu"}
                    load_kwargs["torch_dtype"] = torch.float32
            else:
                # 純 CPU 模式
                load_kwargs["device_map"] = {"": "cpu"}
                load_kwargs["torch_dtype"] = torch.float32
                logger.info("使用 CPU 模式")
            
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
        **kwargs
    ) -> str:
        """生成文本"""
        
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
        
        # 生成
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature if temperature > 0 else 1.0,
                top_p=top_p,
                top_k=top_k,
                do_sample=temperature > 0,
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
                repetition_penalty=1.1,
            )
        
        # 解碼（只取生成的部分）
        input_length = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][input_length:]
        response = self._tokenizer.decode(generated_tokens, skip_special_tokens=True)
        
        return response.strip()
    
    def _mock_generate(self, prompt: str) -> str:
        """Mock 模式的假回應"""
        # 嘗試從 prompt 解析金額
        amount_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)', prompt)
        amount = float(amount_match.group(1).replace(',', '')) if amount_match else 100
        
        # 判斷收入或支出
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
        """釋放模型記憶體"""
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
        except:
            pass
        
        logger.info("模型已釋放")


def get_taide_model(use_mock: Optional[bool] = None) -> TAIDEModel:
    """
    取得 TAIDE 模型實例（Singleton）
    
    Args:
        use_mock: 是否使用 Mock 模式
        
    Returns:
        TAIDEModel 實例
    """
    global _model_instance
    
    if _model_instance is None:
        _model_instance = TAIDEModel(use_mock=use_mock)
    
    return _model_instance


def reset_model():
    """重置模型實例"""
    global _model_instance
    if _model_instance is not None:
        _model_instance.unload()
        _model_instance = None