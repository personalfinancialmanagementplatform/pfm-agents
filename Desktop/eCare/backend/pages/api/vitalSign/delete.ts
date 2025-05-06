import type { NextApiRequest, NextApiResponse } from "next";
import { updateVitalSign } from "@/controllers/vitalSign/updateController";

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === "PUT") {
    return updateVitalSign(req, res);
  }
  return res.status(405).end();
}
