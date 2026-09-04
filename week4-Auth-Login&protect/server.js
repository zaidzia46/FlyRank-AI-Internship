require('dotenv').config();
const express = require('express');
const { pool } = require('./db');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

app.listen(PORT, async () => {
  try {
    // Prove the DB connection works before declaring victory
    await pool.query('SELECT 1');
    console.log(`Server running on port ${PORT} and connected to NeonDB`);
  } catch (err) {
    console.error('Failed to connect to NeonDB:', err.message);
  }
});

module.exports = app;
