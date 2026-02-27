#!/usr/bin/env python3
"""
TAIDE-LX-7B 模型下載腳本
個人理財管理平台 (PFM) - Agent 系統

使用方式：
    python scripts/download_model.py                    # 使用預設設定
    python scripts/download_model.py --quantize 4bit   # 下載並準備 4-bit 量化
    python scripts/download_model.py --check-only      # 只檢查模型是否存在
    python scripts/download_model.py --verify          # 驗證已下載的模型

"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==============================================
# 配置
# ==============================================

MODEL_ID = "taide/TAIDE-LX-7B"
DEFAULT_LOCAL_DIR = "./models/TAIDE-LX-7B"
CONFIG_PATH = "./config/model/taide.yaml"

# 模型檔案清單（用於驗證）
EXPECTED_FILES = [
    "config.json",
    "generation_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    # safetensors 或 pytorch 模型檔
]


# ==============================================
# 輔助函數
# ==============================================

def get_hf_token() -> Optional[str]:
    """取得 HuggingFace Token"""
    # 優先順序：環境變數 > .env 檔案 > huggingface-cli 登入
    
    # 1. 環境變數
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        logger.info("使用環境變數中的 HF_TOKEN")
        return token
    
    # 2. .env 檔案
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("HF_TOKEN="):
                    token = line.strip().split("=", 1)[1].strip('"\'')
                    if token:
                        logger.info("使用 .env 檔案中的 HF_TOKEN")
                        return token
    
    # 3. huggingface-cli 登入的 token
    try:
        from huggingface_hub import HfFolder
        token = HfFolder.get_token()
        if token:
            logger.info("使用 huggingface-cli 登入的 token")
            return token
    except ImportError:
        pass
    
    return None


def check_model_exists(local_dir: str) -> bool:
    """檢查模型是否已下載"""
    local_path = Path(local_dir)
    
    if not local_path.exists():
        return False
    
    # 檢查必要檔案
    config_file = local_path / "config.json"
    if not config_file.exists():
        return False
    
    # 檢查模型權重檔（safetensors 或 pytorch）
    has_weights = (
        any(local_path.glob("*.safetensors")) or
        any(local_path.glob("pytorch_model*.bin")) or
        any(local_path.glob("model*.safetensors"))
    )
    
    return has_weights


def get_model_size(local_dir: str) -> str:
    """計算已下載模型的大小"""
    total_size = 0
    local_path = Path(local_dir)
    
    if local_path.exists():
        for file in local_path.rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size
    
    # 轉換為可讀格式
    if total_size >= 1024 ** 3:
        return f"{total_size / (1024 ** 3):.2f} GB"
    elif total_size >= 1024 ** 2:
        return f"{total_size / (1024 ** 2):.2f} MB"
    else:
        return f"{total_size / 1024:.2f} KB"


# ==============================================
# 主要功能
# ==============================================

def download_model(
    local_dir: str = DEFAULT_LOCAL_DIR,
    token: Optional[str] = None,
    resume: bool = True
) -> bool:
    """
    下載 TAIDE-LX-7B 模型
    
    Args:
        local_dir: 本地儲存路徑
        token: HuggingFace token（可選，會自動偵測）
        resume: 是否支援斷點續傳
    
    Returns:
        bool: 是否成功
    """
    try:
        from huggingface_hub import snapshot_download, HfApi
    except ImportError:
        logger.error("請先安裝 huggingface_hub: pip install huggingface_hub")
        return False
    
    # 取得 token
    if token is None:
        token = get_hf_token()
    
    if token is None:
        logger.warning("=" * 60)
        logger.warning("未找到 HuggingFace Token！")
        logger.warning("TAIDE-LX-7B 是 Gated Model，需要 token 才能下載。")
        logger.warning("")
        logger.warning("請依照以下步驟操作：")
        logger.warning("1. 前往 https://huggingface.co/taide/TAIDE-LX-7B")
        logger.warning("2. 點擊 'Access repository' 並同意使用條款")
        logger.warning("3. 設定 token（三選一）：")
        logger.warning("   a. 環境變數: export HF_TOKEN=your_token")
        logger.warning("   b. .env 檔案: HF_TOKEN=your_token")
        logger.warning("   c. 執行: huggingface-cli login")
        logger.warning("=" * 60)
        return False
    
    # 檢查存取權限
    logger.info(f"檢查模型存取權限: {MODEL_ID}")
    try:
        api = HfApi()
        api.model_info(MODEL_ID, token=token)
        logger.info("✓ 已獲得模型存取權限")
    except Exception as e:
        if "401" in str(e) or "403" in str(e):
            logger.error("✗ 無法存取模型，請確認：")
            logger.error("  1. Token 是否正確")
            logger.error("  2. 是否已在 HuggingFace 上申請存取權限")
            logger.error(f"  申請連結: https://huggingface.co/{MODEL_ID}")
        else:
            logger.error(f"✗ 檢查存取權限時發生錯誤: {e}")
        return False
    
    # 建立目錄
    Path(local_dir).mkdir(parents=True, exist_ok=True)
    
    # 下載模型
    logger.info(f"開始下載模型到: {local_dir}")
    logger.info("這可能需要一些時間，請耐心等待...")
    logger.info("（模型大小約 14GB）")
    
    try:
        snapshot_download(
            repo_id=MODEL_ID,
            local_dir=local_dir,
            token=token,
            resume_download=resume,
            local_dir_use_symlinks=False,  # 不使用符號連結，直接複製檔案
        )
        logger.info("✓ 模型下載完成！")
        logger.info(f"  位置: {Path(local_dir).absolute()}")
        logger.info(f"  大小: {get_model_size(local_dir)}")
        return True
        
    except KeyboardInterrupt:
        logger.warning("\n下載已中斷。下次執行會自動續傳。")
        return False
    except Exception as e:
        logger.error(f"✗ 下載失敗: {e}")
        return False


def verify_model(local_dir: str = DEFAULT_LOCAL_DIR) -> bool:
    """
    驗證已下載的模型
    
    Args:
        local_dir: 模型路徑
    
    Returns:
        bool: 是否有效
    """
    logger.info(f"驗證模型: {local_dir}")
    
    if not check_model_exists(local_dir):
        logger.error("✗ 模型不存在或不完整")
        return False
    
    local_path = Path(local_dir)
    
    # 檢查必要檔案
    missing_files = []
    for filename in EXPECTED_FILES:
        if not (local_path / filename).exists():
            missing_files.append(filename)
    
    if missing_files:
        logger.warning(f"缺少檔案: {missing_files}")
    
    # 嘗試載入 tokenizer
    logger.info("測試載入 tokenizer...")
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(local_dir, trust_remote_code=True)
        logger.info("✓ Tokenizer 載入成功")
        
        # 測試 tokenize
        test_text = "測試記帳：午餐吃便當 80 元"
        tokens = tokenizer.encode(test_text)
        logger.info(f"  測試文字: {test_text}")
        logger.info(f"  Token 數: {len(tokens)}")
        
    except Exception as e:
        logger.error(f"✗ Tokenizer 載入失敗: {e}")
        return False
    
    # 檢查模型大小
    model_size = get_model_size(local_dir)
    logger.info(f"模型大小: {model_size}")
    
    logger.info("✓ 模型驗證通過！")
    return True


def test_inference(
    local_dir: str = DEFAULT_LOCAL_DIR,
    quantize: Optional[str] = None
) -> bool:
    """
    測試模型推論
    
    Args:
        local_dir: 模型路徑
        quantize: 量化方式 ("4bit" | "8bit" | None)
    
    Returns:
        bool: 是否成功
    """
    logger.info("測試模型推論...")
    
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        logger.error("請先安裝必要套件: pip install torch transformers")
        return False
    
    # 載入設定
    load_kwargs = {
        "trust_remote_code": True,
        "device_map": "auto",
    }
    
    # 量化設定
    if quantize == "4bit":
        try:
            from transformers import BitsAndBytesConfig
            load_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            logger.info("使用 4-bit 量化")
        except ImportError:
            logger.error("4-bit 量化需要安裝 bitsandbytes: pip install bitsandbytes")
            return False
    elif quantize == "8bit":
        try:
            from transformers import BitsAndBytesConfig
            load_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_8bit=True,
            )
            logger.info("使用 8-bit 量化")
        except ImportError:
            logger.error("8-bit 量化需要安裝 bitsandbytes: pip install bitsandbytes")
            return False
    else:
        load_kwargs["torch_dtype"] = torch.float16
        logger.info("使用 float16 精度")
    
    # 載入模型
    logger.info("載入模型中...（這可能需要幾分鐘）")
    try:
        tokenizer = AutoTokenizer.from_pretrained(local_dir, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(local_dir, **load_kwargs)
        logger.info("✓ 模型載入成功")
    except Exception as e:
        logger.error(f"✗ 模型載入失敗: {e}")
        return False
    
    # 測試推論
    test_prompts = [
        "請將「午餐吃便當 80 元」轉換為 JSON 格式的交易記錄：",
        "分析以下消費屬於哪個類別：「搭捷運去上班」",
    ]
    
    logger.info("\n" + "=" * 60)
    logger.info("推論測試")
    logger.info("=" * 60)
    
    for prompt in test_prompts:
        logger.info(f"\n輸入: {prompt}")
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=128,
                temperature=0.3,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response[len(prompt):].strip()
        
        logger.info(f"輸出: {response[:200]}...")
    
    logger.info("\n✓ 推論測試完成！")
    return True


# ==============================================
# CLI
# ==============================================

def main():
    parser = argparse.ArgumentParser(
        description="TAIDE-LX-7B 模型下載與管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
    # 下載模型
    python scripts/download_model.py
    
    # 指定下載路徑
    python scripts/download_model.py --local-dir /path/to/models/TAIDE
    
    # 只檢查模型是否存在
    python scripts/download_model.py --check-only
    
    # 驗證已下載的模型
    python scripts/download_model.py --verify
    
    # 測試推論（使用 4-bit 量化）
    python scripts/download_model.py --test --quantize 4bit

注意：
    TAIDE-LX-7B 是 Gated Model，需要先到 HuggingFace 申請存取權限：
    https://huggingface.co/taide/TAIDE-LX-7B
        """
    )
    
    parser.add_argument(
        "--local-dir",
        type=str,
        default=DEFAULT_LOCAL_DIR,
        help=f"模型儲存路徑（預設: {DEFAULT_LOCAL_DIR}）"
    )
    
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="HuggingFace token（可選，會自動從環境變數或 .env 讀取）"
    )
    
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="只檢查模型是否存在，不下載"
    )
    
    parser.add_argument(
        "--verify",
        action="store_true",
        help="驗證已下載的模型"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="測試模型推論"
    )
    
    parser.add_argument(
        "--quantize",
        type=str,
        choices=["4bit", "8bit"],
        default=None,
        help="推論測試時使用的量化方式"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="強制重新下載（即使已存在）"
    )
    
    args = parser.parse_args()
    
    # 檢查模式
    if args.check_only:
        exists = check_model_exists(args.local_dir)
        if exists:
            logger.info(f"✓ 模型已存在: {args.local_dir}")
            logger.info(f"  大小: {get_model_size(args.local_dir)}")
            sys.exit(0)
        else:
            logger.info(f"✗ 模型不存在: {args.local_dir}")
            sys.exit(1)
    
    # 驗證模式
    if args.verify:
        success = verify_model(args.local_dir)
        sys.exit(0 if success else 1)
    
    # 測試推論模式
    if args.test:
        if not check_model_exists(args.local_dir):
            logger.error(f"模型不存在，請先下載: {args.local_dir}")
            sys.exit(1)
        success = test_inference(args.local_dir, args.quantize)
        sys.exit(0 if success else 1)
    
    # 下載模式（預設）
    if check_model_exists(args.local_dir) and not args.force:
        logger.info(f"模型已存在: {args.local_dir}")
        logger.info(f"大小: {get_model_size(args.local_dir)}")
        logger.info("如需重新下載，請使用 --force 參數")
        
        # 詢問是否驗證
        verify_model(args.local_dir)
        sys.exit(0)
    
    # 執行下載
    success = download_model(
        local_dir=args.local_dir,
        token=args.token,
        resume=not args.force
    )
    
    if success:
        verify_model(args.local_dir)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()