const express = require('express');
const path = require('path');
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const app = express();
const PORT = process.env.PORT || 3000;

// MongoDB connection
const MONGO_URI =
  process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/voice2value';

mongoose
  .connect(MONGO_URI)
  .then(() => {
    console.log('Connected to MongoDB');
  })
  .catch((err) => {
    console.error('MongoDB connection error:', err.message);
  });

// User model
const userSchema = new mongoose.Schema({
  fullName: { type: String, required: true },
  email: { type: String, required: true, unique: true, lowercase: true },
  passwordHash: { type: String, required: true },
  createdAt: { type: Date, default: Date.now },
});

const User = mongoose.model('User', userSchema);

// Middleware
app.use(express.urlencoded({ extended: true }));

// Serve static files (login.html, dashboard.html, etc.)
app.use(express.static(path.join(__dirname)));

// Register handler
app.post('/register', async (req, res) => {
  const { fullName, email, password } = req.body;

  if (!fullName || !email || !password) {
    return res.redirect('/register.html?error=missing');
  }

  try {
    const existing = await User.findOne({ email: email.toLowerCase() }).exec();
    if (existing) {
      return res.redirect('/register.html?error=exists');
    }

    const passwordHash = await bcrypt.hash(password, 10);

    await User.create({
      fullName: fullName.trim(),
      email: email.toLowerCase().trim(),
      passwordHash,
    });

    return res.redirect('/login.html?registered=1');
  } catch (err) {
    console.error('Register error:', err);
    return res.redirect('/register.html?error=server');
  }
});

// Login handler
app.post('/login', async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.redirect('/login.html?error=missing');
  }

  try {
    const user = await User.findOne({ email: email.toLowerCase() }).exec();

    if (!user) {
      return res.redirect('/login.html?error=invalid');
    }

    const isMatch = await bcrypt.compare(password, user.passwordHash);

    if (!isMatch) {
      return res.redirect('/login.html?error=invalid');
    }

    // At this point, user is authenticated.
    // For now, just redirect to the dashboard.
    // To add real sessions, integrate express-session or JWT.
    return res.redirect('/dashboard.html');
  } catch (err) {
    console.error('Login error:', err);
    return res.redirect('/login.html?error=server');
  }
});

// Simple route to create a test user (for development only)
app.post('/create-test-user', async (req, res) => {
  const { fullName, email, password } = req.body;

  if (!fullName || !email || !password) {
    return res.status(400).send('Missing fields');
  }

  try {
    const existing = await User.findOne({ email: email.toLowerCase() }).exec();
    if (existing) {
      return res.status(400).send('User already exists');
    }

    const passwordHash = await bcrypt.hash(password, 10);

    await User.create({
      fullName,
      email: email.toLowerCase(),
      passwordHash,
    });

    return res.send('Test user created');
  } catch (err) {
    console.error('Create user error:', err);
    return res.status(500).send('Server error');
  }
});

app.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});

