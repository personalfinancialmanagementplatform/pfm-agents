import type { NextApiRequest, NextApiResponse } from "next";
import { createVitalSign } from "@/controllers/vitalSign/createController";

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === "POST") {
    return createVitalSign(req, res);
  }
  return res.status(405).end();
}
