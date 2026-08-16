//go:build windows

package sysmetrics

import (
	"fmt"
	"unsafe"

	"golang.org/x/sys/windows"
)

// Windows Performance Counters: \GPU Engine(*)\Utilization Percentage
// Works for GPUs that expose WDDM counters (no NVIDIA SDK required).

const (
	pdhFmtDouble   = 0x00000200
	pdhMoreData    = 0x800007D2
	pdhNoData      = 0x800007D5
	pdhInvalidData = 0xC0000BC6
)

var (
	modPdh                        = windows.NewLazySystemDLL("pdh.dll")
	procPdhOpenQueryW             = modPdh.NewProc("PdhOpenQueryW")
	procPdhAddEnglishCounterW     = modPdh.NewProc("PdhAddEnglishCounterW")
	procPdhCollectQueryData       = modPdh.NewProc("PdhCollectQueryData")
	procPdhGetFormattedCounterArrayW = modPdh.NewProc("PdhGetFormattedCounterArrayW")
	procPdhCloseQuery             = modPdh.NewProc("PdhCloseQuery")
)

// pdhFmtCounterValue matches PDH_FMT_COUNTERVALUE for PDH_FMT_DOUBLE (8-byte aligned union).
type pdhFmtCounterValue struct {
	CStatus     uint32
	_           uint32
	DoubleValue float64
}

type pdhFmtCounterValueItem struct {
	Name     *uint16
	FmtValue pdhFmtCounterValue
}

func (s *Sampler) ensurePDH() error {
	if s.gpuPDHFailed {
		return fmt.Errorf("pdh gpu previously failed")
	}
	if s.gpuPDHReady {
		return nil
	}
	var query uintptr
	r, _, e := procPdhOpenQueryW.Call(0, 0, uintptr(unsafe.Pointer(&query)))
	if r != 0 || query == 0 {
		s.gpuPDHFailed = true
		return fmt.Errorf("PdhOpenQueryW: %#x %v", r, e)
	}
	path, err := windows.UTF16PtrFromString(`\GPU Engine(*)\Utilization Percentage`)
	if err != nil {
		procPdhCloseQuery.Call(query)
		s.gpuPDHFailed = true
		return err
	}
	var counter uintptr
	r, _, e = procPdhAddEnglishCounterW.Call(query, uintptr(unsafe.Pointer(path)), 0, uintptr(unsafe.Pointer(&counter)))
	if r != 0 || counter == 0 {
		procPdhCloseQuery.Call(query)
		s.gpuPDHFailed = true
		return fmt.Errorf("PdhAddEnglishCounterW: %#x %v", r, e)
	}
	// First collect primes rate-based counters.
	procPdhCollectQueryData.Call(query)
	s.gpuPDHQuery = query
	s.gpuPDHCounter = counter
	s.gpuPDHReady = true
	return nil
}

func (s *Sampler) sampleGPUPDH() (*float64, error) {
	if err := s.ensurePDH(); err != nil {
		return nil, err
	}
	r, _, e := procPdhCollectQueryData.Call(s.gpuPDHQuery)
	if r != 0 {
		return nil, fmt.Errorf("PdhCollectQueryData: %#x %v", r, e)
	}

	var bufSize, itemCount uint32
	r, _, _ = procPdhGetFormattedCounterArrayW.Call(
		s.gpuPDHCounter,
		pdhFmtDouble,
		uintptr(unsafe.Pointer(&bufSize)),
		uintptr(unsafe.Pointer(&itemCount)),
		0,
	)
	if r != pdhMoreData && r != 0 {
		if r == pdhNoData || r == pdhInvalidData {
			return nil, fmt.Errorf("pdh no gpu data %#x", r)
		}
		return nil, fmt.Errorf("PdhGetFormattedCounterArrayW size: %#x", r)
	}
	if bufSize == 0 || itemCount == 0 {
		return nil, fmt.Errorf("pdh empty gpu counter array")
	}

	buf := make([]byte, bufSize)
	r, _, e = procPdhGetFormattedCounterArrayW.Call(
		s.gpuPDHCounter,
		pdhFmtDouble,
		uintptr(unsafe.Pointer(&bufSize)),
		uintptr(unsafe.Pointer(&itemCount)),
		uintptr(unsafe.Pointer(&buf[0])),
	)
	if r != 0 {
		return nil, fmt.Errorf("PdhGetFormattedCounterArrayW: %#x %v", r, e)
	}

	itemSize := unsafe.Sizeof(pdhFmtCounterValueItem{})
	var n int
	var max float64
	for i := uint32(0); i < itemCount; i++ {
		item := (*pdhFmtCounterValueItem)(unsafe.Pointer(&buf[uintptr(i)*itemSize]))
		if item.FmtValue.CStatus != 0 {
			continue
		}
		v := item.FmtValue.DoubleValue
		if v < 0 || v != v { // NaN
			continue
		}
		n++
		if v > max {
			max = v
		}
	}
	if n == 0 {
		return nil, fmt.Errorf("pdh: no valid gpu engine samples")
	}
	// Max across engines approximates "busiest engine" (Task Manager–like signal).
	// Average can be diluted by many idle copy/encode engines.
	out := clampPct(max)
	return &out, nil
}

func (s *Sampler) closePDH() {
	if s.gpuPDHQuery != 0 {
		procPdhCloseQuery.Call(s.gpuPDHQuery)
		s.gpuPDHQuery = 0
		s.gpuPDHCounter = 0
		s.gpuPDHReady = false
	}
}
