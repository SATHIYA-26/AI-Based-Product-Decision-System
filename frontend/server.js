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
const LANDING_DIST_DIR = path.join(
  __dirname,
  "Landing page",
  "Voice2Value-master",
  "dist"
);

const MONGO_URI =
  process.env.MONGO_URI || "mongodb://127.0.0.1:27017/voice2value";

const upload = multer({ dest: "uploads/" });

app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname)));

let mongoConnected = false;
mongoose
  .connect(MONGO_URI)
  .then(() => {
    mongoConnected = true;
    console.log("Connected to MongoDB");
  })
  .catch((err) => {
    console.error("MongoDB connection error:", err.message);
    console.error("Auth (login/register) will be unavailable until MongoDB is running.");
  });

mongoose.connection.on("connected", () => { mongoConnected = true; });
mongoose.connection.on("disconnected", () => { mongoConnected = false; });

const userSchema = new mongoose.Schema({
  fullName: { type: String, required: true },
  email: { type: String, required: true, unique: true, lowercase: true },
  passwordHash: { type: String, required: true },
  createdAt: { type: Date, default: Date.now },
});

const User = mongoose.model("User", userSchema);

async function registerUser({ fullName, email, password }) {
  if (!mongoConnected) {
    return { ok: false, code: "server", message: "Database unavailable" };
  }

  if (!fullName || !email || !password) {
    return { ok: false, code: "missing", message: "Missing required fields" };
  }

  const existing = await User.findOne({ email: email.toLowerCase() });
  if (existing) {
    return { ok: false, code: "exists", message: "User already exists" };
  }

  const passwordHash = await bcrypt.hash(password, 10);
  await User.create({
    fullName: fullName.trim(),
    email: email.toLowerCase().trim(),
    passwordHash,
  });

  return { ok: true };
}

async function loginUser({ email, password }) {
  if (!mongoConnected) {
    return { ok: false, code: "server", message: "Database unavailable" };
  }

  if (!email || !password) {
    return { ok: false, code: "missing", message: "Missing required fields" };
  }

  const user = await User.findOne({ email: email.toLowerCase() });
  if (!user) {
    return { ok: false, code: "invalid", message: "Invalid credentials" };
  }

  const isMatch = await bcrypt.compare(password, user.passwordHash);
  if (!isMatch) {
    return { ok: false, code: "invalid", message: "Invalid credentials" };
  }

  return {
    ok: true,
    user: {
      fullName: user.fullName,
      email: user.email,
    },
  };
}

// ============================================================================
// AUTH ENDPOINTS
// ============================================================================

app.post("/register", async (req, res) => {
  try {
    const result = await registerUser(req.body);
    if (!result.ok) {
      return res.redirect(`/register.html?error=${result.code}`);
    }
    return res.redirect("/login.html?registered=1");
  } catch (err) {
    console.error("Register error:", err);
    return res.redirect("/register.html?error=server");
  }
});

app.post("/login", async (req, res) => {
  try {
    const result = await loginUser(req.body);
    if (!result.ok) {
      return res.redirect(`/login.html?error=${result.code}`);
    }
    return res.redirect("/dashboard.html");
  } catch (err) {
    console.error("Login error:", err);
    return res.redirect("/login.html?error=server");
  }
});

app.post("/api/auth/register", async (req, res) => {
  try {
    const result = await registerUser(req.body);
    if (!result.ok) {
      return res.status(result.code === "exists" ? 409 : 400).json(result);
    }
    return res.json({ ok: true });
  } catch (err) {
    console.error("Register API error:", err);
    return res.status(500).json({ ok: false, code: "server", message: "Server error" });
  }
});

app.post("/api/auth/login", async (req, res) => {
  try {
    const result = await loginUser(req.body);
    if (!result.ok) {
      return res.status(result.code === "invalid" ? 401 : 400).json(result);
    }
    return res.json(result);
  } catch (err) {
    console.error("Login API error:", err);
    return res.status(500).json({ ok: false, code: "server", message: "Server error" });
  }
});

app.use((req, res, next) => {
  if (!fs.existsSync(LANDING_DIST_DIR)) {
    return next();
  }
  return express.static(LANDING_DIST_DIR)(req, res, next);
});

app.get(["/", "/login", "/signup"], (req, res, next) => {
  const landingIndex = path.join(LANDING_DIST_DIR, "index.html");
  if (fs.existsSync(landingIndex)) {
    return res.sendFile(landingIndex);
  }
  return next();
});

// ============================================================================
// DATA INGESTION ENDPOINTS
// ============================================================================

app.post("/upload-csv", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "No file provided" });
    }
    const FormData = (await import("form-data")).default;
    const form = new FormData();
    form.append("file", fs.createReadStream(req.file.path), {
      filename: req.file.originalname || "reviews.csv",
      contentType: "text/csv",
    });
    if (req.body.source) {
      form.append("source", req.body.source);
    }
    const response = await axios.post(`${PIPELINE_API}/upload-csv`, form, {
      headers: form.getHeaders(),
      maxContentLength: Infinity,
    });
    fs.unlinkSync(req.file.path);
    res.json(response.data);
  } catch (err) {
    if (req.file && fs.existsSync(req.file.path)) fs.unlinkSync(req.file.path);
    console.error("CSV upload error:", err.response?.data || err.message);
    const status = err.response?.status || 500;
    res.status(status).json(err.response?.data || { error: "Upload failed" });
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
    const msg = err.response?.data?.error || "Processing failed";
    console.error("process-reviews error:", msg);
    res.status(err.response?.status || 500).json({ error: msg });
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
// CONNECTOR ENDPOINTS
// ============================================================================

app.post("/connectors", async (req, res) => {
  try {
    const response = await axios.post(`${PIPELINE_API}/connectors`, req.body);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Connector creation failed" });
  }
});

app.get("/connectors", async (req, res) => {
  try {
    const response = await axios.get(`${PIPELINE_API}/connectors`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Connector list failed" });
  }
});

app.get("/connectors/:name", async (req, res) => {
  try {
    const response = await axios.get(
      `${PIPELINE_API}/connectors/${req.params.name}`
    );
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Connector fetch failed" });
  }
});

app.delete("/connectors/:name", async (req, res) => {
  try {
    const response = await axios.delete(
      `${PIPELINE_API}/connectors/${req.params.name}`
    );
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Connector delete failed" });
  }
});

app.post("/connectors/:name/test", async (req, res) => {
  try {
    const response = await axios.post(
      `${PIPELINE_API}/connectors/${req.params.name}/test`
    );
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Connector test failed" });
  }
});

// ============================================================================
// SYNC ENDPOINTS
// ============================================================================

app.post("/sync", async (req, res) => {
  try {
    const response = await axios.post(`${PIPELINE_API}/sync`, req.body);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Sync failed" });
  }
});

app.post("/sync/:connector_name", async (req, res) => {
  try {
    const response = await axios.post(
      `${PIPELINE_API}/sync/${req.params.connector_name}`,
      req.body
    );
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Sync failed" });
  }
});

app.get("/sync/history", async (req, res) => {
  try {
    const url = new URL(`${PIPELINE_API}/sync/history`);
    if (req.query.connector) url.searchParams.set("connector", req.query.connector);
    if (req.query.limit) url.searchParams.set("limit", req.query.limit);
    const response = await axios.get(url.toString());
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Sync history fetch failed" });
  }
});

app.get("/sync/stats", async (req, res) => {
  try {
    const response = await axios.get(`${PIPELINE_API}/sync/stats`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Sync stats fetch failed" });
  }
});

// ============================================================================
// SYNC SCHEDULER ENDPOINTS
// ============================================================================

app.post("/scheduler/sync/start", async (req, res) => {
  try {
    const response = await axios.post(`${PIPELINE_API}/scheduler/sync/start`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Sync scheduler start failed" });
  }
});

app.post("/scheduler/sync/stop", async (req, res) => {
  try {
    const response = await axios.post(`${PIPELINE_API}/scheduler/sync/stop`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Sync scheduler stop failed" });
  }
});

app.get("/scheduler/sync/status", async (req, res) => {
  try {
    const response = await axios.get(`${PIPELINE_API}/scheduler/sync/status`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Sync scheduler status failed" });
  }
});

app.get("/scheduler/sync/jobs", async (req, res) => {
  try {
    const response = await axios.get(`${PIPELINE_API}/scheduler/sync/jobs`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Sync jobs list failed" });
  }
});

app.post("/scheduler/sync/jobs", async (req, res) => {
  try {
    const response = await axios.post(
      `${PIPELINE_API}/scheduler/sync/jobs`,
      req.body
    );
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Sync job creation failed" });
  }
});

app.delete("/scheduler/sync/jobs/:name", async (req, res) => {
  try {
    const response = await axios.delete(
      `${PIPELINE_API}/scheduler/sync/jobs/${req.params.name}`
    );
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Sync job delete failed" });
  }
});

app.post("/scheduler/sync/jobs/:name/trigger", async (req, res) => {
  try {
    const response = await axios.post(
      `${PIPELINE_API}/scheduler/sync/jobs/${req.params.name}/trigger`
    );
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Sync job trigger failed" });
  }
});

// ============================================================================
// HEALTH / INFO
// ============================================================================

app.get("/health", async (req, res) => {
  try {
    const response = await axios.get(`${PIPELINE_API}/health`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Health check failed" });
  }
});

app.get("/info", async (req, res) => {
  try {
    const response = await axios.get(`${PIPELINE_API}/info`);
    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Info fetch failed" });
  }
});

// ============================================================================
// START SERVER
// ============================================================================

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
