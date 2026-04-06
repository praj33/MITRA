require('dotenv').config();
const express = require('express');
const cors = require('cors');
const connectDB = require('./config/db');
const authRoutes = require('./routes/authRoutes');

const app = express();
const PORT = process.env.PORT || 5000;

// ─── Middleware ────────────────────────────────────────────────────────────
app.use(cors({
    origin: [
        'http://localhost:3000', 
        'http://localhost:3001',
        'https://ai-being.onrender.com',
        'https://ai-architect-gray.vercel.app'
    ],
    credentials: true,
}));
app.use(express.json());

// ─── Database ─────────────────────────────────────────────────────────────
connectDB();

// ─── Routes ───────────────────────────────────────────────────────────────
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'ai-being-auth', time: new Date().toISOString() });
});

app.use('/api/auth', authRoutes);

// 404 handler
app.use((req, res) => {
    res.status(404).json({ error: `Route ${req.method} ${req.path} not found.` });
});

// Global error handler
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({ error: 'Internal server error.' });
});

app.listen(PORT, () => {
    console.log(`🚀 Auth server running on http://localhost:${PORT}`);
});
