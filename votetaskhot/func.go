package main

import (
	"net/http"
	"bufio"
	"os"
	"bytes"
	"fmt"
	"strconv"
	"encoding/json"
	"io/ioutil"
	"github.com/lib/pq"
	"github.com/jmoiron/sqlx"
	"io"
)

var voteTable = `CREATE TABLE IF NOT EXISTS votes (id VARCHAR(255) NOT NULL UNIQUE, vote VARCHAR(255) NOT NULL)`

type Input struct {
	Pg_host string `json:"pg_host"`
	Pg_port string `json:"pg_port"`
	Pg_db   string `json:"pg_db"`
	Pg_user string `json:"pg_user"`
	Pg_pswd string `json:"pg_pswd"`
	Vote    string `json:"vote"`
	VoteID  string `json:"vote_id"`
}

func main()  {
	for {
		res := http.Response{
			Proto:      "HTTP/1.1",
			ProtoMajor: 1,
			ProtoMinor: 1,
			StatusCode: 200,
			Status:     "OK",
		}
		r := bufio.NewReader(os.Stdin)
		req, err := http.ReadRequest(r)
		var buf bytes.Buffer
		if err != nil {
			// EOF means no request supplied
			if err != io.EOF {
				res.StatusCode = 500
				res.Status = http.StatusText(res.StatusCode)
				fmt.Fprintln(&buf, err)
				fmt.Fprintf(os.Stderr, "Unable to read request, error: %s", err.Error())
			} else {
				continue
			}
		} else {
			l, _ := strconv.Atoi(req.Header.Get("Content-Length"))
			p := make([]byte, l)
			_, err = r.Read(p)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Unable to read request data, error: %s", err.Error())
			}
			input := &Input{}
			fmt.Fprint(os.Stderr, fmt.Sprintf("%s", p))
			err = json.Unmarshal(p, input)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Unable to decode input object, error: %s", err.Error())
				if e, ok := err.(*json.SyntaxError); ok {
					fmt.Fprintf(os.Stderr, "syntax error at byte offset %d", e.Offset)
				}
			}
			dns := fmt.Sprintf(
				"postgres://%v:%v@%v:%v/%v?sslmode=disable",
				input.Pg_user, input.Pg_pswd,
				input.Pg_host, input.Pg_port, input.Pg_db)
			db, err := sqlx.Connect("postgres", dns)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Unable to talk to PG, error: %s", err.Error())
			}
			_, err = db.Exec(voteTable)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Unable to create table, error: %s", err.Error())
			}
			q := db.Rebind("INSERT INTO votes (id, vote) VALUES (?, ?);")
			_, err = db.Exec(q, input.VoteID, input.Vote)
			if err != nil {
				switch err := err.(type) {
				case *pq.Error:
					if err.Code == "23505" {
						// means vote already exist
						q := db.Rebind("UPDATE votes SET id=? WHERE vote=?")
						res, err := db.Exec(q, input.VoteID, input.Vote)
						if err != nil {
							fmt.Fprintf(os.Stderr, "Unable to update vote, error: %s", err.Error())
						}
						if _, err := res.RowsAffected(); err != nil {
							fmt.Fprintf(os.Stderr, "Unable to get number of rows updated, error: %s", err.Error())
						}
					}
				}
			}
			fmt.Fprint(&buf, "OK\n")
			db.Close()
		}
		res.Body = ioutil.NopCloser(&buf)
		res.ContentLength = int64(buf.Len())
		res.Write(os.Stdout)
	}
}
