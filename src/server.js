const express = require("express");
const dotenv = require("dotenv");
const crypto = require("crypto");

dotenv.config();

const app = express();
const port = process.env.PORT || 3000;
const webhookSecret = process.env.GITHUB_WEBHOOK_SECRET || "";

app.use(
  express.json({
    verify: (req, _res, buf) => {
      req.rawBody = buf;
    }
  })
);

function verifyGitHubSignature(req) {
  const signature = req.header("x-hub-signature-256");

  if (!signature || !webhookSecret || !req.rawBody) {
    return false;
  }

  const expectedSignature = `sha256=${crypto
    .createHmac("sha256", webhookSecret)
    .update(req.rawBody)
    .digest("hex")}`;

  const signatureBuffer = Buffer.from(signature);
  const expectedBuffer = Buffer.from(expectedSignature);

  if (signatureBuffer.length !== expectedBuffer.length) {
    return false;
  }

  return crypto.timingSafeEqual(signatureBuffer, expectedBuffer);
}

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

  if (!verifyGitHubSignature(req)) {
    console.error("Invalid webhook signature", { event, delivery });

    return res.status(401).json({
      ok: false,
      error: "Invalid signature"
    });
  }

  const payload = req.body || {};

  console.log("Received webhook", {
    event,
    delivery,
    action: payload.action || null,
    installationId: payload.installation?.id || null,
    repository: payload.repository?.full_name || null,
    sender: payload.sender?.login || null
  });

  return res.status(202).json({
    ok: true,
    received: true,
    event,
    delivery
  });
});

app.listen(port, () => {
  console.log(`releasepilot-app listening on port ${port}`);
});