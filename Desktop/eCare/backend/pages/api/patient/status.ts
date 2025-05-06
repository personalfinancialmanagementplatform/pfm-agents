import { NextApiRequest, NextApiResponse } from 'next';
import { RowDataPacket, ResultSetHeader } from 'mysql2';
import mysqlConnectionPool from '../../../src/lib/mysql';

// Type for the patient data
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

export const managePatientStatus = async (req: NextApiRequest, res: NextApiResponse) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, message: 'Method Not Allowed' });
  }

  try {
    // Get request body
    const { patientId, userId, isArchived } = req.body;
    
    // 檢查必要欄位
    if (!patientId || !userId || isArchived === undefined) {
      return res.status(400).json({ success: false, message: '缺少必要欄位' });
    }
    
    const connection = await mysqlConnectionPool.getConnection();
    
    try {
      // 當 isArchived = true，標記資料為封存
      if (isArchived) {
        const [result] = await connection.execute<ResultSetHeader>(
          `UPDATE patient SET 
            isArchived = ?, 
            lastUpd = ?, 
            lastUpdId = ? 
            WHERE id = ?`,
          [true, new Date().toISOString(), userId, patientId]
        );
        
        // Check if any rows were affected
        if (result.affectedRows === 0) {
          return res.status(404).json({ success: false, message: '病歷不存在' });
        }
        
        // Get the updated patient data
        const [patients] = await connection.execute<PatientRow[]>(
          'SELECT * FROM patient WHERE id = ?',
          [patientId]
        );
        
        const updatedPatient = patients.length > 0 ? patients[0] : null;
        
        return res.status(200).json({ 
          success: true, 
          message: '病歷已封存', 
          data: updatedPatient 
        });
      }
      
      // 當 isArchived = false，直接刪除病歷
      const [result] = await connection.execute<ResultSetHeader>(
      'DELETE FROM patient WHERE patientId = ?',
      [patientId]
     );
      
      // Check if any rows were affected
      if (result.affectedRows === 0) {
        return res.status(404).json({ success: false, message: '病歷不存在' });
      }
      
      return res.status(200).json({
        success: true,
        message: '病歷已刪除',
        data: null
      });
    } finally {
      connection.release();
    }
  } catch (err: any) {
    console.error('Manage patient status error:', err);
    
    return res.status(500).json({
      success: false,
      message: `內部錯誤: ${err.message}`,
      data: null
    });
  }
};

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    return managePatientStatus(req, res);
  }
  return res.status(405).json({ success: false, message: 'Method Not Allowed' });
}