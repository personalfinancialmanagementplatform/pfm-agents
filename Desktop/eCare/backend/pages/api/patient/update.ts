import type { NextApiRequest, NextApiResponse } from 'next';
import { RowDataPacket, ResultSetHeader } from 'mysql2';
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

export const updatePatient = async (req: NextApiRequest, res: NextApiResponse) => {
  if (req.method !== 'PUT') {
    return res.status(405).json({ success: false, message: 'Method Not Allowed' });
  }

  try {
    // Get request body
    const {
      patientId,
      userId,
      name,
      age,
      gender,
      addr,
      emerName,
      emerPhone,
      info
    } = req.body;
    
    // 檢查必要欄位 - 只檢查 patientId 和 userId 
    if (!patientId || !userId) {
      return res.status(400).json({ success: false, message: '缺少必要欄位' });
    }
    
    const connection = await mysqlConnectionPool.getConnection();
    
    try {
      // 先取得目前病患資料
      const [patients] = await connection.execute<PatientRow[]>(
        'SELECT * FROM patient WHERE patientId = ?',
        [Number(patientId)]
      );
      
      if (patients.length === 0) {
        return res.status(404).json({ success: false, message: '找不到病患資料' });
      }
      
      const currentPatient = patients[0];
      
      // 更新病患資料，若沒有提供則使用原有的值
      const [result] = await connection.execute<ResultSetHeader>(
        `UPDATE patient SET
           userId = ?,
           name = ?,
           age = ?,
           gender = ?,
           addr = ?,
           emerName = ?,
           emerPhone = ?,
           info = ?,
           lastUpd = NOW(),
           lastUpdId = ?
           WHERE patientId = ?`,
         [
         Number(userId),
         name || currentPatient.name,
         age ? parseInt(age) : currentPatient.age,
         gender || currentPatient.gender,
         addr || currentPatient.addr,
         emerName || currentPatient.emerName,
         emerPhone || currentPatient.emerPhone,
         info !== undefined ? info : currentPatient.info,
         Number(userId),
         Number(patientId)
         ]
      );
      
      // Check if update was successful
      if (result.affectedRows === 0) {
        return res.status(500).json({ success: false, message: '更新失敗' });
      }
      
      // Fetch the updated patient data
      const [updatedPatients] = await connection.execute<PatientRow[]>(
        `SELECT 
          patientId,
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
          lastUpd,
          lastUpdId
        FROM patient
        WHERE patientId = ?`,
        [Number(patientId)]
      );
      
      const updatedPatient = updatedPatients[0];
      
      return res.status(200).json({
        success: true,
        data: updatedPatient
      });
    } finally {
      connection.release();
    }
  } catch (err: any) {
    console.error('Update patient error:', err);
    
    return res.status(500).json({
      success: false,
      message: `內部錯誤: ${err.message}`
    });
  }
};

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'PUT') {
    return updatePatient(req, res);
  }
  return res.status(405).json({ success: false, message: 'Method Not Allowed' });
}