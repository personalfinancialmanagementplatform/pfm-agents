'use client'

import { useState } from 'react';
import LoginRegisterCard from '../../../components/LoginRegisterCard'
import Link from 'next/link'; // 引入 Link
import Button from '../../../components/Button';

export default function SignupPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // 這裡可以寫送出資料到後端的邏輯
    console.log('註冊資訊', { username, password, email });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#d6f5f0] px-4">
      <LoginRegisterCard
        title="註冊新帳號"
        subtitle="請輸入帳號、密碼與電子郵件"
        footer={
          <p>
            已有帳號？
            <Link href="/user/login" className="text-blue-500 hover:underline">
              返回登入
            </Link>
          </p>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="使用者帳號"
            className="w-full border border-gray-300 px-4 py-2 rounded text-gray-700 placeholder-gray-500"
            required
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="密碼"
            className="w-full border border-gray-300 px-4 py-2 rounded text-gray-700 placeholder-gray-500"
            required
          />
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="電子郵件"
            className="w-full border border-gray-300 px-4 py-2 rounded text-gray-700 placeholder-gray-500"
            required
          />
          <Button label="註冊" onClick={() => {}} className="w-full" />
        </form>
      </LoginRegisterCard>
    </div>
  );
}
