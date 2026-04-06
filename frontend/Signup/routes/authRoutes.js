const express = require('express');
const { signup, login, getMe, logout } = require('../controllers/authController');
const { protect } = require('../middleware/authMiddleware');

const router = express.Router();

// ─── POST /api/auth/signup ─────────────────────────────────────────────────
router.post('/signup', signup);

// ─── POST /api/auth/login ──────────────────────────────────────────────────
router.post('/login', login);

// ─── GET /api/auth/me ─────────────────────────────────────────────────────
router.get('/me', protect, getMe);

// ─── POST /api/auth/logout ────────────────────────────────────────────────
router.post('/logout', logout);

module.exports = router;
