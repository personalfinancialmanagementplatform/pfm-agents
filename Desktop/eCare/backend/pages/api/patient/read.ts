// For Next.js
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

export const getPatientData = async (req: NextApiRequest, res: NextApiResponse) => {
  if (req.method !== 'GET') {
    return res.status(405).json({ success: false, message: 'Method Not Allowed' });
  }

  const { patientId, userId } = req.query;
  
  // 檢查是否傳入必要參數
  if (!patientId || !userId) {
    return res.status(400).json({ success: false, message: '缺少必要參數' });
  }

  try {
    const connection = await mysqlConnectionPool.getConnection();
    
    try {
      // 查詢病患資料
      const [patients] = await connection.execute<PatientRow[]>(
        `SELECT * FROM patient 
         WHERE patientId = ? AND userId = ?`,
        [Number(patientId), Number(userId)]
      );
      
      // Check if patient exists
      if (patients.length === 0) {
        return res.status(404).json({ 
          success: false, 
          message: '病患資料未找到' 
        });
      }
      
      const patient = patients[0];
      
      // Map database fields to response object
      const patientData = { 
        id: patient.id,
        name: patient.name,
        age: patient.age,
        gender: patient.gender,
        addr: patient.addr,
        idNum: patient.idNum, 
        nhCardNum: patient.nhCardNum, 
        emerName: patient.emerName, 
        emerPhone: patient.emerPhone, 
        info: patient.info,
        isArchived: patient.isArchived,
        lastUpd: patient.lastUpd
      };
      
      // 若成功 回傳以上病患資料
      return res.status(200).json({
        success: true,
        data: patientData
      });
    } finally {
      connection.release();
    }
  } catch (err: unknown) {
    console.error('Get patient data error:', err);
    return res.status(500).json({ 
      success: false, 
      message: err instanceof Error ? err.message : String(err)
    });
  }
};

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    return getPatientData(req, res);
  }
  return res.status(405).json({ success: false, message: 'Method Not Allowed' });
}