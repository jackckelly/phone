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

app.get("/", (req, res) => {
    res.send("Twilio Call Recording Server is Running!");
});

app.post("/incoming-call", (req, res) => {
    const twiml = new twilio.twiml.VoiceResponse();
    const callerId = req.body.From; // Get the inbound caller ID

    twiml.say(
        "Hello. Thank you for calling. Please join us as we say goodbye to our dear friend, the internet. We'll need some information from you. We'll ask you some questions. At the tone, say your answer. Once you are done answering, press 1."
    );

    // Redirect to the first question with caller ID
    twiml.redirect(`/ask-name?callerId=${encodeURIComponent(callerId)}`);

    res.type("text/xml");
    res.send(twiml.toString());
});

app.post("/ask-name", (req, res) => {
    const twiml = new twilio.twiml.VoiceResponse();
    const callSid = req.body.CallSid;
    const callerId = req.query.callerId;

    twiml.say("What is your name?");
    twiml.record({
        maxLength: 60,
        playBeep: true,
        finishOnKey: "1",
        action: `/ask-like?callerId=${encodeURIComponent(callerId)}`,
        recordingStatusCallback: `/recording-complete?question=name&callSid=${callSid}&callerId=${encodeURIComponent(
            callerId
        )}`,
    });

    res.type("text/xml");
    res.send(twiml.toString());
});

app.post("/ask-hate", (req, res) => {
    const twiml = new twilio.twiml.VoiceResponse();
    const callSid = req.body.CallSid;
    const callerId = req.query.callerId;

    twiml.say("What bothered you the most about the internet?");
    twiml.record({
        maxLength: 60,
        playBeep: true,
        finishOnKey: "1",
        action: `/ask-memory?callerId=${encodeURIComponent(callerId)}`,
        recordingStatusCallback: `/recording-complete?question=hate&callSid=${callSid}&callerId=${encodeURIComponent(
            callerId
        )}`,
    });

    res.type("text/xml");
    res.send(twiml.toString());
});

app.post("/ask-like", (req, res) => {
    const twiml = new twilio.twiml.VoiceResponse();
    const callSid = req.body.CallSid;
    const callerId = req.query.callerId;

    twiml.say("What did you like the most about the internet?");
    twiml.record({
        maxLength: 60,
        playBeep: true,
        finishOnKey: "1",
        action: `/ask-hate?callerId=${encodeURIComponent(callerId)}`,
        recordingStatusCallback: `/recording-complete?question=like&callSid=${callSid}&callerId=${encodeURIComponent(
            callerId
        )}`,
    });

    res.type("text/xml");
    res.send(twiml.toString());
});

app.post("/ask-memory", (req, res) => {
    const twiml = new twilio.twiml.VoiceResponse();
    const callSid = req.body.CallSid;
    const callerId = req.query.callerId;

    twiml.say("What is your favorite memory of your time together?");
    twiml.record({
        maxLength: 120,
        playBeep: true,
        finishOnKey: "1",
        action: `/ask-message?callerId=${encodeURIComponent(callerId)}`,
        recordingStatusCallback: `/recording-complete?question=memory&callSid=${callSid}&callerId=${encodeURIComponent(
            callerId
        )}`,
    });

    res.type("text/xml");
    res.send(twiml.toString());
});

app.post("/ask-message", (req, res) => {
    const twiml = new twilio.twiml.VoiceResponse();
    const callSid = req.body.CallSid;
    const callerId = req.query.callerId;

    twiml.say(
        "What is something you wish you could say to the internet if they were still here?"
    );
    twiml.record({
        maxLength: 120,
        playBeep: true,
        finishOnKey: "1",
        action: `/end-call?callerId=${encodeURIComponent(callerId)}`,
        recordingStatusCallback: `/recording-complete?question=message&callSid=${callSid}&callerId=${encodeURIComponent(
            callerId
        )}`,
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

const yaml = require("js-yaml"); // Import the js-yaml package

app.post("/recording-complete", async (req, res) => {
    try {
        const recordingUrl = req.body.RecordingUrl;
        const recordingSid = req.body.RecordingSid;
        const question = req.query.question;

        // Sanitize caller ID and remove leading underscores
        let callerId = req.query.callerId
            .replace(/[^a-zA-Z0-9]/g, "_")
            .replace(/^_+/, "");

        if (recordingUrl && recordingSid) {
            console.log(`Recording for ${question}: ${recordingUrl}`);

            // Create the caller-specific directory
            const callerDir = path.join(__dirname, "../data", callerId);
            if (!fs.existsSync(callerDir)) {
                fs.mkdirSync(callerDir, { recursive: true });
            }

            // Set the filename for the current question's audio file
            const filename = `${question}.wav`;
            const filePath = path.join(callerDir, filename);

            const audioUrl = `${recordingUrl}.wav`;

            const response = await axios({
                method: "get",
                url: audioUrl,
                responseType: "stream",
                auth: {
                    username: TWILIO_ACCOUNT_SID,
                    password: TWILIO_AUTH_TOKEN,
                },
            });

            const writer = fs.createWriteStream(filePath);

            response.data.pipe(writer);

            await new Promise((resolve, reject) => {
                writer.on("finish", resolve);
                writer.on("error", reject);
            });

            console.log(`Recording saved to ${filePath}`);

            // After all recordings for a caller are saved, generate the YAML file
            const yamlFilePath = path.join(callerDir, "calldata.yaml"); // Fixed filename calldata.yaml

            const yamlData = {
                number: `${callerId}`, // number will not be quoted
                name_file: `data/${callerId}/name.wav`,
                memory_file: `data/${callerId}/memory.wav`,
                like_file: `data/${callerId}/like.wav`,
                hate_file: `data/${callerId}/hate.wav`,
                message_file: `data/${callerId}/message.wav`,
            };

            // Write the YAML data to a file without quoting the number field
            const yamlString = yaml.dump(yamlData, {
                noRefs: true, // Disable references
                lineWidth: -1, // Prevent line wrapping
                quoteKeys: false, // Prevent quoting keys
                indent: 2, // Use 2 spaces for indentation
                skipInvalid: true, // Skip invalid properties (if any)
                noCompatMode: true, // Disable YAML 1.1 compatibility mode (prevents quoting numbers)
            });

            fs.writeFileSync(yamlFilePath, yamlString);

            console.log(`YAML file saved to ${yamlFilePath}`);
        }

        res.sendStatus(200);
    } catch (error) {
        console.error("Error downloading recording:", error);
        res.sendStatus(500);
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
