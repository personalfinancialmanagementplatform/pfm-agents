import type { NextApiRequest, NextApiResponse } from "next";
import { getAllVitalSigns } from "@/controllers/vitalSign/getAllController";

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === "GET") {
    return getAllVitalSigns(req, res);
  }
  return res.status(405).end();
}
