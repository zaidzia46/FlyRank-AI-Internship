const express = require('express');
const router = express.Router();

// GET /public/info - open to anyone, no auth
router.get('/info', (req, res) => {
  res.status(200).json({ message: 'Welcome stranger! This info is public.' });
});

module.exports = router;
