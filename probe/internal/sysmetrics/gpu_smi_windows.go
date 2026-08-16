//go:build windows

package sysmetrics

import (
	"bytes"
	"context"
	"fmt"
	"os/exec"
	"strconv"
	"strings"
	"time"
)

// nvidia-smi CLI fallback when NVML DLL binding fails but the tool is on PATH.
func sampleGPUNvidiaSMI() (*float64, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, "nvidia-smi",
		"--query-gpu=utilization.gpu",
		"--format=csv,noheader,nounits",
	)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("nvidia-smi: %w (%s)", err, strings.TrimSpace(stderr.String()))
	}
	lines := strings.Split(strings.TrimSpace(stdout.String()), "\n")
	var sum float64
	var n int
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		// Sometimes "N/A"
		if strings.EqualFold(line, "N/A") || strings.EqualFold(line, "[N/A]") {
			continue
		}
		v, err := strconv.ParseFloat(line, 64)
		if err != nil {
			continue
		}
		sum += v
		n++
	}
	if n == 0 {
		return nil, fmt.Errorf("nvidia-smi: no numeric utilization")
	}
	out := clampPct(sum / float64(n))
	return &out, nil
}
