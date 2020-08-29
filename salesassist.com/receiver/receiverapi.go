package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"regexp"
	"strings"

	"cloud.google.com/go/pubsub"
	"github.com/golang/gddo/httputil/header"
	"github.com/gorilla/mux"

	dialogflow "cloud.google.com/go/dialogflow/apiv2"
	dialogflowpb "google.golang.org/genproto/googleapis/cloud/dialogflow/v2"
)

var projectID string
var topicID string
var pubsubClient *pubsub.Client
var ctx context.Context

func init() {
	var err error
	projectID = os.Getenv("PROJECTID")
	topicID = os.Getenv("TOPICID")
	ctx = context.Background()

	pubsubClient, err = pubsub.NewClient(ctx, projectID)
	if err != nil {
		log.Printf("pubsub.NewClient: %v", err)
		return
	}
}

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

type malformedRequest struct {
	status int
	msg    string
}

func (mr *malformedRequest) Error() string {
	return mr.msg
}

func decodeJSONBody(w http.ResponseWriter, r *http.Request, dst interface{}) error {
	if r.Header.Get("Content-Type") != "" {
		value, _ := header.ParseValueAndParams(r.Header, "Content-Type")
		if value != "application/json" {
			msg := "Content-Type header is not application/json"
			return &malformedRequest{status: http.StatusUnsupportedMediaType, msg: msg}
		}
	}

	r.Body = http.MaxBytesReader(w, r.Body, 1048576)

	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()

	err := dec.Decode(&dst)
	if err != nil {
		var syntaxError *json.SyntaxError
		var unmarshalTypeError *json.UnmarshalTypeError

		switch {
		case errors.As(err, &syntaxError):
			msg := fmt.Sprintf("Request body contains badly-formed JSON (at position %d)", syntaxError.Offset)
			return &malformedRequest{status: http.StatusBadRequest, msg: msg}

		case errors.Is(err, io.ErrUnexpectedEOF):
			msg := fmt.Sprintf("Request body contains badly-formed JSON")
			return &malformedRequest{status: http.StatusBadRequest, msg: msg}

		case errors.As(err, &unmarshalTypeError):
			msg := fmt.Sprintf("Request body contains an invalid value for the %q field (at position %d)", unmarshalTypeError.Field, unmarshalTypeError.Offset)
			return &malformedRequest{status: http.StatusBadRequest, msg: msg}

		case strings.HasPrefix(err.Error(), "json: unknown field "):
			fieldName := strings.TrimPrefix(err.Error(), "json: unknown field ")
			msg := fmt.Sprintf("Request body contains unknown field %s", fieldName)
			return &malformedRequest{status: http.StatusBadRequest, msg: msg}

		case errors.Is(err, io.EOF):
			msg := "Request body must not be empty"
			return &malformedRequest{status: http.StatusBadRequest, msg: msg}

		case err.Error() == "http: request body too large":
			msg := "Request body must not be larger than 1MB"
			return &malformedRequest{status: http.StatusRequestEntityTooLarge, msg: msg}

		default:
			return err
		}
	}

	err = dec.Decode(&struct{}{})
	if err != io.EOF {
		msg := "Request body must only contain a single JSON object"
		return &malformedRequest{status: http.StatusBadRequest, msg: msg}
	}

	return nil
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

func payloadCreate(w http.ResponseWriter, r *http.Request) {
	var p Payload

	err := decodeJSONBody(w, r, &p)
	if err != nil {
		var mr *malformedRequest
		if errors.As(err, &mr) {
			http.Error(w, mr.msg, mr.status)
		} else {
			log.Println(err.Error())
			http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
		}
		return
	}

	msg := &Payload{Transcript: p.Transcript, MeetingID: p.MeetingID}
	msgByte, err := json.Marshal(msg)
	publish(msgByte)

	fmt.Fprintf(w, "ok")
}

func publish(msg []byte) error {

	t := pubsubClient.Topic(topicID)
	result := t.Publish(ctx, &pubsub.Message{
		Data: []byte(msg),
	})
	// Block until the result is returned and a server-generated
	// ID is returned for the published message.
	id, err := result.Get(ctx)

	if err != nil {
		log.Println(err, id)
		return err
	}
	log.Println(id)
	return nil
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	r := mux.NewRouter()
	api := r.PathPrefix("/receiver/v1").Subrouter()
	api.HandleFunc("", payloadCreate).Methods(http.MethodPost)

	log.Printf("Starting server on port: %s ...", port)
	err := http.ListenAndServe(fmt.Sprintf(":%s", port), r)
	log.Fatal(err)
}
