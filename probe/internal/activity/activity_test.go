package activity

import (
	"testing"
	"time"
)

func TestWasActive(t *testing.T) {
	idle := 10 * time.Minute
	if !WasActive(30*time.Second, idle) {
		t.Fatal("expected active when last input 30s ago")
	}
	if WasActive(11*time.Minute, idle) {
		t.Fatal("expected inactive when last input 11m ago")
	}
}
