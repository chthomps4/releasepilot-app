const express = require("express");
const dotenv = require("dotenv");

dotenv.config();

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

app.get("/", (_req, res) => {
  res.status(200).json({
    name: "releasepilot-app",
    status: "ok",
    message: "GitHub App server is running."
  });
});

app.get("/health", (_req, res) => {
  res.status(200).json({
    ok: true
  });
});

app.post("/api/github/webhooks", (req, res) => {
  const event = req.header("x-github-event") || "unknown";
  const delivery = req.header("x-github-delivery") || "unknown";

  console.log("Received webhook", {
    event,
    delivery
  });

  res.status(202).json({
    ok: true,
    received: true,
    event,
    delivery
  });
});

app.listen(port, () => {
  console.log(`releasepilot-app listening on port ${port}`);
});