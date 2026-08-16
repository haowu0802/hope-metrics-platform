package event

import "time"

// UsageHour is one closed hour window of device activity (contract v2).
// Resource fields use pointers so JSON null / omit works for GPU.
type UsageHour struct {
	SchemaVersion  string    `json:"schema_version"`
	ProbeVersion   string    `json:"probe_version"`
	DeviceID       string    `json:"device_id"`
	WindowStart    time.Time `json:"window_start"`
	WindowEnd      time.Time `json:"window_end"`
	ActiveMinutes  int       `json:"active_minutes"`
	CPUUtilAvgPct  float64   `json:"cpu_util_avg_pct"`
	GPUUtilAvgPct  *float64  `json:"gpu_util_avg_pct"`
	MemUtilAvgPct  float64   `json:"mem_util_avg_pct"`
	DiskFreeGB     float64   `json:"disk_free_gb"`
}
