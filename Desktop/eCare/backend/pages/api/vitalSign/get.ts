import type { NextApiRequest, NextApiResponse } from "next";
import { getVitalSign } from "@/controllers/vitalSign/getController";

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === "GET") {
    return getVitalSign(req, res);
  }
  return res.status(405).end();
}
