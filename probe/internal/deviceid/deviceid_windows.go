//go:build windows

package deviceid

import (
	"fmt"
	"strings"

	"golang.org/x/sys/windows/registry"
)

// Resolve returns this machine's Windows MachineGuid.
func Resolve() (id string, err error) {
	k, err := registry.OpenKey(registry.LOCAL_MACHINE, `SOFTWARE\Microsoft\Cryptography`, registry.QUERY_VALUE|registry.WOW64_64KEY)
	if err != nil {
		return "", fmt.Errorf("open MachineGuid key: %w", err)
	}
	defer k.Close()

	guid, _, err := k.GetStringValue("MachineGuid")
	if err != nil {
		return "", fmt.Errorf("read MachineGuid: %w", err)
	}
	guid = strings.TrimSpace(strings.ToLower(guid))
	if guid == "" {
		return "", fmt.Errorf("MachineGuid is empty")
	}
	return guid, nil
}
