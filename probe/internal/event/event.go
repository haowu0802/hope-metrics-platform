package event

import "time"

// UsageHour is one closed hour window of device activity (contract v1).
type UsageHour struct {
	SchemaVersion string    `json:"schema_version"`
	ProbeVersion  string    `json:"probe_version"`
	DeviceID      string    `json:"device_id"`
	WindowStart   time.Time `json:"window_start"`
	WindowEnd     time.Time `json:"window_end"`
	ActiveMinutes int       `json:"active_minutes"`
}
