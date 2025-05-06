import { NextRequest } from 'next/server';
import mysqlConnectionPool from "../../../src/lib/mysql";

export async function GET(request: NextRequest) {
  try {
    // Get the user ID from request headers (set by middleware)
    const uid = request.headers.get('x-uid');
    
    if (!uid) {
      return Response.json(
        { status: 'error', message: '未登入' },
        { status: 401 }
      );
    }
    
    // Example: Get user data from database
    const [users] = await mysqlConnectionPool.execute(
      'SELECT * FROM users WHERE id = ?',
      [uid]
    );
    
    if (!Array.isArray(users) || users.length === 0) {
      return Response.json(
        { status: 'error', message: '使用者不存在' },
        { status: 404 }
      );
    }
    
    const user = users[0];
    
    return Response.json(
      { 
        status: 'success', 
        data: {
          id: user.id,
          name: user.name,
          email: user.email
        }
      },
      { status: 200 }
    );
  } catch (error: any) {
    console.error('Error fetching user data:', error);
    
    return Response.json(
      { status: 'error', message: `內部錯誤: ${error.message}` },
      { status: 500 }
    );
  }
}
