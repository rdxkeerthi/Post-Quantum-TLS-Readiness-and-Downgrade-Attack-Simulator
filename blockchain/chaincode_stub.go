// SPDX-License-Identifier: Apache-2.0
// Hyperledger Fabric chaincode stub for PQ-TLS event logging
package main

import (
	"encoding/json"
	"fmt"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

type Event struct {
	ID        string   `json:"id"`
	Timestamp string   `json:"timestamp"`
	KEM       string   `json:"kem"`
	SIG       string   `json:"sig"`
	Alerts    []string `json:"alerts"`
	Transcript string  `json:"transcript"`
}

type PQTLSEventContract struct {
	contractapi.Contract
}

func (c *PQTLSEventContract) LogEvent(ctx contractapi.TransactionContextInterface, eventJSON string) error {
	return ctx.GetStub().PutState("event_"+eventJSON, []byte(eventJSON))
}

func (c *PQTLSEventContract) QueryAllEvents(ctx contractapi.TransactionContextInterface) ([]*Event, error) {
	resultsIterator, err := ctx.GetStub().GetStateByRange("event_", "event_zzzzzzzz")
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()
	var events []*Event
	for resultsIterator.HasNext() {
		kv, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}
		var event Event
		if err := json.Unmarshal(kv.Value, &event); err != nil {
			return nil, err
		}
		events = append(events, &event)
	}
	return events, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(new(PQTLSEventContract))
	if err != nil {
		fmt.Printf("Error create pq-tls-event chaincode: %s", err)
		return
	}
	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting pq-tls-event chaincode: %s", err)
	}
}
