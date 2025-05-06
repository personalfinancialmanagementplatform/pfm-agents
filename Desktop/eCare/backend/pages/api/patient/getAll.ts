
import type { NextApiRequest, NextApiResponse } from 'next';
import { RowDataPacket } from 'mysql2';
import mysqlConnectionPool from '../../../src/lib/mysql';

interface PatientRow extends RowDataPacket {
  id: number;
  name: string;
  age: number;
  gender: string;
  addr: string;
  idNum: string;
  nhCardNum: string;
  emerName: string;
  emerPhone: string;
  info: string;
  isArchived: boolean;
  lastUpd: string;
  lastUpdId: number;
  userId: number;
}

export const getAllPatients = async (req: NextApiRequest, res: NextApiResponse) => {
  if (req.method !== 'GET') {
    return res.status(405).json({ success: false, message: 'Method Not Allowed' });
  }

  const { userId } = req.query;
  
  // 檢查是否傳入 userId
  if (!userId) {
    return res.status(400).json({ success: false, message: '缺少 userId 參數' });
  }

  try {
    const connection = await mysqlConnectionPool.getConnection();
    
    try {
      // 查詢病患資料
      const [patients] = await connection.execute<PatientRow[]>(
        'SELECT * FROM patient WHERE userId = ? ORDER BY lastUpd DESC',
        [Number(userId)]
      );
      
      // If no patients found
      if (patients.length === 0) {
        return res.status(404).json({ 
          success: false, 
          message: '沒有找到病患資料' 
        });
      }
      
      // 回傳查詢結果
      return res.status(200).json({
        success: true,
        data: patients
      });
    } finally {
      connection.release();
    }
  } catch (err: unknown) {
    console.error('Get all patients error:', err);
    return res.status(500).json({ 
      success: false, 
      message: err instanceof Error ? err.message : String(err)
    });
  }
};

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    return getAllPatients(req, res);
  }
  return res.status(405).json({ success: false, message: 'Method Not Allowed' });
}