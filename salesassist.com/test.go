package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"regexp"

	dialogflow "cloud.google.com/go/dialogflow/apiv2"
	dialogflowpb "google.golang.org/genproto/googleapis/cloud/dialogflow/v2"
)

// Entities for query reference
type Entities struct {
	Entities []EntitySynonyms `json:"entities"`
}

// EntitySynonyms key:value pair
type EntitySynonyms struct {
	Entity   string   `json:"entity"`
	Synonyms []string `json:"synonyms"`
}

func (e *Entities) loadDictFromFile(filePath string) {

	// Open our jsonFile
	jsonFile, err := os.Open(filePath)
	// if we os.Open returns an error then handle it
	if err != nil {
		fmt.Println(err)
	}

	fmt.Println("Successfully Opened json")
	// defer the closing of our jsonFile so that we can parse it later on
	defer jsonFile.Close()

	byteValue, err := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &e)

}

func detectIntentText(projectID string, sessionID string, intents map[string]string, languageCode string) map[string]string {
	intentResponse := make(map[string]string)
	ctx := context.Background()

	sessionClient, err := dialogflow.NewSessionsClient(ctx)
	if err != nil {
		fmt.Println(err)
	}
	defer sessionClient.Close()

	if projectID == "" || sessionID == "" {
		fmt.Println(projectID, sessionID)
	}

	sessionPath := fmt.Sprintf("projects/%s/agent/sessions/%s", projectID, sessionID)

	for key := range intents {
		textInput := dialogflowpb.TextInput{Text: key, LanguageCode: languageCode}
		queryTextInput := dialogflowpb.QueryInput_Text{Text: &textInput}
		queryInput := dialogflowpb.QueryInput{Input: &queryTextInput}
		request := dialogflowpb.DetectIntentRequest{Session: sessionPath, QueryInput: &queryInput}

		response, err := sessionClient.DetectIntent(ctx, &request)
		if err != nil {
			fmt.Println(err)
		}

		queryResult := response.GetQueryResult()
		fulfillmentText := queryResult.GetFulfillmentText()

		intentResponse[key] = fulfillmentText
	}

	return intentResponse
}

// Payload of the JSON structure
type Payload struct {
	MeetingID  string `json:"meetingid"`
	Speaker    string `json:"phrase"`
	Transcript string `json:"transcript"`
	Start      string `json:"start"`
	End        string `json:"end"`
}

func (p *Payload) findSynonyms(entities Entities) map[string]string {

	match := make(map[string]string)

	for _, entity := range entities.Entities {
		for _, synonym := range entity.Synonyms {
			isMatchSynonym, _ := regexp.MatchString(synonym, p.Transcript)
			if isMatchSynonym {
				match[entity.Entity] = synonym
				break
			}
		}
	}

	return match
}

// Responses with intent matching
type Responses struct {
	Responses []ResponseContent `json:"response"`
}

// ResponseContent with intent matching
type ResponseContent struct {
	Title   string `json:"title"`
	Content string `json:"content"`
}

func (resp *Responses) buildResponseContent(intentResponses map[string]string) {
	for key, element := range intentResponses {
		resp.Responses = append(resp.Responses, ResponseContent{key, element})
	}
}

// History to be published
type History struct {
	MeetingID  string            `json:"meetingid"`
	Speaker    string            `json:"phrase"`
	Transcript string            `json:"transcript"`
	Start      string            `json:"start"`
	End        string            `json:"end"`
	Responses  []ResponseContent `json:"response"`
}

func (hist *History) buildHistoryContent(p *Payload, resp *Responses) {
	hist.MeetingID = p.MeetingID
	hist.Speaker = p.Speaker
	hist.Transcript = p.Transcript
	hist.Start = p.Start
	hist.End = p.End
	hist.Responses = resp.Responses
}

func main() {

	// var resp Responses
	// var h History
	// filename := "dictionary.json"
	// var entities Entities
	// p := Payload{"abc-defg-hij", "GOOGLER", "Gosto muito de GCP", "2020-08-22 13:45:00", "2020-08-22 13:45:00"}

	// entities.loadDictFromFile(filename)
	// match := p.findSynonyms(entities)

	// teste := detectIntentText("salesassist-help", "renato-legal", match, "pt-BR")

	// resp.buildResponseContent(teste)
	// // fmt.Println(resp)

	// h.buildHistoryContent(&p, &resp)
	// renato, _ := json.Marshal(h)
	// fmt.Println(string(renato))

	var resp Responses
	resp.Responses = append(resp.Responses, ResponseContent{Title: "", Content: ""})
	resp.Responses = append(resp.Responses, ResponseContent{Title: "", Content: ""})
	resp.Responses = nil
	fmt.Println(resp)
	fmt.Printf("len=%d", len(resp.Responses))
}
