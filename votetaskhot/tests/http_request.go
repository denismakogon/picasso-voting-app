package main

import (
	"fmt"
	"net/http"
	"bytes"
	"net/url"
	"io/ioutil"
	"net/http/httputil"
	"strconv"
	"encoding/json"
	"strings"
	"math/rand"
	"time"
)

const lBytes = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

func init() {
	rand.Seed(time.Now().UnixNano())
}

type RqInput struct {
	Pg_host string `json:"pg_host"`
	Pg_port string `json:"pg_port"`
	Pg_db   string `json:"pg_db"`
	Pg_user string `json:"pg_user"`
	Pg_pswd string `json:"pg_pswd"`
	Vote    string `json:"vote"`
	VoteID  string `json:"vote_id"`
}

func RandStringBytes(n int) string {
	b := make([]byte, n)
	for i := range b {
		b[i] = lBytes[rand.Intn(len(lBytes))]
	}
	return strings.ToLower(string(b))
}

func createRequest(i *RqInput) {
	var buf bytes.Buffer

	err := json.NewEncoder(&buf).Encode(i)
	if err != nil {
		fmt.Println(err.Error())
	}

	req := http.Request{
		Method: http.MethodPost,
		URL: &url.URL{
			Scheme: "http",
			Host: "localhost:8080",
			Path: "/r/apps/route",
		},
		ProtoMajor: 1,
		ProtoMinor: 1,
		Header: http.Header{
			"Host": []string{"localhost:8080"},
			"User-Agent": []string{"curl/7.51.0"},
			"Content-Length": []string{strconv.Itoa(buf.Len())},
			"Content-Type": []string{"application/json"},
		},
		ContentLength: int64(buf.Len()),
		Host: "localhost:8080",
	}
	req.Body = ioutil.NopCloser(&buf)
	raw, err := httputil.DumpRequest(&req, true)
	if err != nil {
		fmt.Println(err.Error())
	}
	fmt.Println(string(raw))
}

func main() {
	i := RqInput{
		Pg_db:   "votes",
		Pg_host: "172.17.0.1",
		Pg_port: "5432",
		Pg_pswd: "postgres",
		Pg_user: "postgres",
		Vote:    "cats",
		VoteID:  RandStringBytes(10),
	}
	createRequest(&i)
}
