package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"net/http/httptest"
	"testing"
)

// Test if JSON body is empty
func TestEmptyJSONBody(t *testing.T) {

	var jsonStr = []byte(``)

	request, err := http.NewRequest("POST", "receiver/v1", bytes.NewBuffer(jsonStr))
	if err != nil {
		log.Fatalln(err)
	}

	request.Header.Set("Content-type", "application/json")

	recorder := httptest.NewRecorder()
	handler := http.HandlerFunc(localPayloadCreate)
	handler.ServeHTTP(recorder, request)

	if status := recorder.Code; status == http.StatusOK {
		t.Errorf("handler returned %v but this is an empty body, want %v",
			http.StatusOK, http.StatusBadRequest)
	}
}

func TestBadlyFormedJSONBody(t *testing.T) {

	var jsonStr = []byte(`{meetingid":"aaa-bbbb-ccc", "phrase":"oi"}`)

	request, err := http.NewRequest("POST", "receiver/v1", bytes.NewBuffer(jsonStr))
	if err != nil {
		log.Fatalln(err)
	}

	request.Header.Set("Content-type", "application/json")

	recorder := httptest.NewRecorder()
	handler := http.HandlerFunc(localPayloadCreate)
	handler.ServeHTTP(recorder, request)

	if status := recorder.Code; status == http.StatusOK {
		t.Errorf("handler returned %v but this is a badly formed JSON Body, want %v",
			http.StatusOK, http.StatusBadRequest)
	}
}

func TestInvalidFieldJSONBody(t *testing.T) {

	var jsonStr = []byte(`{"meet":"aaa-bbbb-ccc", "test":"oi"}`)

	request, err := http.NewRequest("POST", "receiver/v1", bytes.NewBuffer(jsonStr))
	if err != nil {
		log.Fatalln(err)
	}

	request.Header.Set("Content-type", "application/json")

	recorder := httptest.NewRecorder()
	handler := http.HandlerFunc(localPayloadCreate)
	handler.ServeHTTP(recorder, request)

	fmt.Println(recorder.Body.String())

	if status := recorder.Code; status == http.StatusOK {
		t.Errorf("handler returned %v but JSON has invalid fields, want %v",
			http.StatusOK, http.StatusBadRequest)
	}
}

// New definition of PayloadCreate.
func localPayloadCreate(w http.ResponseWriter, r *http.Request) {
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

	msg := &Payload{Phrase: p.Phrase, MeetingID: p.MeetingID}
	msgByte, err := json.Marshal(msg)

	if err == nil {
		fmt.Fprintf(w, "ok")
	} else {
		fmt.Fprintf(w, string(msgByte))
	}
}
