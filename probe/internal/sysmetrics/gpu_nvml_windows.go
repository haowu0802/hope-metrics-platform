//go:build windows

package sysmetrics

import (
	"fmt"
	"unsafe"

	"golang.org/x/sys/windows"
)

// Optional NVIDIA NVML (nvml.dll from the driver). No compile-time CUDA SDK needed.

const (
	nvmlSuccess = 0
)

type nvmlUtilization struct {
	GPU    uint32
	Memory uint32
}

var (
	modNVML                     *windows.LazyDLL
	procNVMLInit                *windows.LazyProc
	procNVMLShutdown            *windows.LazyProc
	procNVMLDeviceGetCount      *windows.LazyProc
	procNVMLDeviceGetHandle     *windows.LazyProc
	procNVMLDeviceGetUtilization *windows.LazyProc
)

func loadNVML() bool {
	if modNVML != nil {
		return procNVMLInit != nil
	}
	modNVML = windows.NewLazyDLL("nvml.dll")
	if err := modNVML.Load(); err != nil {
		// Also try Program Files path via PATH; LazyDLL already searches system dirs.
		modNVML = nil
		return false
	}
	procNVMLInit = modNVML.NewProc("nvmlInit_v2")
	if procNVMLInit.Find() != nil {
		procNVMLInit = modNVML.NewProc("nvmlInit")
	}
	procNVMLShutdown = modNVML.NewProc("nvmlShutdown")
	procNVMLDeviceGetCount = modNVML.NewProc("nvmlDeviceGetCount_v2")
	if procNVMLDeviceGetCount.Find() != nil {
		procNVMLDeviceGetCount = modNVML.NewProc("nvmlDeviceGetCount")
	}
	procNVMLDeviceGetHandle = modNVML.NewProc("nvmlDeviceGetHandleByIndex_v2")
	if procNVMLDeviceGetHandle.Find() != nil {
		procNVMLDeviceGetHandle = modNVML.NewProc("nvmlDeviceGetHandleByIndex")
	}
	procNVMLDeviceGetUtilization = modNVML.NewProc("nvmlDeviceGetUtilizationRates")
	if procNVMLInit.Find() != nil || procNVMLDeviceGetCount.Find() != nil ||
		procNVMLDeviceGetHandle.Find() != nil || procNVMLDeviceGetUtilization.Find() != nil {
		modNVML = nil
		return false
	}
	return true
}

func (s *Sampler) sampleGPUNVML() (*float64, error) {
	if s.gpuNVMLBad {
		return nil, fmt.Errorf("nvml unavailable")
	}
	if !loadNVML() {
		s.gpuNVMLBad = true
		return nil, fmt.Errorf("nvml.dll not found")
	}
	if !s.gpuNVMLReady {
		r, _, _ := procNVMLInit.Call()
		if r != nvmlSuccess {
			s.gpuNVMLBad = true
			return nil, fmt.Errorf("nvmlInit status=%d", r)
		}
		s.gpuNVMLReady = true
	}

	var count uint32
	r, _, _ := procNVMLDeviceGetCount.Call(uintptr(unsafe.Pointer(&count)))
	if r != nvmlSuccess || count == 0 {
		return nil, fmt.Errorf("nvmlDeviceGetCount status=%d count=%d", r, count)
	}

	var sum float64
	var n int
	for i := uint32(0); i < count; i++ {
		var handle uintptr
		r, _, _ = procNVMLDeviceGetHandle.Call(uintptr(i), uintptr(unsafe.Pointer(&handle)))
		if r != nvmlSuccess || handle == 0 {
			continue
		}
		var util nvmlUtilization
		r, _, _ = procNVMLDeviceGetUtilization.Call(handle, uintptr(unsafe.Pointer(&util)))
		if r != nvmlSuccess {
			continue
		}
		sum += float64(util.GPU)
		n++
	}
	if n == 0 {
		return nil, fmt.Errorf("nvml: no device utilization")
	}
	v := clampPct(sum / float64(n))
	return &v, nil
}

func (s *Sampler) closeNVML() {
	if s.gpuNVMLReady && procNVMLShutdown != nil {
		procNVMLShutdown.Call()
		s.gpuNVMLReady = false
	}
}
