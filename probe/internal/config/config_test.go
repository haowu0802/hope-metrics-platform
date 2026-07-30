package config

import "testing"

func TestParseBuildEnv(t *testing.T) {
	raw := `
# comment
HOPE_INGEST_URL=https://hope-metrics.fly.dev/v1/events
HOPE_OUT_DIR=out
`
	m := parseBuildEnv(raw)
	if m["HOPE_INGEST_URL"] != "https://hope-metrics.fly.dev/v1/events" {
		t.Fatalf("ingest url: %q", m["HOPE_INGEST_URL"])
	}
	if m["HOPE_OUT_DIR"] != "out" {
		t.Fatalf("out dir: %q", m["HOPE_OUT_DIR"])
	}
}
