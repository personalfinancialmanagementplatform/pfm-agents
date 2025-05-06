import type { NextApiRequest, NextApiResponse } from 'next'
import { login } from '@/controllers/loginController'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') return login(req, res)
  return res.status(405).end()
}
