const nodemailer = require('nodemailer');

module.exports = async (req, res) => {
  // Enable CORS for Render backend & frontend
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, X-API-Key');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { to, subject, message, user, password } = req.body || {};
  if (!to || !message) {
    return res.status(400).json({ error: 'Missing to or message' });
  }

  const emailUser = user || process.env.EMAIL_USER || 'blackholeinfiverse20@gmail.com';
  const emailPass = password || process.env.EMAIL_PASSWORD || 'ejcotfrrxmesnebv';

  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: emailUser,
      pass: emailPass,
    },
  });

  try {
    const info = await transporter.sendMail({
      from: emailUser,
      to,
      subject: subject || 'Message from Mitra AI',
      text: message,
    });
    return res.status(200).json({
      status: 'success',
      messageId: info.messageId,
      to,
      method: 'vercel_relay',
    });
  } catch (err) {
    console.error('Vercel email relay error:', err);
    return res.status(500).json({ error: err.message });
  }
};
