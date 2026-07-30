package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	_ "embed"

	"github.com/haowu0802/hope-metrics-platform/probe/internal/deviceid"
)

//go:embed probe.build.env
var embeddedBuildEnv string

// Set via -ldflags from build.ps1 (optional; embed is enough if file is synced).
var (
	buildIngestURL string
	buildOutDir    string
	buildTimezone  string
	buildIdleSec   string
)

const (
	DefaultIdleSeconds   = 600 // 10 minutes
	DefaultProbeVersion  = "0.1.0"
	DefaultSchemaVersion = "1"
	DefaultOutDir        = "out"
	DefaultFlushEvery    = time.Minute
	DefaultUploadEvery   = 2 * time.Minute
	DefaultCleanupEvery  = 5 * time.Minute
)

type Config struct {
	DeviceID      string // Windows MachineGuid
	IdleSeconds   int
	OutDir        string
	IngestURL     string
	Timezone      string
	Location      *time.Location
	ProbeVersion  string
	SchemaVersion string
	Debug         bool
	UploadEvery   time.Duration
	CleanupEvery  time.Duration
}

func FromFlagsAndEnv(debug bool, outDir, ingestURL, tz string, idleSeconds int) (Config, error) {
	deviceID, err := deviceid.Resolve()
	if err != nil {
		return Config{}, err
	}

	baked := parseBuildEnv(embeddedBuildEnv)
	if buildIngestURL != "" {
		baked["HOPE_INGEST_URL"] = buildIngestURL
	}
	if buildOutDir != "" {
		baked["HOPE_OUT_DIR"] = buildOutDir
	}
	if buildTimezone != "" {
		baked["HOPE_TZ"] = buildTimezone
	}
	if buildIdleSec != "" {
		baked["HOPE_IDLE_SECONDS"] = buildIdleSec
	}

	cfg := Config{
		DeviceID: deviceID,
		OutDir: firstNonEmpty(
			outDir,
			os.Getenv("HOPE_OUT_DIR"),
			baked["HOPE_OUT_DIR"],
			DefaultOutDir,
		),
		IngestURL: firstNonEmpty(
			ingestURL,
			os.Getenv("HOPE_INGEST_URL"),
			baked["HOPE_INGEST_URL"],
		),
		Timezone: firstNonEmpty(
			tz,
			os.Getenv("HOPE_TZ"),
			baked["HOPE_TZ"],
			"Local",
		),
		ProbeVersion:  firstNonEmpty(os.Getenv("HOPE_PROBE_VERSION"), DefaultProbeVersion),
		SchemaVersion: DefaultSchemaVersion,
		Debug:         debug,
		UploadEvery:   DefaultUploadEvery,
		CleanupEvery:  DefaultCleanupEvery,
		IdleSeconds:   idleSeconds,
	}

	if cfg.IdleSeconds <= 0 {
		if v := os.Getenv("HOPE_IDLE_SECONDS"); v != "" {
			n, err := strconv.Atoi(v)
			if err != nil {
				return Config{}, fmt.Errorf("HOPE_IDLE_SECONDS: %w", err)
			}
			cfg.IdleSeconds = n
		} else if v := baked["HOPE_IDLE_SECONDS"]; v != "" {
			n, err := strconv.Atoi(v)
			if err != nil {
				return Config{}, fmt.Errorf("build HOPE_IDLE_SECONDS: %w", err)
			}
			cfg.IdleSeconds = n
		} else {
			cfg.IdleSeconds = DefaultIdleSeconds
		}
	}

	loc, err := loadLocation(cfg.Timezone)
	if err != nil {
		return Config{}, err
	}
	cfg.Location = loc
	return cfg, nil
}

func parseBuildEnv(raw string) map[string]string {
	out := map[string]string{}
	for _, line := range strings.Split(raw, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		key, val, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		key = strings.TrimSpace(key)
		val = strings.TrimSpace(val)
		val = strings.Trim(val, `"'`)
		if key != "" {
			out[key] = val
		}
	}
	return out
}

func loadLocation(name string) (*time.Location, error) {
	if name == "" || strings.EqualFold(name, "local") {
		return time.Local, nil
	}
	return time.LoadLocation(name)
}

func firstNonEmpty(vals ...string) string {
	for _, v := range vals {
		if strings.TrimSpace(v) != "" {
			return strings.TrimSpace(v)
		}
	}
	return ""
}
