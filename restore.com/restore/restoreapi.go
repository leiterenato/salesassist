package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"

	"cloud.google.com/go/firestore"
	firebase "firebase.google.com/go"
	"github.com/golang/gddo/httputil/header"
	"github.com/gorilla/mux"
	"google.golang.org/api/iterator"
)

var projectID string
var firestoreCtx context.Context
var firestoreClient *firestore.Client

var response map[int]map[string]interface{}

func init() {
	var err error
	projectID = os.Getenv("PROJECTID")
	firestoreCtx = context.Background()

	conf := &firebase.Config{ProjectID: projectID}
	app, err := firebase.NewApp(firestoreCtx, conf)
	if err != nil {
		log.Fatalln(err)
	}

	firestoreClient, err = app.Firestore(firestoreCtx)
	if err != nil {
		log.Fatalln(err)
	}
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
	UID       string `json:"uid"`
	MeetingID string `json:"meetingid"`
}

func (p *Payload) queryFirestore() string {
	response = make(map[int]map[string]interface{})
	i := 0

	iter := firestoreClient.Collection("users").Doc(p.UID).Collection("meetings").
		Doc(p.MeetingID).Collection("interactions").Documents(firestoreCtx)

	for {
		doc, err := iter.Next()
		if err == iterator.Done {
			break
		}
		if err != nil {
			fmt.Println("falhou")
		}
		response[i] = doc.Data()
		i = i + 1
	}

	resp, _ := json.Marshal(response)
	return string(resp)
}

func payloadCreate(w http.ResponseWriter, r *http.Request) {

	// Setup CORS
	if r.Method == http.MethodOptions {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		w.Header().Set("Access-Control-Max-Age", "3600")
		w.WriteHeader(http.StatusNoContent)
		return
	}

	w.Header().Set("Access-Control-Allow-Origin", "*")

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

	// Return response with concatenated responses
	fmt.Fprintf(w, p.queryFirestore())
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	r := mux.NewRouter()
	api := r.PathPrefix("/restore/v1").Subrouter()
	api.HandleFunc("", payloadCreate).Methods(http.MethodPost, http.MethodOptions)

	log.Printf("Starting server on port: %s ...", port)
	err := http.ListenAndServe(fmt.Sprintf(":%s", port), r)
	log.Fatal(err)

}
