package sysmetrics

// Snapshot is one resource sample (percentages 0–100).
type Snapshot struct {
	CPUUtilPct float64
	MemUtilPct float64
	DiskFreeGB float64
	// GPUUtilPct is nil when no readable GPU counter.
	GPUUtilPct *float64
}

// Sampler reads system resource metrics. Platform-specific files implement Sample.
type Sampler struct {
	prevIdle  uint64
	prevTotal uint64
	havePrev  bool

	// Windows GPU state (PDH / NVML). Ignored on non-Windows.
	gpuPDHQuery   uintptr
	gpuPDHCounter uintptr
	gpuPDHReady   bool
	gpuPDHFailed  bool
	gpuNVMLReady  bool
	gpuNVMLBad    bool
	gpuSMIBad     bool
}

// Close releases GPU query handles (Windows). Safe to call multiple times.
func (s *Sampler) Close() {
	s.closeGPU()
}

func clampPct(v float64) float64 {
	if v < 0 {
		return 0
	}
	if v > 100 {
		return 100
	}
	return v
}
