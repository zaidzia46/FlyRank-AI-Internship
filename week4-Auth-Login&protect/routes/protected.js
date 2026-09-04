const express = require('express');
const jwt = require('jsonwebtoken');
const { pool } = require('../db');
const router = express.Router();

// GET /protected/profile
// Stage 3: actually verify the JWT (signature + expiry) and look the user up in Neon.
router.get('/profile', async (req, res) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.startsWith('Bearer ') ? authHeader.split(' ')[1] : null;

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET); // throws if tampered / expired
    const result = await pool.query(
      'SELECT id, email, created_at FROM users WHERE id = $1',
      [decoded.sub]
    );
    const user = result.rows[0];

    if (!user) {
      return res.status(401).json({ error: 'Invalid or expired token' });
    }

    return res.status(200).json({ user });
  } catch (err) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
});

module.exports = router;
