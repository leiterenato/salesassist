package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
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

func (e Entities) loadDictFromFile(filePath string) {

	var entities Entities

	// Open our jsonFile
	jsonFile, err := os.Open(filePath)
	// if we os.Open returns an error then handle it
	if err != nil {
		fmt.Println(err)
	}

	fmt.Println("Successfully Opened users.json")
	// defer the closing of our jsonFile so that we can parse it later on
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &entities)

}

func main() {
	nome := "dictionary.json"
	var entities Entities

	entities.loadDictFromFile(nome)

	fmt.Println(entities.Entities[0].Entity)
	fmt.Println(entities.Entities[0].Synonyms)
}

// Scan by words
// f, err := os.Open("thermopylae.txt")

// if err != nil {
// 	fmt.Println(err)
//  }

// defer f.Close()

// scanner := bufio.NewScanner(f)
// scanner.Split(bufio.ScanWords)

// for scanner.Scan() {

// 	fmt.Println(scanner.Text())
// }

// if err := scanner.Err(); err != nil {
// 	fmt.Println(err)
// }
// }
