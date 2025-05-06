import type { NextApiRequest, NextApiResponse } from 'next'
import { signUp } from '@/controllers/signupController'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') return signUp(req, res)
  return res.status(405).end()
}
