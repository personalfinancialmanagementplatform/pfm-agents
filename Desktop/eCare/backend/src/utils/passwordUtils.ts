// src/utils/passwordUtils.ts

export function validatePassword(password: string): { success: boolean; message?: string } {
    // 範例規則：至少 8 碼、含英文字母與數字
    const minLength = 8;
    const hasLetter = /[a-zA-Z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
  
    if (password.length < minLength) {
      return { success: false, message: '密碼長度需至少 8 碼' };
    }
    if (!hasLetter || !hasNumber) {
      return { success: false, message: '密碼需包含英文字母與數字' };
    }
  
    return { success: true };
  }
  