const express = require("express");
const path = require("path");
const mongoose = require("mongoose");
const bcrypt = require("bcryptjs");
const axios = require("axios");
const multer = require("multer");
const fs = require("fs");
const csv = require("csv-parser");

const app = express();
const PORT = process.env.PORT || 3000;

const PIPELINE_API = process.env.PIPELINE_API || "http://localhost:5000";

const MONGO_URI =
  process.env.MONGO_URI || "mongodb://127.0.0.1:27017/voice2value";

const upload = multer({ dest: "uploads/" });

app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname)));

mongoose
  .connect(MONGO_URI)
  .then(() => {
    console.log("Connected to MongoDB");
  })
  .catch((err) => {
    console.error("MongoDB connection error:", err.message);
  });

const userSchema = new mongoose.Schema({
  fullName: { type: String, required: true },
  email: { type: String, required: true, unique: true, lowercase: true },
  passwordHash: { type: String, required: true },
  createdAt: { type: Date, default: Date.now },
});

const User = mongoose.model("User", userSchema);

// ============================================================================
// AUTH ENDPOINTS
// ============================================================================

app.post("/register", async (req, res) => {
  const { fullName, email, password } = req.body;

  if (!fullName || !email || !password) {
    return res.redirect("/register.html?error=missing");
  }

  try {
    const existing = await User.findOne({ email: email.toLowerCase() });

    if (existing) {
      return res.redirect("/register.html?error=exists");
    }

    const passwordHash = await bcrypt.hash(password, 10);

    await User.create({
      fullName: fullName.trim(),
      email: email.toLowerCase().trim(),
      passwordHash,
    });

    return res.redirect("/login.html?registered=1");
  } catch (err) {
    console.error("Register error:", err);
    return res.redirect("/register.html?error=server");
  }
});

app.post("/login", async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.redirect("/login.html?error=missing");
  }

  try {
    const user = await User.findOne({ email: email.toLowerCase() });

    if (!user) {
      return res.redirect("/login.html?error=invalid");
    }

    const isMatch = await bcrypt.compare(password, user.passwordHash);

    if (!isMatch) {
      return res.redirect("/login.html?error=invalid");
    }

    return res.redirect("/dashboard.html");
  } catch (err) {
    console.error("Login error:", err);
    return res.redirect("/login.html?error=server");
  }
});

// ============================================================================
// DATA INGESTION ENDPOINTS
// ============================================================================

app.post("/upload-csv", upload.single("file"), async (req, res) => {
  try {
    const reviews = [];

    fs.createReadStream(req.file.path)
      .pipe(csv())
      .on("data", (row) => {
        reviews.push({
          text: row.review_text,
          rating: row.rating,
          author: row.author,
          timestamp: row.timestamp,
        });
      })
      .on("end", async () => {
        try {
          await axios.post(`${PIPELINE_API}/ingest-api`, {
            reviews,
            source: "csv_upload",
          });

          fs.unlinkSync(req.file.path);

          res.json({
            status: "success",
            message: `${reviews.length} reviews uploaded`,
          });
        } catch (err) {
          console.error(err);
          res.status(500).json({ error: "Pipeline error" });
        }
      });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Upload error" });
  }
});

app.post("/ingest-api", async (req, res) => {
  try {
    const response = await axios.post(`${PIPELINE_API}/ingest-api`, req.body);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Ingestion failed" });
  }
});

app.get("/ingestion-status", async (req, res) => {
  try {
    const response = await axios.get(`${PIPELINE_API}/ingestion-status`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Status fetch error" });
  }
});

// ============================================================================
// CLUSTERING / PIPELINE ENDPOINTS
// ============================================================================

app.post("/process-reviews", async (req, res) => {
  try {
    const response = await axios.post(`${PIPELINE_API}/process-reviews`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Processing failed" });
  }
});

app.get("/cluster-results/:id", async (req, res) => {
  try {
    const response = await axios.get(
      `${PIPELINE_API}/cluster-results/${req.params.id}`
    );
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Fetch error" });
  }
});

app.get("/top-clusters", async (req, res) => {
  try {
    const response = await axios.get(`${PIPELINE_API}/top-clusters`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Fetch error" });
  }
});

// ============================================================================
// SCHEDULER ENDPOINTS
// ============================================================================

app.post("/scheduler/start", async (req, res) => {
  try {
    const response = await axios.post(`${PIPELINE_API}/scheduler/start`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Scheduler error" });
  }
});

app.post("/scheduler/stop", async (req, res) => {
  try {
    const response = await axios.post(`${PIPELINE_API}/scheduler/stop`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Scheduler error" });
  }
});

app.get("/scheduler/status", async (req, res) => {
  try {
    const response = await axios.get(`${PIPELINE_API}/scheduler/status`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Scheduler status error" });
  }
});

// ============================================================================
// START SERVER
// ============================================================================

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
