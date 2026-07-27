//go:build !windows

package deviceid

import "fmt"

// Resolve is Windows-only in v1.
func Resolve() (string, error) {
	return "", fmt.Errorf("hope-probe v1 supports Windows only (MachineGuid device id)")
}
