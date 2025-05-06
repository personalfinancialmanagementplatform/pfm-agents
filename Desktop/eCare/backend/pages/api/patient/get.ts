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

export const getPatient = async (req: NextApiRequest, res: NextApiResponse) => {
  if (req.method !== 'GET') {
    return res.status(405).json({ success: false, message: 'Method Not Allowed' });
  }

  const { patientId } = req.query;
  
  // 檢查是否傳入 patientId
  if (!patientId) {
    return res.status(400).json({ success: false, message: '缺少 patientId 參數' });
  }

  try {
    const connection = await mysqlConnectionPool.getConnection();
    
    try {
      // 查詢病患資料
      const [patients] = await connection.execute<PatientRow[]>(
        `SELECT 
          userId, 
          name, 
          age, 
          gender, 
          addr, 
          idNum, 
          nhCardNum, 
          emerName, 
          emerPhone, 
          info, 
          isArchived, 
          lastUpd, 
          lastUpdId, 
          userId 
        FROM patient 
        WHERE patientId = ?`,
        [Number(patientId)]
      );
      
      // Check if patient exists
      if (!patients || patients.length === 0) {
        return res.status(404).json({ 
          success: false, 
          message: '病患資料未找到' 
        });
      }
      
      const patient = patients[0];
      
      // 直接回傳查詢結果，保持與 getAllPatients 一致
      return res.status(200).json({
        success: true,
        message: '取得病患資料成功',
        data: patient
      });
    } finally {
      connection.release();
    }
  } catch (err: any) {
    console.error('Get patient error:', err);
    return res.status(500).json({ 
      success: false, 
      message: `內部錯誤: ${err.message}` 
    });
  }
};

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    return getPatient(req, res);
  }
  return res.status(405).json({ success: false, message: 'Method Not Allowed' });
}