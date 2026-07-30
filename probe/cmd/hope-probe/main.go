package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/haowu0802/hope-metrics-platform/probe/internal/activity"
	"github.com/haowu0802/hope-metrics-platform/probe/internal/config"
	"github.com/haowu0802/hope-metrics-platform/probe/internal/logx"
	"github.com/haowu0802/hope-metrics-platform/probe/internal/schedule"
	"github.com/haowu0802/hope-metrics-platform/probe/internal/sink"
	"github.com/haowu0802/hope-metrics-platform/probe/internal/window"
)

func main() {
	debug := flag.Bool("debug", false, "print detailed debug logs to the console")
	outDir := flag.String("out-dir", "", "local output directory (or HOPE_OUT_DIR)")
	ingestURL := flag.String("ingest-url", "", "ingest POST URL (overrides env / build defaults)")
	tz := flag.String("tz", "", "IANA timezone or Local (or HOPE_TZ)")
	idleSeconds := flag.Int("idle-seconds", 0, "idle threshold seconds (default 600 / 10m)")
	sampleEvery := flag.Duration("sample-every", time.Minute, "how often to sample last-input")
	flag.Parse()

	cfg, err := config.FromFlagsAndEnv(*debug, *outDir, *ingestURL, *tz, *idleSeconds)
	if err != nil {
		fmt.Fprintf(os.Stderr, "config: %v\n", err)
		os.Exit(2)
	}

	log := logx.New(cfg.Debug)
	log.Infof("hope-probe starting probe_version=%s schema_version=%s device_id=%s (MachineGuid) idle=%ds out_dir=%s ingest_url=%s debug=%v tz=%s",
		cfg.ProbeVersion, cfg.SchemaVersion, cfg.DeviceID, cfg.IdleSeconds, cfg.OutDir, cfg.IngestURL, cfg.Debug, cfg.Timezone)
	log.Debugf("resolved location=%s upload_every=%s cleanup_every=%s",
		cfg.Location.String(), cfg.UploadEvery, cfg.CleanupEvery)

	store, err := sink.NewStore(cfg.OutDir, cfg.IngestURL, log)
	if err != nil {
		log.Errorf("store: %v", err)
		os.Exit(1)
	}

	acc := window.NewAccumulator(
		cfg.Location,
		cfg.DeviceID,
		cfg.ProbeVersion,
		cfg.SchemaVersion,
		time.Duration(cfg.IdleSeconds)*time.Second,
	)

	runner := &schedule.Runner{
		Sampler:      activity.New(),
		Acc:          acc,
		Store:        store,
		Log:          log,
		Loc:          cfg.Location,
		SampleEvery:  *sampleEvery,
		UploadEvery:  cfg.UploadEvery,
		CleanupEvery: cfg.CleanupEvery,
		CleanupAge:   72 * time.Hour,
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	if err := runner.Run(ctx); err != nil && err != context.Canceled {
		log.Errorf("run: %v", err)
		os.Exit(1)
	}
	log.Infof("hope-probe stopped")
}
