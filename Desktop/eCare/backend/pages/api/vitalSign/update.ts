import type { NextApiRequest, NextApiResponse } from "next";
import { deleteVitalSign } from "@/controllers/vitalSign/deleteController";

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === "PUT") {
    return deleteVitalSign(req, res);
  }
  return res.status(405).end();
}
