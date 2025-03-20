require("dotenv").config();
const express = require("express");
const twilio = require("twilio");
const axios = require("axios");
const fs = require("fs");
const path = require("path");
const app = express();

app.use(express.urlencoded({ extended: true }));
app.use((req, res, next) => {
  res.setHeader("ngrok-skip-browser-warning", "true");
  next();
});

const { TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, SERVER_URL } = process.env;
const twilioClient = twilio(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN);

// Create a directory for storing recordings if it doesn't exist
const recordingsDir = path.join(__dirname, "recordings");
if (!fs.existsSync(recordingsDir)) {
  fs.mkdirSync(recordingsDir);
}

app.get("/", (req, res) => {
  res.send("Twilio Call Recording Server is Running!");
});

app.post("/incoming-call", (req, res) => {
  const twiml = new twilio.twiml.VoiceResponse();
  twiml.say("Hello. Thank you for calling. Please join us as we say goodbye to an important person in our life. We'll need some information from you. We'll ask you some questions. At the tone, say your answer. Once you are done answering, press 1.");
  // Redirect to the first question
  twiml.redirect("/ask-name");
  res.type("text/xml");
  res.send(twiml.toString());
});

app.post("/ask-name", (req, res) => {
  const twiml = new twilio.twiml.VoiceResponse();
  const callSid = req.body.CallSid;
  
  twiml.say("What is your name?");
  twiml.record({
    maxLength: 60,
    playBeep: true,
    finishOnKey: "1",
    action: "/ask-relationship",
    recordingStatusCallback: `/recording-complete?question=name&callSid=${callSid}`
  });
  res.type("text/xml");
  res.send(twiml.toString());
});

app.post("/ask-relationship", (req, res) => {
  const twiml = new twilio.twiml.VoiceResponse();
  const callSid = req.body.CallSid;
  
  twiml.say("What is your relationship to the deceased?");
  twiml.record({
    maxLength: 60,
    playBeep: true,
    finishOnKey: "1",
    action: "/ask-memory",
    recordingStatusCallback: `/recording-complete?question=relationship&callSid=${callSid}`
  });
  res.type("text/xml");
  res.send(twiml.toString());
});

app.post("/ask-memory", (req, res) => {
  const twiml = new twilio.twiml.VoiceResponse();
  const callSid = req.body.CallSid;
  
  twiml.say("What is your favorite memory of your time together?");
  twiml.record({
    maxLength: 120,
    playBeep: true,
    finishOnKey: "1",
    action: "/ask-message",
    recordingStatusCallback: `/recording-complete?question=memory&callSid=${callSid}`
  });
  res.type("text/xml");
  res.send(twiml.toString());
});

app.post("/ask-message", (req, res) => {
  const twiml = new twilio.twiml.VoiceResponse();
  const callSid = req.body.CallSid;
  
  twiml.say("What is something you wish you could say to the deceased if they were still here?");
  twiml.record({
    maxLength: 120,
    playBeep: true,
    finishOnKey: "1",
    action: "/end-call",
    recordingStatusCallback: `/recording-complete?question=message&callSid=${callSid}`
  });
  res.type("text/xml");
  res.send(twiml.toString());
});

app.post("/end-call", (req, res) => {
  const twiml = new twilio.twiml.VoiceResponse();
  twiml.say("Thank you for your responses. Goodbye.");
  res.type("text/xml");
  res.send(twiml.toString());
});

app.post("/recording-complete", async (req, res) => {
  try {
    const recordingUrl = req.body.RecordingUrl;
    const recordingSid = req.body.RecordingSid;
    const question = req.query.question;
    const callSid = req.query.callSid;
    
    if (recordingUrl && recordingSid) {
      console.log(`Recording for ${question}: ${recordingUrl}`);
      
      // Create a unique filename using the callSid and question
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `${callSid}_${question}_${timestamp}.wav`;
      const filePath = path.join(recordingsDir, filename);
      
      // Add .wav extension to get the audio file instead of XML
      const audioUrl = `${recordingUrl}.wav`;
      
      // Download the recording
      const response = await axios({
        method: 'get',
        url: audioUrl,
        responseType: 'stream',
        auth: {
          username: TWILIO_ACCOUNT_SID,
          password: TWILIO_AUTH_TOKEN
        }
      });
      
      // Create a write stream to save the file
      const writer = fs.createWriteStream(filePath);
      
      // Pipe the response data to the file
      response.data.pipe(writer);
      
      // Return a promise that resolves when the file is written
      await new Promise((resolve, reject) => {
        writer.on('finish', resolve);
        writer.on('error', reject);
      });
      
      console.log(`Recording saved to ${filePath}`);
    }
    
    res.sendStatus(200);
  } catch (error) {
    console.error('Error downloading recording:', error);
    res.sendStatus(500);
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));