const express = require('express');
const { verifyToken } = require('../middleware/auth');
const router = express.Router();

// Both routes reuse the SAME middleware - no auth code duplicated between them.
router.get('/profile', verifyToken, (req, res) => {
  res.status(200).json({ user: req.user });
});

router.get('/dashboard', verifyToken, (req, res) => {
  res.status(200).json({
    message: `Welcome to your dashboard, ${req.user.email}`,
    user: req.user,
  });
});

module.exports = router;
