//go:build !windows

package sysmetrics

import "fmt"

// Sample is a stub for non-Windows builds (probe is Windows-only at runtime).
func (s *Sampler) Sample() (Snapshot, error) {
	return Snapshot{}, fmt.Errorf("sysmetrics: Windows only")
}

func (s *Sampler) closeGPU() {}
