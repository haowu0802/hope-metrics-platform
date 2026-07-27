//go:build windows

package activity

import (
	"fmt"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
)

var (
	user32           = windows.NewLazySystemDLL("user32.dll")
	kernel32         = windows.NewLazySystemDLL("kernel32.dll")
	procGetLastInput = user32.NewProc("GetLastInputInfo")
	procGetTickCount = kernel32.NewProc("GetTickCount")
)

type lastInputInfo struct {
	cbSize uint32
	dwTime uint32
}

// WindowsSampler uses GetLastInputInfo (no key contents).
type WindowsSampler struct{}

func New() Sampler {
	return WindowsSampler{}
}

func (WindowsSampler) LastInputAge() (time.Duration, error) {
	info := lastInputInfo{cbSize: uint32(unsafe.Sizeof(lastInputInfo{}))}
	r1, _, err := procGetLastInput.Call(uintptr(unsafe.Pointer(&info)))
	if r1 == 0 {
		return 0, fmt.Errorf("GetLastInputInfo: %w", err)
	}
	tick, _, _ := procGetTickCount.Call()
	now := uint32(tick)
	elapsed := now - info.dwTime // uint32 wrap-safe subtraction
	return time.Duration(elapsed) * time.Millisecond, nil
}
