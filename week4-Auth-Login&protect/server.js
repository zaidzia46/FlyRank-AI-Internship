require('dotenv').config();
const express = require('express');
const { pool } = require('./db');
const authRoutes = require('./routes/auth');

const app = express();
app.use(express.json());

app.use('/auth', authRoutes);

const PORT = process.env.PORT || 3000;

app.listen(PORT, async () => {
  try {
    await pool.query('SELECT 1');
    console.log(`Server running on port ${PORT} and connected to NeonDB`);
  } catch (err) {
    console.error('Failed to connect to NeonDB:', err.message);
  }
});

module.exports = app;
