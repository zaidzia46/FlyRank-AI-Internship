require('dotenv').config();
const express = require('express');
const swaggerUi = require('swagger-ui-express');
const openapiDocument = require('./openapi.json');
const { pool } = require('./db');
const authRoutes = require('./routes/auth');
const publicRoutes = require('./routes/public');
const protectedRoutes = require('./routes/protected');

const app = express();
app.use(express.json());

app.use('/auth', authRoutes);
app.use('/public', publicRoutes);
app.use('/protected', protectedRoutes);
app.use('/docs', swaggerUi.serve, swaggerUi.setup(openapiDocument));

const PORT = process.env.PORT || 3000;

app.listen(PORT, async () => {
  try {
    await pool.query('SELECT 1');
    console.log(`Server running on port ${PORT} and connected to NeonDB`);
    console.log(`Swagger docs at http://localhost:${PORT}/docs`);
  } catch (err) {
    console.error('Failed to connect to NeonDB:', err.message);
  }
});

module.exports = app;
