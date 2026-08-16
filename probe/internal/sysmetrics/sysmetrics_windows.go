//go:build windows

package sysmetrics

import (
	"fmt"
	"unsafe"

	"golang.org/x/sys/windows"
)

var (
	modKernel32              = windows.NewLazySystemDLL("kernel32.dll")
	procGetSystemTimes       = modKernel32.NewProc("GetSystemTimes")
	procGlobalMemoryStatusEx = modKernel32.NewProc("GlobalMemoryStatusEx")
	procGetDiskFreeSpaceExW  = modKernel32.NewProc("GetDiskFreeSpaceExW")
)

type memoryStatusEx struct {
	Length               uint32
	MemoryLoad           uint32
	TotalPhys            uint64
	AvailPhys            uint64
	TotalPageFile        uint64
	AvailPageFile        uint64
	TotalVirtual         uint64
	AvailVirtual         uint64
	AvailExtendedVirtual uint64
}

// Sample returns CPU/mem/disk and GPU when a counter is available
// (NVML → PDH GPU Engine → nvidia-smi). GPU stays nil if none work.
func (s *Sampler) Sample() (Snapshot, error) {
	cpu, err := s.sampleCPU()
	if err != nil {
		return Snapshot{}, err
	}
	mem, err := sampleMem()
	if err != nil {
		return Snapshot{}, err
	}
	disk, err := sampleDiskFreeGB()
	if err != nil {
		return Snapshot{}, err
	}
	return Snapshot{
		CPUUtilPct: cpu,
		MemUtilPct: mem,
		DiskFreeGB: disk,
		GPUUtilPct: s.sampleGPU(),
	}, nil
}

func (s *Sampler) sampleGPU() *float64 {
	if v, err := s.sampleGPUNVML(); err == nil && v != nil {
		return v
	}
	if v, err := s.sampleGPUPDH(); err == nil && v != nil {
		return v
	}
	if !s.gpuSMIBad {
		if v, err := sampleGPUNvidiaSMI(); err == nil && v != nil {
			return v
		}
		s.gpuSMIBad = true
	}
	return nil
}

func (s *Sampler) closeGPU() {
	s.closePDH()
	s.closeNVML()
}

func (s *Sampler) sampleCPU() (float64, error) {
	var idle, kernel, user windows.Filetime
	r1, _, e1 := procGetSystemTimes.Call(
		uintptr(unsafe.Pointer(&idle)),
		uintptr(unsafe.Pointer(&kernel)),
		uintptr(unsafe.Pointer(&user)),
	)
	if r1 == 0 {
		return 0, fmt.Errorf("GetSystemTimes: %w", e1)
	}
	idleU := filetimeToUint64(idle)
	// Kernel includes idle time on Windows.
	totalU := filetimeToUint64(kernel) + filetimeToUint64(user)
	if !s.havePrev {
		s.prevIdle = idleU
		s.prevTotal = totalU
		s.havePrev = true
		return 0, nil
	}
	idleDelta := idleU - s.prevIdle
	totalDelta := totalU - s.prevTotal
	s.prevIdle = idleU
	s.prevTotal = totalU
	if totalDelta == 0 {
		return 0, nil
	}
	busy := 1.0 - float64(idleDelta)/float64(totalDelta)
	if busy < 0 {
		busy = 0
	}
	if busy > 1 {
		busy = 1
	}
	return busy * 100, nil
}

func filetimeToUint64(ft windows.Filetime) uint64 {
	return (uint64(ft.HighDateTime) << 32) | uint64(ft.LowDateTime)
}

func sampleMem() (float64, error) {
	var st memoryStatusEx
	st.Length = uint32(unsafe.Sizeof(st))
	r1, _, e1 := procGlobalMemoryStatusEx.Call(uintptr(unsafe.Pointer(&st)))
	if r1 == 0 {
		return 0, fmt.Errorf("GlobalMemoryStatusEx: %w", e1)
	}
	return float64(st.MemoryLoad), nil
}

func sampleDiskFreeGB() (float64, error) {
	var freeBytesAvailable, totalBytes, totalFreeBytes uint64
	path, err := windows.UTF16PtrFromString(`C:\`)
	if err != nil {
		return 0, err
	}
	r1, _, e1 := procGetDiskFreeSpaceExW.Call(
		uintptr(unsafe.Pointer(path)),
		uintptr(unsafe.Pointer(&freeBytesAvailable)),
		uintptr(unsafe.Pointer(&totalBytes)),
		uintptr(unsafe.Pointer(&totalFreeBytes)),
	)
	if r1 == 0 {
		return 0, fmt.Errorf("GetDiskFreeSpaceExW: %w", e1)
	}
	return float64(freeBytesAvailable) / (1024 * 1024 * 1024), nil
}
