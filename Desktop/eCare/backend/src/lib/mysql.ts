import mysql from 'mysql2/promise';

// Load environment variables
const dbConfig = {
  user: process.env.MYSQL_USER || 'root',
  password: process.env.MYSQL_PASSWORD || '',
  database: process.env.MYSQL_DATABASE || 'health_db',
  
};

// Prevent multiple connections in development
let mysqlConnectionPool: mysql.Pool;

if (process.env.NODE_ENV === 'production') {
  // In production, we create a new pool
  mysqlConnectionPool = mysql.createPool(dbConfig);
} else {
  // In development, we check for an existing connection
  // This is needed because Next.js Fast Refresh can create
  // multiple connections during development
  if (!(global as any).mysqlConnectionPool) {
    (global as any).mysqlConnectionPool = mysql.createPool(dbConfig);
    console.log('Created new MySQL connection pool');
  }
  mysqlConnectionPool = (global as any).mysqlConnectionPool;
}

// Test the connection on startup
(async () => {
  try {
    const connection = await mysqlConnectionPool.getConnection();
    console.log('Database connection established successfully');
    connection.release();
  } catch (error) {
    console.error('Error connecting to database:', error);
  }
})();

export default mysqlConnectionPool;