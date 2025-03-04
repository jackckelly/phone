require("dotenv").config();
const express = require("express");
const twilio = require("twilio");

const app = express();
app.use(express.urlencoded({ extended: true }));
app.use((req, res, next) => {
  res.setHeader("ngrok-skip-browser-warning", "true");
  next();
});

const { TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, SERVER_URL } = process.env;
const twilioClient = twilio(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN);

app.get("/", (req, res) => {
  res.send("Twilio Call Recording Server is Running!");
});

app.post("/incoming-call", (req, res) => {
  const twiml = new twilio.twiml.VoiceResponse();

  const gather = twiml.gather({
    numDigits: 1,
    action: "/handle-keypress",
    method: "POST",
  });

  gather.say("Press 1 for More Sad. Press 2 for Less Sad. Press 3 for Phone.");

  // If no input is received, replay the message
  twiml.redirect("/incoming-call");

  res.type("text/xml");
  res.send(twiml.toString());
});

app.post("/handle-keypress", (req, res) => {
  const twiml = new twilio.twiml.VoiceResponse();
  const digit = req.body.Digits; // Get the key pressed

  if (["1", "2", "3"].includes(digit)) {
    twiml.say("Please leave a message at the tone. When you are done recording, hang up.");
    twiml.record({
      maxLength: 60,
      playBeep: true,
      recordingStatusCallback: "/recording-complete",
      recordingStatusCallbackEvent: ["completed"],
    });
  } else {
    twiml.say("Invalid option. Please try again.");
    twiml.redirect("/incoming-call");
  }

  res.type("text/xml");
  res.send(twiml.toString());
});

app.post("/recording-complete", (req, res) => {
  console.log("Recording URL:", req.body.RecordingUrl);
  res.sendStatus(200);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
