package schedule

import (
	"context"
	"time"

	"github.com/haowu0802/hope-metrics-platform/probe/internal/activity"
	"github.com/haowu0802/hope-metrics-platform/probe/internal/event"
	"github.com/haowu0802/hope-metrics-platform/probe/internal/logx"
	"github.com/haowu0802/hope-metrics-platform/probe/internal/sink"
	"github.com/haowu0802/hope-metrics-platform/probe/internal/window"
)

type Runner struct {
	Sampler      activity.Sampler
	Acc          *window.Accumulator
	Store        *sink.Store
	Log          *logx.Logger
	Loc          *time.Location
	SampleEvery  time.Duration
	UploadEvery  time.Duration
	CleanupEvery time.Duration
	CleanupAge   time.Duration
}

func (r *Runner) Run(ctx context.Context) error {
	if r.SampleEvery <= 0 {
		r.SampleEvery = time.Minute
	}
	if r.UploadEvery <= 0 {
		r.UploadEvery = 2 * time.Minute
	}
	if r.CleanupEvery <= 0 {
		r.CleanupEvery = 5 * time.Minute
	}
	if r.CleanupAge <= 0 {
		r.CleanupAge = 72 * time.Hour
	}

	sampleTick := time.NewTicker(r.SampleEvery)
	uploadTick := time.NewTicker(r.UploadEvery)
	cleanupTick := time.NewTicker(r.CleanupEvery)
	defer sampleTick.Stop()
	defer uploadTick.Stop()
	defer cleanupTick.Stop()

	r.Log.Infof("probe running sample_every=%s upload_every=%s cleanup_every=%s",
		r.SampleEvery, r.UploadEvery, r.CleanupEvery)
	r.sampleOnce()

	for {
		select {
		case <-ctx.Done():
			r.Log.Infof("shutting down; flushing current hour")
			r.flushShutdown()
			if n, err := r.Store.UploadPending(); err != nil {
				r.Log.Errorf("final upload: %v (uploaded=%d)", err, n)
			} else {
				r.Log.Infof("final upload ok count=%d", n)
			}
			return ctx.Err()
		case <-sampleTick.C:
			r.sampleOnce()
		case <-uploadTick.C:
			n, err := r.Store.UploadPending()
			if err != nil {
				r.Log.Errorf("upload: %v (uploaded=%d)", err, n)
			} else if n > 0 {
				r.Log.Infof("uploaded %d event(s)", n)
			} else {
				r.Log.Debugf("upload cycle: nothing pending or no URL")
			}
		case <-cleanupTick.C:
			n, err := r.Store.CleanupLocal(r.CleanupAge)
			if err != nil {
				r.Log.Errorf("cleanup: %v", err)
			} else {
				r.Log.Debugf("cleanup removed=%d", n)
			}
		}
	}
}

func (r *Runner) sampleOnce() {
	now := time.Now().In(r.Loc)
	age, err := r.Sampler.LastInputAge()
	if err != nil {
		r.Log.Errorf("last input: %v", err)
		return
	}
	active := activity.WasActive(age, r.Acc.Idle())
	r.Log.Debugf("sample now=%s last_input_age=%s active=%v hour=%s minutes_so_far=%d",
		now.Format(time.RFC3339), age.Round(time.Second), active,
		r.Acc.CurrentHourStart().Format(time.RFC3339), r.Acc.ActiveMinuteCount())

	if ev, ok := r.Acc.FlushClosedIfNeeded(now); ok {
		r.persist(ev)
	}
	r.Acc.Sample(now, age)
}

func (r *Runner) flushShutdown() {
	now := time.Now().In(r.Loc)
	ev, ok := r.Acc.ForceFlushCurrent(now)
	if !ok {
		return
	}
	r.persist(ev)
}

func (r *Runner) persist(ev event.UsageHour) {
	path, err := r.Store.WriteLocal(ev)
	if err != nil {
		r.Log.Errorf("write local: %v", err)
		return
	}
	r.Log.Infof("flushed hour start=%s end=%s active_minutes=%d file=%s",
		ev.WindowStart.Format(time.RFC3339),
		ev.WindowEnd.Format(time.RFC3339),
		ev.ActiveMinutes,
		path,
	)
}
