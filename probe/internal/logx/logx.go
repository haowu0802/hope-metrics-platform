package logx

import (
	"log"
	"os"
)

type Logger struct {
	debug bool
	std   *log.Logger
}

func New(debug bool) *Logger {
	return &Logger{
		debug: debug,
		std:   log.New(os.Stdout, "", log.LstdFlags|log.Lmsgprefix),
	}
}

func (l *Logger) Infof(format string, args ...any) {
	l.std.Printf("[INFO] "+format, args...)
}

func (l *Logger) Errorf(format string, args ...any) {
	l.std.Printf("[ERROR] "+format, args...)
}

func (l *Logger) Debugf(format string, args ...any) {
	if !l.debug {
		return
	}
	l.std.Printf("[DEBUG] "+format, args...)
}
