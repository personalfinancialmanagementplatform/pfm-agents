'use client'

import { useState } from 'react'
import LoginRegisterCard from '../../../components/LoginRegisterCard'
import Button from '../../../components/Button'
import Link from 'next/link';


//import Button from 'app/components/Button'

export default function LoginPage() {
  //const [email, setEmail] = useState('')
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('email:', username)
    console.log('password:', password)
    // 在這裡呼叫 API
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#d6f5f0] px-4">
    <LoginRegisterCard
      title="登入帳號"
      subtitle="請輸入帳號與密碼"
      footer={<p>還沒帳號？
        <Link href="/user/signup" className="text-blue-500 hover:underline">註冊</Link>
      </p>}
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
        <Button label="登入" onClick={() => {}} className="w-full" />
      </form>
    </LoginRegisterCard>
  </div>
  )
}
