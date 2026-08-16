package window

import (
	"time"

	"github.com/haowu0802/hope-metrics-platform/probe/internal/event"
	"github.com/haowu0802/hope-metrics-platform/probe/internal/sysmetrics"
)

// Accumulator tracks active minutes and resource samples inside the current clock hour.
type Accumulator struct {
	loc           *time.Location
	deviceID      string
	probeVersion  string
	schemaVersion string
	idle          time.Duration

	hourStart time.Time
	active    map[int]struct{} // minute-of-hour marked active

	cpuSum, memSum, diskSum float64
	gpuSum                  float64
	gpuSamples              int
	resourceSamples         int
	lastDiskGB              float64
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
	a.cpuSum, a.memSum, a.diskSum, a.gpuSum = 0, 0, 0, 0
	a.gpuSamples, a.resourceSamples = 0, 0
	a.lastDiskGB = 0
}

// Sample records whether the current minute is active given last-input age.
func (a *Accumulator) Sample(now time.Time, lastInputAge time.Duration) {
	a.SampleWithMetrics(now, lastInputAge, nil)
}

// SampleWithMetrics records activity and optional resource snapshot for the tick.
func (a *Accumulator) SampleWithMetrics(now time.Time, lastInputAge time.Duration, snap *sysmetrics.Snapshot) {
	now = now.In(a.loc)
	hourStart := time.Date(now.Year(), now.Month(), now.Day(), now.Hour(), 0, 0, 0, a.loc)
	if !hourStart.Equal(a.hourStart) {
		a.resetToHour(now)
	}
	if lastInputAge < a.idle {
		a.active[now.Minute()] = struct{}{}
	}
	if snap == nil {
		return
	}
	a.cpuSum += snap.CPUUtilPct
	a.memSum += snap.MemUtilPct
	a.diskSum += snap.DiskFreeGB
	a.lastDiskGB = snap.DiskFreeGB
	a.resourceSamples++
	if snap.GPUUtilPct != nil {
		a.gpuSum += *snap.GPUUtilPct
		a.gpuSamples++
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
	ev := a.snapshot(a.hourStart)
	end := time.Date(now.Year(), now.Month(), now.Day(), now.Hour(), now.Minute(), 0, 0, a.loc).Add(time.Minute)
	if end.Before(a.hourStart.Add(time.Hour)) {
		ev.WindowEnd = end
	}
	a.resetToHour(now)
	return ev, true
}

func (a *Accumulator) snapshot(hourStart time.Time) event.UsageHour {
	ev := event.UsageHour{
		SchemaVersion: a.schemaVersion,
		ProbeVersion:  a.probeVersion,
		DeviceID:      a.deviceID,
		WindowStart:   hourStart,
		WindowEnd:     hourStart.Add(time.Hour),
		ActiveMinutes: len(a.active),
	}
	if a.resourceSamples > 0 {
		n := float64(a.resourceSamples)
		ev.CPUUtilAvgPct = round1(a.cpuSum / n)
		ev.MemUtilAvgPct = round1(a.memSum / n)
		ev.DiskFreeGB = round1(a.lastDiskGB)
	}
	if a.gpuSamples > 0 {
		v := round1(a.gpuSum / float64(a.gpuSamples))
		ev.GPUUtilAvgPct = &v
	}
	return ev
}

func round1(v float64) float64 {
	return float64(int(v*10+0.5)) / 10
}

func (a *Accumulator) Idle() time.Duration { return a.idle }

func (a *Accumulator) CurrentHourStart() time.Time { return a.hourStart }

func (a *Accumulator) ActiveMinuteCount() int { return len(a.active) }
