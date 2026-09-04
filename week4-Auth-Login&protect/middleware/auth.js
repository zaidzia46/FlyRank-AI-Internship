const jwt = require('jsonwebtoken');
const { pool } = require('../db');
const { isBlacklisted } = require('../tokenBlacklist');

// One guard, reusable on any route: verifies the token, attaches req.user, then calls next().
async function verifyToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.startsWith('Bearer ') ? authHeader.split(' ')[1] : null;

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  if (isBlacklisted(token)) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const result = await pool.query(
      'SELECT id, email, created_at FROM users WHERE id = $1',
      [decoded.sub]
    );
    const user = result.rows[0];

    if (!user) {
      return res.status(401).json({ error: 'Invalid or expired token' });
    }

    req.user = user;
    req.token = token;
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
}

module.exports = { verifyToken };
