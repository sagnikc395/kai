package tui

import (
	"context"
	"fmt"
	"io"
	"strings"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	groq "github.com/conneroisu/groq-go"
	groqtools "github.com/conneroisu/groq-go/pkg/tools"
	"github.com/sagnikc395/kai/internal/core"
)

type entryRole int

const (
	roleUser entryRole = iota
	roleAssistant
	roleTool
	roleError
)

type transcriptEntry struct {
	role    entryRole
	content string
}

type model struct {
	ctx          context.Context
	cancel       context.CancelFunc
	conversation *core.Conversation
	modelName    groq.ChatModel
	events       chan streamMsg

	width        int
	height       int
	input        []rune
	cursor       int
	scrollOffset int
	busy         bool
	status       string
	entries      []transcriptEntry
}

type streamMsg struct {
	token       string
	toolCalls   []groqtools.ToolCall
	toolResults []core.ToolExecutionResult
	err         error
	done        bool
}

var (
	headerStyle = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("99"))
	mutedStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("245"))
	userStyle   = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("81"))
	kaiStyle    = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("99"))
	toolStyle   = lipgloss.NewStyle().Foreground(lipgloss.Color("214"))
	errorStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("203"))
	inputStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("252"))
)

func Run(ctx context.Context, client *groq.Client, modelName groq.ChatModel, input io.Reader, output io.Writer) error {
	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	p := tea.NewProgram(newModel(runCtx, cancel, client, modelName), tea.WithContext(runCtx), tea.WithInput(input), tea.WithOutput(output))
	_, err := p.Run()
	return err
}

func newModel(ctx context.Context, cancel context.CancelFunc, client *groq.Client, modelName groq.ChatModel) model {
	return model{
		ctx:          ctx,
		cancel:       cancel,
		conversation: core.NewConversation(client, modelName),
		modelName:    modelName,
		events:       make(chan streamMsg, 128),
		status:       "Ready",
	}
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		return m, nil
	case tea.KeyPressMsg:
		return m.handleKey(msg)
	case streamMsg:
		return m.handleStream(msg)
	}
	return m, nil
}

func (m model) View() tea.View {
	v := tea.NewView(m.render())
	v.AltScreen = true
	v.WindowTitle = "kai"
	return v
}

func (m model) handleKey(msg tea.KeyPressMsg) (tea.Model, tea.Cmd) {
	key := msg.Key()

	switch msg.String() {
	case "ctrl+c", "esc":
		m.cancel()
		return m, tea.Quit
	case "enter":
		if m.busy {
			return m, nil
		}
		message := strings.TrimSpace(string(m.input))
		if message == "" {
			return m, nil
		}
		switch strings.ToLower(message) {
		case "exit", "quit", "/exit", "/quit":
			m.cancel()
			return m, tea.Quit
		}
		m.input = nil
		m.cursor = 0
		m.scrollOffset = 0
		m.busy = true
		m.status = "Thinking"
		m.entries = append(m.entries,
			transcriptEntry{role: roleUser, content: message},
			transcriptEntry{role: roleAssistant},
		)
		return m, tea.Batch(runAssistant(m.ctx, m.conversation, message, m.events), waitForStream(m.ctx, m.events))
	case "backspace", "ctrl+h":
		if m.busy || m.cursor == 0 {
			return m, nil
		}
		m.input = append(m.input[:m.cursor-1], m.input[m.cursor:]...)
		m.cursor--
		return m, nil
	case "delete":
		if m.busy || m.cursor >= len(m.input) {
			return m, nil
		}
		m.input = append(m.input[:m.cursor], m.input[m.cursor+1:]...)
		return m, nil
	case "left":
		if !m.busy && m.cursor > 0 {
			m.cursor--
		}
		return m, nil
	case "right":
		if !m.busy && m.cursor < len(m.input) {
			m.cursor++
		}
		return m, nil
	case "home", "ctrl+a":
		if !m.busy {
			m.cursor = 0
		}
		return m, nil
	case "end", "ctrl+e":
		if !m.busy {
			m.cursor = len(m.input)
		}
		return m, nil
	case "ctrl+u":
		if !m.busy {
			m.input = nil
			m.cursor = 0
		}
		return m, nil
	case "pgup":
		m.scrollOffset += max(1, m.height/2)
		return m, nil
	case "pgdown":
		m.scrollOffset -= max(1, m.height/2)
		if m.scrollOffset < 0 {
			m.scrollOffset = 0
		}
		return m, nil
	}

	if m.busy || key.Text == "" {
		return m, nil
	}
	m.input = append(m.input[:m.cursor], append([]rune(key.Text), m.input[m.cursor:]...)...)
	m.cursor += len([]rune(key.Text))
	return m, nil
}

func (m model) handleStream(msg streamMsg) (tea.Model, tea.Cmd) {
	if msg.err != nil {
		m.busy = false
		m.status = "Error"
		m.entries = append(m.entries, transcriptEntry{role: roleError, content: msg.err.Error()})
		return m, waitForStream(m.ctx, m.events)
	}
	if msg.token != "" {
		m.status = "Streaming"
		m.appendAssistantToken(msg.token)
		return m, waitForStream(m.ctx, m.events)
	}
	if len(msg.toolCalls) > 0 {
		m.status = "Running tools"
		m.entries = append(m.entries, transcriptEntry{role: roleTool, content: fmt.Sprintf("Executing %d tool call(s)...", len(msg.toolCalls))})
		return m, waitForStream(m.ctx, m.events)
	}
	if len(msg.toolResults) > 0 {
		m.status = "Tools complete"
		m.entries = append(m.entries, transcriptEntry{role: roleTool, content: renderToolResults(msg.toolResults)})
		return m, waitForStream(m.ctx, m.events)
	}
	if msg.done {
		m.busy = false
		m.status = "Ready"
		m.dropTrailingEmptyAssistant()
		return m, nil
	}
	return m, waitForStream(m.ctx, m.events)
}

func (m *model) appendAssistantToken(token string) {
	if len(m.entries) == 0 || m.entries[len(m.entries)-1].role != roleAssistant {
		m.entries = append(m.entries, transcriptEntry{role: roleAssistant})
	}
	m.entries[len(m.entries)-1].content += token
}

func (m *model) dropTrailingEmptyAssistant() {
	if len(m.entries) == 0 {
		return
	}
	last := m.entries[len(m.entries)-1]
	if last.role == roleAssistant && strings.TrimSpace(last.content) == "" {
		m.entries = m.entries[:len(m.entries)-1]
	}
}

func runAssistant(ctx context.Context, conversation *core.Conversation, message string, events chan<- streamMsg) tea.Cmd {
	return func() tea.Msg {
		emit := func(msg streamMsg) {
			select {
			case events <- msg:
			case <-ctx.Done():
			}
		}

		conversation.Send(ctx, message, core.MessageLoopCallbacks{
			OnToken: func(token string) {
				emit(streamMsg{token: token})
			},
			OnToolStart: func(toolCalls []groqtools.ToolCall) {
				emit(streamMsg{toolCalls: toolCalls})
			},
			OnToolResult: func(results []core.ToolExecutionResult) {
				emit(streamMsg{toolResults: results})
			},
			OnError: func(err error) {
				emit(streamMsg{err: err})
			},
		})
		emit(streamMsg{done: true})
		return nil
	}
}

func waitForStream(ctx context.Context, events <-chan streamMsg) tea.Cmd {
	return func() tea.Msg {
		select {
		case msg := <-events:
			return msg
		case <-ctx.Done():
			return nil
		}
	}
}

func renderToolResults(results []core.ToolExecutionResult) string {
	var blocks []string
	for _, result := range results {
		status := "done"
		if result.Result.IsError {
			status = "error"
		}
		lines := []string{fmt.Sprintf("+ %s", result.CallSummary)}
		for _, line := range strings.Split(result.ResultSummary, "\n") {
			lines = append(lines, fmt.Sprintf("| %s", line))
		}
		lines = append(lines, fmt.Sprintf("+ %s", status))
		blocks = append(blocks, strings.Join(lines, "\n"))
	}
	return strings.Join(blocks, "\n")
}

func (m model) render() string {
	width := m.width
	height := m.height
	if width <= 0 {
		width = 80
	}
	if height <= 0 {
		height = 24
	}

	header := headerStyle.Render("kai") + mutedStyle.Render("  "+string(m.modelName))
	footer := m.renderFooter(width)
	viewportHeight := max(1, height-lipgloss.Height(header)-lipgloss.Height(footer)-1)
	transcript := m.renderTranscript(width, viewportHeight)

	return strings.Join([]string{
		padRight(header, width),
		transcript,
		footer,
	}, "\n")
}

func (m model) renderFooter(width int) string {
	status := mutedStyle.Render(m.status)
	prompt := "> "
	input := string(m.input)
	if m.busy {
		input = "waiting for response..."
	} else {
		input = withCursor(m.input, m.cursor)
	}
	lineWidth := max(1, width-lipgloss.Width(prompt))
	line := inputStyle.Width(lineWidth).Render(trimToWidth(input, lineWidth))
	return strings.Join([]string{
		padRight(status, width),
		prompt + line,
	}, "\n")
}

func (m model) renderTranscript(width int, height int) string {
	lines := make([]string, 0, height)
	contentWidth := max(12, width-8)
	for _, entry := range m.entries {
		prefix, style := entryPrefix(entry.role)
		wrapped := wrapText(entry.content, contentWidth)
		if len(wrapped) == 0 {
			wrapped = []string{""}
		}
		for index, line := range wrapped {
			if index == 0 {
				lines = append(lines, prefix+" "+style.Render(line))
			} else {
				lines = append(lines, strings.Repeat(" ", lipgloss.Width(prefix)+1)+style.Render(line))
			}
		}
		lines = append(lines, "")
	}
	if len(lines) > 0 && lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1]
	}

	if len(lines) > height {
		maxOffset := len(lines) - height
		offset := min(m.scrollOffset, maxOffset)
		start := maxOffset - offset
		lines = lines[start : start+height]
	}

	for len(lines) < height {
		lines = append(lines, "")
	}
	for i, line := range lines {
		lines[i] = padRight(line, width)
	}
	return strings.Join(lines, "\n")
}

func entryPrefix(role entryRole) (string, lipgloss.Style) {
	switch role {
	case roleUser:
		return userStyle.Render("you"), inputStyle
	case roleTool:
		return toolStyle.Render("tool"), toolStyle
	case roleError:
		return errorStyle.Render("error"), errorStyle
	default:
		return kaiStyle.Render("kai"), inputStyle
	}
}

func withCursor(input []rune, cursor int) string {
	if cursor < 0 {
		cursor = 0
	}
	if cursor > len(input) {
		cursor = len(input)
	}
	before := string(input[:cursor])
	after := string(input[cursor:])
	return before + "|" + after
}

func wrapText(text string, width int) []string {
	if strings.TrimSpace(text) == "" {
		return nil
	}

	var lines []string
	for _, raw := range strings.Split(text, "\n") {
		if raw == "" {
			lines = append(lines, "")
			continue
		}
		words := strings.Fields(raw)
		if len(words) == 0 {
			lines = append(lines, "")
			continue
		}
		current := ""
		for _, word := range words {
			if lipgloss.Width(word) > width {
				if current != "" {
					lines = append(lines, current)
					current = ""
				}
				chunks := splitLongWord(word, width)
				lines = append(lines, chunks[:len(chunks)-1]...)
				current = chunks[len(chunks)-1]
				continue
			}
			next := word
			if current != "" {
				next = current + " " + word
			}
			if lipgloss.Width(next) > width {
				lines = append(lines, current)
				current = word
			} else {
				current = next
			}
		}
		if current != "" {
			lines = append(lines, current)
		}
	}
	return lines
}

func splitLongWord(word string, width int) []string {
	if width <= 0 {
		return []string{word}
	}
	var chunks []string
	var current []rune
	for _, r := range word {
		next := string(append(current, r))
		if lipgloss.Width(next) > width && len(current) > 0 {
			chunks = append(chunks, string(current))
			current = []rune{r}
			continue
		}
		current = append(current, r)
	}
	if len(current) > 0 {
		chunks = append(chunks, string(current))
	}
	return chunks
}

func trimToWidth(text string, width int) string {
	if lipgloss.Width(text) <= width {
		return text
	}
	runes := []rune(text)
	for len(runes) > 0 && lipgloss.Width(string(runes)) > width {
		runes = runes[1:]
	}
	return string(runes)
}

func padRight(text string, width int) string {
	padding := width - lipgloss.Width(text)
	if padding <= 0 {
		return text
	}
	return text + strings.Repeat(" ", padding)
}
