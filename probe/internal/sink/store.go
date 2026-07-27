package sink

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/haowu0802/hope-metrics-platform/probe/internal/event"
	"github.com/haowu0802/hope-metrics-platform/probe/internal/logx"
)

// Store writes events locally and uploads pending files.
type Store struct {
	outDir    string
	ingestURL string
	client    *http.Client
	log       *logx.Logger
}

func NewStore(outDir, ingestURL string, log *logx.Logger) (*Store, error) {
	pending := filepath.Join(outDir, "pending")
	if err := os.MkdirAll(pending, 0o755); err != nil {
		return nil, err
	}
	return &Store{
		outDir:    outDir,
		ingestURL: strings.TrimSpace(ingestURL),
		client:    &http.Client{Timeout: 30 * time.Second},
		log:       log,
	}, nil
}

func (s *Store) pendingDir() string {
	return filepath.Join(s.outDir, "pending")
}

// WriteLocal writes one event as its own JSON file under pending/.
func (s *Store) WriteLocal(ev event.UsageHour) (string, error) {
	name := fmt.Sprintf("%s_%s.json",
		ev.WindowStart.UTC().Format("20060102T150405Z"),
		sanitize(ev.DeviceID),
	)
	path := filepath.Join(s.pendingDir(), name)
	data, err := json.Marshal(ev)
	if err != nil {
		return "", err
	}
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return "", err
	}
	s.log.Debugf("wrote local event %s active_minutes=%d", path, ev.ActiveMinutes)
	return path, nil
}

func sanitize(id string) string {
	r := strings.NewReplacer(`/`, `_`, `\`, `_`, `:`, `_`, ` `, `_`)
	return r.Replace(id)
}

// UploadPending POSTs each pending file; deletes file on HTTP 2xx.
// If ingest URL is empty, skips upload and leaves files in place.
func (s *Store) UploadPending() (uploaded int, err error) {
	if s.ingestURL == "" {
		s.log.Debugf("ingest URL empty; skip upload")
		return 0, nil
	}
	entries, err := os.ReadDir(s.pendingDir())
	if err != nil {
		return 0, err
	}
	var firstErr error
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".json") {
			continue
		}
		path := filepath.Join(s.pendingDir(), e.Name())
		if err := s.uploadOne(path); err != nil {
			s.log.Errorf("upload %s: %v", path, err)
			if firstErr == nil {
				firstErr = err
			}
			continue
		}
		if err := os.Remove(path); err != nil {
			s.log.Errorf("remove after upload %s: %v", path, err)
			if firstErr == nil {
				firstErr = err
			}
			continue
		}
		uploaded++
		s.log.Debugf("uploaded and removed %s", path)
	}
	return uploaded, firstErr
}

func (s *Store) uploadOne(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	req, err := http.NewRequest(http.MethodPost, s.ingestURL, bytes.NewReader(data))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := s.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP %d: %s", resp.StatusCode, strings.TrimSpace(string(body)))
	}
	return nil
}

// CleanupLocal removes pending files older than maxAge when ingest URL is set
// (failed uploads that were never cleared). With no URL, local files are kept.
func (s *Store) CleanupLocal(maxAge time.Duration) (removed int, err error) {
	if s.ingestURL == "" {
		s.log.Debugf("cleanup: no ingest URL; keeping all local pending files")
		return 0, nil
	}
	entries, err := os.ReadDir(s.pendingDir())
	if err != nil {
		return 0, err
	}
	cutoff := time.Now().Add(-maxAge)
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".json") {
			continue
		}
		info, err := e.Info()
		if err != nil {
			continue
		}
		if info.ModTime().After(cutoff) {
			continue
		}
		path := filepath.Join(s.pendingDir(), e.Name())
		if err := os.Remove(path); err != nil {
			s.log.Errorf("cleanup %s: %v", path, err)
			continue
		}
		removed++
		s.log.Debugf("cleanup removed aged pending %s", path)
	}
	return removed, nil
}
