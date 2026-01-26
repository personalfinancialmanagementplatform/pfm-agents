"""
TAIDE 模型封裝
"""
import os
import logging
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

class TAIDEModel:
    """TAIDE-LX-7B 模型封裝"""
    
    def __init__(
        self,
        model_path: str = "taide/TAIDE-LX-7B",
        device: str = "cuda",
        max_new_tokens: int = 512,
    ):
        self.model_path = model_path
        self.device = device
        self.max_new_tokens = max_new_tokens
        self.tokenizer = None
        self.model = None
        self._is_loaded = False
    
    def load(self) -> None:
        """載入模型"""
        if self._is_loaded:
            return
        
        logger.info(f"Loading TAIDE model from {self.model_path}...")
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                device_map="auto",
                trust_remote_code=True,
            )
            
            self._is_loaded = True
            logger.info("TAIDE model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load TAIDE model: {e}")
            raise
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """生成回應"""
        if not self._is_loaded:
            self.load()
        
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        else:
            full_prompt = f"User: {prompt}\n\nAssistant:"
        
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens or self.max_new_tokens,
            temperature=temperature,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response.split("Assistant:")[-1].strip()
        
        return response


_model_instance: Optional[TAIDEModel] = None

def get_taide_model() -> TAIDEModel:
    """取得 TAIDE 模型單例"""
    global _model_instance
    
    if _model_instance is None:
        _model_instance = TAIDEModel(
            model_path=os.getenv("TAIDE_MODEL_PATH", "taide/TAIDE-LX-7B"),
            device=os.getenv("TAIDE_DEVICE", "cuda"),
            max_new_tokens=int(os.getenv("TAIDE_MAX_NEW_TOKENS", "512")),
        )
    
    return _model_instance
