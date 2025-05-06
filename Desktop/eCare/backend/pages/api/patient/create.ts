
// For Next.js
import { NextApiRequest, NextApiResponse} from 'next';
// For MySQL2
//import ReselutSetHeader from 'mysql2/promise';
import PatientData from 'mysql2'; //..?
import mysqlConnectionPool from '../../../src/lib/mysql';

// Create a connection pool
//const pool = mysql.createPool({
 // host: 'localhost', // Replace with database host
  //user: 'root',      // Replace with database user
//   password: 'password', // Replace with database password
//   database: 'health_db', // Replace with database name
//});

// Type for the patient data
type PatientData = {
  userId: number;
  name: string;
  age: number;
  gender: string;
  addr: string;
  idNum: string;
  nhCardNum: string;
  emerName?: string;
  emerPhone?: string;
  info?: string;
};

// The function to create a patient in the database
async function createPatient(patientData: PatientData): Promise<number> {


  // Check if patient with this ID number already exists
  const [existingPatients] = await mysqlConnectionPool.execute(
    'SELECT id FROM patients WHERE id_num = ?',
    [patientData.idNum]
  );
  
  if (Array.isArray(existingPatients) && existingPatients.length > 0) {
    throw new Error('Patient with this ID number already exists');
  }

  // Insert the patient into the database
  const [result] = await mysqlConnectionPool.execute(
    `INSERT INTO patients (
      userId, name, age, gender, addr, idNum, nhCardNum, 
      emerName, emerPhone, info, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())`,
    [
      patientData.userId,
      patientData.name,
      patientData.age,
      patientData.gender,
      patientData.addr,
      patientData.idNum,
      patientData.nhCardNum,
      patientData.emerName || null,
      patientData.emerPhone || null,
      patientData.info || null
    ]
  );

  // Return the ID of the newly created patient
  return (result as any).insertId;
}

// Main API handler
export default async function POST(req: NextApiRequest, res: NextApiResponse) {
    try {
      // Parse the request body
   
      const {
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
      } = req.body;


    // Validate required fields
    if (!userId || !name || !age || !gender || !addr || !idNum || !nhCardNum) {
        return res.status(400).json(
            {
              success: false,
              message: '缺少必要資料',
              error: 'Missing required fields'
             }
          );
        }

    // Call the controller function
    const patientId = await createPatient({
      userId: Number(userId),
      name,
      age: Number(age),
      gender,
      addr,
      idNum,
      nhCardNum,
      emerName,
      emerPhone,
      info
    });

    return res.status(201).json(
        {
          success: true,
          message: '成功新增病患',
          data: { patientId }
         }
      );
    } catch (error) {
      console.error('Create patient error:', error);
      
      // Handle specific error cases
      if (error instanceof Error) {
        if (error.message === 'Patient with this ID number already exists') {
          return res.status(409).json(
            {
              success: false,
              message: '病患已存在',
              error: error.message
            }
          );
        }
      }
      
      // General error case
      return res.status(500).json(
        {
          success: false,
          message: '新增病患失敗',
          error: error instanceof Error ? error.message : '未知錯誤'
        }
      );
    }
  }