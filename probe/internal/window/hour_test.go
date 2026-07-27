package window

import (
	"testing"
	"time"
)

func TestFlushOnHourChange(t *testing.T) {
	loc := time.FixedZone("CST", 8*3600)
	acc := NewAccumulator(loc, "dev-1", "0.1.0", "1", 10*time.Minute)

	t0 := time.Date(2026, 7, 27, 14, 10, 0, 0, loc)
	acc.resetToHour(t0)
	acc.Sample(t0, 1*time.Second)
	acc.Sample(t0.Add(2*time.Minute), 1*time.Second)

	tNext := time.Date(2026, 7, 27, 15, 0, 5, 0, loc)
	ev, ok := acc.FlushClosedIfNeeded(tNext)
	if !ok {
		t.Fatal("expected flush")
	}
	if ev.ActiveMinutes != 2 {
		t.Fatalf("active_minutes=%d want 2", ev.ActiveMinutes)
	}
	if !ev.WindowStart.Equal(time.Date(2026, 7, 27, 14, 0, 0, 0, loc)) {
		t.Fatalf("window_start=%s", ev.WindowStart)
	}
	if !ev.WindowEnd.Equal(time.Date(2026, 7, 27, 15, 0, 0, 0, loc)) {
		t.Fatalf("window_end=%s", ev.WindowEnd)
	}
}
