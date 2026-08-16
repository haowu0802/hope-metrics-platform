//go:build windows

package sysmetrics

import (
	"fmt"
	"testing"
)

func TestSampleGPUSmoke(t *testing.T) {
	s := &Sampler{}
	defer s.Close()
	// Prime CPU delta + GPU backends.
	if _, err := s.Sample(); err != nil {
		t.Fatal(err)
	}
	snap, err := s.Sample()
	if err != nil {
		t.Fatal(err)
	}
	gpu := "null"
	if snap.GPUUtilPct != nil {
		gpu = fmt.Sprintf("%.1f", *snap.GPUUtilPct)
	}
	t.Logf("cpu=%.1f mem=%.1f disk=%.1f gpu=%s", snap.CPUUtilPct, snap.MemUtilPct, snap.DiskFreeGB, gpu)
	// GPU may legitimately be nil on machines without counters; just ensure Sample works.
}
