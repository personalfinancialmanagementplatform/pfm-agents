import type { NextApiRequest, NextApiResponse } from 'next'
import { logout } from '@/controllers/logoutController'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') return logout(req, res)
  return res.status(405).end()
}
