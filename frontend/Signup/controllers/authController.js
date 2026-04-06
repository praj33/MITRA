const jwt = require('jsonwebtoken');
const User = require('../models/User');

// Helper: sign a JWT for a user
const signToken = (userId) => {
    return jwt.sign({ id: userId }, process.env.JWT_SECRET, {
        expiresIn: '7d',
    });
};

// Helper: send token response
const sendAuthResponse = (res, statusCode, user, token) => {
    res.status(statusCode).json({
        token,
        user: {
            id: user._id,
            name: user.name,
            email: user.email,
        },
    });
};

// ─── POST /api/auth/signup ─────────────────────────────────────────────────
exports.signup = async (req, res) => {
    try {
        const { name, email, password } = req.body;

        if (!name || !email || !password) {
            return res.status(400).json({ error: 'Name, email, and password are required.' });
        }

        // Check for existing user
        const existing = await User.findOne({ email: email.toLowerCase() });
        if (existing) {
            return res.status(409).json({ error: 'Email already registered.' });
        }

        // Create user (password hashed via pre-save hook)
        const user = await User.create({ name, email, password });

        const token = signToken(user._id);
        sendAuthResponse(res, 201, user, token);
    } catch (err) {
        console.error('Signup error:', err);
        if (err.name === 'ValidationError') {
            const messages = Object.values(err.errors).map((e) => e.message);
            return res.status(400).json({ error: messages.join('. ') });
        }
        res.status(500).json({ error: 'Server error. Please try again.' });
    }
};

// ─── POST /api/auth/login ──────────────────────────────────────────────────
exports.login = async (req, res) => {
    try {
        const { email, password } = req.body;

        if (!email || !password) {
            return res.status(400).json({ error: 'Email and password are required.' });
        }

        // Find user with password included
        const user = await User.findOne({ email: email.toLowerCase() }).select('+password');
        if (!user) {
            return res.status(401).json({ error: 'Invalid email or password.' });
        }

        // Compare password
        const isMatch = await user.comparePassword(password);
        if (!isMatch) {
            return res.status(401).json({ error: 'Invalid email or password.' });
        }

        // Update lastLoginAt
        user.lastLoginAt = new Date();
        await user.save({ validateBeforeSave: false });

        const token = signToken(user._id);
        sendAuthResponse(res, 200, user, token);
    } catch (err) {
        console.error('Login error:', err);
        res.status(500).json({ error: 'Server error. Please try again.' });
    }
};

// ─── GET /api/auth/me ─────────────────────────────────────────────────────
exports.getMe = async (req, res) => {
    res.status(200).json({
        user: {
            id: req.user._id,
            name: req.user.name,
            email: req.user.email,
        },
    });
};

// ─── POST /api/auth/logout ────────────────────────────────────────────────
// JWT is stateless; logout is handled client-side by deleting the token.
exports.logout = (req, res) => {
    res.status(200).json({ message: 'Logged out successfully.' });
};
