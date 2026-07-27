//go:build !windows

package activity

import (
	"sync"
	"time"
)

// StubSampler always reports "just now" so non-Windows builds can compile.
// Not for production donated devices.
type StubSampler struct {
	mu   sync.Mutex
	last time.Time
}

func New() Sampler {
	return &StubSampler{last: time.Now()}
}

func (s *StubSampler) LastInputAge() (time.Duration, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.last.IsZero() {
		s.last = time.Now()
	}
	return time.Since(s.last), nil
}
