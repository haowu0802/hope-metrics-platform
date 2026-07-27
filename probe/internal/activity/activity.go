package activity

import "time"

// Sampler reports how long since the last user input.
type Sampler interface {
	// LastInputAge returns duration since last keyboard/mouse input.
	LastInputAge() (time.Duration, error)
}

// WasActive returns true if last input was within idleThreshold.
func WasActive(age, idleThreshold time.Duration) bool {
	return age < idleThreshold
}
