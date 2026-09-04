const express = require('express');
const router = express.Router();

// GET /protected/profile
// Stage 2: we only check that a token was PRESENTED - we don't verify it's real yet (Stage 3).
router.get('/profile', (req, res) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.startsWith('Bearer ') ? authHeader.split(' ')[1] : null;

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  return res.status(200).json({ message: 'A token was presented (not verified yet)' });
});

module.exports = router;
