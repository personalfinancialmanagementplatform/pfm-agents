"""
TAIDE Model Wrapper
TAIDE-LX-7B 模型載入與推論封裝
"""

import os
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# 全域模型實例（Singleton）
_model_instance: Optional["TAIDEModel"] = None


class TAIDEModel:
    """
    TAIDE 模型封裝
    
    提供統一的介面來載入和使用 TAIDE-LX-7B 模型。
    支援本地載入和 Hugging Face 載入兩種方式。
    
    使用範例：
        model = TAIDEModel()
        model.load()
        response = model.generate("今天午餐吃什麼？")
    """
    
    def __init__(
        self,
        model_name: str = "taide/TAIDE-LX-7B",
        local_dir: Optional[str] = None,
        device_map: str = "auto",
        torch_dtype: str = "float16",
        load_in_4bit: bool = False,
        load_in_8bit: bool = False,
    ):
        """
        初始化 TAIDE 模型
        
        Args:
            model_name: Hugging Face 模型名稱
            local_dir: 本地模型路徑（優先使用）
            device_map: 裝置映射策略
            torch_dtype: 張量資料類型
            load_in_4bit: 是否使用 4-bit 量化
            load_in_8bit: 是否使用 8-bit 量化
        """
        self.model_name = model_name
        self.local_dir = local_dir or os.getenv("TAIDE_MODEL_PATH", "./models/TAIDE-LX-7B")
        self.device_map = device_map
        self.torch_dtype = torch_dtype
        self.load_in_4bit = load_in_4bit
        self.load_in_8bit = load_in_8bit
        
        self._model = None
        self._tokenizer = None
        self._loaded = False
    
    @property
    def is_loaded(self) -> bool:
        """模型是否已載入"""
        return self._loaded
    
    def load(self) -> None:
        """
        載入模型
        
        優先從本地路徑載入，若不存在則從 Hugging Face 下載。
        """
        if self._loaded:
            logger.info("模型已載入，跳過")
            return
        
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            # 決定載入來源
            model_path = self._get_model_path()
            logger.info(f"正在載入模型: {model_path}")
            
            # 設定 dtype
            dtype = self._get_torch_dtype()
            
            # 載入 tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
            )
            
            # 設定量化配置
            quantization_config = self._get_quantization_config()
            
            # 載入模型
            load_kwargs = {
                "device_map": self.device_map,
                "torch_dtype": dtype,
                "trust_remote_code": True,
                "low_cpu_mem_usage": True,
            }
            
            if quantization_config:
                load_kwargs["quantization_config"] = quantization_config
            
            self._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                **load_kwargs
            )
            
            self._loaded = True
            logger.info("模型載入完成")
            
        except ImportError as e:
            logger.error(f"缺少必要套件: {e}")
            logger.error("請執行: pip install torch transformers")
            raise
        except Exception as e:
            logger.error(f"模型載入失敗: {e}")
            raise
    
    def _get_model_path(self) -> str:
        """取得模型路徑"""
        local_path = Path(self.local_dir)
        if local_path.exists() and (local_path / "config.json").exists():
            logger.info(f"使用本地模型: {local_path}")
            return str(local_path)
        else:
            logger.info(f"本地模型不存在，將從 Hugging Face 載入: {self.model_name}")
            return self.model_name
    
    def _get_torch_dtype(self):
        """取得 torch dtype"""
        import torch
        
        dtype_map = {
            "float16": torch.float16,
            "float32": torch.float32,
            "bfloat16": torch.bfloat16,
            "auto": "auto",
        }
        return dtype_map.get(self.torch_dtype, torch.float16)
    
    def _get_quantization_config(self):
        """取得量化配置"""
        if not self.load_in_4bit and not self.load_in_8bit:
            return None
        
        try:
            from transformers import BitsAndBytesConfig
            
            if self.load_in_4bit:
                return BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=self._get_torch_dtype(),
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
            elif self.load_in_8bit:
                return BitsAndBytesConfig(load_in_8bit=True)
                
        except ImportError:
            logger.warning("bitsandbytes 未安裝，跳過量化")
            return None
        
        return None
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
        do_sample: bool = True,
        **kwargs
    ) -> str:
        """
        生成回應
        
        Args:
            prompt: 輸入提示
            max_new_tokens: 最大生成 token 數
            temperature: 溫度（越高越隨機）
            top_p: nucleus sampling 參數
            top_k: top-k sampling 參數
            repetition_penalty: 重複懲罰
            do_sample: 是否使用採樣
            
        Returns:
            生成的文字
        """
        if not self._loaded:
            self.load()
        
        # Tokenize
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
        )
        inputs = {k: v.to(self._model.device) for k, v in inputs.items()}
        
        # Generate
        with __import__("torch").no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature if do_sample else 1.0,
                top_p=top_p if do_sample else 1.0,
                top_k=top_k if do_sample else 0,
                repetition_penalty=repetition_penalty,
                do_sample=do_sample,
                pad_token_id=self._tokenizer.eos_token_id,
                **kwargs
            )
        
        # Decode（只取新生成的部分）
        input_length = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][input_length:]
        response = self._tokenizer.decode(generated_tokens, skip_special_tokens=True)
        
        return response.strip()
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        對話模式生成
        
        Args:
            messages: 對話歷史 [{"role": "user", "content": "..."}, ...]
            system_prompt: 系統提示
            
        Returns:
            生成的回應
        """
        # 組合 prompt
        prompt_parts = []
        
        if system_prompt:
            prompt_parts.append(f"[系統] {system_prompt}\n")
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                prompt_parts.append(f"[使用者] {content}")
            elif role == "assistant":
                prompt_parts.append(f"[助理] {content}")
        
        prompt_parts.append("[助理] ")
        prompt = "\n".join(prompt_parts)
        
        return self.generate(prompt, **kwargs)
    
    def unload(self) -> None:
        """卸載模型釋放記憶體"""
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
        except ImportError:
            pass
        
        logger.info("模型已卸載")


# ============================================================================
# Singleton 存取函式
# ============================================================================

def get_taide_model(
    force_reload: bool = False,
    **kwargs
) -> TAIDEModel:
    """
    取得 TAIDE 模型實例（Singleton）
    
    Args:
        force_reload: 是否強制重新載入
        **kwargs: 傳遞給 TAIDEModel 的參數
        
    Returns:
        TAIDEModel 實例
    """
    global _model_instance
    
    if _model_instance is None or force_reload:
        if _model_instance is not None:
            _model_instance.unload()
        
        _model_instance = TAIDEModel(**kwargs)
    
    return _model_instance


def unload_model() -> None:
    """卸載全域模型實例"""
    global _model_instance
    
    if _model_instance is not None:
        _model_instance.unload()
        _model_instance = None


# ============================================================================
# 匯出
# ============================================================================

__all__ = [
    "TAIDEModel",
    "get_taide_model",
    "unload_model",
]