import { NextApiRequest, NextApiResponse} from 'next';
import PatientData from 'mysql2';
import mysqlConnectionPool from '../../../src/lib/mysql';

// Create a connection pool
// const pool = mysql.createPool({
//   host: process.env.DB_HOST || 'localhost',
//   user: process.env.DB_USER || 'root',
//   password: process.env.DB_PASSWORD || 'password',
//   database: process.env.DB_NAME || 'health_db',
// });

export default async function POST(req: NextApiRequest, res: NextApiResponse) {
  try {
    // Parse the request body
    //const body = await req.json();
    const { patientId, userId, isArchived } = req.body;
    
    // 檢查必要欄位
    if (!patientId || !userId || isArchived === undefined) {
      return res.status(400).json(
        { success: false, err: '缺少必要欄位' },
        
      );
    }
    
    // 當 isArchived = true，標記資料為封存
    if (isArchived) {
      const [result] = await mysqlConnectionPool.execute(
        `UPDATE patients SET 
          isArchived = ?, 
          lastUpd = ?, 
          lastUpdId = ? 
          WHERE id = ?`,
        [true, new Date().toISOString(), userId, patientId]
      );
      
      // Check if any rows were affected
      if ((result as any).affectedRows === 0) {
        return res.status(404).json(
          { success: false, err: '病歷不存在' },
        );
      }
      
      // Get the updated patient data
      const [patients] = await mysqlConnectionPool.execute(
        'SELECT * FROM patients WHERE id = ?',
        [patientId]
      );
      
      const updatedPatient = Array.isArray(patients) && patients.length > 0 
        ? patients[0] 
        : null;
      
      return res.status(200).json(
        { 
          success: true, 
          message: '病歷已封存', 
          data: updatedPatient 
        },
        
      );
    }
    
    // 當 isArchived = false，直接刪除病歷
    const [result] = await mysqlConnectionPool.execute(
      'DELETE FROM patients WHERE id = ?',
      [patientId]
    );
    
    // Check if any rows were affected
    if ((result as any).affectedRows === 0) {
      return res.status(404).json(
        { success: false, err: '病歷不存在' },       
      );
    }
    
    return res.status(200).json(
      {
        success: true,
        message: '病歷已刪除',
        data: null
      },
    );
  } catch (err: any) {
    console.error('Manage patient status error:', err);
    
    return res.status(500).json(
      {
        success: false,
        err: `內部錯誤: ${err.message}`,
        data: null
      },
    );
  }
}