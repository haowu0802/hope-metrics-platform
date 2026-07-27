package window

import (
	"time"

	"github.com/haowu0802/hope-metrics-platform/probe/internal/event"
)

// Accumulator tracks active minutes inside the current clock hour.
type Accumulator struct {
	loc           *time.Location
	deviceID      string
	probeVersion  string
	schemaVersion string
	idle          time.Duration

	hourStart time.Time
	active    map[int]struct{} // minute-of-hour marked active
}

func NewAccumulator(loc *time.Location, deviceID, probeVersion, schemaVersion string, idle time.Duration) *Accumulator {
	a := &Accumulator{
		loc:           loc,
		deviceID:      deviceID,
		probeVersion:  probeVersion,
		schemaVersion: schemaVersion,
		idle:          idle,
		active:        make(map[int]struct{}),
	}
	a.resetToHour(time.Now().In(loc))
	return a
}

func (a *Accumulator) resetToHour(now time.Time) {
	a.hourStart = time.Date(now.Year(), now.Month(), now.Day(), now.Hour(), 0, 0, 0, a.loc)
	a.active = make(map[int]struct{})
}

// Sample records whether the current minute is active given last-input age.
func (a *Accumulator) Sample(now time.Time, lastInputAge time.Duration) {
	now = now.In(a.loc)
	hourStart := time.Date(now.Year(), now.Month(), now.Day(), now.Hour(), 0, 0, 0, a.loc)
	if !hourStart.Equal(a.hourStart) {
		// Caller should FlushClosed before crossing; still protect state.
		a.resetToHour(now)
	}
	if lastInputAge < a.idle {
		a.active[now.Minute()] = struct{}{}
	}
}

// FlushClosedIfNeeded returns a completed hour event when the clock moved to a new hour.
func (a *Accumulator) FlushClosedIfNeeded(now time.Time) (event.UsageHour, bool) {
	now = now.In(a.loc)
	hourStart := time.Date(now.Year(), now.Month(), now.Day(), now.Hour(), 0, 0, 0, a.loc)
	if hourStart.Equal(a.hourStart) {
		return event.UsageHour{}, false
	}
	ev := a.snapshot(a.hourStart)
	a.resetToHour(now)
	return ev, true
}

// ForceFlushCurrent closes the current partial hour (shutdown).
func (a *Accumulator) ForceFlushCurrent(now time.Time) (event.UsageHour, bool) {
	now = now.In(a.loc)
	if len(a.active) == 0 && now.Truncate(time.Hour).Equal(a.hourStart) {
		// still emit for audit of empty partial? emit always for shutdown clarity
	}
	ev := a.snapshot(a.hourStart)
	// end is now truncated to minute+1 or now? Contract: window_end exclusive hour end for full hours.
	// For partial shutdown, use next minute boundary or now rounded up to minute.
	end := time.Date(now.Year(), now.Month(), now.Day(), now.Hour(), now.Minute(), 0, 0, a.loc).Add(time.Minute)
	if end.Before(a.hourStart.Add(time.Hour)) {
		ev.WindowEnd = end
	}
	a.resetToHour(now)
	return ev, true
}

func (a *Accumulator) snapshot(hourStart time.Time) event.UsageHour {
	return event.UsageHour{
		SchemaVersion: a.schemaVersion,
		ProbeVersion:  a.probeVersion,
		DeviceID:      a.deviceID,
		WindowStart:   hourStart,
		WindowEnd:     hourStart.Add(time.Hour),
		ActiveMinutes: len(a.active),
	}
}

func (a *Accumulator) Idle() time.Duration { return a.idle }

func (a *Accumulator) CurrentHourStart() time.Time { return a.hourStart }

func (a *Accumulator) ActiveMinuteCount() int { return len(a.active) }
