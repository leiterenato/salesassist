# Sales Assist
Offer a set of tools to help the Sales Agent have real-time information to assist their customers with relevant information. Features list:  

**Assist**: Assist the sales agent in real time with content about topics being discussed in a virtual meeting. Possible suggestions:
- Discovery Questions
- Answers to customer questions
- Suggestions of solutions / products
- Videos the customer may watch on Youtube
- Slides / Papers / Demonstrations  

**Summary**: Summarize what was discussed in the meeting.
- Analyse the audio transcription from the meeting to summarise what was discussed (topics).
- Recommend content the customer may like about products and solutions
- Suggest who (people and teams) can help in the next meeting based on topics discussed
- Help on resource planning of resources to be allocated

**Next**: Analyse information from emails and audio transcriptions from meetings to suggest the next topic to be discussed.
- Email reminder before the meeting with a summary of topics to be discussed.
- Daily email with meetings, topics to be discussed and pointer to preparation content (slides, documentation, etc).
- Bot can start the meeting with a list of topics to be covered.

**Scale**: Create presentations (videos) of products / solutions from static slides.
- Render a vídeo with audio and an avatar from static slides with notes.


## Assist
This module will suggest in real-time relevant content for the Sales Agent to discuss with their customer. The information will be recorded and, along with exchange emails with the customer, it will be later summarized.  

### Prerequisites
- Get the transcriptions in real time
- Suggest content as fast as possible (help Agent avoid silent moments).
- Information can't be too verbose. The Sales Assist provides the necessary information to keep the flow of the conversation.
- Record all information (history)

### Features
Core
- Transcribe text from audio
 - Cloud Speech API
- Extract entities from transcribed audio
 - Regular expression with match in a dictionary (keywords)
- Interact with Cloud Help! to get discovery questions and additional resources to use during the presentation
- Interact with Cloud KB! to search for answers to customer questions

Bots being used
- salesassist-help
Bot to get responses from keywords
- salesassist-kb
 - Bot to get information related to a knowledge base


### Audio Transcription

The audio will be captured in the browser while the meeting is happening. It won't be necessary to record the meeting for this purpose. The audio will be separated in 2 streams: Customer and Sales Representative (Google side). Speech API will be used to transcribe the audio to text.

<img src="https://drive.google.com/uc?export=view&id=1xjw8-umCMNclJL5yeYMVIJZrF383mYDP" width="70%">


### Intent Matching
After the audio is transcribed to text, we will search for words from our dictionary of Cloud Products / Solutions and complete phrases from the customer. If a match is found, it will be sended to Dialogflow agent. The response is presented to the customer, as demonstrated in the following diagram. 

<img src="https://drive.google.com/uc?export=view&id=1k9Lp8924GEQ8cfW_vRL2MzI7-BB3bpHu" width="70%">

Speech API with authentication:  
[1] [An architecture for production-ready live audio transcription using Speech-to-Text](https://cloud.google.com/solutions/media-entertainment/architecture-for-production-ready-live-transcription-using-speech-to-text)  
[2] [Implementing production-ready live audio transcription using Speech-to-Text (Tutorial)](https://cloud.google.com/solutions/media-entertainment/architecture-for-production-ready-live-transcription-tutorial)